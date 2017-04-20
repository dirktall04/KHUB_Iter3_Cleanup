#!/usr/bin/env python
# datareviewerchecks_kdotprocessimprovements_iter2.py
# -*- coding: utf-8 -*-
# Created 2017-01-11, by dirktall04
# Updated 2017-01-27, by dirktall04
# Updated 2017-02-02, by dirktall04
# Updated 2017-03-02, by dirktall04
# Updated 2017-03-06, by dirktall04
# Updated 2017-03-15, by dirktall04
# Updated 2017-03-27, by dirktall04
# Updated 2017-03-28, by dirktall04

# Still need to investigate why there are large areas that didn't calculate a local key.
# Several of them are KDOT Rejected or Private, or Other, but some have Local Funclass
# LRS Key and a null KDOTLRSKey.


import gc
import os
import time

from pathFunctions import (returnGDBOrSDEPath,
    returnFeatureClass, returnGDBOrSDEName)##, returnGDBOrSDEFolder) -- Using mainFolder instead.

from arcpy import (AddField_management, AddIndex_management, AddJoin_management,
    Append_management, CalculateField_management, CopyFeatures_management,
    CreateFileGDB_management, CreateRoutes_lr, DeleteFeatures_management,
    Delete_management, DefineProjection_management, Describe,
    Dissolve_management, env, Exists, ##FeatureVerticesToPoints_management,
    FieldInfo, FieldMap, FieldMappings, FlipLine_edit, GetCount_management,
    GetMessages, ListFields, MakeFeatureLayer_management,
    Merge_management, RepairGeometry_management, RemoveIndex_management,
    RemoveJoin_management, Result, SelectLayerByAttribute_management,
    RemoveDomainFromField_management, SelectLayerByLocation_management)

from arcpy.da import InsertCursor as daInsertCursor, UpdateCursor as daUpdateCursor, SearchCursor as daSearchCursor

import datareviewerchecks_multithreadedfeaturesimplification as featuresimplification

from datareviewerchecks_config import (reviewerSessionGDBFolder,
    inputCenterlines, interchangeRampFC, interchangeRampFCRepairCopy,
    outputRoutes, featureLayerCL_For_Start_CP, featureLayerCL_For_End_CP,
    routesSourceCenterlines, routesSourceFCOne, fcAsFeatureLayer,
    startCalibrationPoints, endCalibrationPoints,
    mergedCalibrationPoints, dissolvedCalibrationPoints, mainFolder,
    nullable, gdbForProcessing, featureSimplificationOutput, inMemModifiedData,
    conflationCountyBoundary, stewardIndexNameCB, stewardIndexNameRSC,
    routesSourceIntermediate, flippedOutput,
    routesSource1, routesSource2, routesSource3, n1RouteId, 
    n1FromMeas, n1ToMeas, rampsOutputGDB,
    rampsOutputFC, rampsOutputFullPath, dissolveErrorsFile,
    dissolvedFlippedOutput, dissolveOutFC, useNewFieldLogic, KDOTRouteId,
    KDOTMeasBeg, KDOTMeasEnd, rampsBeginMeasure, rampsEndMeasure)


env.overwriteOutput = True
inputCenterlinesSR = Describe(inputCenterlines).spatialReference
env.outputCoordinateSystem = inputCenterlinesSR
env.workspace = returnGDBOrSDEPath(routesSourceFCOne)

# For the spatial sort used in the LRS_Unique_Local_Routes file, experiment with both
# the 'LL' and the 'PEANO' (Peano curve algorithm) options to see which gives a better
# result for the sorting. - Might also be worth including the road label in the sort
# just after the spatial option.


def routesSourceCreation():
    ''' Replaced RoutesSourceCenterlines with routesSourceFCOne so that I wouldn't
    be making a version of it that was important for testing/debugging, and then
    later exporting over it for the final output.'''
    
    # Need to rework this part so that they pass the feature class back and forth
    # instead of each creating one for their own use and the next one
    # having to chain on top of that.
    '''
    KDOTSourceDataInit()
    KDOTRampReplacement_Update_HPMS() #-- Done, KDOTKeyCalculation_Update() can (re)start from here.
    ##KDOTRampReplacement_Update()
    
    if useNewFieldLogic == True:
        KDOTKeyCalculation_NewFieldLogic()
    else:
        KDOTKeyCalculation_Update()
    '''
    # Restart after KDOTKeyCalculation_Update()
    KDOTFeatureSimplification()
    
    KDOTFlipProcessing() #-- Probably still needs improvement to flipping logic.
    #KDOTOverlappingRoutesFix() #Replaced by the next two processes.
    # If the KDOTFlipProcessing function completes, then (re)start from here.
    
    KDOTOverlappingRoutesDissolveFix()
    KDOTOverlappingRoutesFlaggingFix()
    
    ##KDOTKeyCalculation_OLD()
    ##KDOTKeyCalculation() # Looks like it's meant to generate target network route keys, but...
    ## it doesn't work well just yet. I probably mistranslated some of the SQL to Python equivalents.
    
    KDOT3RoutesSourceExport()


def KDOTSourceDataInit():
    if Exists(returnGDBOrSDEPath(routesSourceFCOne)):
        pass
    else:
        CreateFileGDB_management(mainFolder, returnGDBOrSDEName(returnGDBOrSDEPath(routesSourceFCOne)))
    # Checking to see if the output already exists.
    # If so, remove it.
    if Exists(routesSourceFCOne):
        print("Deleting the previous routesSourceFCOne at " + str(routesSourceFCOne) + ".")
        Delete_management(routesSourceFCOne)
        time.sleep(15)
    else:
        pass
    # Create a new file for the output.
    print("Making a copy of " + returnFeatureClass(inputCenterlines) + " at " + routesSourceFCOne + ".")
    CopyFeatures_management(inputCenterlines, routesSourceFCOne)
    
    print("Adding fields to " + routesSourceFCOne + ".")
    #Addfields:
    # SourceRouteId (Text, 50)
    AddField_management(routesSourceFCOne, n1RouteId, "TEXT", "", "", 50, n1RouteId, nullable)
    # SourceFromMeasure (Double)
    AddField_management(routesSourceFCOne, n1FromMeas, "DOUBLE", "", "", "", n1FromMeas, nullable)
    # SourceToMeasure (Double)
    AddField_management(routesSourceFCOne, n1ToMeas, "DOUBLE", "", "", "", n1ToMeas, nullable)


def KDOTRampReplacement_Update_HPMS():
    # Tested correct and working as expected on 2017-03-03
    # Needs retested after HPMS routes were selected to be
    # used since they have a different structure.
    # Also needs retested after the source data's fields
    # had their names changed.
    # Tested on 2017-03-28 and did not move measures to geometry updated routes.
    # Tested on 2017-03-29 and had been fixed to work as expected.
    # with the modification to the ramps selection on
    # LRS_Routes_Prefix from """ = 'X' """
    # to """ IN ('X', 'L') """
    
    # This should look at the Ramps_LRSKeys that exist in the
    # All_Road_Centerlines layer and the Interchange_Ramp layer
    # then create a list of the ones that are common between the
    # two. Then, reduce that list to the set which is unique so
    # that we don't have to worry about possible duplicates.
    #
    # The non-duplicated list will then be used as a source
    # to get a ramp in the All_Road_Centerlines
    # FC and replace it's geometry with that from
    # the Interchange_Ramp FC. Then, if there are any
    # other All_Road_Centerlines features with that same
    # Ramps_LRSKey, they should be removed.
    # -- We'll still have the key relationship in the
    # All_Roads_Centerline class, so might not need to
    # make an additional table that tells which additional
    # segments were removed, but it might be good for reporting
    # and for making sure that the data doesn't disappear if we
    # end up making changes to one of the feature classes that
    # could destroy the data later on.
    #
    # Can probably just make a table in the *_Source table that
    # lists all of the Ramp_LRSKeys and the GCIDs of the features
    # that had geometry copied into them and the ones that were
    # removed without having geometry copied into them.
    #
    # If there is a ramp in the Interchange_Ramps FC that does
    # not have any matches in the All_Road_Centerlines FC, then
    # it is probably from a region outside of the current set.
    # This won't be a problem once we have the properly conflated
    # R1-R5 with LRS_Backwards keys, but until that time, the
    # script will need to recognize that there will be some areas
    # that do not have features that correspond to everything
    # in the Interchange_Ramps FC, so we'll need to not transfer
    # those, but log them.
    #
    # After all of the regions are in the same GDB, the logging
    # of the unmatched Interchange_Ramp features will be useful
    # in determining conflation errors or missing data. We could
    # even use it to see if there are missing Ramp keys in the
    # All_Road_Centerline data at that point.
    
    # ^^ This exists now, so we should be able to find out which
    # Interchange_Ramp features lack matching features in the
    # conflation dataset.
    
    # Checking to see if the copy for repairing already exists.
    # If so, remove it.
    if Exists(interchangeRampFCRepairCopy):
        print('Removing the previous copy of repaired interchange ramps.')
        Delete_management(interchangeRampFCRepairCopy)
    else:
        pass
    
    # Create a new file for the copy for repairing since repair modifies the input.
    CopyFeatures_management(interchangeRampFC, interchangeRampFCRepairCopy)
    
    # Repairs the geometry, modifies input.
    # Deletes features with null geometry (2 expected, until Shared.Interchange_Ramp is fixed).
    print("Repairing ramp geometry in the " + returnFeatureClass(interchangeRampFCRepairCopy) + " layer.")
    RepairGeometry_management(interchangeRampFCRepairCopy, "DELETE_NULL")
    
    originalRampsKeysList = list()
    rampsFCFields = ['LRS_KEY', 'SHAPE@', rampsBeginMeasure, rampsEndMeasure]
    
    rampsSearchCursor1 = daSearchCursor(interchangeRampFC, rampsFCFields)
    
    for cursorRow in rampsSearchCursor1:  
        originalRampsKeysList.append(str(cursorRow[0]))
    
    try:
        del rampsSearchCursor1
    except:
        pass
    
    # Test the ramps lrs keys that get removed during the cleaned
    # ramps feature class creation... find out which 2 get
    # removed.
    repairedRampsKeysList = list()
    rampsSearchCursor2 = daSearchCursor(interchangeRampFCRepairCopy, rampsFCFields)
    
    for cursorRow in rampsSearchCursor2:  
        repairedRampsKeysList.append(str(cursorRow[0]))
    
    try:
        del rampsSearchCursor2
    except:
        pass
    
    comparisonList1 = [x for x in originalRampsKeysList if x not in repairedRampsKeysList]
    print("These are the keys that were found in the originalRampsKeysList, but not in the repairedRampsKeysList:")
    for comparisonItem1 in comparisonList1:
        print(str(comparisonItem1))
    
    # Cursor out the Ramp_LRSKeys for all the ramps in the
    # unrepaired feature class, then cursor out all of the Ramp_LRSKeys
    # in the repaired feature class.
    sourceCenterinesFCFields = ["Ramps_LRSKey"]
    routesSourceCenterlinesKeysList = list()
    selectionQuery = """ LRS_ROUTE_PREFIX IN ('X', 'L') AND Ramps_LRSKey IS NOT NULL AND Ramps_LRSKey <> '' """
    roadsSearchCursor1 = daSearchCursor(routesSourceFCOne, sourceCenterinesFCFields, selectionQuery)
    
    for cursorRow in roadsSearchCursor1:
        routesSourceCenterlinesKeysList.append(str(cursorRow[0]))
    
    try:
        del roadsSearchCursor1
    except:
        pass
    
    comparisonList4 = [x for x in routesSourceCenterlinesKeysList if x in repairedRampsKeysList]
    print('These are the keys that were found in the routesSourceCenterlinesKeysList and are also in the repairedRampsKeysList.')
    print('Will deduplicate the items with these keys in the routesSourceCenterline and add the ramp geometry from the repairedRampsKeysList for them.')
    
    # Scoop up the geometries needed for the update cursor to use here, from ramps.
    #searchCursor that gets the ramp feature LRS_KEY and the geometry associated with it.
    newCursor = daSearchCursor(interchangeRampFCRepairCopy, rampsFCFields)
    rampsGeometryDict = dict()
    for cursorItem in newCursor:
        if cursorItem[0] in comparisonList4:
            if cursorItem[0] not in rampsGeometryDict.keys():
                rampsGeometryDict[cursorItem[0]] = [cursorItem[1], cursorItem[2], cursorItem[3]]
            else:
                print(str(cursorItem[0]) + ' is already in the rampsGeometryDict.')
    
    try:
        del newCursor
    except:
        pass
    
    # Updates the Ramps_LRSKey, SHAPE@, and the two other route id fields and the two other important begin
    # measure fields and the two other important end measure fields.
    updateCenterlinesFields = ['Ramps_LRSKey', 'SHAPE@', KDOTRouteId,  n1RouteId, KDOTMeasBeg, n1FromMeas, KDOTMeasEnd, n1ToMeas]
    newCursor = daUpdateCursor(routesSourceFCOne, updateCenterlinesFields)
    deDuplicateList = list()
    
    for cursorItem in newCursor:
        if cursorItem[0] in rampsGeometryDict.keys():
            if cursorItem[0] in deDuplicateList:
                print('Will delete this row due to cursorItem[0] being a duplicate key: ' + str(cursorItem[0]) + '.')
                newCursor.deleteRow()
            else:
                print('Found the cursorItem[0] in rampsGeometryDict.keys(): ' + str(cursorItem[0]) + '.')
                print("Will update its geometry in the routesSourceCenterlines feature class and add it to the deDuplicateList.")
                deDuplicateList.append(cursorItem[0])
                currentRampRouteId = cursorItem[0]
                currentRampShapeToken = rampsGeometryDict[cursorItem[0]][0]
                currentRampBeginMeasure = rampsGeometryDict[cursorItem[0]][1]
                currentRampEndMeasure = rampsGeometryDict[cursorItem[0]][2]
                newCursor.updateRow((currentRampRouteId, currentRampShapeToken, currentRampRouteId, currentRampRouteId,
                    currentRampBeginMeasure, currentRampBeginMeasure, currentRampEndMeasure, currentRampEndMeasure))
        else:
            pass
            
    try:
        del newCursor
    except:
        pass
    
    comparisonList3 = [x for x in repairedRampsKeysList if x not in routesSourceCenterlinesKeysList]
    
    fcAsFeatureLayerForRampSelection = 'FeatureClassAsFeatureLayer_Ramps'
    
    if Exists(fcAsFeatureLayerForRampSelection):
        Delete_management(fcAsFeatureLayerForRampSelection)
    else:
        pass
    
    MakeFeatureLayer_management(interchangeRampFCRepairCopy, fcAsFeatureLayerForRampSelection)
    
    # build the selection list & select up to but not more than 999 features at at time
    selectionCounter = 0
    rampsOutputWhereClause = """ "LRS_KEY" IN ("""
    
    for comparisonItem3 in comparisonList3:
        print(str(comparisonItem3))
        # Remove duplicate LRS Keys here such that only one feature per key remains in the routesSourceCenterlines feature class,
        # then, replace the geometry of each routesSourceCenterlines ramp with an LRSKey in the repairedRampsKeysList with the repairedRamps geometry.
        
        if selectionCounter <= 998:
            rampsOutputWhereClause = rampsOutputWhereClause + """'""" + str(comparisonItem3) + """'""" + """, """
            selectionCounter += 1
        else:
            # Remove the trailing ", " and add a closing parenthesis.
            rampsOutputWhereClause = rampsOutputWhereClause[:-2] + """) """ 
            SelectLayerByAttribute_management(fcAsFeatureLayerForRampSelection, "ADD_TO_SELECTION", rampsOutputWhereClause)
            
            selectionCounter = 0
            rampsOutputWhereClause = """ "LRS_KEY" IN ("""
            rampsOutputWhereClause = rampsOutputWhereClause + """'""" + str(comparisonItem3) + """'""" + """, """
        
    # Remove the trailing ", " and add a closing parenthesis.
    rampsOutputWhereClause = rampsOutputWhereClause[:-2] + """) """
    SelectLayerByAttribute_management(fcAsFeatureLayerForRampSelection, "ADD_TO_SELECTION", rampsOutputWhereClause)
    
    print("Counting...")
    selectedRampsResult = GetCount_management(fcAsFeatureLayerForRampSelection)
    selectedRampsCount = int(selectedRampsResult.getOutput(0))
    print("Counted " + str(selectedRampsCount) + " features to append with.")
    
    rampsAppendSource = 'in_memory\RampsAppendSource'
    
    if Exists(rampsAppendSource):
        try:
            Delete_management(rampsAppendSource)
        except:
            pass
    else:
        pass
    
    CopyFeatures_management(fcAsFeatureLayerForRampSelection, rampsAppendSource)
    
    print("Starting ramps append process for ramps in repairedRampsKeysList but not in routesSourceCenterlinesKeysList.")
    # Append logic goes here:
    # Where appendInputs = [rampsAppendSource]
    # and appendTarget = routesSourceFCOne
    
    # Create a fieldmapping object so that the Interchange_Ramps can be correctly imported with append.
    appendInputs = [rampsAppendSource]
    appendTarget = routesSourceFCOne
    schemaType = "NO_TEST"
    
    # Field mapping goes here.
    # Interchange_Ramp.LRS_KEY to RoutesSource_Test.KDOT_LRS_KEY
    fm_Field1 = FieldMap()
    fm_Field1.addInputField(appendInputs[0], "LRS_KEY")
    fm_Field1_OutField = fm_Field1.outputField
    fm_Field1_OutField.name = 'Ramps_LRSKey'
    fm_Field1.outputField = fm_Field1_OutField
    
    # Interchange_Ramp.BEG_CNTY_LOGMILE to RoutesSource_Test.county_log_begin
    fm_Field2 = FieldMap()
    fm_Field2.addInputField(appendInputs[0], "BEG_CNTY_LOGMILE")
    fm_Field2_OutField = fm_Field2.outputField
    fm_Field2_OutField.name = KDOTMeasBeg
    fm_Field2.outputField = fm_Field2_OutField
    
    # Interchange_Ramp.END_CNTY_LOGMILE to RoutesSource_Test.county_log_end
    fm_Field3 = FieldMap()
    fm_Field3.addInputField(appendInputs[0], "END_CNTY_LOGMILE")
    fm_Field3_OutField = fm_Field3.outputField
    fm_Field3_OutField.name = KDOTMeasEnd
    fm_Field3.outputField = fm_Field3_OutField
    
    # Create the fieldMappings object and add the fieldMap objects to it.
    interchangeRampsMappings = FieldMappings()
    interchangeRampsMappings.addFieldMap(fm_Field1)
    interchangeRampsMappings.addFieldMap(fm_Field2)
    interchangeRampsMappings.addFieldMap(fm_Field3)
    
    # Perform the append.
    print("Appending the features from " + returnFeatureClass(interchangeRampFCRepairCopy) + " into " + returnFeatureClass(routesSourceCenterlines) + ".")
    Append_management(appendInputs, appendTarget, schemaType, interchangeRampsMappings)
    
    # Go ahead and save that to a gdb so that you can view the results:
    if Exists(rampsOutputGDB):
        try:
            Delete_management(rampsOutputGDB)
        except:
            pass
    else:
        pass
    
    print('Creating a new gdb to hold the ramps update output at ' + str(rampsOutputGDB) + '.')
    CreateFileGDB_management(mainFolder, returnGDBOrSDEName(rampsOutputGDB))
    
    print('Copying the routesSourceFCOne to ' + str(rampsOutputFullPath) + '.')
    CopyFeatures_management(routesSourceFCOne, rampsOutputFullPath)
    # Clear memory used by the routesSourceFCOne after it's copied to disk.
    time.sleep(15)
    Delete_management(routesSourceFCOne)
    
    #Select features where Ramps_LRSKey is not null or ''
    #Then, calculate the KDOT_LRS_KEY to be the Ramps_LRS_Key for
    # the selected routes.
    fcAsFeatureLayerFromRampsOutput = 'fcAsFeatureLayerFromRampsOutput'
    
    MakeFeatureLayer_management(rampsOutputFullPath, fcAsFeatureLayerFromRampsOutput)
    selectionQuery = """ Ramps_LRSKey IS NOT NULL AND Ramps_LRSKey <> '' """
    SelectLayerByAttribute_management(fcAsFeatureLayerFromRampsOutput, "NEW_SELECTION", selectionQuery)
    CalculateField_management(fcAsFeatureLayerFromRampsOutput, KDOTRouteId, "!Ramps_LRSKey!", "PYTHON_9.3")


def KDOTRampReplacement_Update():
    # Tested correct and working as expected on 2017-03-03
    # with the modification to the ramps selection on
    # LRS_Routes_Prefix from """ = 'X' """
    # to """ IN ('X', 'L') """
    
    # This should look at the Ramps_LRSKeys that exist in the
    # All_Road_Centerlines layer and the Interchange_Ramp layer
    # then create a list of the ones that are common between the
    # two. Then, reduce that list to the set which is unique so
    # that we don't have to worry about possible duplicates.
    #
    # The non-duplicated list will then be used as a source
    # to get a ramp in the All_Road_Centerlines
    # FC and replace it's geometry with that from
    # the Interchange_Ramp FC. Then, if there are any
    # other All_Road_Centerlines features with that same
    # Ramps_LRSKey, they should be removed.
    # -- We'll still have the key relationship in the
    # All_Roads_Centerline class, so might not need to
    # make an additional table that tells which additional
    # segments were removed, but it might be good for reporting
    # and for making sure that the data doesn't disappear if we
    # end up making changes to one of the feature classes that
    # could destroy the data later on.
    #
    # Can probably just make a table in the *_Source table that
    # lists all of the Ramp_LRSKeys and the GCIDs of the features
    # that had geometry copied into them and the ones that were
    # removed without having geometry copied into them.
    #
    # If there is a ramp in the Interchange_Ramps FC that does
    # not have any matches in the All_Road_Centerlines FC, then
    # it is probably from a region outside of the current set.
    # This won't be a problem once we have the properly conflated
    # R1-R5 with LRS_Backwards keys, but until that time, the
    # script will need to recognize that there will be some areas
    # that do not have features that correspond to everything
    # in the Interchange_Ramps FC, so we'll need to not transfer
    # those, but log them.
    #
    # After all of the regions are in the same GDB, the logging
    # of the unmatched Interchange_Ramp features will be useful
    # in determining conflation errors or missing data. We could
    # even use it to see if there are missing Ramp keys in the
    # All_Road_Centerline data at that point.
    
    # ^^ This exists now, so we should be able to find out which
    # Interchange_Ramp features lack matching features in the
    # conflation dataset.
    
    # Checking to see if the copy for repairing already exists.
    # If so, remove it.
    if Exists(interchangeRampFCRepairCopy):
        print('Removing the previous copy of repaired interchange ramps.')
        Delete_management(interchangeRampFCRepairCopy)
    else:
        pass
    
    # Create a new file for the copy for repairing since repair modifies the input.
    CopyFeatures_management(interchangeRampFC, interchangeRampFCRepairCopy)
    
    # Repairs the geometry, modifies input.
    # Deletes features with null geometry (2 expected, until Shared.Interchange_Ramp is fixed).
    print("Repairing ramp geometry in the " + returnFeatureClass(interchangeRampFCRepairCopy) + " layer.")
    RepairGeometry_management(interchangeRampFCRepairCopy, "DELETE_NULL")
    
    originalRampsKeysList = list()
    rampsFCFields = ['LRS_KEY', 'SHAPE@']
    
    rampsSearchCursor1 = daSearchCursor(interchangeRampFC, rampsFCFields)
    
    for cursorRow in rampsSearchCursor1:  
        originalRampsKeysList.append(str(cursorRow[0]))
    
    try:
        del rampsSearchCursor1
    except:
        pass
    
    # Test the ramps lrs keys that get removed during the cleaned
    # ramps feature class creation... find out which 2 get
    # removed.
    repairedRampsKeysList = list()
    rampsSearchCursor2 = daSearchCursor(interchangeRampFCRepairCopy, rampsFCFields)
    
    for cursorRow in rampsSearchCursor2:  
        repairedRampsKeysList.append(str(cursorRow[0]))
    
    try:
        del rampsSearchCursor2
    except:
        pass
    
    comparisonList1 = [x for x in originalRampsKeysList if x not in repairedRampsKeysList]
    print("These are the keys that were found in the originalRampsKeysList, but not in the repairedRampsKeysList:")
    for comparisonItem1 in comparisonList1:
        print(str(comparisonItem1))
    
    # Cursor out the Ramp_LRSKeys for all the ramps in the
    # unrepaired feature class, then cursor out all of the Ramp_LRSKeys
    # in the repaired feature class.
    sourceCenterinesFCFields = ["Ramps_LRSKey"]
    routesSourceCenterlinesKeysList = list()
    selectionQuery = """ LRS_ROUTE_PREFIX IN ('X', 'L') AND Ramps_LRSKey IS NOT NULL AND Ramps_LRSKey <> '' """
    roadsSearchCursor1 = daSearchCursor(routesSourceFCOne, sourceCenterinesFCFields, selectionQuery)
    
    for cursorRow in roadsSearchCursor1:
        routesSourceCenterlinesKeysList.append(str(cursorRow[0]))
    
    try:
        del roadsSearchCursor1
    except:
        pass
    
    comparisonList4 = [x for x in routesSourceCenterlinesKeysList if x in repairedRampsKeysList]
    print('These are the keys that were found in the routesSourceCenterlinesKeysList and are also in the repairedRampsKeysList.')
    print('Will deduplicate the items with these keys in the routesSourceCenterline and add the ramp geometry from the repairedRampsKeysList for them.')
    
    # Scoop up the geometries needed for the update cursor to use here, from ramps.
    #searchCursor that gets the ramp feature LRS_KEY and the geometry associated with it.
    newCursor = daSearchCursor(interchangeRampFCRepairCopy, rampsFCFields)
    rampsGeometryDict = dict()
    for cursorItem in newCursor:
        if cursorItem[0] in comparisonList4:
            if cursorItem[0] not in rampsGeometryDict.keys():
                rampsGeometryDict[cursorItem[0]] = cursorItem[1]
            else:
                print(str(cursorItem[0]) + ' is already in the rampsGeometryDict.')
    
    try:
        del newCursor
    except:
        pass
    
    updateCenterlinesFields = ['Ramps_LRSKey', 'SHAPE@']
    newCursor = daUpdateCursor(routesSourceFCOne, updateCenterlinesFields)
    deDuplicateList = list()
    
    for cursorItem in newCursor:
        if cursorItem[0] in rampsGeometryDict.keys():
            if cursorItem[0] in deDuplicateList:
                print('Will delete this row due to cursorItem[0] being a duplicate key: ' + str(cursorItem[0]) + '.')
                newCursor.deleteRow()
            else:
                print('Found the cursorItem[0] in rampsGeometryDict.keys(): ' + str(cursorItem[0]) + '.')
                print("Will update its geometry in the routesSourceCenterlines feature class and add it to the deDuplicateList.")
                deDuplicateList.append(cursorItem[0])
                newCursor.updateRow([cursorItem[0], rampsGeometryDict[cursorItem[0]]])
        else:
            pass
            
    try:
        del newCursor
    except:
        pass
    
    comparisonList3 = [x for x in repairedRampsKeysList if x not in routesSourceCenterlinesKeysList]
    
    fcAsFeatureLayerForRampSelection = 'FeatureClassAsFeatureLayer_Ramps'
    
    if Exists(fcAsFeatureLayerForRampSelection):
        Delete_management(fcAsFeatureLayerForRampSelection)
    else:
        pass
    
    MakeFeatureLayer_management(interchangeRampFCRepairCopy, fcAsFeatureLayerForRampSelection)
    
    # build the selection list & select up to but not more than 999 features at at time
    selectionCounter = 0
    rampsOutputWhereClause = """ "LRS_KEY" IN ("""
    
    for comparisonItem3 in comparisonList3:
        print(str(comparisonItem3))
        # Remove duplicate LRS Keys here such that only one feature per key remains in the routesSourceCenterlines feature class,
        # then, replace the geometry of each routesSourceCenterlines ramp with an LRSKey in the repairedRampsKeysList with the repairedRamps geometry.
        
        if selectionCounter <= 998:
            rampsOutputWhereClause = rampsOutputWhereClause + """'""" + str(comparisonItem3) + """'""" + """, """
            selectionCounter += 1
        else:
            # Remove the trailing ", " and add a closing parenthesis.
            rampsOutputWhereClause = rampsOutputWhereClause[:-2] + """) """ 
            SelectLayerByAttribute_management(fcAsFeatureLayerForRampSelection, "ADD_TO_SELECTION", rampsOutputWhereClause)
            
            selectionCounter = 0
            rampsOutputWhereClause = """ "LRS_KEY" IN ("""
            rampsOutputWhereClause = rampsOutputWhereClause + """'""" + str(comparisonItem3) + """'""" + """, """
        
    # Remove the trailing ", " and add a closing parenthesis.
    rampsOutputWhereClause = rampsOutputWhereClause[:-2] + """) """
    SelectLayerByAttribute_management(fcAsFeatureLayerForRampSelection, "ADD_TO_SELECTION", rampsOutputWhereClause)
    
    print("Counting...")
    selectedRampsResult = GetCount_management(fcAsFeatureLayerForRampSelection)
    selectedRampsCount = int(selectedRampsResult.getOutput(0))
    print("Counted " + str(selectedRampsCount) + " features to append with.")
    
    rampsAppendSource = 'in_memory\RampsAppendSource'
    
    if Exists(rampsAppendSource):
        try:
            Delete_management(rampsAppendSource)
        except:
            pass
    else:
        pass
    
    CopyFeatures_management(fcAsFeatureLayerForRampSelection, rampsAppendSource)
    
    print("Starting ramps append process for ramps in repairedRampsKeysList but not in routesSourceCenterlinesKeysList.")
    # Append logic goes here:
    # Where appendInputs = [rampsAppendSource]
    # and appendTarget = routesSourceFCOne
    
    # Create a fieldmapping object so that the Interchange_Ramps can be correctly imported with append.
    appendInputs = [rampsAppendSource]
    appendTarget = routesSourceFCOne
    schemaType = "NO_TEST"
    
    # Field mapping goes here.
    # Interchange_Ramp.LRS_KEY to RoutesSource_Test.LRSKEY
    fm_Field1 = FieldMap()
    fm_Field1.addInputField(appendInputs[0], "LRS_KEY")
    fm_Field1_OutField = fm_Field1.outputField
    fm_Field1_OutField.name = 'Ramps_LRSKey'
    fm_Field1.outputField = fm_Field1_OutField
    
    # Interchange_Ramp.BEG_CNTY_LOGMILE to RoutesSource_Test.NON_STATE_BEGIN_MP
    fm_Field2 = FieldMap()
    fm_Field2.addInputField(appendInputs[0], "BEG_CNTY_LOGMILE")
    fm_Field2_OutField = fm_Field2.outputField
    fm_Field2_OutField.name = 'NON_STATE_BEGIN_MP'
    fm_Field2.outputField = fm_Field2_OutField
    
    # Interchange_Ramp.END_CNTY_LOGMILE to RoutesSource_Test.NON_STATE_END_MP
    fm_Field3 = FieldMap()
    fm_Field3.addInputField(appendInputs[0], "END_CNTY_LOGMILE")
    fm_Field3_OutField = fm_Field3.outputField
    fm_Field3_OutField.name = 'NON_STATE_END_MP'
    fm_Field3.outputField = fm_Field3_OutField
    
    # Create the fieldMappings object and add the fieldMap objects to it.
    interchangeRampsMappings = FieldMappings()
    interchangeRampsMappings.addFieldMap(fm_Field1)
    interchangeRampsMappings.addFieldMap(fm_Field2)
    interchangeRampsMappings.addFieldMap(fm_Field3)
    
    # Perform the append.
    print("Appending the features from " + returnFeatureClass(interchangeRampFCRepairCopy) + " into " + returnFeatureClass(routesSourceCenterlines) + ".")
    Append_management(appendInputs, appendTarget, schemaType, interchangeRampsMappings)
    
    # Go ahead and save that to a gdb so that you can view the results:
    if Exists(rampsOutputGDB):
        try:
            Delete_management(rampsOutputGDB)
        except:
            pass
    else:
        pass
    
    print('Creating a new gdb to hold the ramps update output at ' + str(rampsOutputGDB) + '.')
    CreateFileGDB_management(mainFolder, returnGDBOrSDEName(rampsOutputGDB))
    
    print('Copying the routesSourceFCOne to ' + str(rampsOutputFullPath) + '.')
    CopyFeatures_management(routesSourceFCOne, rampsOutputFullPath)
    # Clear memory used by the routesSourceFCOne after it's copied to disk.
    time.sleep(15)
    Delete_management(routesSourceFCOne)


def ParseLRS_ROUTE_PREFIX(passedFeatureLayer):
    # If LRS_ROUTE_PREFIX doesn't exist, add it.
    # Then, populate it.
    
    lrsPrefixField = 'LRS_ROUTE_PREFIX'
    
    # Domains mess up SQL value testing. Instead of looking for a column to be
    # equal to an 'X' you would be looking for it to be equal to a 7 or an 8.
    # But, whereas the letter is always the same, it might not always be the
    # same number and that's bad. -- Possibly able to get around this by
    # knowing the domain's name and doing a domain lookup for the values that
    # you're interested, but that method is not yet tested.
    try:
        RemoveDomainFromField_management(passedFeatureLayer, lrsPrefixField)
    except:
        print("Could not remove the domain from the '" + str(lrsPrefixField) + "' column.")
        print("The domain or field might not have existed previously.")
    
    # Test for the new fields. If they're not there yet,
    # then add them before the rest of the calculations.
    tempDesc = Describe(passedFeatureLayer)
    print("Parsing the LRS values in  " + returnFeatureClass(tempDesc.catalogPath) + " to figure out what the LRS_ROUTE_PREFIX should be.")
    currentFieldObjects = tempDesc.fields
    try:
        del tempDesc
    except:
        pass
    
    currentFieldNames = [x.name for x in currentFieldObjects]
    
    print("currentFieldNames:")
    for fieldNameItem in currentFieldNames:
        print fieldNameItem
    
    fieldsNeeded = [lrsPrefixField]
    fieldsToAdd = [x for x in fieldsNeeded if x not in currentFieldNames]
    
    if lrsPrefixField in fieldsToAdd:
        AddField_management(passedFeatureLayer, lrsPrefixField, "DATE", "", "", "", "LRS_ROUTE_PREFIX", nullable)
    else:
        pass
    
    # Need to reparse the LRSKEY with the current LRS_ROUTE_PREFIX value (if it isn't null or empty)
    # prior to doing all of this or you will overwrite the changes made by Tim's manual edits
    # to the LRS_ROUTE_PREFIX field.
    
    if 'State_System_LRSKEY' in currentFieldNames:
        #Parse from State_System_LRSKEY.
        # LRS_ROUTE_PREFIX = "I"
        selectionQuery1 = '''State_System_LRSKEY LIKE '___I%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'I'", "PYTHON_9.3")
        
        # LRS_ROUTE_PREFIX = "U"
        selectionQuery1 = '''State_System_LRSKEY LIKE '___U%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'U'", "PYTHON_9.3")
        
        # LRS_ROUTE_PREFIX = "K"
        selectionQuery1 = '''State_System_LRSKEY LIKE '___K%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'K'", "PYTHON_9.3")
        
    elif 'Non_State_System_LRSKEY' in currentFieldNames:
        #Parse from Non_State_System_LRSKEY.
        # LRS_ROUTE_PREFIX = "C"
        selectionQuery1 = '''Non_State_System_LRSKEY LIKE '___C%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'C'", "PYTHON_9.3")
        
        # LRS_ROUTE_PREFIX = "R"
        selectionQuery1 = '''Non_State_System_LRSKEY LIKE '___R%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'R'", "PYTHON_9.3")
        
        # LRS_ROUTE_PREFIX = "M"
        selectionQuery1 = '''Non_State_System_LRSKEY LIKE '___M%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'M'", "PYTHON_9.3")
        
        # LRS_ROUTE_PREFIX = "L"
        selectionQuery1 = '''Non_State_System_LRSKEY LIKE '___L%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'L'", "PYTHON_9.3")
        
    elif 'Ramps_LRSKEY' in currentFieldNames:
        selectionQuery1 = '''Ramps_LRSKEY LIKE '___X%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        # LRS_ROUTE_PREFIX = "X"
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'X'", "PYTHON_9.3")
    
    elif 'SourceRouteId' in currentFieldNames:
        #Parse from SourceRouteId instead of the other fields.
        # LRS_ROUTE_PREFIX = "I"
        selectionQuery1 = '''SourceRouteId LIKE 'I%' OR SourceRouteId LIKE '___I%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'I'", "PYTHON_9.3")
        
        # LRS_ROUTE_PREFIX = "U"
        selectionQuery1 = '''SourceRouteId LIKE 'U%' OR SourceRouteId LIKE '___U%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'U'", "PYTHON_9.3")
        
        # LRS_ROUTE_PREFIX = "K"
        selectionQuery1 = '''SourceRouteId LIKE 'K%' OR SourceRouteId LIKE '___K%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'K'", "PYTHON_9.3")
        
        # LRS_ROUTE_PREFIX = "C"
        selectionQuery1 = '''SourceRouteId LIKE '___C%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'C'", "PYTHON_9.3")
        
        # LRS_ROUTE_PREFIX = "R"
        selectionQuery1 = '''SourceRouteId LIKE '___R%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'R'", "PYTHON_9.3")
        
        # LRS_ROUTE_PREFIX = "M"
        selectionQuery1 = '''SourceRouteId LIKE '___M%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'M'", "PYTHON_9.3")
        
        # LRS_ROUTE_PREFIX = "X"
        selectionQuery1 = '''SourceRouteId LIKE '___X%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'X'", "PYTHON_9.3")
        
        # LRS_ROUTE_PREFIX = "L"
        selectionQuery1 = '''SourceRouteId LIKE '___L%' '''
        SelectLayerByAttribute_management(passedFeatureLayer, "NEW_SELECTION", selectionQuery1)
        CalculateField_management (passedFeatureLayer, lrsPrefixField, "'L'", "PYTHON_9.3")
        
    try:
        AddDomainToField_management(passedFeatureLayer, "LRS_ROUTE_PREFIX", "LRS_ROUTES")
    except:
        print("Could not add the domain to the 'LRS_ROUTE_PREFIX' column.")
        print("The domain or field might not have existed previously.")


def KDOTFeatureSimplification():

    # Do the ghost route identification after the other processes here
    # and create 2 separate feature classes that can be used
    # - One for network2 and network3 and one for
    # network1 (the network with current keys for event data)
    
    featuresimplification.main()


def KDOTFlipProcessing():
    # Take everything out of the in_memory gdb.
    try:
        Delete_management('in_memory')
    except:
        print("Could not delete 'in_memory'.")
    
    if Exists(fcAsFeatureLayer):
        try:
            Delete_management(fcAsFeatureLayer)
        except:
            pass
    else:
        pass
    
    print("Copying features from their new location to an in_memory location for flipping.")
    CopyFeatures_management(featureSimplificationOutput, inMemModifiedData)
    print("Copy complete.")
    MakeFeatureLayer_management(inMemModifiedData, fcAsFeatureLayer)
    
    # Define a function to do feature and measure flipping, then just send in the feature class
    # and the selectionQuery and receive the feature class with flipped geometry and measures back.
    
    ## Always do Non_State_Flip_Flag and LRS_BACKWARD check from here on out.
    ## Should be in the data set.
    ############ --- Requires new logic for flipping and measure checking -- see notes from talking with Kevin K
    ### and others in the Manual Data Editing Sessions. --- ############ 
    print("Using the LRS_BACKWARD field in the selectionQuery for flipping.")
    # All the capitals, all the time.
    selectionQuery1 = """ ((NON_STATE_FLIP_FLAG IS NOT NULL AND NON_STATE_FLIP_FLAG = 'Y') OR (STATE_FLIP_FLAG IS NOT NULL AND STATE_FLIP_FLAG = 'Y')) """
    selectionQuery2 = """ LRS_BACKWARD IS NULL OR LRS_BACKWARD = 1 OR LRS_BACKWARD = -1 """
    selectionQuery3 = """ """ + str(n1FromMeas) + """ > """ + str(n1ToMeas) + """ """
    
    SelectLayerByAttribute_management(fcAsFeatureLayer, "CLEAR_SELECTION")
    fieldNamesToSwap = [n1FromMeas, n1ToMeas]
    
    print("Selecting features with a 'Y' for NON_STATE_FLIP_FLAG OR STATE_FLIP_FLAG.")
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery1)
    print("Flipping selected features.")
    FlipLine_edit(fcAsFeatureLayer)
    returnedFcAsFeatureLayer = cursorSwapColumnValues(fcAsFeatureLayer, fieldNamesToSwap, selectionQuery1)
    
    print("Selecting features with a LRS_BACKWARD of 1 or -1.")
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery2)
    print("Flipping selected features.")
    FlipLine_edit(fcAsFeatureLayer)
    returnedFcAsFeatureLayer = cursorSwapColumnValues(returnedFcAsFeatureLayer, fieldNamesToSwap, selectionQuery2)
    
    print("Selecting features with larger " + str(n1FromMeas) + " than " + str(n1ToMeas) + ".")
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery3)
    print("Flipping selected features.")
    FlipLine_edit(fcAsFeatureLayer)
    returnedFcAsFeatureLayer = cursorSwapColumnValues(returnedFcAsFeatureLayer, fieldNamesToSwap, selectionQuery3)
    print("Feature flipping complete.")
    
    # Also test with doing the measure flipping separate from the geometry flipping.
    # Seems like that should produce more errors rather than less, however.
    
    print("Saving the flipped in_memory layer back to the disk as " + str(flippedOutput) + ".")
    CopyFeatures_management(inMemModifiedData, flippedOutput)
    print("Save complete.")


def cursorSwapColumnValues(layerAsFeatureLayer, fieldValuesToSwap, selectionQueryToUse):
    newCursor = daUpdateCursor(layerAsFeatureLayer, fieldValuesToSwap, selectionQueryToUse)
    print("Updating the measure fields, where the data meets the flipping criteria.")
    
    ## Need to flip the measures on everything that was flipped in FlipLine_edit
    
    for updateItem in newCursor:
        if updateItem[0] is not None:
            if updateItem[1] is not None:
                updateItemList = list(updateItem)
                updateItemSwap = updateItemList[0]
                updateItemList[0] = updateItemList[1]
                updateItemList[1] = updateItemSwap
                newCursor.updateRow(updateItemList)
            
        if 'updateItemSwap' in locals():
            try:
                del updateItemSwap
            except:
                pass
        if 'updateItemList' in locals():
            try:
                del updateItemList
            except:
                pass
    
    print("Finished updating the measure fields where applicable.")
    
    ## Check to see if the output dataset exists. If so, delete it
    # then save the features.
    if Exists(flippedOutput):
        Delete_management(flippedOutput)
    else:
        pass
    
    time.sleep(10)
    
    return layerAsFeatureLayer


def KDOTKeyCalculation_NewFieldLogic():
    print("Using the new field logic to calculate the values of the source lrs ID and measure fields.")
    MakeFeatureLayer_management(rampsOutputFullPath, fcAsFeatureLayer)
    # As long as the KDOT_LRS_KEY is not null, calculate from the
    # current fields.
    
    # For the 3rd version:
    '''
    n1FromMeas, n1ToMeas, rampsOutputGDB,
    rampsOutputFC, rampsOutputFullPath, dissolveErrorsFile,
    dissolvedFlippedOutput, dissolveOutFC, useNewFieldLogic, KDOTRouteId,
    KDOTMeasBeg, KDOTMeasEnd
    # Send the data to the source output fields with the correct decimal formatting.
    expressionText1 = 'float("{0:.3f}".format(!' + str(KDOTMeasBeg) + '!))'
    CalculateField_management(fcAsFeatureLayerForMeasuring, n1FromMeas, expressionText1, "PYTHON_9.3")
    expressionText2 = 'float("{0:.3f}".format(!' + str(KDOTMeasEnd) + '!))'
    CalculateField_management(fcAsFeatureLayerForMeasuring, n1ToMeas, expressionText2, "PYTHON_9.3")
    # Reverse the data flow to correct decimals in the original fields.
    expressionText3 = 'float("{0:.3f}".format(!' + str(n1FromMeas) + '!))'
    CalculateField_management(fcAsFeatureLayerForMeasuring, KDOTMeasBeg, expressionText3, "PYTHON_9.3")
    expressionText4 = 'float("{0:.3f}".format(!' + str(n1ToMeas) + '!))'
    CalculateField_management(fcAsFeatureLayerForMeasuring, KDOTMeasEnd, expressionText4, "PYTHON_9.3")
    '''
    selectionQuery = """ "KDOT_LRS_KEY" IS NOT NULL """
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteId = KDOT_LRS_KEY
    CalculateField_management (fcAsFeatureLayer, n1RouteId, "!" + str(KDOTRouteId) + "!", "PYTHON_9.3")
    # SourceFromMeasure = county_log_begin
    CalculateField_management (fcAsFeatureLayer, n1FromMeas, "!" + str(KDOTMeasBeg) + "!", "PYTHON_9.3")
    # SourceToMeasure = county_log_end
    CalculateField_management (fcAsFeatureLayer, n1ToMeas, "!" + str(KDOTMeasEnd) + "!", "PYTHON_9.3")
    selectionQuery = """ KDOT_LRS_KEY IS NOT NULL AND county_log_begin IS NULL AND county_log_end IS NULL AND (COUNTY_BEGIN_MP IS NOT NULL OR COUNTY_END_MP IS NOT NULL) """
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery)
    countResult = GetCount_management(fcAsFeatureLayer)
    intCount = int(countResult.getOutput(0))
    print("After the new selection query to deal with the fact that State routes did not have their begin and end measure populated correctly, " +
        str(intCount) + " were selected.")
    # SourceFromMeasure = COUNTY_BEGIN_MP
    CalculateField_management (fcAsFeatureLayer, n1FromMeas, "!COUNTY_BEGIN_MP!", "PYTHON_9.3")
    # SourceToMeasure = COUNTY_END_MP
    CalculateField_management (fcAsFeatureLayer, n1ToMeas, "!COUNTY_END_MP!", "PYTHON_9.3")


def KDOTKeyCalculation_Update():
    #FieldPopulation with selections and FieldCalculate:
    
    MakeFeatureLayer_management(rampsOutputFullPath, fcAsFeatureLayer)
    
    ParseLRS_ROUTE_PREFIX(fcAsFeatureLayer)
    
    tempDesc = Describe(fcAsFeatureLayer)
    print("Calculating values for new LRS and measure fields in " + returnFeatureClass(tempDesc.catalogPath) + ".")
    try:
        del tempDesc
    except:
        pass
    
    # A better solution than parsing the LRS ROUTE PREFIX from the LRSKEY
    # and then relying on the LRS ROUTE PREFIX to make decision about where
    # to pull the LRSKEY from would be to just start at the LRSKEY locations...
    
    # -------------------- Start of old calculations. ----------------------- #
    # Select LRS_ROUTE_PREFIX IN ('I', 'U', 'K')
    selectionQuery = """ "LRS_ROUTE_PREFIX" IN ('I', 'U', 'K') """
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteId = StateKey1
    CalculateField_management (fcAsFeatureLayer, n1RouteId, "!StateKey1!", "PYTHON_9.3")
    # SourceFromMeasure = STATE_BEGIN_MP
    CalculateField_management (fcAsFeatureLayer, n1FromMeas, "!STATE_BEGIN_MP!", "PYTHON_9.3")
    # SourceToMeasure = STATE_END_MP
    CalculateField_management (fcAsFeatureLayer, n1ToMeas, "!STATE_END_MP!", "PYTHON_9.3")
    
    # Select LRS_ROUTE_PREFIX NOT IN ('I', 'U', 'K') AND LRSKEY IS NOT NULL
    selectionQuery = """ "LRS_ROUTE_PREFIX" NOT IN ('I', 'U', 'K') AND "LRSKEY" IS NOT NULL """
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteId = LRSKEY
    CalculateField_management (fcAsFeatureLayer, n1RouteId,  "!LRSKEY!", "PYTHON_9.3")
    # SourceFromMeasure = NON_STATE_BEGIN_MP
    CalculateField_management (fcAsFeatureLayer, n1FromMeas, "!NON_STATE_BEGIN_MP!", "PYTHON_9.3")
    # SourceToMeasure = NON_STATE_END_MP
    CalculateField_management (fcAsFeatureLayer, n1ToMeas, "!NON_STATE_END_MP!", "PYTHON_9.3")
    
    # Select LRS_ROUTE_PREFIX IN ('C') AND LRSKEY NOT LIKE '%W0'
    selectionQuery = """ "LRS_ROUTE_PREFIX" IN ('C') AND "LRSKEY" NOT LIKE '%W0' """
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteID = left([LRSKEY], 11) & "W0"
    # This is the VB version.
    # Python version would be calcExpression1 = "!LRSKEY![0:11] + 'W0'"
    calcExpression1 = 'Left([LRSKEY] ,11 ) & "W0"'
    CalculateField_management(fcAsFeatureLayer, n1RouteId, calcExpression1, "VB")
    
    # --------------------- End of old calculations. ------------------------ #
    # -------------------- Start of new calculations. ----------------------- #
    # Local system LRSKeys should go first, before Ramps, but the local system LRSKeys
    # need to be calculated unique prior to that and the code for that hasn't been tested.
    
    # Select where Ramps_LRSKey is not null or '' or ' '.
    selectionQuery = """ "Ramps_LRSKey" IS NOT NULL AND "Ramps_LRSKey" NOT IN ('', ' ') """
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteId = Ramps_LRSKey
    CalculateField_management (fcAsFeatureLayer, n1RouteId,  "!Ramps_LRSKey!", "PYTHON_9.3")
    # SourceFromMeasure = NON_STATE_BEGIN_MP
    CalculateField_management (fcAsFeatureLayer, n1FromMeas, "!NON_STATE_BEGIN_MP!", "PYTHON_9.3")
    # SourceToMeasure = NON_STATE_END_MP
    CalculateField_management (fcAsFeatureLayer, n1ToMeas, "!NON_STATE_END_MP!", "PYTHON_9.3")
    
    # Select where Non_State_System_LRSKey is not null or '' or ' '.
    selectionQuery = """ "Non_State_System_LRSKey" IS NOT NULL AND "Non_State_System_LRSKey" NOT IN ('', ' ') """
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteId = Non_State_System_LRSKey
    CalculateField_management (fcAsFeatureLayer, n1RouteId,  "!Non_State_System_LRSKey!", "PYTHON_9.3")
    # SourceFromMeasure = NON_STATE_BEGIN_MP
    CalculateField_management (fcAsFeatureLayer, n1FromMeas, "!NON_STATE_BEGIN_MP!", "PYTHON_9.3")
    # SourceToMeasure = NON_STATE_END_MP
    CalculateField_management (fcAsFeatureLayer, n1ToMeas, "!NON_STATE_END_MP!", "PYTHON_9.3")
    
    # Would go last as it takes precedence over any other keys, but only needed for State Measure Network System.
    '''
    # Select where State_System_LRSKey is not null or '' or ' '
    selectionQuery = """ "State_System_LRSKey" IS NOT NULL AND "State_System_LRSKey" NOT IN ('', ' ') """
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteId = State_System_LRSKey
    CalculateField_management (fcAsFeatureLayer, n1RouteId, "!State_System_LRSKey!", "PYTHON_9.3")
    # SourceFromMeasure = STATE_BEGIN_MP
    CalculateField_management (fcAsFeatureLayer, n1FromMeas, "!STATE_BEGIN_MP!", "PYTHON_9.3")
    # SourceToMeasure = STATE_END_MP
    CalculateField_management (fcAsFeatureLayer, n1ToMeas, "!STATE_END_MP!", "PYTHON_9.3")
    '''
    
    # Should have better information than the other fields.
    # Select where CountyKey1 is not null or '' or ' '.
    selectionQuery = """ "CountyKey1" IS NOT NULL AND "CountyKey1" NOT IN ('', ' ') """
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteId = Non_State_System_LRSKey
    CalculateField_management (fcAsFeatureLayer, n1RouteId,  "!CountyKey1!", "PYTHON_9.3")
    # SourceFromMeasure = NON_STATE_BEGIN_MP
    CalculateField_management (fcAsFeatureLayer, n1FromMeas, "!F_CNTY_1!", "PYTHON_9.3")
    # SourceToMeasure = NON_STATE_END_MP
    CalculateField_management (fcAsFeatureLayer, n1ToMeas, "!T_CNTY_1!", "PYTHON_9.3")
    
    # Get a count of the features that now have a non-null LRS key in the
    # n1RouteId field along with non-null measures in the n1FromMeas and n1ToMeas fields.
    selectionQuery = ''' "''' + n1RouteId + '''" IS NOT NULL AND "''' + n1RouteId + '''" NOT IN ('', ' ') '''
    selectionQuery += ''' AND "''' + n1FromMeas + '''" IS NOT NULL AND ''' 
    selectionQuery += ''' "''' + n1ToMeas + '''" IS NOT NULL'''
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery)
    
    countResult = GetCount_management(fcAsFeatureLayer)
    intCount = int(countResult.getOutput(0))
    print('Counted ' + str(intCount) + ' features with populated ' + str(n1RouteId) + ', ' +
        str(n1FromMeas) +', and ' +str(n1ToMeas) + '.')
    
    SelectLayerByAttribute_management(fcAsFeatureLayer, "CLEAR_SELECTION")


def KDOTKeyCalculation():
    # Using the new method from Kyle.
    #FieldPopulation with selections and FieldCalculate:
    
    # Get the code from Kyle's github - RHUG repository
    # to calibrate the State Highway measures.
    
    MakeFeatureLayer_management(routesSourceIntermediate, fcAsFeatureLayer)
    
    try:
        RemoveDomainFromField_management(fcAsFeatureLayer, "LRS_ROUTE_PREFIX")
    except:
        print("Could not remove the domain from the 'LRS_ROUTE_PREFIX' column.")
        print("It might not have existed previously.")
    
    # Test for the new fields. If they're not there yet,
    # then add them before the rest of the calculations.
    tempDesc = Describe(fcAsFeatureLayer)
    print("Calculating values for new LRS and measure fields in " + returnFeatureClass(tempDesc.catalogPath) + ".")
    currentFields = tempDesc.fields
    try:
        del tempDesc
    except:
        pass
    
    fieldsNeeded = ['FromDate2', 'ToDate2', 'COUNTYKEY2', 'STATEKEY2']
    fieldsToAdd = [x for x in fieldsNeeded if x not in currentFields]
    
    if 'FromDate2' in fieldsToAdd:
        AddField_management(fcAsFeatureLayer, "FromDate2", "DATE", "", "", "", "FromDate2", nullable)
    else:
        pass
    
    if 'ToDate2' in fieldsToAdd:
        AddField_management(fcAsFeatureLayer, "ToDate2", "DATE", "", "", "", "ToDate2", nullable)
    else:
        pass
    
    if 'COUNTYKEY2' in fieldsToAdd:
        AddField_management(fcAsFeatureLayer, "COUNTYKEY2", "TEXT", "", "", 50, "COUNTYKEY2", nullable)
    else:
        pass
    
    if 'STATEKEY2' in fieldsToAdd:
        AddField_management(fcAsFeatureLayer, "STATEKEY2", "TEXT", "", "", 50, "STATEKEY2", nullable)
    else:
        pass
    
    ###-- For the current network keys to LRS Routes for Network 1 (Source). --###
    # Select LRS_ROUTE_PREFIX IN ('I', 'U', 'K')
    selectionQuery = """ "LRS_ROUTE_PREFIX" IN ('I', 'U', 'K') """
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteId = StateKey1
    CalculateField_management (fcAsFeatureLayer, n1RouteId, "!StateKey1!", "PYTHON_9.3")
    # SourceFromMeasure = STATE_BEGIN_MP
    CalculateField_management (fcAsFeatureLayer, n1FromMeas, "!STATE_BEGIN_MP!", "PYTHON_9.3")
    # SourceToMeasure = STATE_END_MP
    CalculateField_management (fcAsFeatureLayer, n1ToMeas, "!STATE_END_MP!", "PYTHON_9.3")
    
    # Select LRS_ROUTE_PREFIX NOT IN ('I', 'U', 'K') AND LRSKEY IS NOT NULL
    selectionQuery = """ "LRS_ROUTE_PREFIX" NOT IN ('I', 'U', 'K') AND "LRSKEY" IS NOT NULL """
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteId = LRSKEY
    CalculateField_management (fcAsFeatureLayer, n1RouteId,  "!LRSKEY!", "PYTHON_9.3")
    # SourceFromMeasure = NON_STATE_BEGIN_MP
    CalculateField_management (fcAsFeatureLayer, n1FromMeas, "!NON_STATE_BEGIN_MP!", "PYTHON_9.3")
    # SourceToMeasure = NON_STATE_END_MP
    CalculateField_management (fcAsFeatureLayer, n1ToMeas, "!NON_STATE_END_MP!", "PYTHON_9.3")
    
    # Select LRS_ROUTE_PREFIX IN ('C') AND LRSKEY NOT LIKE '%W0'
    selectionQuery = """ "LRS_ROUTE_PREFIX" IN ('C') AND "LRSKEY" NOT LIKE '%W0' """
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteID = left([LRSKEY], 11) & "W0"
    # This is the VB version.
    # Python version would be calcExpression1 = "!LRSKEY![0:11] + 'W0'"
    calcExpression1 = 'Left([LRSKEY] ,11 ) & "W0"'
    CalculateField_management(fcAsFeatureLayer, n1RouteId, calcExpression1, "VB")
    
    ###-- For the networks that will be LRM->LRM'd onto. --###    
    # Negatively numbered statements do preprocessing of the Keys needed to
    # set parsing information for the positively numbered statements to follow.
    ##--------------------Start of Parsing/Precalculation--------------------##
    #-1
    selectionQuery = '''"State_System_LRSKey" IS NOT NULL AND "KDOT_LRS_KEY" IS NULL'''
    setExpression = "!State_System_LRSKey!"
    CalculateField_management(fcAsFeatureLayer, "KDOT_LRS_KEY", setExpression, "PYTHON_9.3")
    
    #-2
    selectionQuery = '''"Non_State_System_LRSKey" IS NOT NULL AND "KDOT_LRS_KEY" IS NULL'''
    setExpression = "!Non_State_System_LRSKey!"
    CalculateField_management(fcAsFeatureLayer, "KDOT_LRS_KEY", setExpression, "PYTHON_9.3")
    
    #-3
    selectionQuery = '''"KDOT_LRS_KEY" IS NULL AND "Non_State_System_LRSKey" IS NULL AND "RAMPS_LRSKEY" IS NOT NULL'''
    setExpression = "!RAMPS_LRSKEY!"
    CalculateField_management(fcAsFeatureLayer, "KDOT_LRS_KEY", setExpression, "PYTHON_9.3")
    
    #-4
    selectionQuery = '''"LRS_ROUTE_PREFIX" IS NULL'''
    setExpression = "str(!RAMPS_LRSKEY!)[4:5]"
    CalculateField_management(fcAsFeatureLayer, "KDOT_LRS_KEY", setExpression, "PYTHON_9.3")
    
    #-5 -- Parse the fields for STATE HIGHWAY SYSTEM
    # Use an update cursor to set several fields at once:
    updateFields = ["KDOT_LRS_KEY", "LRS_COUNTY_PRE", "LRS_ROUTE_NUM", "LRS_ROUTE_NUM1", "LRS_ROUTE_SUFFIX", "LRS_DIRECTION", "LRS_SUBCLASS", "LRS_ADMO", "LRS_UNIQUE_IDENT", "LRS_UNIQUE_IDENT1"]
    selectionQuery = '''"LRS_ROUTE_PREFIX" in ('I', 'U', 'K')'''
    newCursor = daUpdateCursor(fcAsFeatureLayer, updateFields, selectionQuery)
    for cursorRow in newCursor:
        editRow = list(cursorRow)
        editRow[1] = editRow[0][0:3]
        editRow[2] = editRow[0][4:9]
        editRow[3] = editRow[0][4:9]
        editRow[4] = editRow[0][10:11]
        editRow[5] = editRow[0][13:15]
        editRow[6] = None
        editRow[7] = None
        editRow[8] = editRow[0][11:12]
        editRow[9] = editRow[0][11:12]
        newCursor.updateRow(editRow)
    try:
        del newCursor
    except:
        pass
    
    #-6 -- Parse the fields for NON_STATE_HIGHWAYS_URBAN_CLASSIFIEDS
    ### - Do something separately to --UPDATE THE COUNTY NUMBER IN LRS_COUNTY_PRE BY SPATIAL LOCATION - ###
    # Use an update cursor to set several fields at once:
    updateFields = ["KDOT_LRS_KEY", "LRS_URBAN_PRE", "LRS_ROUTE_NUM", "LRS_ROUTE_NUM1", "LRS_ROUTE_SUFFIX", "LRS_UNIQUE_IDENT", "LRS_UNIQUE_IDENT1", "LRS_ADMO", "LRS_SUBCLASS", "FMEAS", "TMEAS", "NON_STATE_BEGIN_MP", "NON_STATE_END_MP"]
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'C' AND FMEAS IS NULL AND TMEAS IS NULL'''
    newCursor = daUpdateCursor(fcAsFeatureLayer, updateFields, selectionQuery)
    for cursorRow in newCursor:
        editRow = list(cursorRow)
        editRow[1] = editRow[0][0:3]
        editRow[2] = editRow[0][4:9]
        editRow[3] = editRow[0][4:9]
        editRow[4] = editRow[0][10:11]
        editRow[5] = editRow[0][11:12]
        editRow[6] = '0' + editRow[0][13:14]
        editRow[7] = editRow[0][14:15]
        editRow[8] = editRow[10]
        editRow[9] = editRow[11]
        newCursor.updateRow(editRow)
    try:
        del newCursor
    except:
        pass
    
    #-7 Parse the fields for NON_STATE_HIGHWAYS Rural Secondary
    # Use an update cursor to set several fields at once:
    updateFields = ["KDOT_LRS_KEY", "LRS_COUNTY_PRE", "LRS_ROUTE_NUM", "LRS_ROUTE_NUM1", "LRS_ROUTE_SUFFIX", "LRS_UNIQUE_IDENT", "LRS_UNIQUE_IDENT1", "LRS_ADMO", "LRS_SUBCLASS", "FMEAS", "TMEAS", "NON_STATE_BEGIN_MP", "NON_STATE_END_MP"]
    selectionQuery = '''"LRS_ROUTE_PREFIX" in ('R', 'M') AND FMEAS IS NULL AND TMEAS IS NULL'''
    newCursor = daUpdateCursor(fcAsFeatureLayer, updateFields, selectionQuery)
    for cursorRow in newCursor:
        editRow = list(cursorRow)
        editRow[1] = editRow[0][0:3]
        editRow[2] = editRow[0][4:9]
        editRow[3] = editRow[0][4:9]
        editRow[4] = editRow[0][10:11]
        editRow[5] = editRow[0][11:12]
        editRow[6] = '0' + editRow[0][13:14]
        editRow[7] = editRow[0][14:15]
        editRow[8] = editRow[10]
        editRow[9] = editRow[11]
        newCursor.updateRow(editRow)
    try:
        del newCursor
    except:
        pass
    
    #-8 Parse the fields for NON_STATE_HIGHWAYS Local Roads
    # Use an update cursor to set several fields at once:
    updateFields = ["KDOT_LRS_KEY", "LRS_COUNTY_PRE", "LRS_ROUTE_NUM", "LRS_ROUTE_NUM1", "LRS_ROUTE_SUFFIX", "LRS_UNIQUE_IDENT", "LRS_UNIQUE_IDENT1", "LRS_ADMO", "LRS_SUBCLASS", "FMEAS", "TMEAS", "NON_STATE_BEGIN_MP", "NON_STATE_END_MP"]
    selectionQuery = '''"LRS_ROUTE_PREFIX" in ('R', 'M') AND FMEAS IS NULL AND TMEAS IS NULL'''
    newCursor = daUpdateCursor(fcAsFeatureLayer, updateFields, selectionQuery)
    for cursorRow in newCursor:
        editRow = list(cursorRow)
        editRow[1] = editRow[0][0:3]
        editRow[2] = editRow[0][4:9]
        editRow[3] = editRow[0][4:9]
        editRow[4] = editRow[0][10:11]
        editRow[5] = editRow[0][11:12]
        editRow[6] = '0' + editRow[0][13:14]
        editRow[7] = editRow[0][14:15]
        editRow[8] = editRow[10]
        editRow[9] = editRow[11]
        newCursor.updateRow(editRow)
    try:
        del newCursor
    except:
        pass
    
    #-9 Parse the fields for RAMPS
    # Use an update cursor to set several fields at once:
    updateFields = ["KDOT_LRS_KEY", "LRS_COUNTY_PRE", "LRS_ROUTE_NUM", "LRS_ROUTE_NUM1", "LRS_UNIQUE_IDENT", "LRS_UNIQUE_IDENT1", "LRS_ADMO", "FMEAS"]
    selectionQuery = '''"LRS_ROUTE_PREFIX" in ('R', 'M') AND FMEAS IS NULL AND TMEAS IS NULL'''
    newCursor = daUpdateCursor(fcAsFeatureLayer, updateFields, selectionQuery)
    for cursorRow in newCursor:
        editRow = list(cursorRow)
        editRow[1] = editRow[0][0:3]
        editRow[2] = editRow[0][4:9]
        editRow[3] = editRow[0][4:9]
        editRow[4] = editRow[0][9:11]
        editRow[5] = editRow[0][9:11]
        editRow[6] = editRow[0][11:12]
        editRow[7] = 0
        newCursor.updateRow(editRow)
    try:
        del newCursor
    except:
        pass
    
    #-10
    selectionQuery = '''"LRS_PRIMARY_DIR" IS NULL'''
    setExpression = "0"
    CalculateField_management(fcAsFeatureLayer, "LRS_PRIMARY_DIR", setExpression, "PYTHON_9.3")
    
    #-11
    selectionQuery = '''"FromDate" IS NULL'''
    setExpression = "'1827-01-01'" ## Will have to check this.
    CalculateField_management(fcAsFeatureLayer, "FromDate2", setExpression, "PYTHON_9.3")
    
    #-12
    selectionQuery = '''"STATUS" IN ('Not Built', 'NOT BUILT')'''
    setExpression = "'2020-01-01'" ## Will have to check this.
    CalculateField_management(fcAsFeatureLayer, "FromDate2", setExpression, "PYTHON_9.3")
    
    #-13
    selectionQuery = '''"STATUS" IN ('CLOSED', 'Closed')'''
    setExpression = "'2014-01-01'" ## Will have to check this.
    CalculateField_management(fcAsFeatureLayer, "ToDate2", setExpression, "PYTHON_9.3")
    
    #-14
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'L' AND "RouteID" IS NULL'''
    setExpression = "!LRS_COUNTY_PRE! + !LRS_ROUTE_PREFIX! + !LRS_ROUTE_NUM1! + !LRS_ROUTE_SUFFIX! + !LRS_UNIQUE_IDENT1! + !LRS_PRIMARY_DIR!"
    CalculateField_management(fcAsFeatureLayer, "RouteID", setExpression, "PYTHON_9.3")
    
    #-15
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'X' AND "RouteID" IS NULL'''
    setExpression = "!LRS_COUNTY_PRE! + !LRS_ROUTE_PREFIX! + !LRS_ROUTE_NUM1! + !LRS_UNIQUE_IDENT1! + !LRS_PRIMARY_DIR!"
    CalculateField_management(fcAsFeatureLayer, "RouteID", setExpression, "PYTHON_9.3")
    
    #-16
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'C' AND "LRS_PRIMARY_DIR" IS NULL'''
    setExpression = "0"
    CalculateField_management(fcAsFeatureLayer, "LRS_PRIMARY_DIR", setExpression, "PYTHON_9.3")
    ##---------------------End of Parsing/Precalculation---------------------##
    
    # This (the 2nd email version) should entirely supersede the contents of the first email
    # version, but the attachment content from the first email still runs prior to this,
    # hence the negatively numbered calculations above.
    
    ##--------------------------Start of County Key2-------------------------##
    #1
    #/*  set all unique Identifiers to 00 if they werent calculated from the LRS Key   */
    selectionQuery = '''"LRS_UNIQUE_IDENT1" IS NULL'''
    setExpression = "'00'"
    CalculateField_management(fcAsFeatureLayer, "LRS_UNIQUE_IDENT1", setExpression, "PYTHON_9.3")
    
    #2
    #/*  Calculate the County key field for centerlines identified as Ramps   */
    #/*  Assume all route suffix codes for ramps are 0   */
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'X' '''
    setExpression = "!LRS_COUNTY_PRE! + '4' + !LRS_ROUTE_NUM! + '0' + !KDOT_DIRECTION_CALC! + !LRS_UNIQUE_IDENT1!"
    CalculateField_management(fcAsFeatureLayer, "COUNTYKEY2", setExpression, "PYTHON_9.3")
    
    #3
    #/*  Calculate the County key field for rural major, minor, and urban collector   */
    #/*  Assume all route suffix codes for these classified routes are 0   */
    selectionQuery = '''"LRS_ROUTE_PREFIX" in ('R', 'M', 'C')'''
    setExpression = "!LRS_COUNTY_PRE! + '5' + !LRS_ROUTE_NUM! + '0' + !KDOT_DIRECTION_CALC! + !LRS_UNIQUE_IDENT1!"
    CalculateField_management(fcAsFeatureLayer, "COUNTYKEY2", setExpression, "PYTHON_9.3")
    
    #4
    #/*  Calculate the County key field Kansas State Highwayas without a unique identifier  */
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'K' AND "LRS_UNIQUE_IDENT1" = '00' '''
    setExpression = "!LRS_COUNTY_PRE! + '3' + !LRS_ROUTE_NUM! + !LRS_ROUTE_SUFFIX! + !KDOT_DIRECTION_CALC!"
    CalculateField_management(fcAsFeatureLayer, "COUNTYKEY2", setExpression, "PYTHON_9.3")
    
    #5
    #/*  Calculate the County key field Kansas State Highways with a unique identifier */
    #/*  Assume State Key unique identifier is the same as the county route unique identifier   */
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'K' AND "LRS_UNIQUE_IDENT1" <> '00'  '''
    setExpression = "!LRS_COUNTY_PRE! + '3' + !LRS_ROUTE_NUM! + !LRS_ROUTE_SUFFIX! + !KDOT_DIRECTION_CALC! + !LRS_UNIQUE_IDENT1!"
    CalculateField_management(fcAsFeatureLayer, "COUNTYKEY2", setExpression, "PYTHON_9.3")
    
    #6
    #/*  Calculate the County key field for US Numbered Routes with no unique identifier   */
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'U' AND "LRS_UNIQUE_IDENT1" = '00' '''
    setExpression = "!LRS_COUNTY_PRE! + '2' + !LRS_ROUTE_NUM! + !LRS_ROUTE_SUFFIX! + !KDOT_DIRECTION_CALC!"
    CalculateField_management(fcAsFeatureLayer, "COUNTYKEY2", setExpression, "PYTHON_9.3")
    
    #7
    #/*  Calculate the County key field for US Numbered Routes with unique identifier   */
    #/*  Assume State Key unique identifier is the same as the county route unique identifier   */
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'U' AND "LRS_UNIQUE_IDENT1" <> '00' '''
    setExpression = "!LRS_COUNTY_PRE! + '2' + !LRS_ROUTE_NUM! + !LRS_ROUTE_SUFFIX! + !KDOT_DIRECTION_CALC! + !LRS_UNIQUE_IDENT1!"
    CalculateField_management(fcAsFeatureLayer, "COUNTYKEY2", setExpression, "PYTHON_9.3")
    
    #8
    #/*  Calculate the County key field for Interstate Highways */
    #/*  Assume there are no unique identifiers on these */
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'I' '''
    setExpression = "!LRS_COUNTY_PRE! + '1' + !LRS_ROUTE_NUM! + !LRS_ROUTE_SUFFIX! + !KDOT_DIRECTION_CALC!"
    CalculateField_management(fcAsFeatureLayer, "COUNTYKEY2", setExpression, "PYTHON_9.3")
    ##---------------------------End of County Key2--------------------------##
    
    ##---------------------------Start of State Key2-------------------------##
    #9
    #/*  Calculate the State Key field for Kansas State Highways with Unique Identifiers */
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'K' AND "LRS_UNIQUE_IDENT1" <> '00' '''
    setExpression = "'3' + str(!LRS_ROUTE_NUM!)[2:5] + !LRS_ROUTE_SUFFIX! + !KDOT_DIRECTION_CALC! + str(!LRS_UNIQUE_IDENT1!)[1]"
    CalculateField_management(fcAsFeatureLayer, "STATEKEY2", setExpression, "PYTHON_9.3")
    
    #10
    #/*  Calculate the State Key field for Kansas State Highways without Unique Identifiers */
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'K' AND "LRS_UNIQUE_IDENT1" = '00' '''
    setExpression = "'3' + str(!LRS_ROUTE_NUM!)[2:5] + !LRS_ROUTE_SUFFIX! + !KDOT_DIRECTION_CALC!"
    CalculateField_management(fcAsFeatureLayer, "STATEKEY2", setExpression, "PYTHON_9.3")
    
    #11
    #/*  Calculate the State Key field for Kansas State Highways with Unique Identifiers */
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'U' AND "LRS_UNIQUE_IDENT1" <> '00' '''
    setExpression = "'2' + str(!LRS_ROUTE_NUM!)[2:5] + !LRS_ROUTE_SUFFIX! + !KDOT_DIRECTION_CALC! + str(!LRS_UNIQUE_IDENT1!)[1]"
    CalculateField_management(fcAsFeatureLayer, "STATEKEY2", setExpression, "PYTHON_9.3")
    
    #12
    #/*  Calculate the State key field for US Numbered Routes without unique identifiers   */
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'U' AND "LRS_UNIQUE_IDENT1" = '00' '''
    setExpression = "'2' + str(!LRS_ROUTE_NUM!)[2:5] + !LRS_ROUTE_SUFFIX! + !KDOT_DIRECTION_CALC!"
    CalculateField_management(fcAsFeatureLayer, "STATEKEY2", setExpression, "PYTHON_9.3")
    
    #13
    #/*  Calculate the State key field for US Numbered Routes with unique identifiers   */
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'I' AND "LRS_UNIQUE_IDENT1" <> '00' '''
    setExpression = "'1' + str(!LRS_ROUTE_NUM!)[2:5] + !LRS_ROUTE_SUFFIX! + !KDOT_DIRECTION_CALC! + str(!LRS_UNIQUE_IDENT1!)[1]"
    CalculateField_management(fcAsFeatureLayer, "STATEKEY2", setExpression, "PYTHON_9.3")
    
    #14
    #/*  Calculate the County key field for Interstate Highways */
    #/*  Assume there are no unique identifiers on these */
    selectionQuery = '''"LRS_ROUTE_PREFIX" = 'I' '''
    setExpression = "'1' + str(!LRS_ROUTE_NUM!)[2:5] + !LRS_ROUTE_SUFFIX! + !KDOT_DIRECTION_CALC!"
    CalculateField_management(fcAsFeatureLayer, "STATEKEY2", setExpression, "PYTHON_9.3")
    ##----------------------------End of State Key2--------------------------##
    print("KDOT Key Calculation Complete.")


def KDOTOverlappingRoutesDissolveFix():
    #IMPORTANT!
    #TODO: Multithread this before iteration 3.
    # Also, check again to see if it actually fixes anything.
    # If not, then don't even do it.
    # It seems like it should, but....
    
    # Function steps
    # 0a.) Run the garbage collector.
    # 0b.) Make a new error report file.
    # 1.) Make an in_memory copy of the centerlines.
    #### A field map would have to be created for each dissolved feature layer, so it's not really worth it.
    # 2.) Get a list of all of the unique LRS Keys
    # 3.) Loop through the list of unique LRS Keys
    # 4.) For each LRS Key, select all the features with that LRS Key.
    # 5.) Count selected features.
    # 6.) Make a new layer or dissolved layer from this selection. -- Question about fields.
    # 7.) Count the number of dissolved features.
    # 8a.) If the number of dissolved features is 0, then append the error to the error file
    #       and go on to the next LRS Key in the loop.
    # 8b.) Else, spatially select features in the original feature class with 'SHARE_A_LINE_SEGMENT_WITH'.
    # 9.) From the spatial select, reselect features that have the same LRS Key.
    # 10.) Count to make sure that at least one feature is selected.
    # 11.) If so, delete that feature.
    # 12.) Cursor the features out of the dissolve layer.
    # 13.) Insert the features from the dissolve layer into the in_memory copy of the centerlines.
    # 14.) When the loop is complete, save the in_memory copy of the centerlines
    #       to a gdb on disk.
    
    # 0a.) Run the garbage collector.
    print("Calling gc.collect() prior to starting the dissolve process.")
    gc.collect()
    
    try:
        Delete_management('in_memory')
    except:
        pass
    
    # 0b.) Make a new error report file.
    # Open/create a file with overwrite ('w') and say
    # 'These are the multiSelectionQueries which have 0 features returned when a dissolve is attempted: \n'
    with open(dissolveErrorsFile, 'w') as errorFile:
        errorFile.write('These are the multiSelectionQueries which have 0 features returned when a dissolve is attempted: \n')
    
    # 1a.) Make an copy of the simplified and flipped centerlines to modify with dissolves.
    CopyFeatures_management(flippedOutput, dissolvedFlippedOutput)
    
    # 1b.) Make a feature layer from the simplified and flipped centerlines.
    MakeFeatureLayer_management(dissolvedFlippedOutput, fcAsFeatureLayer)
    
    # 2.) Get a list of all of the unique LRS Keys
    ############ Modify this process to only get a list of LRS Keys that have more than one feature.
    ############ everything else can be skipped for the purpose of dissolving.
    lrsKeyFieldList = [str(n1RouteId)]
    newCursor = daSearchCursor(fcAsFeatureLayer, lrsKeyFieldList)
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
    print('Found ' + str(len(uniqueLRSKeysList)) + ' unique LRS Keys in the centerline data.')
    
    #Single selection was way too slow (approximately 68 hours just for the selections, not including other processes).
    #selectionQuery = ''' "''' + str(n1RouteId) + '''" IS NOT NULL AND "''' + str(n1RouteId) + '''" IN (\'''' + str(uniqueKeyItem) + '''\')'''
    
    #Use multiSelection instead.
    multiSelectionQuery = ''' "''' + str(n1RouteId) + '''" IS NOT NULL AND "''' + str(n1RouteId) + '''" IN ('''
    multiCounter = 0
    
    #multiDissolveFields = str(n1RouteId) + ";LRS_COUNTY_PRE;LRS_ROUTE_PREFIX;LRS_ROUTE_NUM;LRS_ROUTE_SUFFIX;LRS_UNIQUE_IDENT;LRS_DIRECTION"
    multiDissolveFields = [str(n1RouteId), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX', 'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX', 'LRS_UNIQUE_IDENT',
        'LRS_DIRECTION']
    multiStatsFields = str(n1FromMeas) + " MIN;" + str(n1ToMeas) + " MAX"
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
        
        try:
            Delete_management(dissolveOutFC)
        except:
            print("Could not delete the dissolveOutFC layer.")
        
        # 4.) For groups of up to 2000 LRS Keys, select all the features with those LRS Keys.
        maxDissolveCount = 1999
        if multiCounter <= maxDissolveCount:
            multiSelectionQuery += """'""" + str(uniqueKeyItem) + """'""" + """, """
            multiCounter += 1
        else:
            # Add the current item, then
            multiSelectionQuery += """'""" + str(uniqueKeyItem) + """'""" + """, """
            # Remove the trailing ", " and add a closing parenthesis.
            multiSelectionQuery = multiSelectionQuery[:-2] + """) """
            SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", multiSelectionQuery)
            # Have to do from step 5 on here also.
            
            ### -shouldbeafunctionblock#1- ###
            # 5.) Count selected features.
            countResult0 = GetCount_management(fcAsFeatureLayer)
            intCount0 = int(countResult0.getOutput(0))
            if intCount0 == 1:
                print('Counted just ' + str(intCount) + ' feature returned for that dissolve.')
            elif intCount0 >= 2:
                # 6.) Make a new layer or dissolved layer from this selection. -- Question about fields.
                Dissolve_management(fcAsFeatureLayer, dissolveOutFC, multiDissolveFields, multiStatsFields, singlePart, unsplitLines)
                
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
                    SelectLayerByAttribute_management(fcAsFeatureLayer, 'NEW_SELECTION', multiSelectionQuery)
                    # 9.) Else, spatially select features in the original feature class with 'SHARE_A_LINE_SEGMENT_WITH'.
                    SelectLayerByLocation_management(fcAsFeatureLayer, 'SHARE_A_LINE_SEGMENT_WITH', dissolveOutFC, 0, 'SUBSET_SELECTION')
                    # 10.) Count to make sure that at least one feature is selected.
                    countResult2 = GetCount_management(fcAsFeatureLayer)
                    intCount2 = int(countResult2.getOutput(0))
                    print('There were ' + str(intCount2) + ' features selected in the fcAsFeatureLayer layer.')
                    if intCount2 >= 1:
                        # 11.) If so, cursor the features out of the dissolve layer.
                        featureList = list()
                        searchCursorFields = [str(n1RouteId), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX', 'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX',
                            'LRS_UNIQUE_IDENT', 'LRS_DIRECTION', 'MIN_' + str(n1FromMeas), 'MAX_' + str(n1ToMeas), 'SHAPE@']
                        newCursor = daSearchCursor(dissolveOutFC, searchCursorFields)
                        
                        for cursorItem in newCursor:
                            featureList.append(list(cursorItem))
                        
                        try:
                            del newCursor
                        except:
                            pass
                        
                        # 12.) Delete the selected features in the input layer.
                        try:
                            DeleteFeatures_management(fcAsFeatureLayer)
                        except:
                            print("Could not delete features for the selection " + str(multiSelectionQuery) + ".")
                        # 13.) Insert the features from the dissolve layer into the copy of the centerlines.
                        insertCursorFields = [str(n1RouteId), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX', 'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX',
                            'LRS_UNIQUE_IDENT', 'LRS_DIRECTION', str(n1FromMeas), str(n1ToMeas), 'SHAPE@']
                        newCursor = daInsertCursor(fcAsFeatureLayer, insertCursorFields)
                        
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
            multiSelectionQuery = ''' "''' + str(n1RouteId) + '''" IS NOT NULL AND "''' + str(n1RouteId) + '''" IN ('''
            multiCounter = 0
            ### -shouldbeafunctionblock#1- ###
    
    # After the for loop, if there is still anything remaining which was unselected in the
    # the previous multiSelectionQuery steps.
    # Remove the trailing ", " and add a closing parenthesis.
    multiSelectionQuery = multiSelectionQuery[:-2] + """) """
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", multiSelectionQuery)    
    
    # Then redo from step 5 on at the end of the loop IF there is anything left to select
    # which was not selected... so if selectionCounter != 0.        
    
    ### -shouldbeafunctionblock#2- ###
    # 5.) Count selected features.
    countResult0 = GetCount_management(fcAsFeatureLayer)
    intCount0 = int(countResult0.getOutput(0))
    if intCount0 == 1:
        print('Counted just ' + str(intCount) + ' feature returned for that dissolve.')
    elif intCount0 >= 2:
        # 6.) Make a new layer or dissolved layer from this selection. -- Question about fields.
        Dissolve_management(fcAsFeatureLayer, dissolveOutFC, multiDissolveFields, multiStatsFields, singlePart, unsplitLines)
        
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
            SelectLayerByAttribute_management(fcAsFeatureLayer, 'NEW_SELECTION', multiSelectionQuery)
            # 9.) Else, spatially select features in the original feature class with 'SHARE_A_LINE_SEGMENT_WITH'.
            SelectLayerByLocation_management(fcAsFeatureLayer, 'SHARE_A_LINE_SEGMENT_WITH', dissolveOutFC, 0, 'SUBSET_SELECTION')
            # 10.) Count to make sure that at least one feature is selected.
            countResult2 = GetCount_management(fcAsFeatureLayer)
            intCount2 = int(countResult2.getOutput(0))
            print('There were ' + str(intCount2) + ' features selected in the fcAsFeatureLayer layer.')
            if intCount2 >= 1:
                # 11.) If so, cursor the features out of the dissolve layer.
                featureList = list()
                searchCursorFields = [str(n1RouteId), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX', 'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX',
                    'LRS_UNIQUE_IDENT', 'LRS_DIRECTION', 'MIN_' + str(n1FromMeas), 'MAX_' + str(n1ToMeas), 'SHAPE@']
                newCursor = daSearchCursor(dissolveOutFC, searchCursorFields)
                
                for cursorItem in newCursor:
                    featureList.append(list(cursorItem))
                
                try:
                    del newCursor
                except:
                    pass
                
                # 12.) Delete the selected features in the input layer.
                try:
                    DeleteFeatures_management(fcAsFeatureLayer)
                except:
                    print("Could not delete features for the selection " + str(multiSelectionQuery) + ".")
                # 13.) Insert the features from the dissolve layer into the copy of the centerlines.
                insertCursorFields = [str(n1RouteId), 'LRS_COUNTY_PRE', 'LRS_ROUTE_PREFIX', 'LRS_ROUTE_NUM', 'LRS_ROUTE_SUFFIX',
                    'LRS_UNIQUE_IDENT', 'LRS_DIRECTION', str(n1FromMeas), str(n1ToMeas), 'SHAPE@']
                newCursor = daInsertCursor(fcAsFeatureLayer, insertCursorFields)
                
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
    
    # Now calculate the data from the dissolve back into the KDOT_LRS_KEY and county_log_begin and county_log_end.
    # Fields to calculate into are: KDOTRouteId, KDOTMeasBeg, KDOTMeasEnd
    # Fields to calculate from are: n1RouteId, n1FromMeas, n1ToMeas
    CalculateField_management(fcAsFeatureLayer, KDOTRouteId, "!" + str(n1RouteId) + "!", "PYTHON_9.3")
    CalculateField_management(fcAsFeatureLayer, KDOTMeasBeg, "!" + str(n1FromMeas) + "!", "PYTHON_9.3")
    CalculateField_management(fcAsFeatureLayer, KDOTMeasEnd, "!" + str(n1ToMeas) + "!", "PYTHON_9.3")


def KDOTOverlappingRoutesFlaggingFix():
    # conflationCountyBoundary = r'\\gisdata\ArcGIS\GISdata\Connection_files\Conflation2012_RO.sde\Conflation.SDE.NG911\Conflation.SDE.CountyBoundary'
    # Copy the "Conflation.SDE.CountyBoundary" layer to the FGDB.
    
    if Exists(routesSourceIntermediate):
        Delete_management(routesSourceIntermediate)
    else:
        pass
    
    CopyFeatures_management(dissolvedFlippedOutput, routesSourceIntermediate)
    
    tempDesc = Describe(routesSourceIntermediate)
    print("Calculating values for new LRS and measure fields in " + returnFeatureClass(tempDesc.catalogPath) + ".")
    
    currentFields = [x.name for x in tempDesc.fields]
    
    try:
        del tempDesc
    except:
        pass
    
    fieldsNeeded = ['OverlapStatus']
    
    fieldsToAdd = [x for x in fieldsNeeded if x not in currentFields]
    
    if 'OverlapStatus' in fieldsToAdd:
        AddField_management(routesSourceIntermediate, "OverlapStatus", "TEXT", "", "", 1, "OverlapStatus", nullable)
    else:
        pass
    
    fcAsFeatureLayerRSCFL = 'routesSourceIntermediateFL'
    fcAsFeatureLayerRSCFL_FCName = returnFeatureClass(routesSourceIntermediate)
    countyBoundary_FCName = returnFeatureClass(conflationCountyBoundary)
    
    joinField1 = 'STEWARD'
    indexFieldList = [joinField1]
    selectionQuery2 = "NOT (KDOT_COUNTY_L = KDOT_COUNTY_R)"
    MakeFeatureLayer_management(routesSourceIntermediate, fcAsFeatureLayerRSCFL, selectionQuery2)
    
    countResult = GetCount_management(fcAsFeatureLayerRSCFL)
    intCount = int(countResult.getOutput(0))
    
    print(str(intCount) + " records were added to the feature layer defined by the query, " + str(selectionQuery2) +  ".")
    
    try:
        RemoveIndex_management(fcAsFeatureLayerRSCFL, stewardIndexNameRSC)
    except:
        print("The attribute index " + stewardIndexNameRSC + " could not be removed, or it may not have existed to begin with.")
    try:
        RemoveIndex_management(conflationCountyBoundary, stewardIndexNameCB)
    except:
        print("The attribute index " + stewardIndexNameCB + " could not be removed, or it may not have existed to begin with.")
    
    print("Adding attribute indexes...")
    # Then, add an index on the "Steward" field to both of them.
    AddIndex_management(routesSourceIntermediate, indexFieldList, stewardIndexNameRSC)
    AddIndex_management(conflationCountyBoundary, indexFieldList, stewardIndexNameCB)
    
    # Join the tables based on their "STEWARD" fields.
    AddJoin_management(fcAsFeatureLayerRSCFL, joinField1, conflationCountyBoundary, joinField1)
    print("Attribute indexes added and join created.")
    # Select by Attributes from said table where "CountyLRSPrefix" field == "Conflation.SDE.CountyBoundary"."KDOT_CountyNumStr" field
    # Then, reverse the selection.
    # These are the "zombie routes".
    
    # ----------------------------------------------------------------------- #
    # "NOT (RoutesSource.LRS_COUNTY_PRE = CountyBoundary.KDOT_CountyNumStr)"
    # causes Python and ArcMap to both crash when passed to
    # SelectLayerByAttribute_management for this layer.
    # Instead, use RoutesSource.LRS_COUNTY_PRE = CountyBoundary.KDOT_CountyNumStr, then
    # invert the selection.
    
    fieldNameToFind1 = fcAsFeatureLayerRSCFL_FCName + '.LRS_COUNTY_PRE'
    fieldNameToFind2 = countyBoundary_FCName + '.KDOT_CountyNumStr'
    
    listedFields = ListFields(fcAsFeatureLayerRSCFL)
    
    for fieldObject in listedFields:
        if fieldObject.aliasName == 'LRS_COUNTY_PRE' or fieldObject.aliasName == fieldNameToFind1:
            print 'LRS_COUNTY_PRE found!'
            fieldNameToFind1 = fieldObject.name 
        else:
            pass
        if fieldObject.aliasName == 'KDOT_CountyNumStr' or fieldObject.aliasName == fieldNameToFind2:
            print 'KDOT_CountyNumStr found!'
            fieldNameToFind2 = fieldObject.name 
        else:
            pass
    
    selectionQuery3 = fieldNameToFind1 + ''' <> ''' + '''''' + fieldNameToFind2
    
    print(str(selectionQuery3) + " is being used as the selection query.")
    
    
    SelectLayerByAttribute_management(fcAsFeatureLayerRSCFL, "NEW_SELECTION", selectionQuery3)
    #getCount, then Print the results.
    countResult = GetCount_management(fcAsFeatureLayerRSCFL)
    intCount = int(countResult.getOutput(0))
    print(str(intCount) + " records were selected by the query, " + str(selectionQuery3) +  ".")
    
    # Clean-up try/excepts.
    print ('Removing joins and indexes.')
    try:
        RemoveJoin_management(fcAsFeatureLayerRSCFL)
    except:
        print("The join could not be removed, or it may not have existed to begin with.")
    try:
        RemoveIndex_management(fcAsFeatureLayerRSCFL, stewardIndexNameRSC)
    except:
        print("The attribute index " + stewardIndexNameRSC + " could not be removed, or it may not have existed to begin with.")
    try:
        RemoveIndex_management(conflationCountyBoundary, stewardIndexNameCB)
    except:
        print("The attribute index " + stewardIndexNameCB + " could not be removed, or it may not have existed to begin with.")
    
    countResult = GetCount_management(fcAsFeatureLayerRSCFL)
    intCount = int(countResult.getOutput(0))
    
    # Then, calculate the field for the Zombie Suffix.
    print("Setting the OverlapStatus for " + str(intCount) + " records to 'Z'.")
    expressionText = "'Z'"
    CalculateField_management(fcAsFeatureLayerRSCFL, "OverlapStatus", expressionText, "PYTHON_9.3")
    
    # Instead of just excluding these, could calculate the LRS Key to a modified version that
    # includes the Z.


def KDOT3RoutesSourceExport():
    # For this to work, you have to do whatever is needed to populate the LRS_ROUTE_PREFIX field correctly,
    # and also to populate the LRS_ROUTE_SUFFIX field with 'G' where necessary. -- Then, you can
    # run this prior to route creation to copy the routes that should be created to a separate feature
    # class and create the routes using that feature class as a base.
    
    # Do the LRS_ROUTE_PREFIX key parsing right here.
    
    # Also requires an improved Ramp movement process so that the LRS Key information doesn't get
    # disrupted during the move. Otherwise, that data is missing for this part of the selection.
    
    processedFeatureLayer = 'ProcessedRoutes'
    MakeFeatureLayer_management(routesSourceIntermediate, processedFeatureLayer)
    
    # Contains only the routes that we (should) have event data for.
    # Won't work correctly for some of the ramps that get appended in since they don't have
    # a calculated LRS_ROUTE_PREFIX -- so add that for them until you work out the improved process.
    selectionQuery1 = '''LRS_ROUTE_PREFIX IN ('I', 'U', 'K', 'C', 'R', 'M', 'X') AND (OverlapStatus IS NULL OR OverlapStatus = '') '''
    SelectLayerByAttribute_management(processedFeatureLayer, "NEW_SELECTION", selectionQuery1)
    # Probably won't work without a delete, so delete if it exists (it should always exist at this step.)
    ## Check to see if the output dataset exists. If so, delete it
    # then save the features.
    if Exists(routesSource1):
        Delete_management(routesSource1)
    else:
        pass
    print("Exporting to: " + str(routesSource1) + ".")
    CopyFeatures_management(processedFeatureLayer, routesSource1)
    DefineProjection_management(routesSource1, inputCenterlinesSR)
    print("Export complete.")
    
    # Contains all the routes that we could find in Kansas and some that Oklahoma left unguarded.
    selectionQuery2 = ''
    # Clear + Switch = All selected
    SelectLayerByAttribute_management(processedFeatureLayer, "CLEAR_SELECTION")
    SelectLayerByAttribute_management(processedFeatureLayer, "SWITCH_SELECTION")
    ## Check to see if the output dataset exists. If so, delete it
    # then save the features.
    if Exists(routesSource2):
        Delete_management(routesSource2)
    else:
        pass
    print("Exporting to: " + str(routesSource2) + ".")
    CopyFeatures_management(processedFeatureLayer, routesSource2)
    DefineProjection_management(routesSource2, inputCenterlinesSR)
    print("Export complete.")
    
    # Contains only the state network routes and uses a different measure for the location along the route.
    selectionQuery3 = '''LRS_ROUTE_PREFIX IN ('I', 'U', 'K')'''
    SelectLayerByAttribute_management(processedFeatureLayer, "NEW_SELECTION", selectionQuery3)
    ## Check to see if the output dataset exists. If so, delete it
    # then save the features.
    if Exists(routesSource3):
        Delete_management(routesSource3)
    else:
        pass
    print("Exporting to: " + str(routesSource3) + ".")
    CopyFeatures_management(processedFeatureLayer, routesSource3)
    DefineProjection_management(routesSource3, inputCenterlinesSR)
    print("Export complete.")
    
    print("All exports done.")
    
    # See Kyle's code for calibrating the route measures for the State Network prior to creating
    # either routesSource1 or routesSource3.
    # Related -- Probably don't need to actually delete the fields, since you can just turn them off
    # if you don't want them in the output, and then export to another feature class with only
    # what you want turned on.


def main():
    print("Starting the routes source creation process.")
    routesSourceCreation() # Currently modified for testing.
    print("Routes source creation completed.")


if __name__ == "__main__":
    main()

else:
    pass
    
# Several places in the Non-State system where measures are backwards and need to be flipped -- geometry also needs to be flipped.
# 23 ----------- 34
# 34 --26.3 26.3-23