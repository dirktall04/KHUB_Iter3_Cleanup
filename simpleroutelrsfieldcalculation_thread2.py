#simpleroutelrsfieldcalculation.py
# -*- coding: utf-8 -*-
# Created by: Dirk Talley
# 2017-01-24

from arcpy import (env, CopyFeatures_management, CalculateField_management, Describe,
    MakeFeatureLayer_management, SelectLayerByAttribute_management)

from pathFunctions import (returnFeatureClass)

env.overwriteOutput = True
env.MResolution = 0.0001
env.MTolerance = 0.001

routesSourceCenterlines = r'C:\GIS\Geodatabases\KHUB\Testing\R6_For_Vertex_Simplification_05Ft.gdb\RoadCenterlines_05Ft'
featureLayer = 'centerlinesSource'

print("Calculating the lrs fields from the modified data.")

def KDOTKeyCalculation_Modified():
    # Until the KDOT process is included here,
    # this defaults to the Transcend process.
    #FieldPopulation with selections and FieldCalculate:
    MakeFeatureLayer_management(routesSourceCenterlines, featureLayer)
    
    tempDesc = Describe(featureLayer)
    print("Calculating values for new LRS and measure fields in " + returnFeatureClass(tempDesc.catalogPath) + ".")
    try:
        del tempDesc
    except:
        pass
    # Select LRS_ROUTE_PREFIX IN ('I', 'U', 'K')
    selectionQuery = """ "LRS_ROUTE_PREFIX" IN ('I', 'U', 'K') """
    SelectLayerByAttribute_management(featureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteId = StateKey1
    CalculateField_management (featureLayer, "SourceRouteId", "!StateKey1!", "PYTHON_9.3")
    # SourceFromMeasure = STATE_BEGIN_MP
    CalculateField_management (featureLayer, "SourceFromMeasure", "!STATE_BEGIN_MP!", "PYTHON_9.3")
    # SourceToMeasure = STATE_END_MP
    CalculateField_management (featureLayer, "SourceToMeasure", "!STATE_END_MP!", "PYTHON_9.3")
    
    # Select LRS_ROUTE_PREFIX NOT IN ('I', 'U', 'K') AND LRSKEY IS NOT NULL
    selectionQuery = """ "LRS_ROUTE_PREFIX" NOT IN ('I', 'U', 'K') AND "LRSKEY" IS NOT NULL """
    SelectLayerByAttribute_management(featureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteId = LRSKEY
    CalculateField_management (featureLayer, "SourceRouteId",  "!LRSKEY!", "PYTHON_9.3")
    # SourceFromMeasure = NON_STATE_BEGIN_MP
    CalculateField_management (featureLayer, "SourceFromMeasure", "!NON_STATE_BEGIN_MP!", "PYTHON_9.3")
    # SourceToMeasure = NON_STATE_END_MP
    CalculateField_management (featureLayer, "SourceToMeasure", "!NON_STATE_END_MP!", "PYTHON_9.3")
    
    # Select LRS_ROUTE_PREFIX IN ('C') AND LRSKEY NOT LIKE '%W0'
    selectionQuery = """ "LRS_ROUTE_PREFIX" IN ('C') AND "LRSKEY" NOT LIKE '%W0' """
    SelectLayerByAttribute_management(featureLayer, "NEW_SELECTION", selectionQuery)
    # SourceRouteID = left([LRSKEY], 11) & "W0"
    # This is the VB version.
    # Python version would be calcExpression1 = "!LRSKEY![0:11] + 'W0'"
    calcExpression1 = 'Left([LRSKEY] ,11 ) & "W0"'
    CalculateField_management(featureLayer, "SourceRouteID", calcExpression1, "VB")

KDOTKeyCalculation_Modified()

print("Finished calculating the fields from the modified data.")