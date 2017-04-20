#!usr/bin/env python
# -*- coding:utf-8 -*-
# dataimprovements_targetnetworkkeycalculation.py
# Created by dirktall04 on 2017-03-27
# Updated by dirktall04 on 2017-03-29

# Need to take the current source key parts and 
# translate them to their target key part equivalents.
# Then, need to concatenate the target key parts
# into their full target keys for both the 
# county-measure-based target network of All Roads
# and the state-measure-based target network
# of state system only.

import os

from arcpy import (AddField_management, CalculateField_management,
    CopyFeatures_management, Delete_management, DeleteFeatures_management,
    Describe, env, Exists, GetCount_management, MakeFeatureLayer_management,
    SelectLayerByAttribute_management, SelectLayerByLocation_management)

from arcpy.da import (SearchCursor as daSearchCursor,
    InsertCursor as daInsertCursor, UpdateCursor as daUpdateCursor)

from datareviewerchecks_config import (nullable)

from pathFunctions import (returnFeatureClass)

fcToCalculateTargetKeysIn = r'C:\GIS\Geodatabases\KHUB\Data_Mirroring_17D_AllRegions_Source.gdb\RoutesSource_StateLRS_StateNetwork'
targetKeyCalculationLayer = 'targetKeyCalculationLayer'
# Add a field called targetRouteNumChanged.
targetRouteNumChanged = 'targetRouteNumChanged'
sourceRouteNum = "LRS_ROUTE_NUM"
targetRouteNum = "LRS_ROUTE_NUM_TARGET"
uniqueIdTarget = "LRS_UNIQUE_TARGET"
targetCountyLRSKey = 'TargetCountyLRSKey'
targetStateLRSKey = 'TargetStateLRSKey'


def main():
    tempDesc = Describe(fcToCalculateTargetKeysIn)
    print("Parsing the LRS values in " + returnFeatureClass(tempDesc.catalogPath) + " to figure out what the LRS_ROUTE_PREFIX should be.")
    currentFieldObjects = tempDesc.fields
    try:
        del tempDesc
    except:
        pass
    
    currentFieldNames = [x.name for x in currentFieldObjects]
    
    if targetRouteNumChanged not in currentFieldNames:
        AddField_management(fcToCalculateTargetKeysIn, targetRouteNumChanged, "TEXT", "", "", 10, targetRouteNumChanged, nullable)
        print("The " + str(targetRouteNumChanged) + " field was added to the " + str(fcToCalculateTargetKeysIn) + " layer.")
    else:
        print("The " + str(targetRouteNumChanged) + " field will not be added to the " + str(fcToCalculateTargetKeysIn) +
            " layer, because it already exists.")
    
    if targetCountyLRSKey not in currentFieldNames:
        AddField_management(fcToCalculateTargetKeysIn, targetCountyLRSKey, "TEXT", "", "", 13, targetCountyLRSKey, nullable)
        print("The " + str(targetCountyLRSKey) + " field was added to the " + str(fcToCalculateTargetKeysIn) + " layer.")
    else:
        print("The " + str(targetCountyLRSKey) + " field will not be added to the " + str(fcToCalculateTargetKeysIn) +
            " layer, because it already exists.")
    
    if targetStateLRSKey not in currentFieldNames:
        AddField_management(fcToCalculateTargetKeysIn, targetStateLRSKey, "TEXT", "", "", 9, targetStateLRSKey, nullable)
        print("The " + str(targetStateLRSKey) + " field was added to the " + str(fcToCalculateTargetKeysIn) + " layer.")
    else:
        print("The " + str(targetStateLRSKey) + " field will not be added to the " + str(fcToCalculateTargetKeysIn) +
            " layer, because it already exists.")
    
    MakeFeatureLayer_management(fcToCalculateTargetKeysIn, targetKeyCalculationLayer)
    
    routePrefixTarget = "ROUTE_PREFIX_TARGET"
    lrsRouteNumSource = "LRS_ROUTE_NUM"
    lrsRouteNumTarget = "LRS_ROUTE_NUM_TARGET"
    lrsUniqueSource = "LRS_UNIQUE_IDENT"
    ##lrsUniqueSource2 = "LRS_UNIQUE_IDENT1"
    lrsUniqueTarget = "LRS_UNIQUE_TARGET"
    
    # County source to county target
    selectionQuery = """ SourceRouteId LIKE '___I%' OR LRS_ROUTE_PREFIX = 'I' """
    SelectLayerByAttribute_management(targetKeyCalculationLayer, "NEW_SELECTION", selectionQuery)
    CalculateField_management(targetKeyCalculationLayer, routePrefixTarget, "'1'", "PYTHON_9.3")
    
    selectionQuery = """ SourceRouteId LIKE '___U%' OR LRS_ROUTE_PREFIX = 'U' """
    SelectLayerByAttribute_management(targetKeyCalculationLayer, "NEW_SELECTION", selectionQuery)
    CalculateField_management(targetKeyCalculationLayer, routePrefixTarget, "'2'", "PYTHON_9.3")

    selectionQuery = """ SourceRouteId LIKE '___K%' OR LRS_ROUTE_PREFIX = 'K' """
    SelectLayerByAttribute_management(targetKeyCalculationLayer, "NEW_SELECTION", selectionQuery)
    CalculateField_management(targetKeyCalculationLayer, routePrefixTarget, "'3'", "PYTHON_9.3")

    selectionQuery = """ SourceRouteId LIKE '___X%' OR LRS_ROUTE_PREFIX = 'X' """
    SelectLayerByAttribute_management(targetKeyCalculationLayer, "NEW_SELECTION", selectionQuery)
    CalculateField_management(targetKeyCalculationLayer, routePrefixTarget, "'4'", "PYTHON_9.3")

    selectionQuery = """ SourceRouteId LIKE '___R%' OR LRS_ROUTE_PREFIX = 'R' """
    SelectLayerByAttribute_management(targetKeyCalculationLayer, "NEW_SELECTION", selectionQuery)
    CalculateField_management(targetKeyCalculationLayer, routePrefixTarget, "'5'", "PYTHON_9.3")

    selectionQuery = """ SourceRouteId LIKE '___M%' OR LRS_ROUTE_PREFIX = 'M' """
    SelectLayerByAttribute_management(targetKeyCalculationLayer, "NEW_SELECTION", selectionQuery)
    CalculateField_management(targetKeyCalculationLayer, routePrefixTarget, "'5'", "PYTHON_9.3")

    selectionQuery = """ SourceRouteId LIKE '___C%' OR LRS_ROUTE_PREFIX = 'C' """
    SelectLayerByAttribute_management(targetKeyCalculationLayer, "NEW_SELECTION", selectionQuery)
    CalculateField_management(targetKeyCalculationLayer, routePrefixTarget, "'5'", "PYTHON_9.3")

    selectionQuery = """ SourceRouteId LIKE '___L%' OR LRS_ROUTE_PREFIX = 'L' """
    SelectLayerByAttribute_management(targetKeyCalculationLayer, "NEW_SELECTION", selectionQuery)
    CalculateField_management(targetKeyCalculationLayer, routePrefixTarget, "'6'", "PYTHON_9.3")

    selectionQuery = """ SourceRouteId LIKE '___P%' OR LRS_ROUTE_PREFIX = 'P' """
    SelectLayerByAttribute_management(targetKeyCalculationLayer, "NEW_SELECTION", selectionQuery)
    CalculateField_management(targetKeyCalculationLayer, routePrefixTarget, "'7'", "PYTHON_9.3")

    selectionQuery = """ SourceRouteId LIKE '___A%' OR LRS_ROUTE_PREFIX = 'A' """
    SelectLayerByAttribute_management(targetKeyCalculationLayer, "NEW_SELECTION", selectionQuery)
    CalculateField_management(targetKeyCalculationLayer, routePrefixTarget, "'8'", "PYTHON_9.3")

    selectionQuery = """ SourceRouteId LIKE '___O%' OR LRS_ROUTE_PREFIX = 'O' """
    SelectLayerByAttribute_management(targetKeyCalculationLayer, "NEW_SELECTION", selectionQuery)
    CalculateField_management(targetKeyCalculationLayer, routePrefixTarget, "'8'", "PYTHON_9.3")

    selectionQuery = """ SourceRouteId LIKE '___Q%' OR LRS_ROUTE_PREFIX = 'Q' """
    SelectLayerByAttribute_management(targetKeyCalculationLayer, "NEW_SELECTION", selectionQuery)
    CalculateField_management(targetKeyCalculationLayer, routePrefixTarget, "'8'", "PYTHON_9.3")
    
    # For every Prefix:
    SelectLayerByAttribute_management(targetKeyCalculationLayer, "CLEAR_SELECTION", selectionQuery)
    SelectLayerByAttribute_management(targetKeyCalculationLayer, "SWITCH_SELECTION", selectionQuery)
    CalculateField_management(targetKeyCalculationLayer, lrsRouteNumTarget, "!" + str(lrsRouteNumSource) + "!", "PYTHON_9.3")
    # Using the 2 characters for unique id. Local routes with more than 2 characters in unique id are probably errors.
    CalculateField_management(targetKeyCalculationLayer, lrsUniqueSource, "!" + str(uniqueIdTarget) + "!", "PYTHON_9.3")
    
    # Since the above calculation might not be accurate for ramps, use this one instead.
    calculateRampUniqueIdValues()
    
    # Function that looks at the M and C routes and renumbers them if there are conflicts between
    # an M route and an R route, or between a C route and an R/M route.
    duplicateCheckForMAndC()
    
    # Calculate the full target route keys from their pieces.
    concatFullTargetKeys()


# For each one, calculate it so that the LRS_ROUTE_NUM_TAGET = LRS_ROUTE_NUM
## But will be reviewed for M & C Routes, based on R & M #'s.
# If there is a change in the route number based on R/M/C conflict, then the M or C route number
# that gets changed, should retain a flag so that we can query for it.

###Inventory direction is 0 or 1

def duplicateCheckForMAndC():
    print("Checking for duplicate route numbers in the target route numbers for R, M, and C Routes.")
    # Select the R routes.
    # Cursor them, and add their route number to a dict.
    # Then, select the M routes.
    # Cursor them and add their route number to a dict.
    # Then, select the C routes.
    # Cursor them and add their route number to a dict.
    # Create a list of free route numbers that are not in any of the 3 dicts.
    # Then, for each M route, if its routenumber is not in the R routes dict,
    # mark the M route's targetRouteNumChanged to "Kept".
    # Otherwise, if its routenumber is in the R routes dict,
    # Select the next free route number in the free route numbers list.
    # Remove the free route number from the free route numbers list.
    # Assign the free route number to the M route and mark the M route's
    # targetRouteNumChanged to "Changed".
    # Then, for each C route, if its routenumber is not in the R routes dict
    # and if it is also not in the M routes dict,
    # mark the C route's targetRouteNumChanged to "Kept".
    # Otherwise, if its routenumber is in the R routes dict or the M routes dict,
    # Select the next free route number in the free route numbers list.
    # Remove the free route number from the free route numbers list.
    # Assign the free route number to the C route and mark the C route's
    # targetRouteNumChanged to "Changed".
    rRoutesDict = dict()
    mRoutesDict = dict()
    cRoutesDict = dict()
    
    rRoutesSelectionQuery = """ SourceRouteId LIKE '___R%' OR LRS_ROUTE_PREFIX = 'R' """
    mRoutesSelectionQuery = """ SourceRouteId LIKE '___M%' OR LRS_ROUTE_PREFIX = 'M' """
    cRoutesSelectionQuery = """ SourceRouteId LIKE '___C%' OR LRS_ROUTE_PREFIX = 'C' """
    
    searchCursorFields = [sourceRouteNum, targetRouteNum, targetRouteNumChanged]
    
    newCursor = daSearchCursor(fcToCalculateTargetKeysIn, searchCursorFields, rRoutesSelectionQuery)
    for cursorItem in newCursor:
        rRoutesDict[cursorItem[-3]] = 1
    try:
        del newCursor
    except:
        pass
    
    newCursor = daSearchCursor(fcToCalculateTargetKeysIn, searchCursorFields,  mRoutesSelectionQuery)
    for cursorItem in newCursor:
        mRoutesDict[cursorItem[-3]] = 1
    try:
        del newCursor
    except:
        pass
    
    newCursor = daSearchCursor(fcToCalculateTargetKeysIn, searchCursorFields, cRoutesSelectionQuery)
    for cursorItem in newCursor:
        cRoutesDict[cursorItem[-3]] = 1
    try:
        del newCursor
    except:
        pass
    
    usedRoutesList = [x for x in rRoutesDict.keys()]
    usedRoutesList = usedRoutesList + [y for y in mRoutesDict.keys()]
    usedRoutesList = usedRoutesList + [z for z in cRoutesDict.keys()]
    sortedUsedRoutesList = sorted(usedRoutesList)
    freeRoutesList = [str(x).zfill(5) for x in xrange(12000, 64000) if str(x).zfill(5) not in sortedUsedRoutesList]
    
    print("Used routes are as follows:")
    for usedRouteNumber in sortedUsedRoutesList:
        print("Used route number = " + str(usedRouteNumber) + ".")
    
    sortedFreeRoutesList = sorted(freeRoutesList)
    reverseSortedFreeRoutesList = sortedFreeRoutesList[::-1]
    
    print("Updating lrs target numbers for M routes where they conflict with R routes.")
    # Check the target lrs route numbers for M routes against the R routes.
    rRoutesKeys = rRoutesDict.keys()
    newCursor = daUpdateCursor(fcToCalculateTargetKeysIn, searchCursorFields, mRoutesSelectionQuery)
    for mRouteItem in newCursor:
        mRouteListItem = list(mRouteItem)
        if mRouteListItem[-2] in rRoutesKeys:
            mRouteListItem[-1] = 'Changed'
            mRouteListItem[-2] = reverseSortedFreeRoutesList.pop()
            mRoutesDict[mRouteListItem[-2]] = 1
            newCursor.updateRow(mRouteListItem)
        else:
            pass
    try:
        del newCursor
    except:
        pass
    
    print("Updating lrs target numbers for C routes where they conflict with R routes or M routes.")
    # Check the target lrs route numbers for C routes against the R routes and the M routes.
    mRoutesKeys = mRoutesDict.keys()
    newCursor = daUpdateCursor(fcToCalculateTargetKeysIn, searchCursorFields, cRoutesSelectionQuery)
    for cRouteItem in newCursor:
        cRouteListItem = list(cRouteItem)
        if cRouteListItem[-2] in rRoutesKeys or cRouteListItem[-2] in mRoutesKeys:
            cRouteListItem[-1] = 'Changed'
            cRouteListItem[-2] = reverseSortedFreeRoutesList.pop()
            newCursor.updateRow(cRouteListItem)
        else:
            pass
    try:
        del newCursor
    except:
        pass


# County source to state target

# This should be a 8-9 character key, with the last character being a reduced length unique id that's nullable.
# Prefix (1) + Route number (5) + Suffix (1) + Inventory Direction (1) = 8 characters.
# Prefix (1) + Route number (5) + Suffix (1) + Inventory Direction (1) + Unique ID (2 reduced to 1) = 9 characters.

# Target networks should use shape length. If there are problems with pure
# shape length, they may need to be chained and calibrated with their actual lengths,
# but that will have to be reviewed in iteration 2 and decided for iteration 3.

'''
--Email from Kyle on this topic--
Details:

County code for C routes should be the county code, not the UAB code as in the source network

Route numbers for I, U, K (1,2,3) prefixes stay the same, 

Route numbers for Ramps (4) mostly stay the same, but the “Ramp ID” unique number part of the ramp goes in “Unique ID”

I think there are a couple state highways, a K route (K-15) and maybe some US Business routes that would have a Unique ID in source and target.

Route numbers for R, M stay the same, and C stays the same unless the number conflicts with an R or M route (we should be able to query to see if/where this happens) where county code, prefix, suffix, inventory direction are identical.  If Route ID is identical, we have a choice to either change the route ID or add a non-null unique ID.  I’d prefer to change the Route ID and I think Kevin K is OK with that.

Suffix should be the same between source and target, no mapping necessary.  

Inventory Direction for I, U, K (123) 0 is Eastbound EB, NB, and 1 is SB/WB.  

Not much to say about Locals or below, there isn’t “source network” routes, the only suffix should be 0 or Ghost.   

Kyle
'''
# The above was preGhost changes that resulted in Ghost being a prefix had having most of it's meaning
# taken over by the Zombie prefix designation instead.


def calculateRampUniqueIdValues():
    layerForRampsSelection = 'layerForRampsSelection'
    MakeFeatureLayer_management(fcToCalculateTargetKeysIn, layerForRampsSelection)
    selectionQuery = """ SourceRouteId LIKE '___X%' OR LRS_ROUTE_PREFIX = 'X' """
    updateFields = ['SourceRouteId', uniqueIdTarget]
    
    newCursor = daUpdateCursor(fcToCalculateTargetKeysIn, updateFields, selectionQuery)
    
    for updateItem in newCursor:
        updateListItem = list(updateItem)
        keyToUse = ''
        if updateListItem[0] is not None:
            sourceIdFull = str(updateListItem[0])
            if len(sourceIdFull) >= 11:
                idToUse = sourceIdFull[9:11]
            else:
                idToUse = '00'
        else:
            idToUse = '00'
        
        updateListItem[1] = idToUse
        newCursor.updateRow(updateListItem)
    
    try:
        del newCursor
    except:
        pass


def concatFullTargetKeys():
    # County Key Calculation
    # County Code (3) + Prefix (1) + Route number (5) + Suffix (1) + Inventory Direction (1) = 11 characters.
    # County Code (3) + Prefix (1) + Route number (5) + Suffix (1) + Inventory Direction (1) + Unique ID (2) = 13 characters.
    # First, start an update cursor,
    # then update the columns with this format:
    # lrsKeyCountyTarget = countycode.zfill(3) + prefix_target + routenumber_target + suffix + inventorydirection or 0 + unique id (ramp code), or null if not a ramp (PREFIX_TARGET is not 'X') and unique id/ramp code == '00'.
    updateFields = ['LRS_COUNTY_PRE', 'ROUTE_PREFIX_TARGET', 'LRS_ROUTE_NUM_TARGET', 'LRS_ROUTE_SUFFIX', 'LRS_DIRECTION', 'KDOT_DIRECTION_CALC',
        uniqueIdTarget, 'LRS_UNIQUE_IDENT', 'LRS_UNIQUE_IDENT1', targetCountyLRSKey]
    # If uniqueID is None OR uniqueID == '00' and prefix_target != 'X',
    # uniqueIDPartForConcat = ''
    
    newCursor = daUpdateCursor(fcToCalculateTargetKeysIn, updateFields)
    
    for updateItem in newCursor:
        updateListItem = list(updateItem)
        keyToUse = ''
        if str(updateListItem[0]).lower() != 'none':
            countyPre = updateListItem[0]
        else:
            countyPre = '404' # County Not Found
        if str(updateListItem[1]).lower() != 'none':
            prefixTarget = updateListItem[1]
        else:
            prefixTarget = '8' # For 'other'.
        if str(updateListItem[2]).lower() != 'none':
            routeNumTarget = updateListItem[2]
        else:
            routeNumTarget = str('').zfill(5)
        if str(updateListItem[3]).lower() != 'none':
            if updateListItem[1] in ('1', '2', '3', '4', '5', '6'):
                routeSuffix = updateListItem[3]
            elif updateListItem[1] in ('0', 'G'):
                routeSuffix = updateListItem[3]
            else:
                routeSuffix = '0'
        else:
            routeSuffix = '0'
        
        lrsDirToUse = ''
        if updateListItem[5] in ('0', '1'):
            lrsDirToUse = str(updateListItem[5])
        elif updateListItem[4] in ('EB', 'NB'):
            lrsDirToUse = '0'
        elif updateListItem[4] in ('WB', 'SB'):
            lrsDirToUse = '1'
        else:
            lrsDirToUse = '0'
        
        uniqueToUse = ''
        if str(updateListItem[6]).lower() != 'none':
            uniqueToUse = updateListItem[6]
        elif str(updateListItem[8]).lower() != 'none':
            uniqueToUse = updateListItem[8]
        elif str(updateListItem[7]).lower() != 'none':
            uniqueToUse = updateListItem[7]
        
        if uniqueToUse == '00' and prefixTarget != 'X':
            uniqueToUse = ''
        else:
            pass
        
        keyToUse = countyPre + prefixTarget + routeNumTarget + routeSuffix + lrsDirToUse + uniqueToUse
        
        updateListItem[9] = keyToUse
        newCursor.updateRow(updateListItem)
    
    try:
        del newCursor
    except:
        pass
    
    # state system only
    # This should be a 8-9 character key, with the last character being a reduced length unique id that's nullable.
    # Prefix (1) + Route number (5) + Suffix (1) + Inventory Direction (1) = 8 characters.
    # Prefix (1) + Route number (5) + Suffix (1) + Inventory Direction (1) + Unique ID (2 reduced to 1) = 9 characters.
    stateSystemSelectionQuery = """ SourceRouteId LIKE '___I%' OR LRS_ROUTE_PREFIX = 'I' OR SourceRouteId LIKE '___U%' OR LRS_ROUTE_PREFIX = 'U' OR SourceRouteId LIKE '___K%' OR LRS_ROUTE_PREFIX = 'K' """
    updateFields = ['LRS_COUNTY_PRE', 'ROUTE_PREFIX_TARGET', 'LRS_ROUTE_NUM_TARGET', 'LRS_ROUTE_SUFFIX', 'LRS_DIRECTION', 'KDOT_DIRECTION_CALC',
        uniqueIdTarget, 'LRS_UNIQUE_IDENT', 'LRS_UNIQUE_IDENT1', targetStateLRSKey]
    
    newCursor = daUpdateCursor(fcToCalculateTargetKeysIn, updateFields, stateSystemSelectionQuery)
    
    for updateItem in newCursor:
        updateListItem = list(updateItem)
        keyToUse = ''
        #ignore countyPre for state network keys
        countyPre = ''
        '''
        if updateListItem[0] is not None:
            countyPre = updateListItem[0]
        else:
            countyPre = '404' # County Not Found
        '''
        if str(updateListItem[1]).lower() != 'none':
            prefixTarget = updateListItem[1]
        else:
            prefixTarget = '8' # For 'other'.
        if str(updateListItem[2]).lower() != 'none':
            routeNumTarget = updateListItem[2]
        else:
            routeNumTarget = str('').zfill(5)
        if str(updateListItem[3]).lower() != 'none':
            if int(str(updateListItem[1])) <= 6:
                routeSuffix = updateListItem[3]
            elif updateListItem in ('0', 'G'):
                routeSuffix = updateListItem[3]
            else:
                routeSuffix = '0'
        else:
            routeSuffix = '0'
        
        lrsDirToUse = ''
        if updateListItem[5] in ('0', '1'):
            lrsDirToUse = str(updateListItem[5])
        elif updateListItem[4] in ('EB', 'NB'):
            lrsDirToUse = '0'
        elif updateListItem[4] in ('WB', 'SB'):
            lrsDirToUse = '1'
        else:
            lrsDirToUse = '0'
        
        uniqueToUse = ''
        if str(updateListItem[6]).lower() != 'none':
            uniqueToUse = str(updateListItem[6])[-1]
        elif str(updateListItem[8]).lower() != 'none':
            uniqueToUse = str(updateListItem[8])[-1]
        elif str(updateListItem[7]).lower() != 'none':
            uniqueToUse = str(updateListItem[7])[-1]
        
        if uniqueToUse == '00' and prefixTarget != 'X':
            uniqueToUse = ''
        else:
            pass
        
        keyToUse = countyPre + prefixTarget + routeNumTarget + routeSuffix + lrsDirToUse + uniqueToUse
        
        updateListItem[9] = keyToUse
        newCursor.updateRow(updateListItem)
    
    try:
        del newCursor
    except:
        pass

if __name__ == "__main__":
    main()

else:
    pass