#simpleroutecreation.py
# -*- coding: utf-8 -*-
# Created by: Dirk Talley
# 2017-01-24

from arcpy import (env, CopyFeatures_management, CreateRoutes_lr, FlipLine_edit,
    MakeFeatureLayer_management, SelectLayerByAttribute_management)

env.overwriteOutput = True
env.MResolution = 0.0001
env.MTolerance = 0.001

modifiedData = r'C:\GIS\Geodatabases\KHUB\Testing\R6_For_Vertex_Simplification_05Ft.gdb\RoadCenterlines_05Ft'
modifiedRouteOutput = r'C:\GIS\Geodatabases\KHUB\Testing\R6_For_Vertex_Simplification_05Ft.gdb\RoadCenterlines_05Ft_Routes'

routeId = 'SourceRouteId'
measureSource = 'TWO_FIELDS'
fMeasureField = 'SourceFromMeasure'
tMeasureField = 'SourceToMeasure'
coordinatePriority = 'LOWER_LEFT'
measureFactor = 1
measureOffset = 0
ignoreGaps = True
buildIndex = True

print("Creating routes from the modified data.")
CreateRoutes_lr (modifiedData, routeId, modifiedRouteOutput, measureSource, fMeasureField, tMeasureField, coordinatePriority, measureFactor, measureOffset, ignoreGaps, buildIndex)
print("Finished creating routes from the modified data.")