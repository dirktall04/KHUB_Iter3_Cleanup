#!/usr/bin/env python
# -*- coding:utf-8 -*-
# dataimprovements_dissolveandmeasurelocalroutes.py
# Created by dirktall04 on 2017-03-22

## Start using data that has been preprocessed to give better local route
## keys. The route keys are currently being calculated. Need to concat them
## next, then dissolve based on them. After the dissolves, will need to calculate
## their mileage based on shapelength for the dissolved features.

# For features which match the feature query given in the local route renumbering
# script. I need you to concatenate new route keys from their constituent parts.
# Then, for that same set of features only, dissolve each one and update the
# feature class so that if there is a long stretch of segments that all
# share the same new route key, they will all become one segment (hopefully singlepart).
# Next, calculate each feature's start and end mileage with 0 and shapelength.
# Then, the features should be ready to be used in the next parts of the script.

# Should also carry forward the 'LABEL' field.

from arcpy import (CalculateField_management, Delete_management,
    DeleteFeatures_management, Describe, Dissolve_management,
    env, Exists, GetCount_management, MakeFeatureLayer_management,
    SelectLayerByAttribute_management, SelectLayerByLocation_management)

from arcpy.da import SearchCursor as daSearchCursor, InsertCursor as daInsertCursor, UpdateCursor as daUpdateCursor

fcWithLocalRoutesToDissolveAndMeasure = r'C:\GIS\Geodatabases\KHUB\LocalRoutesImprovement\Data_Mirroring_15B_AllRegions_Source.gdb\All_Road_Centerlines_Copy_Local_Dissolve'

lrsKeyToUse = 'KDOT_LRS_KEY'

dissolveOutFC = 'in_memory\Dissolved_Temp_Features'

from datareviewerchecks_config import (dissolveErrorsFile, nullable)

from pathFunctions import (returnFeatureClass)

startMeasure = "county_log_begin"
endMeasure = "county_log_end"

# concatLocalRouteKeys()
def main():
    # Do this by county.
    # Get a list of all of the available county numbers.
    # Then create an updateCursor for each county, using
    # a selection that looks at the LRS_COUNTY_PRE and LRS_PREFIX or existing KDOT_LRS_KEY.
    tempDesc = Describe(fcWithLocalRoutesToDissolveAndMeasure)
    print("Updating the concatenated LRS Key Field and start/end measures for selected features in " + returnFeatureClass(tempDesc.catalogPath) + ".")
    OIDFieldName = str(tempDesc.OIDFieldName)
    
    try:
        del tempDesc
    except:
        pass
    
    uniqueCountyCodeDict = dict()
    countyCodeFieldsList = ['KDOT_COUNTY_L', 'KDOT_COUNTY_R']
    newCursor = daSearchCursor(fcWithLocalRoutesToDissolveAndMeasure, countyCodeFieldsList)
    for cursorRow in newCursor:
        uniqueCountyCodeDict[str(cursorRow[0])] = 1
        uniqueCountyCodeDict[str(cursorRow[1])] = 1
    
    try:
        del newCursor
    except:
        pass
    
    uniqueCountyCodeList = list()
    
    for uniqueCountyCode in uniqueCountyCodeDict.keys():
        uniqueCountyCodeList.append(uniqueCountyCode)
    
    try:
        del uniqueCountyCodeDict
    except:
        pass
    
    try:
        uniqueCountyCodeList.remove('None')
    except:
        pass
    
    sortedUniqueCountyCodes = sorted(uniqueCountyCodeList) # No need to specify a key since it's one column.
    
    for uniqueCountyCodeItem in sortedUniqueCountyCodes:
        print('Selecting features based on countyCode: ' + str(uniqueCountyCodeItem) + '.')
        routeFeaturesList = list()
        
        listOfFieldsToUse = [OIDFieldName, 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX', 'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX',
            'LRS_UNIQUE_IDENT', 'LRS_UNIQUE_IDENT1', lrsKeyToUse]
        
        # Modified from the original localroutenumbering sql to include an exception for '%W%' routes, because I don't think that those
        # were included in the localroutenumbering, even though they should have been.
        selectionQuery1 = """ KDOT_COUNTY_L = '""" + str(uniqueCountyCodeItem) + """' AND (((KDOT_LRS_KEY IS NULL AND LRS_ROUTE_PREFIX = 'L') OR KDOT_LRS_KEY LIKE '%L%') AND NOT KDOT_LRS_KEY LIKE '%W%') """
        selectionQuery2 = """ KDOT_COUNTY_L IS NULL AND KDOT_COUNTY_R = '""" + str(uniqueCountyCodeItem) + """' AND (((KDOT_LRS_KEY IS NULL AND LRS_ROUTE_PREFIX = 'L') OR KDOT_LRS_KEY LIKE '%L%') AND NOT KDOT_LRS_KEY LIKE '%W%') """
        
        newCursor = daUpdateCursor(fcWithLocalRoutesToDissolveAndMeasure, listOfFieldsToUse, selectionQuery1)
        for cursorRow in newCursor:
            cursorListItem = list(cursorRow)
            # change each cursorRow to a list
            # then pass the list to a function that concats the parts
            # into the LRS key field.
            concattedKeyListItem = concatTheLRSParts(cursorListItem, uniqueCountyCodeItem)
            # Receive the list back and use it to update the
            # row.
            newCursor.updateRow(concattedKeyListItem)
        
        try:
            del newCursor
        except:
            pass
        
        newCursor = daUpdateCursor(fcWithLocalRoutesToDissolveAndMeasure, listOfFieldsToUse, selectionQuery2)
        for cursorRow in newCursor:
            cursorListItem = list(cursorRow)
            # change each cursorRow to a list
            # then pass the list to a function that concats the parts
            # into the LRS key field.
            concattedKeyListItem = concatTheLRSParts(cursorListItem, uniqueCountyCodeItem)
            # Receive the list back and use it to update the
            # row.
            newCursor.updateRow(concattedKeyListItem)
        
        try:
            del newCursor
        except:
            pass
        
        # At this point, all of the local features in a county should have had
        # their LRS keys updated.
        # What we need to do now is to dissolve them based on LRS key.
        dissolveBasedOnLocalRouteKeys(fcWithLocalRoutesToDissolveAndMeasure, selectionQuery1)
        dissolveBasedOnLocalRouteKeys(fcWithLocalRoutesToDissolveAndMeasure, selectionQuery2)
        
        # At this point, all of the local featuers should be dissolved into
        # single part lines.
        # Go ahead and add the measures based on 0-to-shapelength.
        calculateMeasuresForLocalRoutes(fcWithLocalRoutesToDissolveAndMeasure, selectionQuery1)
        calculateMeasuresForLocalRoutes(fcWithLocalRoutesToDissolveAndMeasure, selectionQuery2)
        


def concatTheLRSParts(passedInList, countyCodeToUse):
    ##print('passedInList = ' + str(passedInList))
    #LRS_COUNTY_PRE     (3)
    part1 = str(countyCodeToUse).zfill(3)
    passedInList[1] = part1
    # Fixing an oversight in the localroutenumbering script.
    '''part1 = ''
    if passedInList[1] is None:
        part1 = '000'
    else:
        part1 = str(passedInList[1]).zfill(3)
    '''
    
    #LRS_PREFIX		    (1)
    part2 = ''
    if passedInList[2] is None:
        part2 = '0'
    else:
        part2 = str(passedInList[2])
    
    #LRS_NUMBER		    (5)
    part3 = ''
    if passedInList is None:
        part3 = '00000'
    else:
        part3 = str(passedInList[3]).zfill(5)
    
    #LRS_SUFFIX		    (1)
    part4 = ''
    if passedInList[4] is None:
        part4 = '0'
    else:
        part4 = str(passedInList[4])
    
    #LRS_UNIQUE_ID		(1)
    part5 = ''
    if passedInList[5] is None:
        part5 = '0'
    else:
        part5 = str(passedInList[5]).zfill(1)
    
    #LRS_UNIQUE_ID1		(2)
    part6 = ''
    if passedInList[6] is None:
        part6 = '00'
    else:
        part6 = str(passedInList[6]).zfill(2)
    
    lrsRouteKeyToUpdate = part1 + part2 + part3 + part4 + part5 + part6
    print("The updated route key is: " + str(lrsRouteKeyToUpdate) + ".")
    passedInList[7] = lrsRouteKeyToUpdate
    
    return passedInList


# selectLocalRouteKeysInMultiSelection()
def dissolveBasedOnLocalRouteKeys(routesToDissolve, subsetSelectionQuery):
    # Moved out the selection building code to the other function where
    # it makes more sense.
    # Use similar code here to what is found in the main dissolve loop.
    # Just need to do multiselection on all of the possible routes that
    # match the subsetSelectionQuery and for each multiselection, create
    # a dissolve feature set, then use the same reintroduction tests
    # that are used in the main dissolve to reintroduce the dissolved
    # lines without removing any that weren't dissolved or adding
    # any new overlaps.
    
    fcAsFeatureLayerForDissolves = 'FCAsFeatureLayer_Dissolves'
    
    if Exists(fcAsFeatureLayerForDissolves):
        Delete_management(fcAsFeatureLayerForDissolves)
    else:
        pass
    
    MakeFeatureLayer_management(routesToDissolve, fcAsFeatureLayerForDissolves)
    
    lrsKeyFieldList = [str(lrsKeyToUse)]
    newCursor = daSearchCursor(routesToDissolve, lrsKeyFieldList, subsetSelectionQuery)
    uniqueLRSKeysDict = dict()
    for cursorRow in newCursor:
        uniqueLRSKeysDict[str(cursorRow[0])] = 1
    
    try:
        del newCursor
    except:
        pass
    
    uniqueLRSKeysList = uniqueLRSKeysDict.keys()
    try:
        uniqueLRSKeysList.remove('None')
    except:
        print("Could not remove 'None' from the list of uniqueLRSKeys since it was not a part of the list.")
    
    print("LRSKey list creation successful.")
    print('Found ' + str(len(uniqueLRSKeysList)) + ' unique LRS Keys in the centerline data for this query:')
    print(str(subsetSelectionQuery))
    
    #Use multiSelection
    
    multiSelectionQueryBase = str(str(subsetSelectionQuery) + ''' AND ''' + ''' "''' + str(lrsKeyToUse) + '''" IS NOT NULL AND "''' + str(lrsKeyToUse) +
        '''" IN (''')
    multiSelectionQuery = multiSelectionQueryBase
    multiCounter = 0
    multiDissolveFields = [str(lrsKeyToUse), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX', 'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX', 'LRS_UNIQUE_IDENT',
        'LRS_UNIQUE_IDENT1', 'KDOT_COUNTY_L', 'KDOT_COUNTY_R']
    ##multiDissolveFields = str(lrsKeyToUse) + ';LRS_COUNTY_PRE;LRS_ROUTE_PREFIX;LRS_ROUTE_NUM;LRS_ROUTE_SUFFIX;LRS_UNIQUE_IDENT;LRS_UNIQUE_IDENT1'
    ##multiStatsFields = str(n1FromMeas) + " MIN;" + str(n1ToMeas) + " MAX"
    multiStatsFields = ""
    singlePart = "SINGLE_PART"
    unsplitLines = "UNSPLIT_LINES"
    
    # 3.) Loop through the list of unique LRS Keys
    for uniqueKeyItem in uniqueLRSKeysList:
        # Make a selection list that includes 50 keys, then select the keys and dissolve to make a new
        # feature class.
        # After the selection is dissolved, use a spatial select on the original feature class and
        # an attribute selection on the original feature class to see which original features should
        # be deleted.
        # Then, delete the selected features (if at least 1 selected).
        #
        try:
            Delete_management(dissolveOutFC)
        except:
            print("Could not delete the dissolveOutFC layer.")
        
        # 4.) For groups of 2000 LRS Keys, select all the features with those LRS Keys.
        if multiCounter <= 1999:
            multiSelectionQuery += """'""" + str(uniqueKeyItem) + """'""" + """, """
            multiCounter += 1
        else:
            # Add the current item, then
            multiSelectionQuery += """'""" + str(uniqueKeyItem) + """'""" + """, """
            # Remove the trailing ", " and add a closing parenthesis.
            multiSelectionQuery = multiSelectionQuery[:-2] + """) """
            SelectLayerByAttribute_management(fcAsFeatureLayerForDissolves, "NEW_SELECTION", multiSelectionQuery)
            # Have to do from step 5 on here also.
            
            ### -shouldbeafunctionblock#1- ###
            # 5.) Count selected features.
            countResult0 = GetCount_management(fcAsFeatureLayerForDissolves)
            intCount0 = int(countResult0.getOutput(0))
            if intCount0 >= 1:
                # 6.) Make a new layer or dissolved layer from this selection.
                Dissolve_management(fcAsFeatureLayerForDissolves, dissolveOutFC, multiDissolveFields, multiStatsFields, singlePart, unsplitLines)
                
                # 7.) Count the number of dissolved features.
                countResult1 = GetCount_management(dissolveOutFC)
                intCount1 = int(countResult1.getOutput(0))
                print('Counted ' + str(intCount1) + ' features returned for that dissolve.')
                # 8a.) If the number of dissolved features is 0, then append the error to the error file
                #       and go on to the next LRS Key in the loop.
                if intCount1 == 0:
                    with open(dissolveErrorsFile, 'a') as errorFile:
                        errorFile.write(str(multiSelectionQuery))
                # 8b.) From the spatial select, select the subset of features that also have a matching LRS Key.
                else:
                    SelectLayerByAttribute_management(fcAsFeatureLayerForDissolves, 'NEW_SELECTION', multiSelectionQuery)
                    # 9.) Else, spatially select features in the original feature class with 'SHARE_A_LINE_SEGMENT_WITH'.
                    SelectLayerByLocation_management(fcAsFeatureLayerForDissolves, 'SHARE_A_LINE_SEGMENT_WITH', dissolveOutFC, 0, 'SUBSET_SELECTION')
                    # 10.) Count to make sure that at least one feature is selected.
                    countResult2 = GetCount_management(fcAsFeatureLayerForDissolves)
                    intCount2 = int(countResult2.getOutput(0))
                    print('There were ' + str(intCount2) + ' features selected for replacement in the fcAsFeatureLayerForDissolves layer.')
                    if intCount2 >= 1:
                        # 11.) If so, cursor the features out of the dissolve layer.
                        featureList = list()
                        searchCursorFields = [str(lrsKeyToUse), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX', 'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX',
                            'LRS_UNIQUE_IDENT', 'LRS_UNIQUE_IDENT1', 'KDOT_COUNTY_L', 'KDOT_COUNTY_R', 'SHAPE@']
                        newCursor = daSearchCursor(dissolveOutFC, searchCursorFields)
                        
                        for cursorItem in newCursor:
                            featureList.append(list(cursorItem))
                        
                        try:
                            del newCursor
                        except:
                            pass
                        
                        # 12.) Delete the selected features in the input layer.
                        try:
                            DeleteFeatures_management(fcAsFeatureLayerForDissolves)
                        except:
                            print("Could not delete features for the selection " + str(multiSelectionQuery) + ".")
                        # 13.) Insert the features from the dissolve layer into the copy of the centerlines.
                        insertCursorFields = [str(lrsKeyToUse), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX', 'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX',
                            'LRS_UNIQUE_IDENT', 'LRS_UNIQUE_IDENT1', 'KDOT_COUNTY_L', 'KDOT_COUNTY_R', 'SHAPE@']
                        newCursor = daInsertCursor(fcAsFeatureLayerForDissolves, insertCursorFields)
                        
                        for featureItem in featureList:
                            newCursor.insertRow(featureItem)
                        
                        try:
                            del newCursor
                        except:
                            pass
                        try:
                            del featureList
                        except:
                            pass
                    else:
                        pass
            multiSelectionQuery = ''' "''' + str(lrsKeyToUse) + '''" IS NOT NULL AND "''' + str(lrsKeyToUse) + '''" IN ('''
            multiCounter = 0
            ### -shouldbeafunctionblock#1- ###
    
    # After the for loop, if there is still anything remaining which was unselected in the
    # the previous multiSelectionQuery steps.
    # Remove the trailing ", " and add a closing parenthesis.
    if multiSelectionQuery != multiSelectionQueryBase:
        multiSelectionQuery = multiSelectionQuery[:-2] + """) """
    else:
        # The selection query would not select anything.
        return
    SelectLayerByAttribute_management(fcAsFeatureLayerForDissolves, "NEW_SELECTION", multiSelectionQuery)    
    
    # Then redo from step 5 on at the end of the loop IF there is anything left to select
    # which was not selected... so if selectionCounter != 0.
    
    ### -shouldbeafunctionblock#2- ###
    # 5.) Count selected features.
    countResult0 = GetCount_management(fcAsFeatureLayerForDissolves)
    intCount0 = int(countResult0.getOutput(0))
    if intCount0 >= 1:
        # 6.) Make a new layer or dissolved layer from this selection. -- Question about fields.
        Dissolve_management(fcAsFeatureLayerForDissolves, dissolveOutFC, multiDissolveFields, multiStatsFields, singlePart, unsplitLines)
        
        # 7.) Count the number of dissolved features.
        countResult1 = GetCount_management(dissolveOutFC)
        intCount1 = int(countResult1.getOutput(0))
        print('Counted ' + str(intCount1) + ' features returned for that dissolve.')
        # 8a.) If the number of dissolved features is 0, then append the error to the error file
        #       and go on to the next LRS Key in the loop.
        if intCount1 == 0:
            with open(dissolveErrorsFile, 'a') as errorFile:
                errorFile.write(str(multiSelectionQuery))
        # 8b.) From the spatial select, select the subset of features that also have a matching LRS Key.
        else:
            SelectLayerByAttribute_management(fcAsFeatureLayerForDissolves, 'NEW_SELECTION', multiSelectionQuery)
            # 9.) Else, spatially select features in the original feature class with 'SHARE_A_LINE_SEGMENT_WITH'.
            SelectLayerByLocation_management(fcAsFeatureLayerForDissolves, 'SHARE_A_LINE_SEGMENT_WITH', dissolveOutFC, 0, 'SUBSET_SELECTION')
            # 10.) Count to make sure that at least one feature is selected.
            countResult2 = GetCount_management(fcAsFeatureLayerForDissolves)
            intCount2 = int(countResult2.getOutput(0))
            print('There were ' + str(intCount2) + ' features selected in the fcAsFeatureLayerForDissolves layer.')
            if intCount2 >= 1:
                # 11.) If so, cursor the features out of the dissolve layer.
                featureList = list()
                searchCursorFields = [str(lrsKeyToUse), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX', 'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX',
                    'LRS_UNIQUE_IDENT', 'LRS_UNIQUE_IDENT1', 'KDOT_COUNTY_L', 'KDOT_COUNTY_R', 'SHAPE@']
                newCursor = daSearchCursor(dissolveOutFC, searchCursorFields)
                
                for cursorItem in newCursor:
                    featureList.append(list(cursorItem))
                
                try:
                    del newCursor
                except:
                    pass
                
                # 12.) Delete the selected features in the input layer.
                try:
                    DeleteFeatures_management(fcAsFeatureLayerForDissolves)
                except:
                    print("Could not delete features for the selection " + str(multiSelectionQuery) + ".")
                # 13.) Insert the features from the dissolve layer into the copy of the centerlines.
                insertCursorFields = [str(lrsKeyToUse), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX', 'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX',
                    'LRS_UNIQUE_IDENT', 'LRS_UNIQUE_IDENT1', 'KDOT_COUNTY_L', 'KDOT_COUNTY_R', 'SHAPE@']
                newCursor = daInsertCursor(fcAsFeatureLayerForDissolves, insertCursorFields)
                
                for featureItem in featureList:
                    newCursor.insertRow(featureItem)
                
                try:
                    del newCursor
                except:
                    pass
                try:
                    del featureList
                except:
                    pass
            else:
                pass
    ### -shouldbeafunctionblock#2- ###


def calculateMeasuresForLocalRoutes(routesToMeasure, subsetSelectionQuery):
    # Make a feature layer
    # Select it with the subsetSelectionQuery
    # If the number of selected features is at least 1
    # Then, run the calculateField_management calls for
    # the selected features.
    fcAsFeatureLayerForMeasuring = 'FCAsFeatureLayer_Measures'
    
    if Exists(fcAsFeatureLayerForMeasuring):
        Delete_management(fcAsFeatureLayerForMeasuring)
    else:
        pass
    
    MakeFeatureLayer_management(routesToMeasure, fcAsFeatureLayerForMeasuring)
    
    SelectLayerByAttribute_management(fcAsFeatureLayerForMeasuring, 'CLEAR_SELECTION')
    SelectLayerByAttribute_management(fcAsFeatureLayerForMeasuring, 'NEW_SELECTION', subsetSelectionQuery)
    
    countResult = GetCount_management(fcAsFeatureLayerForMeasuring)
    intCount = int(countResult.getOutput(0))
    print('There were ' + str(intCount) + ' features selected in the fcAsFeatureLayerForMeasuring layer.')
    if intCount >= 1:
        expressionText1 = 0
        CalculateField_management(fcAsFeatureLayerForMeasuring, startMeasure, expressionText1, "PYTHON_9.3")
        expressionText2 = 'float("{0:.3f}".format(!Shape_Length! / 5280.00))'
        CalculateField_management(fcAsFeatureLayerForMeasuring, endMeasure, expressionText2, "PYTHON_9.3")
    else:
        print "Not calculating due to lack of selected features."


if __name__ == "__main__":
    main()

else:
    pass