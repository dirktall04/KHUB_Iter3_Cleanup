#!/usr/bin/env python
# -*- coding: utf-8 -*-
#datareviewerchecks_kdotprocessimprovements_iter2_unusedcode.py


# Don't use this. It causes issues with the KDOT3RoutesSourceExport function.
def KDOTRampReplacement_Old():
    # Until the KDOT process is included here,
    # this defaults to the Transcend process.
    
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
    # Can probably just make a table in the *_Source gdb that
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
    
    MakeFeatureLayer_management(routesSourceCenterlines, featureLayer)
    
    SelectLayerByAttribute_management(featureLayer, "CLEAR_SELECTION")
    selectionQuery = """ LRS_ROUTE_PREFIX = 'X' AND Ramps_LRSKey IS NOT NULL AND Ramps_LRSKey <> '' """
    SelectLayerByAttribute_management(featureLayer, "NEW_SELECTION", selectionQuery)
    
    countResult = GetCount_management(featureLayer)
    intCount = int(countResult.getOutput(0))
    
    print('Selected ' + str(intCount) + ' ramp features to be replaced.')
    
    if intCount > 0:
        print("Deleting those ramp features from the " + returnFeatureClass(routesSourceCenterlines) + " layer.")
        DeleteFeatures_management(featureLayer)
    else:
        print("No features selected. Skipping feature deletion.")
    
    # Remove the matching routes to prepare for the Interchange_Ramps information.
    ## After error matching is achieved, use replace geometry and replace attributes to not lose data
    ## from using the less effective method of:
    ## deleting the old Interchange_Ramps information, then re-adding with append.
    
    # Add the Interchange_Ramps information.
    
    # Checking to see if the copy for repairing already exists.
    # If so, remove it.
    if Exists(interchangeRampFCRepairCopy):
        Delete_management(interchangeRampFCRepairCopy)
    else:
        pass
    # Create a new file for the copy for repairing since repair modifies the input.
    CopyFeatures_management(interchangeRampFC, interchangeRampFCRepairCopy)

    # Repairs the geometry, modifies input.
    # Deletes features with null geometry (2 expected, until Shared.Interchange_Ramp is fixed).
    print("Repairing ramp geometry in the " + returnFeatureClass(interchangeRampFCRepairCopy) + " layer.")
    RepairGeometry_management(interchangeRampFCRepairCopy, "DELETE_NULL")

    # Create a fieldmapping object so that the Interchange_Ramps can be correctly imported with append.
    appendInputs = [interchangeRampFCRepairCopy]
    appendTarget = routesSourceCenterlines
    schemaType = "NO_TEST"

    # Field mapping goes here.
    # Interchange_Ramp.LRS_KEY to RoutesSource_Test.LRSKEY
    fm_Field1 = FieldMap()
    fm_Field1.addInputField(interchangeRampFCRepairCopy, "LRS_KEY")
    fm_Field1_OutField = fm_Field1.outputField
    fm_Field1_OutField.name = 'LRSKEY'
    fm_Field1.outputField = fm_Field1_OutField

    # Interchange_Ramp.BEG_CNTY_LOGMILE to RoutesSource_Test.NON_STATE_BEGIN_MP
    fm_Field2 = FieldMap()
    fm_Field2.addInputField(interchangeRampFCRepairCopy, "BEG_CNTY_LOGMILE")
    fm_Field2_OutField = fm_Field2.outputField
    fm_Field2_OutField.name = 'NON_STATE_BEGIN_MP'
    fm_Field2.outputField = fm_Field2_OutField

    # Interchange_Ramp.END_CNTY_LOGMILE to RoutesSource_Test.NON_STATE_END_MP
    fm_Field3 = FieldMap()
    fm_Field3.addInputField(interchangeRampFCRepairCopy, "END_CNTY_LOGMILE")
    fm_Field3_OutField = fm_Field3.outputField
    fm_Field3_OutField.name = 'NON_STATE_END_MP'
    fm_Field3.outputField = fm_Field3_OutField

    # Interchange_Ramp.Shape_Length to RoutesSource_Test.Shape_Length
    fm_Field4 = FieldMap()
    fm_Field4.addInputField(interchangeRampFCRepairCopy, "Shape_Length")
    fm_Field4_OutField = fm_Field4.outputField
    fm_Field4_OutField.name = 'Shape_Length'
    fm_Field4.outputField = fm_Field4_OutField

    # Create the fieldMappings object and add the fieldMap objects to it.
    interchangeRampsMappings = FieldMappings()
    interchangeRampsMappings.addFieldMap(fm_Field1)
    interchangeRampsMappings.addFieldMap(fm_Field2)
    interchangeRampsMappings.addFieldMap(fm_Field3)
    interchangeRampsMappings.addFieldMap(fm_Field4)

    # Perform the append.
    print("Appending the features from " + returnFeatureClass(interchangeRampFCRepairCopy) + " into " + returnFeatureClass(routesSourceCenterlines) + ".")
    Append_management(appendInputs, appendTarget, schemaType, interchangeRampsMappings)


def unusedFieldMapData():
    pass
    ## Try without this part. -- Seems to work. Continue testing.
    '''
    # Interchange_Ramp.Shape_Length to RoutesSource_Test.Shape_Length
    fm_Field4 = FieldMap()
    fm_Field4.addInputField(appendInputs[0], "Shape_Length")
    fm_Field4_OutField = fm_Field4.outputField
    fm_Field4_OutField.name = 'Shape_Length'
    fm_Field4.outputField = fm_Field4_OutField
    '''
    '''
    # Interchange_Ramp.Shape_Length to RoutesSource_Test.Shape_Length
    fm_Field5 = FieldMap()
    fm_Field5.addInputField(appendInputs[0], "Shape")
    fm_Field5_OutField = fm_Field5.outputField
    fm_Field5_OutField.name = 'Shape'
    fm_Field5.outputField = fm_Field5_OutField
    '''


def KDOTOverlappingRoutesDissolveFix_OLD():
    ######## --- Current Work Area --- ########
    ###TODO: IMPORTANT!!!: Reuse and adapt the ramp integration process for the dissolve results re-integration (per dissolve set)
    ### -- detect duplicates in the original data and only keep one piece per piece in the dissolved set -- may require
    ### -- additional QC however, as the dissolve set can return more than one feature per LRSKEY and there may need to
    ### -- be a spatial test involved to make sure that what gets returned covers all of the area that the original
    ### -- features for a given LRSKEY provided.
    
    ### -- Cont'd: Spatial select on attribute selected FC to see which ones can be safely deleted. -- Need to find
    ### -- which spatial selection method works on segments that are exactly the same as a another segment OR which
    ### -- segments (for the smaller segment share a start/end point and all other points with a larger segment, but which
    ### -- will not select smaller segments that share only a start/end point with 
    
    ### -- Test 'WITHIN' as the spatial selection method -- the dissolve will have to run prior to simplify
    ### -- or it will need to use the same simplification version -- okay, that should be fine. Just do it post simplify
    ### -- Except in cases where the geometry is identical except with there possibly being an additional vertex in one... hmm.
    
    ### -- Also test 'SHARE_A_LINE_SEGMENT_WITH' -- might work correctly, but not sure.
    
    ## Both 'WITHIN' and 'SHARE_A_LINE_SEGMENT_WITH' return 975 for the R route dissolve test data.
    ## Both 'WITHIN' and 'SHARE_A_LINE_SEGMENT_WITH' return 498 for the M route dissolve test data.
    ## 'SHARE_A_LINE_SEGMENT_WITH' is probably the safest, because one of the WITHIN types gave me an
    ## error in the Select By Location window the 3rd or 4th time I clicked through it, but then not
    ## again later. -- May have just been because I was clicking quickly, but try to:
    ## Stay away from buggy and buggish settings.
    
    ## Because of the ridiculously high number of fields that contain LRS information, you have to do the dissolve
    ## using all of them, and then compress their information into a smaller chunk and do the dissolve again.
    
    ## I.E. Five field min/max dissolve
    
    
    # -///////////////////- Current Work Area -///////////////////- #
    MakeFeatureLayer_management(routesSourceIntermediate, featureLayer)
    # Reparse the LRS_KEY_Prefix and use it to select dissolve targets.
    ParseLRS_ROUTE_PREFIX(featureLayer) #probably shouldn't count on this
    # existing if it's not passed into this function... use something else.
    
    # Do I, U, K, C, R, M, X, L, etc. separately to try to keep dissolve from
    # messing up and skipping some of the features, but returning 'Success'
    # as though nothing was wrong.
    # Then, combine them all back into one feature set.
    prefixesToDissolve = ['I', 'U', 'K', 'C', 'R', 'X']#, 'L']
    # -- Don't try dissolving prefix L until after new unique
    # keys are genned.
    
    undissolvedFeatureLayer = 'undissolvedFeatureLayer'
    dissolvedFC_gdb = 'in_memory'
    dissolvedFC_basename = 'dissolvedFC_'
    dissolveOutputCombined = 'dissolvedOutput'
    # Have to add MIN_BEG_NODE, MAX_BEG_NODE, MIN_END_NODE, MAX_END_NODE fields to
    # the output feature class.
    floatFieldsToAdd = ['MIN_BEG_NODE', 'MAX_BEG_NODE', 'MIN_END_NODE', 'MAX_END_NODE']
    
    CopyFeatures_management(routesSourceCenterlines, routesSourcePreDissolveOutput)
    MakeFeatureLayer_management(routesSourceCenterlines, stateSystemSelectedFeatures, selectQuery1)
    
    #///////////
    print("Starting to dissolve the routes source.")
    stateSystemSelectedFeatures = 'StateSystem_Features'
    selectQuery1 = '''LRS_ROUTE_PREFIX in ('I', 'U', 'K')'''
    MakeFeatureLayer_management (routesSourceCenterlines, stateSystemSelectedFeatures, selectQuery1)
    CopyFeatures_management(stateSystemSelectedFeatures, routesSourcePreDissolveOutput)
    
    #GetCount on the features in the layer here.
    countResult = GetCount_management(stateSystemSelectedFeatures)
    intCount = int(countResult.getOutput(0))
    print('Found ' + str(intCount) + ' state system features to be dissolved.')
    
    # Why isn't all of the relevant information already in the KDOT_LRS_KEY?
    # Why do we need 5 other fields if we're using an intelligent key?
    # Removed STATE_FLIP_FLAG because we've already flipped the data prior to this process,
    # as we should given that we want the geometry to dissolve correctly.
    dissolveFields = "KDOT_LRS_KEY"#"KDOT_DIRECTION_CALC;KDOT_LRS_KEY;LRS_COUNTY_PRE;LRS_ROUTE_PREFIX;LRS_ROUTE_SUFFIX;LRS_UNIQUE_IDENT"
    statisticsFields = "BEG_NODE MIN;BEG_NODE MAX;END_NODE MAX;END_NODE MIN;SourceFrom MIN;SourceTo MAX"
    multipart = "SINGLE_PART"
    unsplitLines = "DISSOLVE_LINES"
    ## Use a selection for the state system so that it will work the first time.
    ## Then, later expand the selection and the amount of routes that are attempted for
    ## the dissolve.
    Dissolve_management(stateSystemSelectedFeatures, routesSourceDissolveOutput, dissolveFields, statisticsFields, multipart, unsplitLines)
    print("Completed dissolving the routes source.")
    #///////////
    
    #Add the cursor process here.
    
    
    undissolvedFeatureLayer = 'undissolvedFeatureLayer'
    prefixesToDissolve = ['I', 'U', 'K', 'C', 'R', 'X']#, 'L']
    # -- Don't try dissolving prefix L until after new unique
    # keys are genned.
    dissolvedFC_gdb = 'in_memory'
    dissolvedFC_basename = 'dissolvedFC_'
    dissolveOutputCombined = 'dissolvedOutput'
    
    selectQuery0 = None
    for prefixItem in prefixesToDissolve:
        pass
    
    SelectLayerByAttribute_management(undissolvedFeatureLayer, "NEW_SELECTION", selectQuery0)
    
    
    for prefixItem in prefixesToDissolve:
        # Select by LRS_KEY_Prefix.
        # Move selection to a separate dataset or perform dissolve with selection.
        # Might work better to move it to a separate dataset, given the problems with
        # the feature layer dissolve attempts made earlier in this process, but
        # that may have been due to the fact that you had attempted at least one
        # from an in_memory location.
        # i.e. dissolvedFC_I
        dissolvedFC_partname = dissolvedFC_basename + prefixItem
        dissolvedFC_location = os.path.join(dissolvedFC_gdb, dissolvedFC_partname)
        selectQuery1 = """LRS_KEY_Prefix = '""" + prefixItem + """'"""
        SelectLayerByAttribute_management(undissolvedFeatureLayer, "NEW_SELECTION", selectQuery1)
        countResult = GetCount_management(undissolvedFeatureLayer)
        intCount = int(countResult.getOutput(0))
        
        print("Will dissolve " + str(intCount) + " features in the " + " dissolvedFC_partname " + " feature class.")
        
        Dissolve_management(undissolvedFeatureLayer, dissolvedFC_location, dissolveFields, statisticsFields, multipart, unsplitLines)
    
    rowsToInsert = list()
    
    for prefixItem in prefixesToDissolve:
        dissolvedFC_partname = dissolvedFC_basename + prefixItem
        dissolvedFC_location = os.path.join(dissolvedFC_gdb, dissolvedFC_partname)
        
        tableFields = ['ORIGINTABLE', 'CHECKTITLE', 'OBJECTID']
        newCursor = daSearchCursor(dissolvedFC_location, tableFields)
        
        for cursorRow in newCursor:  
            rowsToInsert.append(cursorRow)
            
        try:
            del newCursor
        except:
            pass
            
        newCursor = daInsertCursor()
        #cursor out the features
    
    # then write them to the output feature class which receives its structure from using the original feature class
    # as a template. -- Will need to update the fields using data from the original feature class prior to the dissolve
    # since dissolve destroys information -- not sure how to do that just yet. Maybe select the largest feature which
    # shares geometry with the dissolved feature...? -- Possibly not necessary since we'll just be using the dissolved
    # feature to create a route now and not using it for error correction, since we have people editing the
    # post-conflation base data for that.
    
    # Need to not just make a template but also copy everything where the 
    # LRS_KEY_Prefix is not in the list of prefixesToDissolve.


    def OverlapsMain():
        print("Starting to dissolve the routes source.")
        stateSystemSelectedFeatures = 'StateSystem_Features'
        selectQuery1 = '''LRS_ROUTE_PREFIX in ('I', 'U', 'K')'''
        MakeFeatureLayer_management (routesSourceCenterlines, stateSystemSelectedFeatures, selectQuery1)
        CopyFeatures_management(stateSystemSelectedFeatures, routesSourcePreDissolveOutput)
        
        #GetCount on the features in the layer here.
        countResult = GetCount_management(stateSystemSelectedFeatures)
        intCount = int(countResult.getOutput(0))
        print('Found ' + str(intCount) + ' state system features to be dissolved.')
        
        # Removed STATE_FLIP_FLAG because we've already flipped the data prior to this process.
        dissolveFields = "KDOT_DIRECTION_CALC;KDOT_LRS_KEY;LRS_COUNTY_PRE;LRS_ROUTE_PREFIX;LRS_ROUTE_SUFFIX;LRS_UNIQUE_IDENT"
        statisticsFields = "BEG_NODE MIN;BEG_NODE MAX;END_NODE MAX;END_NODE MIN;COUNTY_BEGIN_MP MIN;COUNTY_END_MP MAX"
        multipart = "SINGLE_PART"
        unsplitLines = "DISSOLVE_LINES"
        ## Use a selection for the state system so that it will work the first time.
        ## Then, later expand the selection and the amount of routes that are attempted for
        ## the dissolve.
        Dissolve_management(stateSystemSelectedFeatures, routesSourceDissolveOutput, dissolveFields, statisticsFields, multipart, unsplitLines)
        print("Completed dissolving the routes source.")
    
    import os
    
    from arcpy import (AddField_management, CalculateField_management,
        CopyFeatures_management, Dissolve_management, env,
        FeatureClassToFeatureClass_conversion,
        FlipLine_edit, GetCount_management,
        MakeFeatureLayer_management, SelectLayerByAttribute_management)
    
    from datareviewerchecks_config import (gdbForSourceCreation, routesSourceCenterlines,
        routesSourceDissolveOutput)
    
    env.workspace = gdbForSourceCreation
    env.overwriteOutput = True
    
    inMemFeatureClassName = 'State_System'
    inMemFeatureClass = os.path.join('in_memory', inMemFeatureClassName)
    stateSystemFeatureLayer = 'StateSystemFL'
    nonStateSystemFeatureLayer = 'NonStateSystemFL'


    def StateHighwaySystemDissolve():
        # Create an in-memory copy of state highay system routes based on LRS Route Prefix
        FeatureClassToFeatureClass_conversion(routesSourceCenterlines, "in_memory", inMemFeatureClassName, "LRS_ROUTE_PREFIX in ('I', 'U', 'K')")
        MakeFeatureLayer_management(inMemFeatureClass, stateSystemFeatureLayer)
        #about 941 records in Southwest Kansas had reverse mileages and need to be flipped
        #this should be corrected in the final conflation delivery
        #if it is not corrected, these route segments should be explored in more detail
        
        SelectLayerByAttribute_management(stateSystemFeatureLayer, "NEW_SELECTION", """("COUNTY_BEGIN_MP" > "COUNTY_END_MP" OR "STATE_BEGIN_MP" > "STATE_END_MP") AND "STATE_FLIP_FLAG" IS NULL""")
        CalculateField_management(stateSystemFeatureLayer, "STATE_FLIP_FLAG", """'Y'""", "PYTHON_9.3", "")
        
        SelectLayerByAttribute_management(stateSystemFeatureLayer, "NEW_SELECTION", """"STATE_FLIP_FLAG" = 'Y' """)
        FlipLine_edit(stateSystemFeatureLayer)
        #need to flip mileages where geometry was flipped so add fields
        AddField_management(stateSystemFeatureLayer, "F_CNTY_2", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        AddField_management(stateSystemFeatureLayer, "T_CNTY_2", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        AddField_management(stateSystemFeatureLayer, "F_STAT_2", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        AddField_management(stateSystemFeatureLayer, "T_STAT_2", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        
        #check if there are any state system segments where the to is greater than the from and flag them for review
        AddField_management(stateSystemFeatureLayer, "MileFlipCheck", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        
        CalculateField_management(stateSystemFeatureLayer, "F_CNTY_2", "!COUNTY_END_MP!", "PYTHON_9.3", "")
        CalculateField_management(stateSystemFeatureLayer, "T_CNTY_2", "!COUNTY_BEGIN_MP!", "PYTHON_9.3", "")
        CalculateField_management(stateSystemFeatureLayer, "F_STAT_2", "!STATE_END_MP!", "PYTHON_9.3", "")
        CalculateField_management(stateSystemFeatureLayer, "T_STAT_2", "!STATE_BEGIN_MP!", "PYTHON_9.3", "")
        
        # Switch selection and calculate mileages
        
        SelectLayerByAttribute_management(in_layer_or_view=stateSystemFeatureLayer, selection_type="SWITCH_SELECTION", where_clause="")
        
        CalculateField_management(stateSystemFeatureLayer, "F_CNTY_2", "!COUNTY_BEGIN_MP!", "PYTHON_9.3", "")
        CalculateField_management(stateSystemFeatureLayer, "T_CNTY_2", "!COUNTY_END_MP!", "PYTHON_9.3", "")
        CalculateField_management(stateSystemFeatureLayer, "F_STAT_2", "!STATE_BEGIN_MP!", "PYTHON_9.3", "")
        CalculateField_management(stateSystemFeatureLayer, "T_STAT_2", "!STATE_END_MP!", "PYTHON_9.3", "")
        #KDOT Direction should already be calculated, by running "DualCarriagweayIdentity.py" and updating the KDOT_DIRECTION_CALC to 1 where dual carriagway is found
        #Validation_CheckOverlaps can also help do identify sausage link/parallel geometries that may indicate dual carriagway, but that script does not yet 
        #identify and calculate the KDOT_DIRECTION_CALC flag.  It probably could with more development
        # Select the EB routes and change the LRS_Direction to WB
        
        SelectLayerByAttribute_management(stateSystemFeatureLayer, "NEW_SELECTION", """"KDOT_DIRECTION_CALC" = '1' AND "LRS_DIRECTION" = 'EB'""")
        CalculateField_management(stateSystemFeatureLayer, "LRS_DIRECTION", "'WB'", "PYTHON_9.3", "")
        #Select the SB routes to chante hte LRS direction to SB
        SelectLayerByAttribute_management(stateSystemFeatureLayer, "NEW_SELECTION", """"KDOT_DIRECTION_CALC" = '1' AND "LRS_DIRECTION" = 'NB'""")
        CalculateField_management(stateSystemFeatureLayer, "LRS_DIRECTION", "'SB'", "PYTHON_9.3", "")
        # Clear the selections
        SelectLayerByAttribute_management(stateSystemFeatureLayer, "CLEAR_SELECTION", "")
        
        #Calculate County LRS Key in CountyKey1 field for State Highway system
        #Need to add CountyKey2 for iteration 2, also go ahead and add new LRS Key format
        CalculateField_management(stateSystemFeatureLayer, "CountyKey1", """[LRS_COUNTY_PRE] + [LRS_ROUTE_PREFIX] + [LRS_ROUTE_NUM] + [LRS_ROUTE_SUFFIX] + [LRS_UNIQUE_IDENT] +"-" + [LRS_DIRECTION]""", "VB")
        CalculateField_management(stateSystemFeatureLayer, "StateKey1", """[LRS_ROUTE_PREFIX] + [LRS_ROUTE_NUM] + [LRS_ROUTE_SUFFIX] + [LRS_UNIQUE_IDENT] +"-" + [LRS_DIRECTION]""", "VB")
        
        #this is the dissolve - the output of this is a feature class which is clean for route creation of the state highway system
        Dissolve_management(stateSystemFeatureLayer, routesSourceDissolveOutput+"_Dissolve_EO", "CountyKey1;LRS_COUNTY_PRE;LRS_ROUTE_PREFIX;LRS_ROUTE_NUM;LRS_ROUTE_SUFFIX;LRS_UNIQUE_IDENT;LRS_DIRECTION", "F_CNTY_2 MIN;T_CNTY_2 MAX", "SINGLE_PART", "DISSOLVE_LINES")
        Dissolve_management(stateSystemFeatureLayer, routesSourceDissolveOutput+"_Unsplit_EO", "CountyKey1;LRS_COUNTY_PRE;LRS_ROUTE_PREFIX;LRS_ROUTE_NUM;LRS_ROUTE_SUFFIX;LRS_UNIQUE_IDENT;LRS_DIRECTION", "F_CNTY_2 MIN;T_CNTY_2 MAX", "SINGLE_PART", "UNSPLIT_LINES")
        # Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
        # The following inputs are layers or table views: stateSystemFeatureLayer
        #review the dissolve output, go back and flag the input data
    
    OverlapsMain()
    StateHighwaySystemDissolve()
    
def unusedFromKDOTDataPreparation():
    '''
    ## Only do the Non_State_Flip_Flag for data where LRS_Backwards is populated. -- Not data we have yet.
    ## Can do a check on the fieldnames and if LRS_Backwards exists, then use the other selection
    ## query instead of the currently selected one.
    ## testFields = Describe.fields or similar, then if LRS_Backwards in testFields:
    ### ^^ Won't work. There's an LRS_Backwards field currently, it's just not properly populated.
    if useSettingsForRegion6 == True:
        print("Using the LRS_BACKWARD field in the selectionQuery for flipping.") # All the capitals, all the time.
        # LRS_BACKWARD should be set to -1 if the segment is backwards compared
        # to how we expect the road directions to go.
        selectionQuery1 = """ ((NON_STATE_FLIP_FLAG IS NOT NULL AND NON_STATE_FLIP_FLAG = 'Y') OR (STATE_FLIP_FLAG IS NOT NULL AND STATE_FLIP_FLAG = 'Y')) 
            AND (LRS_BACKWARD IS NULL OR LRS_BACKWARD = 0) """
    else:
        print("Not using the LRS_BACKWARD field in the selectionQuery for flipping.")
        selectionQuery1 = """ STATE_FLIP_FLAG IS NOT NULL AND STATE_FLIP_FLAG = 'Y' """
    '''
    
def KDOTKeyCalculation_OLD():
    # Until the KDOT process is included here,
    # this defaults to the Transcend process.
    #FieldPopulation with selections and FieldCalculate:
    
    MakeFeatureLayer_management(routesSourceIntermediate, fcAsFeatureLayer)
    
    try:
        RemoveDomainFromField_management(fcAsFeatureLayer, "LRS_ROUTE_PREFIX")
    except:
        print("Could not remove the domain from 'LRS_ROUTE_PREFIX'.")
        print("It may have not existed previously.")
        pass
    
    tempDesc = Describe(fcAsFeatureLayer)
    print("Calculating values for new LRS and measure fields in " + returnFeatureClass(tempDesc.catalogPath) + ".")
    try:
        del tempDesc
    except:
        pass
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
    
    #interchangeRampsMappings.addFieldMap(fm_Field4)
    #interchangeRampsMappings.addFieldMap(fm_Field5)
    
    print("These are the keys that were found in the repairedRampsKeysList, but not in the routesSourceCenterlinesKeysList.")
    print("These need to be appended into the routesSourceCenterlines.")
    #for comparisonItem3 in comparisonList3:
    #    print(str(comparisonItem3))
        ##selectionListForMFL1
        # Append them into the routesSourceCenterlines.
        # Need to make a selection and copy or a feature layer that only includes the
        # specified items, so you'll have to build a custom selection loop or query
        # to build the feature layer.
        
    # Uncommented for full test #
    ######## Skip this part for the partial test ########
    # Uncommented for full test #
    #'''
    # Get the common ramps so that we know which lrskeys need to be deduplicated in the routesSoureCenterlineKeysList
    # and have their geometries updated to that of the geometry which exists in the repairedRampsKeysList.
    #'''
    
from dataimprovements_localroutenumbering.py
    newCursor = daSearchCursor(routeFeaturesFC, currentFields, selectionQuery1)
    for cursorRow in newCursor:
        routeFeaturesList.append(list(cursorRow))
    
    try:
        del newCursor
    except:
        pass
    
    newCursor = daSearchCursor(routeFeaturesFC, currentFields, selectionQuery2)
    for cursorRow in newCursor:
        routeFeaturesList.append(list(cursorRow))
    
    try:
        del newCursor
    except:
        pass
   
    minXCoord = 100000000
    minYCoord = 100000000
    
    # Do a quick check to make sure that your cursor is correctly selecting only Morton County items.
    for routeFeatureItem in routeFeaturesList:
        routeFeatureCentroid = routeFeatureItem[-1]
        ##routeFeatureCentroid = routeFeatureGeom.centroid
        routeFeatureCentroidX = routeFeatureCentroid[0]
        routeFeatureCentroidY = routeFeatureCentroid[1]
        ##print routeFeatureGeom
        ##print("X Coord: " + str(routeFeatureGeom.centroid.X) + "  \tY Coord: " + str(routeFeatureGeom.centroid.Y))
        if minXCoord > routeFeatureCentroidX:
            minXCoord = routeFeatureCentroidX
        else:
            pass
        if minYCoord > routeFeatureCentroidY:
            minYCoord = routeFeatureCentroidY
        else:
            pass
    
    
    print("Minimum X Coord = " + str(minXCoord) + "  \tMinimum Y Coord = " + str(minYCoord))
    distStartPointX = minXCoord - 9000
    distStartPointY = minYCoord - 9000
    print("distStartPoint X Coord = " + str(distStartPointX) + "  \tdistStartPoint Y Coord = " + str(distStartPointY))
    featureDistance = ((minYCoord - distStartPointY)**2 +  (minXCoord - distStartPointX)**2)
    print("Distance from minimum X Coord + minimum Y Coord to the distStartPoint = " + str(math.sqrt(featureDistance)))
    print("Unsqrt'd Distance from minimum X Coord + minimum Y Coord to the distStartPoint = " + str(featureDistance))
    ## Get the minimum x and minimum y based on the centroid values for each feature.
    
    for routeFeatureItem in routeFeaturesList:
        routeFeatureCentroid = routeFeatureItem[-1]
        ##routeFeatureCentroid = routeFeatureGeom.centroid
        routeFeatureCentroidX = routeFeatureCentroid[0]
        routeFeatureCentroidY = routeFeatureCentroid[1]
        
        routeFeatureSortDist = ((routeFeatureCentroidX - distStartPointY)**2 +  (routeFeatureCentroidY - distStartPointX)**2)
        routeFeatureItem.append(routeFeatureSortDist)
    
    sortedLineList = sorted(routeFeaturesList, key=itemgetter(-1))
    
    for sortedLineItem in sortedLineList:
        print(str(sortedLineItem[-1]))
    
    del routeFeaturesList
    
    # Perform renumbering here... need to make sure that the fields are in a particular order.
    countyLocalNumber = 0
    sortedLinesByRoadNameDict = dict()
    
    for sortedLineItem in sortedLineList:
        if sortedLineItem[-2] not in sortedLinesByRoadNameDict.keys()
            newList = list()
            newList.append(sortedLineItem)
            sortedLinesByRoadNameDict[str(sortedLineItem[-2])] = sortedLineItem
        else:
            existingList = sortedLinesByRoadNameDict[str(sortedLineItem[-2])]
            existingList.append(sortedLineItem)
            sortedLinesByRoadNameDict[str(sortedLineItem[-2])] = existingList
    
    for roadNameItem in sortedLinesByRoadNameDict.keys():
        routesToNumberList = sortedLinesByRoadNameDict[roadNameItem]
        for roadToNumberItem in routesToNumberList:
            # Don't have the first and last point, so can't make the
            # decision that I need to here. :(
            # May need to get a list of all road names in a particular
            # county and then select/cursor those prior to doing the
            # spatial sort, then just perform the numbering on them
            # as soon as the spatial sort is done and update the
            # feature class then.
            numberToAssign = str(countyLocalNumber).zfill(5)
    
    currentFields = [x.name for x in tempDesc.fields]
    fieldsToRemove = ['SHAPE', 'Shape', OIDFieldName, 'LABEL', 'LRS_ROUTE_PREFIX', 'LRS_ROUTE_NUM', 'LRS_UNIQUE_IDENT', 'LRS_UNIQUE_IDENT1', 'LRS_UNIQUE_TARGET']
    
    for fieldItem in fieldsToRemove:
        try:
            currentFields.remove(fieldItem)
        except:
            pass
    
    ### Removed previous logic.
    #for fieldItem in fieldsToAdd:
    #    currentFields.append(fieldItem)