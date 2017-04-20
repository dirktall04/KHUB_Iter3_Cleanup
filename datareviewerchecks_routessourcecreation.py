#!/usr/bin/env python
# -*- coding:utf-8 -*-
# datareviewerchecks_routessourcecreation.py
# Created 2016-01-03, by dirktall04
# Updated 2017-01-11, by dirktall04
# Updated 2017-03-15, by dirktall04

# Do all of the tasks that are necessary to get the
# routes and ramps together that you would
# normally do prior to the start of creating
# routes -- all of the steps that it takes to
# have a functioning RoutesSource feature class
# that people can start making corrections on/in.

# This should be in a different GDB than the
# routes an calibration points eventually end up
# going into.

# The reason to make this is so that we can run processes
# to clean up the routes source prior to creating routes
# from that source data.

from pathFunctions import returnGDBOrSDEPath, returnFeatureClass

from arcpy import (Append_management, AddField_management,
    CalculateField_management, CopyFeatures_management,
    DeleteFeatures_management, Delete_management, Describe,
    env, Exists, FieldMap, FieldMappings, GetCount_management,
    MakeFeatureLayer_management, RepairGeometry_management,
    SelectLayerByAttribute_management)#, CreateFileGDB_management) 

from datareviewerchecks_config import (inputCenterlines, interchangeRampFC,
    interchangeRampFCRepairCopy, routesSourceCenterlines,
    routesSourceFeatureLayer, nullable, useNewFieldLogic, fcAsFeatureLayer,
    n1RouteId, n1FromMeas, n1ToMeas)


def routesSourceCreation():
    env.workspace = returnGDBOrSDEPath(routesSourceCenterlines)
    env.overwriteOutput = 1
    
    # Checking to see if the output already exists.
    # If so, remove it.
    if Exists(routesSourceCenterlines):
        Delete_management(routesSourceCenterlines)
    else:
        pass
    # Create a new file for the output.
    print("Making a copy of " + returnFeatureClass(inputCenterlines) + " called " + returnFeatureClass(routesSourceCenterlines) + ".")
    CopyFeatures_management(inputCenterlines, routesSourceCenterlines)
    
    print("Adding fields to " + returnFeatureClass(routesSourceCenterlines) + ".")
    #Addfields:
    # SourceRouteId (Text, 50)
    AddField_management(routesSourceCenterlines, "SourceRouteId", "TEXT", "", "", 50, "SourceRouteId", nullable)
    # SourceFromMeasure (Double)
    AddField_management(routesSourceCenterlines, "SourceFromMeasure", "DOUBLE", "", "", "", "SourceFromMeasure", nullable)
    # SourceToMeasure (Double)
    AddField_management(routesSourceCenterlines, "SourceToMeasure", "DOUBLE", "", "", "", "SourceToMeasure", nullable)
    
    if useNewFieldLogic == True:
        KDOTKeyCalculation_NewFieldLogic()
    else:
        TranscendFieldCalculation()
    
    TranscendRampReplacement()
    
    if useNewFieldLogic == True:
        KDOTKeyCalculation_NewFieldLogic()
    else:
        TranscendFieldCalculation()
    LocalRouteReduction()


def KDOTKeyCalculation_NewFieldLogic():
    MakeFeatureLayer_management(routesSourceCenterlines, fcAsFeatureLayer)
    # As long as the KDOT_LRS_KEY is not null, calculate from the
    # current fields.
    selectionQuery = """ "KDOT_LRS_KEY" IS NOT NULL """
    SelectLayerByAttribute_management(fcAsFeatureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteId = KDOT_LRS_KEY
    CalculateField_management (fcAsFeatureLayer, n1RouteId, "!KDOT_LRS_KEY!", "PYTHON_9.3")
    # SourceFromMeasure = county_log_begin
    CalculateField_management (fcAsFeatureLayer, n1FromMeas, "!county_log_begin!", "PYTHON_9.3")
    # SourceToMeasure = county_log_end
    CalculateField_management (fcAsFeatureLayer, n1ToMeas, "!county_log_end!", "PYTHON_9.3")


def TranscendRampReplacement():
    MakeFeatureLayer_management (routesSourceCenterlines, routesSourceFeatureLayer)

    SelectLayerByAttribute_management(routesSourceFeatureLayer, "CLEAR_SELECTION")
    selectionQuery = """ "LRS_ROUTE_PREFIX" = 'X' AND "Ramps_LRSKey" IS NOT NULL AND "Ramps_LRSKey" <> '' """
    SelectLayerByAttribute_management(routesSourceFeatureLayer, "NEW_SELECTION", selectionQuery)

    countResult = GetCount_management(routesSourceFeatureLayer)
    intCount = int(countResult.getOutput(0))

    print('Selected ' + str(intCount) + ' ramp features to be replaced.')

    if intCount > 0:
        print("Deleting those ramp features from the " + returnFeatureClass(routesSourceCenterlines) + " layer.")
        DeleteFeatures_management(routesSourceFeatureLayer)
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

    # Create the fieldMappings object
    interchangeRampsMappings = FieldMappings()
    interchangeRampsMappings.addFieldMap(fm_Field1)
    interchangeRampsMappings.addFieldMap(fm_Field2)
    interchangeRampsMappings.addFieldMap(fm_Field3)

    # Add the fieldMap objects to the fieldMappings object.
    print("Appending the features from " + returnFeatureClass(interchangeRampFCRepairCopy) + " into " + returnFeatureClass(routesSourceCenterlines) + ".")
    Append_management(appendInputs, appendTarget, schemaType, interchangeRampsMappings)


def TranscendFieldCalculation():
    #FieldPopulation with selections and FieldCalculate:
    tempDesc = Describe(routesSourceFeatureLayer)
    print("Calculating values for new LRS and measure fields in " + returnFeatureClass(tempDesc.catalogPath) + ".")
    try:
        del tempDesc
    except:
        pass
    # Select LRS_ROUTE_PREFIX IN ('I', 'U', 'K')
    selectionQuery = """ "LRS_ROUTE_PREFIX" IN ('I', 'U', 'K') """
    SelectLayerByAttribute_management(routesSourceFeatureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteId = StateKey1
    CalculateField_management (routesSourceFeatureLayer, "SourceRouteId", "!StateKey1!", "PYTHON_9.3")
    # SourceFromMeasure = STATE_BEGIN_MP
    CalculateField_management (routesSourceFeatureLayer, "SourceFromMeasure", "!STATE_BEGIN_MP!", "PYTHON_9.3")
    # SourceToMeasure = STATE_END_MP
    CalculateField_management (routesSourceFeatureLayer, "SourceToMeasure", "!STATE_END_MP!", "PYTHON_9.3")

    # Select LRS_ROUTE_PREFIX NOT IN ('I', 'U', 'K') AND LRSKEY IS NOT NULL
    selectionQuery = """ "LRS_ROUTE_PREFIX" NOT IN ('I', 'U', 'K') AND "LRSKEY" IS NOT NULL """
    SelectLayerByAttribute_management(routesSourceFeatureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteId = LRSKEY
    CalculateField_management (routesSourceFeatureLayer, "SourceRouteId",  "!LRSKEY!", "PYTHON_9.3")
    # SourceFromMeasure = NON_STATE_BEGIN_MP
    CalculateField_management (routesSourceFeatureLayer, "SourceFromMeasure", "!NON_STATE_BEGIN_MP!", "PYTHON_9.3")
    # SourceToMeasure = NON_STATE_END_MP
    CalculateField_management (routesSourceFeatureLayer, "SourceToMeasure", "!NON_STATE_END_MP!", "PYTHON_9.3")

    # Select LRS_ROUTE_PREFIX IN ('C') AND LRSKEY NOT LIKE '%W0'
    selectionQuery = """ "LRS_ROUTE_PREFIX" IN ('C') AND "LRSKEY" NOT LIKE '%W0' """
    SelectLayerByAttribute_management(routesSourceFeatureLayer, "NEW_SELECTION", selectionQuery)

    # SourceRouteID = left([LRSKEY], 11) & "W0"
    # This is the VB version.
    # Python version would be calcExpression1 = "!LRSKEY![0:11] + 'W0'"
    calcExpression1 = 'Left([LRSKEY] ,11 ) & "W0"'
    CalculateField_management(routesSourceFeatureLayer, "SourceRouteID", calcExpression1, "VB")
    # ^^ This might be a problem. Check to make sure that this one in particular worked afterwards.


def LocalRouteReduction():
    '''Removes local roads for which we should have little to no event/attribute data.'''
    # Never got the details on this, so it's a pass.
    pass
    

def main():
    print('Routes Source Creation started.')
    routesSourceCreation()
    print('Routes Source Creation finished.')


if __name__ == "__main__":
    main()

else:
    pass