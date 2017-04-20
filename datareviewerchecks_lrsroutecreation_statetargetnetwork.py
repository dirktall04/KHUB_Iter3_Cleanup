#!/usr/bin/env python
# -*- coding:utf-8 -*-
# datareviewerchecks_lrsroutecreation_statetargetnetwork.py
# Created 2017-03-29, by dirktall04


from pathFunctions import returnGDBOrSDEPath, returnFeatureClass, returnGDBOrSDEName

from arcpy import (AddField_management, CalculateField_management,
    CreateFileGDB_management, CreateRoutes_lr,
    Delete_management, Describe, Dissolve_management, env,
    Exists, FeatureVerticesToPoints_management, FieldInfo,
    FieldMap, FieldMappings, MakeFeatureLayer_management,
    Merge_management)

from datareviewerchecks_config import (reviewerSessionGDBFolder,
    outputRoutes, featureLayerCL_For_Start_CP, featureLayerCL_For_End_CP,
    routesSourceCenterlines, startCalibrationPoints, endCalibrationPoints,
    mergedCalibrationPoints, dissolvedCalibrationPoints,
    mainFolder, nullable)

# createRoutesInputFC Variables: routesSourceCenterlines,
# createRoutesOutputFC Variable: outputRoutes
createRoutesInputFC = routesSourceCenterlines
createRoutesOutputFC = outputRoutes


def routeCreation():
    env.workspace = returnGDBOrSDEPath(createRoutesOutputFC)
    env.overwriteOutput = 1
    
    # Need to match what Transcend used. -- Done.
    routeId = 'SourceRouteId'
    measureSource = 'TWO_FIELDS'
    fMeasureField = 'SourceFromMeasure'
    tMeasureField = 'SourceToMeasure'
    coordinatePriority = 'UPPER_LEFT'
    measureFactor = 1
    measureOffset = 0
    ignoreGaps = True
    buildIndex = True
    
    routesOutputGDB = returnGDBOrSDEPath(createRoutesOutputFC)
    routesOutputGDBName = returnGDBOrSDEName(routesOutputGDB)
    # Need to implement a new path function to get the GDB's folder.
    routesOutputGDBFolder = mainFolder
    if Exists(routesOutputGDB):
        Delete_management(routesOutputGDB)
    else:
        pass
    CreateFileGDB_management(routesOutputGDBFolder, routesOutputGDBName)
    
    # Checking to see if the copy for routes output exists.
    # If so, remove it.
    #if Exists(createRoutesOutputFC):
    #    Delete_management(createRoutesOutputFC)
    #else:
    #    pass
    
    print("Creating the lrs routes.")
    # CreateRoutes_lr GP Tool
    CreateRoutes_lr (createRoutesInputFC, routeId, createRoutesOutputFC, measureSource, fMeasureField, tMeasureField, coordinatePriority, measureFactor, measureOffset, ignoreGaps, buildIndex)

    print("Adding date fields to " + returnFeatureClass(createRoutesOutputFC) + ".")
    #Addfields:
    AddField_management(createRoutesOutputFC, "F_Date", "DATE", "", "", "", "F_Date", nullable)
    pyDateExpression = '''def pyFindTheDate():
        import time
        return time.strftime("%Y/%m/%d")'''
    
    CalculateField_management(createRoutesOutputFC, "F_Date", "pyFindTheDate()", "PYTHON_9.3", pyDateExpression)
    # T_Date (Date)
    AddField_management(createRoutesOutputFC, "T_Date", "DATE", "", "", "", "T_Date", nullable)

    # ---- Add route calibration point creation steps for Start & End points. ----
    MakeFeatureLayer_management(createRoutesInputFC, 'tempFeatureLayer')

    # Checking to see if the output already exists.
    # If so, remove it so that it can be recreated.
    if Exists(startCalibrationPoints):
        Delete_management(startCalibrationPoints)
    else:
        pass
    if Exists(endCalibrationPoints):
        Delete_management(endCalibrationPoints)
    else:
        pass

    # Create 2 fieldInfo objects. Turn off all the fields in each one.
    featureDesc = Describe('tempFeatureLayer')
    if featureDesc.dataType == "FeatureLayer":
        fieldInfo_For_Start_CP_Fields = featureDesc.fieldInfo
        fieldInfo_For_End_CP_Fields = featureDesc.fieldInfo
        # Use the count property to iterate through all the fields
        for index in range(0, fieldInfo_For_Start_CP_Fields.count):
            fieldInfo_For_Start_CP_Fields.setVisible(index, 'HIDDEN')
            fieldInfo_For_End_CP_Fields.setVisible(index, 'HIDDEN')

    # Turn on the needed fields.
    visibile_Fields_For_Start_CP_Layer = ['SourceRouteId', 'SourceFromMeasure']
    for visibile_Field in visibile_Fields_For_Start_CP_Layer:
        tempIndex = fieldInfo_For_Start_CP_Fields.findFieldByName(visibile_Field)
        fieldInfo_For_Start_CP_Fields.setVisible(tempIndex, 'VISIBLE')
    # Create a feature layer that only shows the needed fields.
    MakeFeatureLayer_management(createRoutesInputFC, featureLayerCL_For_Start_CP, "", "", fieldInfo_For_Start_CP_Fields)
    # Use that feature layer to create the 1st calibration point set.
    FeatureVerticesToPoints_management(featureLayerCL_For_Start_CP, startCalibrationPoints, "START")

    # Turn on the needed fields.
    visibile_Fields_For_End_CP_Layer = ['SourceRouteId', 'SourceToMeasure']
    for visibile_Field in visibile_Fields_For_End_CP_Layer:
        tempIndex = fieldInfo_For_End_CP_Fields.findFieldByName(visibile_Field)
        fieldInfo_For_End_CP_Fields.setVisible(tempIndex, 'VISIBLE')
    # Create a feature layer that only shows the needed fields.
    MakeFeatureLayer_management(createRoutesInputFC, featureLayerCL_For_End_CP, "", "", fieldInfo_For_End_CP_Fields)
    # Use that feature layer to create the 2nd calibration point set.
    FeatureVerticesToPoints_management(featureLayerCL_For_End_CP, endCalibrationPoints, "END")

    # ---- Merge the Start & End calibration points. ----
    # Checking to see if the output already exists.
    # If so, remove it so that it can be recreated.
    if Exists(mergedCalibrationPoints):
        Delete_management(mergedCalibrationPoints)
    else:
        pass
    # RoutesSource_Start_CP.SourceRouteId to CalPts_Merge.RouteId
    # RoutesSource_End_CP.SourceRouteId to CalPts_Merge.RouteId
    mcp_Field1 = FieldMap()
    mcp_Field1.addInputField(startCalibrationPoints, 'SourceRouteId')
    mcp_Field1.addInputField(endCalibrationPoints, 'SourceRouteId')
    mcp_Field1_OutField = mcp_Field1.outputField
    mcp_Field1_OutField.name = 'RouteId'
    mcp_Field1_OutField.aliasName = 'RouteId'
    mcp_Field1_OutField.type = 'String'
    mcp_Field1_OutField.length = 50
    mcp_Field1.outputField = mcp_Field1_OutField

    # RoutesSource_Start_CP.SourceFromMeasure to CalPts_Merge.Measure
    mcp_Field2 = FieldMap()
    mcp_Field2.addInputField(startCalibrationPoints, 'SourceFromMeasure')
    mcp_Field2.addInputField(endCalibrationPoints, 'SourceToMeasure')
    mcp_Field2_OutField = mcp_Field2.outputField
    mcp_Field2_OutField.name = 'Measure'
    mcp_Field2_OutField.aliasName = 'Measure'
    mcp_Field2_OutField.type = 'Double'
    mcp_Field2.outputField = mcp_Field2_OutField

    # Create a fieldMappings object for the layer merge.
    calibrationPointsMappings = FieldMappings()
    calibrationPointsMappings.addFieldMap(mcp_Field1)
    calibrationPointsMappings.addFieldMap(mcp_Field2)

    #Merge the points together into a single feature class.
    inputMergeLayers = [startCalibrationPoints, endCalibrationPoints]
    Merge_management(inputMergeLayers, mergedCalibrationPoints, calibrationPointsMappings)

    MakeFeatureLayer_management(mergedCalibrationPoints, 'tempMergedPoints')

    dissolveFields = ["RouteId", "Measure"]
    print('Dissolving points.')
    Dissolve_management('tempMergedPoints', dissolvedCalibrationPoints, dissolveFields, "#", "SINGLE_PART")


def main():
    print('Route creation started.')
    routeCreation()
    print('Route creation finished.')


if __name__ == "__main__":
    main()

else:
    pass