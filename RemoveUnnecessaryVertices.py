#RemoveUnnecessaryVertices.py
# -*- coding: utf-8 -*-
# Created by: Dirk Talley
# 2016-11-21

from arcpy import (env, CopyFeatures_management, CreateRoutes_lr, Describe,
    FlipLine_edit,
    MakeFeatureLayer_management, SelectLayerByAttribute_management)

from arcpy.da import UpdateCursor as daUpdateCursor

# Use a very small tolerance and see what it looks like when
# Cowley's features are simplified.

# Then, build routes and test them for monotonicity.

# If that still doesn't work. Look into problems like where
# the routes don't build correctly if the from measure is exactly
# the same as the to measure on the source centerlines.
# Look at the source centerlines and see if the ends of each
# line are exactly on top of one another or if they're just
# a little bit off.

env.overwriteOutput = True
env.MResolution = 0.0001
env.MTolerance = 0.001

inputData = r'C:\GIS\Geodatabases\KHUB\KHUB_Data_Thread3.gdb\All_Road_Centerlines'
modifiedData = r'C:\GIS\Geodatabases\KHUB\KHUB_Data_Thread3.gdb\Modified_Road_Centerlines'
modifiedRouteOutput = r'C:\GIS\Geodatabases\KHUB\KHUB_Data_Thread3.gdb\Modified_Routes'

featureLayer = 'Roads_FC'
routeId = 'CountyKey1'
measureSource = 'TWO_FIELDS'
fMeasureField = 'F_CNTY_1'
tMeasureField = 'T_CNTY_1'
coordinatePriority = 'LOWER_LEFT'
measureFactor = 1
measureOffset = 0
ignoreGaps = True
buildIndex = True

updateFields = ['F_CNTY_1', 'T_CNTY_1']

# Make a copy of the input data first. FlipLine_edit modifies the input data.
# FlipLine_edit *does* honor selections, so create a feature layer, then select
# the necessary routes prior to running FlipLine_edit.

#print("Copying features to a new location.")
#CopyFeatures_management(inputData, modifiedData)

MakeFeatureLayer_management (modifiedData, featureLayer)

featureSpatialReference = Describe(featureLayer).spatialReference

selectionQuery = """ "Non_State_Flip_Flag" IS NOT NULL OR "State_Flip_Flag" IS NOT NULL """

#print("Selecting features.")
#SelectLayerByAttribute_management (featureLayer, "NEW_SELECTION", selectionQuery)

#print("Flipping selected features.")
#FlipLine_edit(featureLayer)
#print("Feature flipping complete.")

print("Swapping measures where necessary.")
print("Creating a new selection.")
SelectLayerByAttribute_management (featureLayer, "NEW_SELECTION", selectionQuery)
print("Swapping selected from and to values.")

newCursor = daUpdateCursor(featureLayer, updateFields, selectionQuery, featureSpatialReference)

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

print("Creating routes from the modified data.")
CreateRoutes_lr (modifiedData, routeId, modifiedRouteOutput, measureSource, fMeasureField, tMeasureField, coordinatePriority, measureFactor, measureOffset, ignoreGaps, buildIndex)
print("Finished creating routes from the modified data.")