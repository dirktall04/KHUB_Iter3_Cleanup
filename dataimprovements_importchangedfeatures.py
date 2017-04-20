#!/usr/bin/env python
# -*- coding:utf-8 -*-
# dataimprovements_importchangedfeatures.py
# Created by dirktall04 on 2017-03-13

import os

from arcpy import (AddField_management, CopyFeatures_management,
    Delete_management, DeleteFeatures_management,
    Describe, Exists, GetCount_management, MakeFeatureLayer_management,
    SelectLayerByAttribute_management, SelectLayerByLocation_management)

from arcpy.da import (SearchCursor as daSearchCursor,
    InsertCursor as daInsertCursor, UpdateCursor as daUpdateCursor)

from datareviewerchecks_config import (nullable)

from pathFunctions import (returnFeatureClass)

## Need to find a way to get the updates from the manual edit
## sessions into the All_Road_Centerlines feature class in
## a way that is easily repeatable and which allows blocking
## certain segments from migrating.

targetGDB1 = r'C:\GIS\Geodatabases\KHUB\Manual_Edit_Aggregation\2017-03-22\Data_Mirroring_14B_AllRegions_IntegrationTest_Source.gdb'
targetGDB2 = r'C:\GIS\Geodatabases\KHUB\Manual_Edit_Aggregation\2017-03-22\Data_Mirroring_14B_StateSystemOnly_IntegrationTest_Source.gdb'
targetFCName1 = 'All_Road_Centerlines'
targetFCName2 = 'All_Road_Centerlines'
targetFC1 = os.path.join(targetGDB1, targetFCName1)
targetFC2 = os.path.join(targetGDB2, targetFCName2)

targetFeatureClasses = [targetFC1, targetFC2]

changeSourceGDB = r'C:\GIS\Geodatabases\KHUB\Manual_Edit_Aggregation\2017-03-08\ModifiedRoadCenterlinesManual_roads.gdb'
changeSourceFCName = 'NG\RoadCenterlines'
changeSource = os.path.join(changeSourceGDB, changeSourceFCName)

changeSourceWithCommentsGDB = r'C:\GIS\Geodatabases\KHUB\Manual_Edit_Aggregation\2017-03-08\ModifiedRoadCenterlinesManual.gdb'
changeSourceWithCommentsFCName = 'CombinedEdits_20170308'
changeSourceWithComments = os.path.join(changeSourceGDB, changeSourceFCName)

listOfSegmentsToNotMigrate = ['11481', '324451']

GCIDFieldName = 'GCID'

uniqueKeyFieldToUse = 'GCID' # Also use the OID.

# Only migrate pieces that are in the current features, which should
# allow the StateSystemOnly feature class to be easy to manage.
# If not, rerun the StateSystemOnly selection for that feature class.

# Probably want to do this as part of the process improvements, so make this
# importable and have it accept a feature class which is passed in,
# to work on. 

# Also include a way to filter based on the kind of comment that is received.
# Maybe that can be the list of segments to not migrate. -- I.E. if the
# column contains something like '%Kyle or Bill need to review%'
# then, don't migrate it.

# Otherwise, use the GCID and a nearby sort of spatial select to see if the
# piece should be migrated.

# Also, if GCID == StewardID, OR the GCID doesn't include a space, OR the SEGID is NULL,
# then flag the segment for review as the road segment is most likely incorrect.
def importCommentsToChangedSource(sourceWithComments, targetToHaveCommentsAdded):
    # Since I forgot to ask that the ReviewUser and ReviewInfo fields be kept, need to get the
    # data back. Thankfully, it appears to still be in the same objectID order, so we can
    # use that and the GCIDs to try to transfer it over, then make additional quality checks
    # to be sure that the transfer was successful and did not introduce any errors.
    # 0.) Add the ReviewUser and ReviewInfo fields to the copy if they do not already exist.
    #       That way, the information from the edits can flow through to future edit sessions
    #       and error checks.
    tfcDesc = Describe(targetToHaveCommentsAdded)
    tfcFields = tfcDesc.fields
    tfcFieldNames = [x.name for x in tfcFields]
    
    try:
        del tfcDesc
    except:
        pass
    
    # Check for ReviewUser field in the targetFeaturesCopy, then add it if missing.
    if 'ReviewUser' not in tfcFieldNames:
        #ReviewUser (String, 50)
        AddField_management(targetToHaveCommentsAdded, 'ReviewUser', "TEXT", "", "", 50, 'ReviewUser', nullable)
    else:
        pass
    
    # Check for ReviewInfo field in the targetFeaturesCopy, then add it if missing.
    if 'ReviewInfo' not in tfcFieldNames:
        #ReviewInfo (String, 250)
        AddField_management(targetToHaveCommentsAdded, 'ReviewInfo', "TEXT", "", "", 250, 'ReviewInfo', nullable)
    else:
        pass
    
    tfcUpdatedDesc = Describe(targetToHaveCommentsAdded)
    tfcUpdatedFields = tfcUpdatedDesc.fields
    tfcUpdatedOIDFieldName = tfcUpdatedDesc.OIDFieldName
    tfcUpdatedFieldNames = [x.name for x in tfcUpdatedFields]
    
    try:
        del tfcUpdatedDesc
    except:
        pass
    try:
        tfcUpdatedFieldNames.remove(tfcUpdatedOIDFieldName)
    except:
        pass
    try:
        tfcUpdatedFieldNames.remove(GCIDFieldName)
    except:
        pass
    
    tfcUpdatedFieldNames.append(tfcUpdatedOIDFieldName)
    tfcUpdatedFieldNames.append(GCIDFieldName)
    
    swcDesc = Describe(sourceWithComments)
    swcFields = swcDesc.fields
    swcOIDFieldName = swcDesc.OIDFieldName
    swcFieldNames = [x.name for x in swcFields]
    
    try:
        del swcDesc
    except:
        pass
    try:
        swcFieldNames.remove(swcOIDFieldName)
    except:
        pass
    try:
        swcFieldNames.remove(GCIDFieldName)
    except:
        pass
    
    swcFieldNames.append(swcOIDFieldName) # Add the OIDFieldName so that it is the 2nd to last
    swcFieldNames.append(GCIDFieldName) # Add 'GCID' so that it is the last
    
    sharedFieldNames = [x for x in tfcUpdatedFieldNames if x in swcFieldNames]
    
    # 1.) Use a searchCursor to pull the sourceWithComments features, including the OID and their GCID.
    withCommentsList = list()
    newCursor = daSearchCursor(sourceWithComments, sharedFieldNames)
    
    for cursorRow in newCursor:
        withCommentsList.append(cursorRow)
    
    try:
        del newCursor
    except:
        pass
    
    print("The sharedFieldNames are: " + str(sharedFieldNames) + ".")
    # 2.) Use an updateCursor to match the pulled rows and update the target rows with the ReviewUser and ReviewInfo.
    newCursor = daUpdateCursor(targetToHaveCommentsAdded, sharedFieldNames)
    
    for cursorRow in newCursor:
        for commentedRowItem in withCommentsList:
            if cursorRow[-1] == commentedRowItem[-1] and cursorRow[-2] == commentedRowItem[-2]:
                print ('Updating a row with GCID: ' + str(cursorRow[-1]) + ' and OID: ' + str(cursorRow[-2]) + '.')
                newCursor.updateRow(commentedRowItem)
    
    try:
        del newCursor
    except:
        pass


def changedFeaturesImport(sourceFeatures, targetFeatures):
    # 1.) Make an in_memory copy of the centerlines.
    #### A field map would have to be created for each dissolved feature layer, so it's not really worth it.
    # 2.) Get a list of all of the unique Keys
    # 3.) Loop through the list of unique Keys
    # 4.) For each Key, select all the features with that Key.
    # 5.) Count selected features.
    # 6.) Make a new layer or dissolved layer from this selection.
    # 7.) Count the number of dissolved features.
    # 8a.) If the number of dissolved features is 0, then append the error to the error file
    #       and go on to the next Key in the loop.
    # 8b.) Else, spatially select features in the original feature class with 'SHARE_A_LINE_SEGMENT_WITH'.
    # 9.) From the spatial select, reselect features that have the same Key.
    # 10.) Count to make sure that at least one feature is selected.
    # 11.) If so, delete that feature.
    # 12.) Cursor the features out of the dissolve layer.
    # 13.) Insert the features from the dissolve layer into the in_memory copy of the centerlines.
    # 14.) When the loop is complete, save the in_memory copy of the centerlines
    #       to a gdb on disk.
    
    # Won't work for shapefiles. Hopefully you're not using those though.
    targetFeaturesCopy = targetFeatures + '_Copy'
    try:
        del targetFeatureLayer
    except:
        pass
    targetFeatureLayer = returnFeatureClass(targetFeaturesCopy) + '_FL'
    try:
        del sourceFeatureLayer
    except:
        pass
    sourceFeatureLayer = returnFeatureClass(sourceFeatures) + '_FL'
    
    # Perform cleanup to prevent object creation collisions.
    layersOrFCsToRemove = [targetFeaturesCopy, targetFeatureLayer, sourceFeatureLayer]
    for layerOrFCItem in layersOrFCstoRemove:
        if Exists(layerOrFCItem):
            try:
                Delete_management(layerOrFCItem)
            except:
                pass
        else:
            pass
    
    # 1a.) Make an copy of the simplified and flipped centerlines to modify with dissolves.
    CopyFeatures_management(targetFeatures, targetFeaturesCopy)
    
    # 1b.) Add the ReviewUser and ReviewInfo fields to the copy if they do not already exist.
    #       That way, the information from the edits can flow through to future edit sessions
    #       and error checks.
    tfcDesc = Describe(targetFeaturesCopy)
    tfcFields = tfcDesc.fields
    tfcFieldNames = [x.name for x in tfcFields]
    
    # Check for ReviewUser field in the targetFeaturesCopy, then add it if missing.
    if 'ReviewUser' not in tfcFieldNames:
        #ReviewUser (String, 50)
        AddField_management(targetFeaturesCopy, 'ReviewUser', "TEXT", "", "", 50, 'ReviewUser', nullable)
    else:
        pass
    
    # Check for ReviewInfo field in the targetFeaturesCopy, then add it if missing.
    if 'ReviewInfo' not in tfcFieldNames:
        #ReviewInfo (String, 250)
        AddField_management(targetFeaturesCopy, 'ReviewInfo', "TEXT", "", "", 250, 'ReviewInfo', nullable)
    else:
        pass
    
    sourceSelectionQuery = ''' "''' + str(uniqueKeyFieldToUse) + '''" IS NOT NULL AND "''' + str(uniqueKeyFieldToUse) + '''" IN ('''
    sourceSelectionQuery = sourceSelectionQuery[:-2] + ''') '''
    
    MakeFeatureLayer_management(targetFeaturesCopy, targetFeatureLayer)
    MakeFeatureLayer_management(sourceFeatures, sourceFeatureLayer)
    
    # 2.) Get a list of all of the unique Keys in the source.
    ############ Modify this process to only get a list of Keys that have more than one feature.
    ############ everything else can be skipped for the purpose of dissolving.
    uniqueKeyFieldList = [str(uniqueKeyFieldToUse)]
    newCursor = daSearchCursor(sourceFeatureLayer, uniqueKeyFieldList)
    uniqueKeysDict = dict()
    for cursorRow in newCursor:
        uniqueKeysDict[str(cursorRow[0])] = 1
    
    try:
        del newCursor
    except:
        pass
    
    uniqueKeysList = uniqueKeysDict.keys()
    try:
        uniqueKeysList.remove('None')
    except:
        print("Could not remove 'None' from the list of uniqueKeys since it was not a part of the list.")
    
    print("Unique Key list creation successful.")
    print('Found ' + str(len(uniqueKeysList)) + ' unique Keys in the changed features.')
    
    #Use multiSelection instead.
    multiSelectionQuery = ''' "''' + str(uniqueKeyFieldToUse) + '''" IS NOT NULL AND "''' + str(uniqueKeyFieldToUse) + '''" IN ('''
    multiCounter = 0
    
    # 3.) Loop through the list of unique Keys
    for uniqueKeyItem in uniqueKeysList:
        # 4.) For groups of 2000 Keys, select all the features with those Keys.
        if multiCounter <= 1999:
            multiSelectionQuery += """'""" + str(uniqueKeyItem) + """'""" + """, """
            multiCounter += 1
        else:
            # Add the current item
            multiSelectionQuery += """'""" + str(uniqueKeyItem) + """'""" + """, """
            # Then, remove the trailing ", " and add a closing parenthesis.
            multiSelectionQuery = multiSelectionQuery[:-2] + ''') '''
            
            featureReplacement(sourceFeatureLayer, targetFeatureLayer, multiSelectionQuery)
            
            multiSelectionQuery = ''' "''' + str(uniqueKeyFieldToUse) + '''" IS NOT NULL AND "''' + str(uniqueKeyFieldToUse) + '''" IN ('''
            multiCounter = 0
    
    # After the for loop, if there is still anything remaining which was unselected in the
    # the previous multiSelectionQuery steps.
    # Remove the trailing ", " and add a closing parenthesis.
    multiSelectionQuery = multiSelectionQuery[:-2] + """) """
    
    featureReplacement(sourceFeatureLayer, targetFeatureLayer, multiSelectionQuery)


def featureReplacement(sourceFL, targetFL, featuresToSelect):
    # 1c.) Get the common fields so that you can search and insert correctly.
    targetFeatureDesc = Describe(targetFL)
    targetFeatureFields = targetFeatureDesc.fields
    targetFeatureOIDField = targetFeatureDesc.OIDFieldName
    targetFeatureShapeField = targetFeatureDesc.shapeFieldName
    targetFeatureFieldNames = [x.name for x in targetFeatureFields]
    
    sourceFeatureDesc = Describe(sourceFL)
    sourceFeatureFields = sourceFeatureDesc.fields
    sourceFeatureOIDField = sourceFeatureDesc.OIDFieldName
    sourceFeatureShapeField = sourceFeatureDesc.shapeFieldName
    sourceFeatureFieldNames = [x.name for x in sourceFeatureFields]
    
    excludeFieldNames = [targetFeatureOIDField, targetFeatureShapeField, sourceFeatureOIDField, sourceFeatureShapeField]
    
    searchCursorFields = [x for x in targetFeatureFieldNames if x in sourceFeatureFieldNames and x not in excludeFieldNames]
    searchCursorFields.append('SHAPE@')
    
    # Remove and then re-add the uniqueKeyField so that it is the last column and can be easily referenced.
    searchCursorFields.remove(str(uniqueKeyFieldToUse))
    searchCursorFields.append(str(uniqueKeyFieldToUse))
    insertCursorFields = searchCursorFields
    
    # Select the features in the source layer
    SelectLayerByAttribute_management(sourceFL, "NEW_SELECTION", featuresToSelect)
    # Repeat the selection in the target layer
    SelectLayerByAttribute_management(targetFL, "NEW_SELECTION", featuresToSelect)
    # Then select the common segments spatially, with some room for possible movement.
    SelectLayerByLocation_management(targetFL, 'WITHIN_A_DISTANCE', sourceFL, 50, 'SUBSET_SELECTION')
    
    # 5.) Count selected features in the target and delete them if there is at least 1.
    countResult0 = GetCount_management(targetFL)
    intCount0 = int(countResult0.getOutput(0))
    if intCount0 >= 1:
        # 12.) Delete the selected features in the input layer, if any.
        try:
            DeleteFeatures_management(targetFL)
        except:
            print("Could not delete features for the selection " + str(featuresToSelect) + ".")
    else:
        pass
    
    # 10.) Count to make sure that at least one feature is selected.
    countResult1 = GetCount_management(sourceFL)
    intCount1 = int(countResult1.getOutput(0))
    if intCount1 >= 1:
        # If so, cursor the features out
        featureList = list()
        
        newCursor = daSearchCursor(sourceFL, searchCursorFields)
        
        for cursorItem in newCursor:
            featureList.append(list(cursorItem))
        
        try:
            del newCursor
        except:
            pass
        
        # 11.) Insert the selected source features into the copy of the centerlines.
        newCursor = daInsertCursor(targetFL, insertCursorFields)
        
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


if __name__ == "__main__":
    importCommentsToChangedSource(changeSourceWithComments, changeSource)
    #for changeTargetItem in targetFeatureClasses:
    #    changedFeaturesImport(changeSource, changeTargetItem)


else:
    pass