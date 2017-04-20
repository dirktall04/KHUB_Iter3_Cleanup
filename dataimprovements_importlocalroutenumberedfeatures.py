#!/usr/bin/env python
# -*- coding:utf-8 -*-
# dataimprovements_importlocalroutenumberedfeatures.py
# Created by dirktall04 on 2017-03-27

import os

from arcpy import (AddField_management, CalculateField_management,
    CopyFeatures_management, Delete_management, DeleteFeatures_management,
    Describe, env, Exists, GetCount_management, MakeFeatureLayer_management,
    SelectLayerByAttribute_management, SelectLayerByLocation_management)

from arcpy.da import (SearchCursor as daSearchCursor,
    InsertCursor as daInsertCursor, UpdateCursor as daUpdateCursor)

from pathFunctions import (returnFeatureClass)

## Need to find a way to get the updates from the manual edit
## sessions into the All_Road_Centerlines feature class in
## a way that is easily repeatable and which allows blocking
## certain segments from migrating.

# Need to rerun this on the 

targetGDB1 = r'C:\GIS\Geodatabases\KHUB\Data_Mirroring_16D_AllRegions_Source.gdb'
##targetGDB2 = r'C:\GIS\Geodatabases\KHUB\Manual_Edit_Aggregation\2017-03-22\Data_Mirroring_14B_StateSystemOnly_IntegrationTest_Source.gdb'
###targetFCName1 = 'RoutesSource_CountyLRS_ARNOLD' ## -- Completed successfully 2017-03-27, 6:15PM
targetFCName1 = 'All_Road_Centerlines'
##targetFCName2 = 'All_Road_Centerlines'
targetFC1 = os.path.join(targetGDB1, targetFCName1)
##targetFC2 = os.path.join(targetGDB2, targetFCName2)
targetFC1asFeatureLayer = 'targetFC1asFeatureLayer'

##targetFeatureClasses = [targetFC1]#, targetFC2]

uniqueKeyFieldToUse = 'KDOT_LRS_KEY' # Also use the OID.

# Should be a spatial replacement, not a key based replacement, but still need to
# select a limited number of the features that we want to spatial select with in the
# source and then transfer them to the target after the spatial select & deletion
# have occurred.

# Fields to transfer = [KDOT_LRS_KEY, county_log_begin, county_log_end, LRS_ROUTE_NUM, _LRS_COUNTY_PRE, LRS_ROUTE_SUFFIX, LRS_ROUTE_PREFIX, LRS_UNIQUE_IDENT, LRS_UNIQUE_IDENT1, Non_State_System_LRSKey, Ramps_LRSKey, GCID, STEWARD, L_UPDATE, EFF_DATE, EXP_DATE, NGSEGID, RD, LABEL, KDOT_COUNTY_L, KDOT_COUNTY_R, KDOT_MUNI_L, KDOT_MUNI_R, 'SHAPE@']

fcWithroutesToTransferFrom = r'C:\GIS\Geodatabases\KHUB\LocalRoutesImprovement\Data_Mirroring_15B_AllRegions_Source.gdb\All_Road_Centerlines_Copy_Local_Dissolve'

lrsKeyToUse = 'KDOT_LRS_KEY'

from pathFunctions import (returnFeatureClass)

startMeasure = "county_log_begin"
endMeasure = "county_log_end"

# selectLocalRouteKeysInMultiSelection()
def transferBasedOnLocalRouteKeys():
    # Build a list of the unique route keys that match the given criteria:
    # Then, use that list to select the features in the source with those
    # keys.
    # Next, spatially select features in the target layer with the
    # selected features from the source layer.
    # If there are more than 0 features selected, delete the selected
    # target features.
    # Then, cursor in the selected source features.
    
    subsetSelectionQuery = """ KDOT_LRS_KEY LIKE '%L%' AND NOT KDOT_LRS_KEY LIKE '%W%' """
    
    fcAsFeatureLayerForTransferring = 'FCAsFeatureLayer_Transferring'
    
    if Exists(fcAsFeatureLayerForTransferring):
        Delete_management(fcAsFeatureLayerForTransferring)
    else:
        pass
    
    MakeFeatureLayer_management(fcWithroutesToTransferFrom, fcAsFeatureLayerForTransferring)
    MakeFeatureLayer_management(targetFC1, targetFC1asFeatureLayer)
    
    lrsKeyFieldList = [str(lrsKeyToUse)]
    newCursor = daSearchCursor(fcWithroutesToTransferFrom, lrsKeyFieldList, subsetSelectionQuery)
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
    ##multiDissolveFields = [str(lrsKeyToUse), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX', 'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX', 'LRS_UNIQUE_IDENT',
    ##    'LRS_UNIQUE_IDENT1', 'KDOT_COUNTY_L', 'KDOT_COUNTY_R']
    ##multiDissolveFields = str(lrsKeyToUse) + ';LRS_COUNTY_PRE;LRS_ROUTE_PREFIX;LRS_ROUTE_NUM;LRS_ROUTE_SUFFIX;LRS_UNIQUE_IDENT;LRS_UNIQUE_IDENT1'
    ##multiStatsFields = str(n1FromMeas) + " MIN;" + str(n1ToMeas) + " MAX"
    ##multiStatsFields = ""
    ##singlePart = "SINGLE_PART"
    ##unsplitLines = "UNSPLIT_LINES"
    
    # 3.) Loop through the list of unique LRS Keys
    for uniqueKeyItem in uniqueLRSKeysList:
        # Make a selection list that includes 50 keys, then select the keys and dissolve to make a new
        # feature class.
        # After the selection is dissolved, use a spatial select on the original feature class and
        # an attribute selection on the original feature class to see which original features should
        # be deleted.
        # Then, delete the selected features (if at least 1 selected).
        
        # Basically, doing it piece by piece is a problem since I'm not including LRS KEY
        # selections to prevent the spatial selection from deleting pieces that overlap, but
        # that should have different LRS Keys. Need to do all of the features
        # at once to make sure that I'm not deleting pieces that should actually be there.
        # Seems like it shouldn't be a problem, but the numbers say it is.
        # 4.) For groups of 200000 LRS Keys, select all the features with those LRS Keys.
        if multiCounter <= 199999:
            multiSelectionQuery += """'""" + str(uniqueKeyItem) + """'""" + """, """
            multiCounter += 1
        else:
            # Add the current item, then
            multiSelectionQuery += """'""" + str(uniqueKeyItem) + """'""" + """, """
            # Remove the trailing ", " and add a closing parenthesis.
            multiSelectionQuery = multiSelectionQuery[:-2] + """) """
            SelectLayerByAttribute_management(fcAsFeatureLayerForTransferring, "NEW_SELECTION", multiSelectionQuery)
            # Have to do from step 5 on here also.
            
            ### -shouldbeafunctionblock#1- ###
            # 5.) Count selected features.
            countResult0 = GetCount_management(fcAsFeatureLayerForTransferring)
            intCount0 = int(countResult0.getOutput(0))
            if intCount0 >= 1:
                print("Spatially selecting with the fcAsFeatureLayerForTransferring features, of which there are " + str(intCount0) + " selected.")
                ##print("Selected by this query:")
                ##print(str(multiSelectionQuery))
                # 9.) Else, spatially select features in the original feature class with 'SHARE_A_LINE_SEGMENT_WITH'.
                SelectLayerByLocation_management(targetFC1asFeatureLayer, "SHARE_A_LINE_SEGMENT_WITH", fcAsFeatureLayerForTransferring, 0, "NEW_SELECTION")
                # Added to prevent the Selection from taking over '%W%' routes at this time.
                SelectLayerByAttribute_management(targetFC1asFeatureLayer, "SUBSET_SELECTION", subsetSelectionQuery)
                
                # 10.) Count to make sure that at least one feature is selected.
                countResult2 = GetCount_management(targetFC1asFeatureLayer)
                intCount2 = int(countResult2.getOutput(0))
                print('There were ' + str(intCount2) + ' features selected for replacement in the targetFC1asFeatureLayer layer.')
                if intCount2 >= 1:
                    # 11.) If so, cursor the features out of the dissolve layer.
                    featureList = list()
                    searchCursorFields = [str(lrsKeyToUse), str(startMeasure), str(endMeasure), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX',
                        'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX', 'LRS_UNIQUE_IDENT', 'LRS_UNIQUE_IDENT1', 'KDOT_COUNTY_L', 'KDOT_COUNTY_R',
                        'LABEL', 'SHAPE@']
                    newCursor = daSearchCursor(fcAsFeatureLayerForTransferring, searchCursorFields)
                    
                    for cursorItem in newCursor:
                        featureList.append(list(cursorItem))
                    
                    try:
                        del newCursor
                    except:
                        pass
                    
                    # 12.) Delete the selected features in the input layer.
                    try:
                        DeleteFeatures_management(targetFC1asFeatureLayer)
                    except:
                        print("Could not delete features for the selection " + str(multiSelectionQuery) + ".")
                    # 13.) Insert the features from the dissolve layer into the copy of the centerlines.
                    insertCursorFields = [str(lrsKeyToUse), str(startMeasure), str(endMeasure), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX',
                        'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX', 'LRS_UNIQUE_IDENT', 'LRS_UNIQUE_IDENT1', 'KDOT_COUNTY_L', 'KDOT_COUNTY_R',
                        'LABEL', 'SHAPE@']
                    newCursor = daInsertCursor(targetFC1asFeatureLayer, insertCursorFields)
                    
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
            ### -shouldbeafunctionblock#1- ###
            multiSelectionQuery = ''' "''' + str(lrsKeyToUse) + '''" IS NOT NULL AND "''' + str(lrsKeyToUse) + '''" IN ('''
            multiCounter = 0
            
    
    # After the for loop, if there is still anything remaining which was unselected in the
    # the previous multiSelectionQuery steps.
    # Remove the trailing ", " and add a closing parenthesis.
    if multiSelectionQuery != multiSelectionQueryBase:
        multiSelectionQuery = multiSelectionQuery[:-2] + """) """
    else:
        # The selection query would not select anything.
        return
    SelectLayerByAttribute_management(fcAsFeatureLayerForTransferring, "NEW_SELECTION", multiSelectionQuery)    
    
    # Then redo from step 5 on at the end of the loop IF there is anything left to select
    # which was not selected... so if selectionCounter != 0.
    
    ### -shouldbeafunctionblock#2- ###
    # 5.) Count selected features.
    countResult0 = GetCount_management(fcAsFeatureLayerForTransferring)
    intCount0 = int(countResult0.getOutput(0))
    if intCount0 >= 1:
        print("Spatially selecting with the fcAsFeatureLayerForTransferring features, of which there are " + str(intCount0) + " selected.")
        ##print("Selected by this query:")
        ##print(str(multiSelectionQuery))
        # 9.) Else, spatially select features in the original feature class with 'SHARE_A_LINE_SEGMENT_WITH'.
        SelectLayerByLocation_management(targetFC1asFeatureLayer, "SHARE_A_LINE_SEGMENT_WITH", fcAsFeatureLayerForTransferring, 0, "NEW_SELECTION")
        # Added to prevent the Selection from taking over '%W%' routes at this time.
        SelectLayerByAttribute_management(targetFC1asFeatureLayer, "SUBSET_SELECTION", subsetSelectionQuery)
        
        # 10.) Count to make sure that at least one feature is selected.
        countResult2 = GetCount_management(targetFC1asFeatureLayer)
        intCount2 = int(countResult2.getOutput(0))
        print('There were ' + str(intCount2) + ' features selected for replacement in the targetFC1asFeatureLayer layer.')
        if intCount2 >= 1:
            # 11.) If so, cursor the features out of the dissolve layer.
            featureList = list()
            searchCursorFields = [str(lrsKeyToUse), str(startMeasure), str(endMeasure), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX',
                'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX', 'LRS_UNIQUE_IDENT', 'LRS_UNIQUE_IDENT1', 'KDOT_COUNTY_L', 'KDOT_COUNTY_R',
                'LABEL', 'SHAPE@']
            newCursor = daSearchCursor(fcAsFeatureLayerForTransferring, searchCursorFields)
            
            for cursorItem in newCursor:
                featureList.append(list(cursorItem))
            
            try:
                del newCursor
            except:
                pass
            
            # 12.) Delete the selected features in the input layer.
            try:
                DeleteFeatures_management(targetFC1asFeatureLayer)
            except:
                print("Could not delete features for the selection " + str(multiSelectionQuery) + ".")
            # 13.) Insert the features from the dissolve layer into the copy of the centerlines.
            insertCursorFields = [str(lrsKeyToUse), str(startMeasure), str(endMeasure), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX',
                'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX', 'LRS_UNIQUE_IDENT', 'LRS_UNIQUE_IDENT1', 'KDOT_COUNTY_L', 'KDOT_COUNTY_R',
                'LABEL', 'SHAPE@']
            newCursor = daInsertCursor(targetFC1asFeatureLayer, insertCursorFields)
            
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

if __name__ == "__main__":
    transferBasedOnLocalRouteKeys()

else:
    pass