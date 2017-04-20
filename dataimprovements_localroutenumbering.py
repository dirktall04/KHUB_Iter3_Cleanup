#!/usr/bin/env python
# -*- coding:utf-8 -*-
# dataimprovements_localroutenumbering.py

# For code enhancement on the Route Numbering and code correctness on the Unique Numbering:
# use the Sort_management function from ArcPy.
# Sort_management (in_dataset, out_dataset, sort_field, {spatial_sort_method})

# Compute X & Y coordinates for the centroid of each line,
# then get the distance from the point of interest, in this case, a point
# which is below(south of) and left of(west of) the other points.

# Use a pythagorean theorem, skipping the square root operation at the end
# since the distance ordering won't change when taking the square root.

# searchcursor in the data with centroid information for each line.
# compute the distance from the arbitrary point with the centroid's
# x & y values.

# then, sort by county, then sort by name, then sort by distance from the point
# that should give you an ordered list of roads that breaks at the county
# and breaks at name changes
# and is sorted by distance, making ordering all of the segments in a particular
# route very easy, just loop through them in order and assign a new unique id
# until the name stops being the same, then reset to the base value that you
# start with.

from operator import itemgetter, attrgetter, methodcaller ## For sorting.

from arcpy import Array as arcpyArray, Describe, env, Point, Polyline

from arcpy.da import SearchCursor as daSearchCursor, UpdateCursor as daUpdateCursor

from pathFunctions import (returnFeatureClass, returnGDBOrSDEName)

##import math

#from datareviewerchecks_config import (localRouteInputLines,
#    localRouteOutputLines)

routeFeaturesFC = r'C:\GIS\Geodatabases\KHUB\Manual_Edit_Aggregation\2017-03-08\Data_Mirroring_12B_AllRegions_IntegrationTest_Source.gdb\All_Road_Centerlines_Copy'

if returnGDBOrSDEName(routeFeaturesFC) != None:
    env.workspace = returnGDBOrSDEName(routeFeaturesFC)
else:
    pass

print(env.workspace)

#currentXYTolerance = env.XYTolerance

tempDesc = Describe(routeFeaturesFC)
currentSR = tempDesc.spatialReference
currentXYTolerance = currentSR.XYTolerance 
print("currentXYTolerance: " + str(currentXYTolerance))
try:
    del tempDesc
except:
    pass

'''
unsortedLineList = list()

unsortedLineFields = ['OBJECTID', 'COUNTY_NUMBER', 'LABEL', 'SHAPE@TRUECENTROID'] # Don't use TRUECENTROID. Use SHAPE@, then .centroid.

newCursor = daSearchCursor(localRouteInputLines, inputLineFields)

for cursorItem in newCursor:
    unsortedLineList.append(list(cursorItem))

for unsortedLineItem in unsortedLineList:
    distFromPoint = calculateDistance(unsortedLineItem[3])
    unsortedLineItem.append(distFromPoint)

# sort here by the county_number, the label, and the distFromPoint.
sortedLineList = sorted(unsortedLineList, key=itemgetter(1, 2, 4)) # 1 = COUNTY_NUMBER, 2 = LABEL, 3 = appended distFromPoint
'''

# after sorting, chain together the routes by county, label and distance. -- since they should be in the proper order for it,
# you can see whether or not the firstpoint of one line segment and lastpoint of the next line segment are coincident.
# If they are, then you don't need to increment the unique number. -- Kind of goes back to having things flipped properly
# prior to creation of the routes, however.

## might want some additional code to see if, for sorted lines, the firstpoint and firstpoint match, or the lastpoint and firstpoint
## match -- could be indicative of a flipping issue.

# Not sure if I should update here or just remove them from the original data and then add them back in with an insert
# cursor. The insert cursor approach would likely be more performant.
#####newCursor = daUpdateCursor(localRouteOutputLines, ouputLineFields) 

## Might be worthwhile to explore similar code to this for making a route's underlying segments more likely
## to build into a route which is monotonic.
## -- Sort by LRSKey & spatial location.
## Then, for each segment, test whether the first or last point matches the first or last point in the next ordered segment.
## If so, then join those two together and merge their measures.
## 

# Get the minimum for the X measure and the minimum for the Y measure.
# Then, subtract 10000 from each and use it that as the absolute minimum point
# from which to measure the distance of all of the other features and derive
# a sortable distance away from column.

#  ffy----ffx,ffy
#   |   a  /|
#   |     / |
#   |b   /  |
#   |   /   |
#   |  /c   |
#   | /     |
#   |/      |
#  minxy---ffx

# Then, you can derive the distance between the minxy and each features xy, since you know that
# the minxy is going to be more southerly and westerly than the first feature's (when sorted spatially)
# x & y.
## The minimum x and the minimum y could come from different features. That's okay.

# Cursor over the features that have an 'L' in their LRS key, or as the LRS key prefix.
# Include SHAPE@ in the list, and get the on-feature centroid instead of the
# SHAPE@XY centroid or the centroid that you get by calling 'truecentroid'.
# Neither of those is what you want. Instead, use the .centroid
# of the geometry feature from SHAPE@.
# This is documented as "The true centroid if it is within or on the feature;
# otherwise, the label point is returned. Returns a point object."

# Start with a subset by looking for MORTON COUNTY in the KDOT_COUNTY_L or KDOT_COUNTY_R.
# Just not sure how to do that SQL select since it's a domain. Guess I'll have to look it
# up in the domains to figure out how to code it.

# Morton is 065.
###selectionQuery1 = ''' KDOT_COUNTY_L = '065' OR KDOT_COUNTY_R = '065' '''

## May need to do this county by county. Trying to do the entire state at once
## resulted in a memory error once the Python process hit ~1.6GB of
## memory in its private working set.

## If doing county by county, then you just need to check the road name
## and if it's contiguous.

## If the road name is the same and it's not contigous, then you need to
## increment the uniqueID for the route.
## That should also get rid of problems with the local road names of
## some cities being the same, since even though mainStreet in City1
## will be the same name as mainStreet in City2, the uniqueIDs for
## them will be different.
## Will have to test it and see if that works, or if you need to
## increment the routes by a grouped spatial location first and
## by name second, which would be more effort, but might produce
## a better result in the end.

## For each countyNumber, select based on KDOT_COUNTY_L = ''
## Then, select based on KDOT_COUNTY_L IS NULL AND KDOT_COUNTY_R = ''.

def localRouteNumbering():
    tempDesc = Describe(routeFeaturesFC)
    print("Calculating LRS Key sub-parts for features in " + returnFeatureClass(tempDesc.catalogPath) + ".")
    OIDFieldName = tempDesc.OIDFieldName
    
    try:
        del tempDesc
    except:
        pass
    
    # ReAdd the fields that we're interested in, in the correct order.
    # sortPointDist will be appended later, making it [-1] and 'LRS_UNIQUE_IDENT1' will be [-2].
    fieldsToUse = [OIDFieldName, 'SHAPE@', 'LABEL', 'LRS_ROUTE_PREFIX', 'LRS_ROUTE_NUM', 'LRS_UNIQUE_IDENT', 'LRS_UNIQUE_IDENT1']
    
    currentFields = fieldsToUse
    
    shapeTokenPosition = 1
    
    uniqueCountyCodeDict = dict()
    countyCodeFieldsList = ['KDOT_COUNTY_L', 'KDOT_COUNTY_R']
    newCursor = daSearchCursor(routeFeaturesFC, countyCodeFieldsList)
    for cursorRow in newCursor:
        uniqueCountyCodeDict[str(cursorRow[0])] = 1
        uniqueCountyCodeDict[str(cursorRow[1])] = 1
    
    try:
        del newCursor
    except:
        pass
    
    uniqueCountyCodeList = list()
    
    for uniqueCountyCode in uniqueCountyCodeDict.keys():
        uniqueCountyCodeList.append(uniqueCountyCode)
    
    try:
        del uniqueCountyCodeDict
    except:
        pass
    
    try:
        uniqueCountyCodeList.remove('None')
    except:
        pass
    
    sortedUniqueCountyCodes = sorted(uniqueCountyCodeList) # No need to specify a key since it's one column.
    
    for uniqueCountyCodeItem in sortedUniqueCountyCodes:
        print('Selecting features based on countyCode: ' + str(uniqueCountyCodeItem) + '.')
        routeFeaturesList = list()
        
        uniqueLabelDict = dict()
        
        # This should include a check for LRS_PREFIX = 'L' when the KDOT_LRS_KEY IS NULL, instead of taking everything that has a NULL
        # KDOT LRS_KEY. Need another parenthesis to group the condition inside the current parenthesis. 
        selectionQuery1 = """ KDOT_COUNTY_L = '""" + str(uniqueCountyCodeItem) + """' AND ((KDOT_LRS_KEY IS NULL AND LRS_PREFIX = 'L') OR KDOT_LRS_KEY LIKE '%L%') """
        selectionQuery2 = """ KDOT_COUNTY_L IS NULL AND KDOT_COUNTY_R = '""" + str(uniqueCountyCodeItem) + """' AND ((KDOT_LRS_KEY IS NULL AND LRS_PREFIX = 'L') OR KDOT_LRS_KEY LIKE '%L%') """
        
        labelField = ['LABEL']
        newCursor = daSearchCursor(routeFeaturesFC, labelField, selectionQuery1)
        for cursorRow in newCursor:
            uniqueLabelDict[str(cursorRow[0])] = 1
        
        try:
            del newCursor
        except:
            pass
        
        newCursor = daSearchCursor(routeFeaturesFC, labelField, selectionQuery2)
        for cursorRow in newCursor:
            uniqueLabelDict[str(cursorRow[0])] = 1
        
        try:
            del newCursor
        except:
            pass
        
        countyLocalNumber = 0
        
        # Narrow the features that are looked at further.
        ### Change this to just give you the features instead of    ###
        ### cursoring them back out.                                ###
        ### Figure out a way to create dicts/lists that store the features
        ### in the way that you want them instead of having to run another
        ### separate pair of selects after this.
        for uniqueLabelKey in uniqueLabelDict.keys():
            if uniqueLabelKey is not 'None':
                # Labels with single quotes cause problems in selections.
                if str.find(uniqueLabelKey, "'") > -1:
                    # So, escape them by replacing individual single quotes with double single quotes.
                    uniqueLabelKey = str.replace(uniqueLabelKey, "'", "''") 
                else:
                    pass
                print("Using the LABEL field value of: " + str(uniqueLabelKey) + ".")
                countyLocalNumber += 1
                selectionQuery3 = selectionQuery1 + """ AND LABEL = '""" + str(uniqueLabelKey) + """' """
                selectionQuery4 = selectionQuery2 + """ AND LABEL = '""" + str(uniqueLabelKey) + """' """
                
                labeledRouteFeaturesList = list()
                firstCounter = 0
                newCursor = daSearchCursor(routeFeaturesFC, currentFields, selectionQuery3)
                for cursorRow in newCursor:
                    firstCounter += 1
                    labeledRouteFeaturesList.append(list(cursorRow))
                
                try:
                    del newCursor
                except:
                    pass
                print("FirstCounter found : " + str(firstCounter) + " segments.")
                
                secondCounter = 0
                newCursor = daSearchCursor(routeFeaturesFC, currentFields, selectionQuery4)
                for cursorRow in newCursor:
                    secondCounter += 1
                    labeledRouteFeaturesList.append(list(cursorRow))
                
                try:
                    del newCursor
                except:
                    pass
                
                print("SecondCounter found : " + str(secondCounter) + " segments.")
                
                sortedLabeledRouteFeaturesList = addDistanceAndSort(labeledRouteFeaturesList, shapeTokenPosition)
                
                del labeledRouteFeaturesList
                
                labelUniqueNumber = 0
                previousFeatureGeom = None
                outputFeaturesDict = dict()
                for sortedLabeledRouteFeatureItem in sortedLabeledRouteFeaturesList:
                    if previousFeatureGeom == None:
                        # This is the first feature of this label.
                        # Don't need to check for incrementing the labelUniqueNumber.
                        # Just assign the current countyLocalNumber to this feature.
                        # Then, set the previousFeatureGeom to this feature's shape.
                        previousFeatureGeom = sortedLabeledRouteFeatureItem[shapeTokenPosition]
                    else:
                        # Check to see if this feature's firstpoint or lastpoint are
                        # a match for the previous feature's firstpoint or lastpoint.
                        thisFeatureGeom = sortedLabeledRouteFeatureItem[shapeTokenPosition]
                        ## This part needs work because it always fails. :(.
                        ## Create a function to check the arrays for relevant matching values instead.
                        ## And let it "match" when there are points that are within the feature tolerance
                        ## of one another. The non-matching is most likely a problem with floating point
                        ## math and equalities. -- See videolog lookup C# for ideas, if needed.
                        
                        # Change this to look at math.abs(firstPoint.X - other.firstPoint.X) < 2*Epsilon,
                        # and math.abs(firstPoint.Y - other.firstPoint.Y) < 2*Epsilon
                        # Since each Point is a Python object and they won't have the same
                        # identity in Python when it performs a comparison on them.
                        # The only time that this will work correctly is when you have
                        # two variable names referencing the same object
                        # (in the same memory location).
                        if polylineStartEndPointsMatch(thisFeatureGeom, previousFeatureGeom, currentXYTolerance) == True:
                            # The feature is contiguous without a gap. The labelUniqueNumber doesn't need to be incremented.
                            # Assign the county code as it's routeNumber and the labelUniqueNumber as its unique ID.
                            pass
                        else:
                            # If not, increment the labelUniqueNumber by 1
                            # prior to assignment on this feature.
                            labelUniqueNumber += 1
                        
                        # If greater than 99, then you have to split it so that part of it goes into LRS_UNIQUE_IDENT
                        # and part of it goes into LRS_UNIQUE_IDENT1.
                        if labelUniqueNumber > 99:
                            onesAndTens = labelUniqueNumber % 100
                            hundredsAndThousands = labelUniqueNumber / 100
                            pass
                        else:
                            onesAndTens = labelUniqueNumber
                            hundredsAndThousands = 0
                        sortedLabeledRouteFeatureItem[-2] = str(onesAndTens).zfill(2) ## 2 chars
                        sortedLabeledRouteFeatureItem[-3] = str(hundredsAndThousands).zfill(1) ## 2 chars # Should only be 1char, but /shrug
                        sortedLabeledRouteFeatureItem[-4] = str(countyLocalNumber).zfill(5) ## 5 chars
                        # Then, set the previousFeatureGeom to this feature's shape.
                        previousFeatureGeom = sortedLabeledRouteFeatureItem[shapeTokenPosition]
                    
                    print("Adding a feature to the outputFeaturesDict with a countyLocalNumber of: " + str(countyLocalNumber) + " and a labelUniqueNumber of: " + str(labelUniqueNumber) + ".")
                    outputFeaturesDict[sortedLabeledRouteFeatureItem[0]] = sortedLabeledRouteFeatureItem[:-1]
                
                newCursor = daUpdateCursor(routeFeaturesFC, currentFields, selectionQuery3)
                
                for cursorRow in newCursor:
                    if cursorRow[0] in outputFeaturesDict.keys():
                        newCursor.updateRow(outputFeaturesDict[cursorRow[0]])
                
                try:
                    del newCursor
                except:
                    pass
                
                newCursor = daUpdateCursor(routeFeaturesFC, currentFields, selectionQuery4)
                
                for cursorRow in newCursor:
                    if cursorRow[0] in outputFeaturesDict.keys():
                        newCursor.updateRow(outputFeaturesDict[cursorRow[0]])
                
                try:
                    del newCursor
                except:
                    pass
                
                try:
                    del sortedLabeledRouteFeaturesList
                except:
                    pass
                
            else:
                pass
            
            #Cleanup
            try:
                del sortedLabeledRouteFeaturesList
            except:
                pass
        try:
            del sortedLabeledRouteFeaturesList
        except:
            pass
        ###########################################################################


def polylineStartEndPointsMatch(firstFeature, secondFeature, epsilonValue):
    testResult = False
    
    firstFeatureFirstPoint = firstFeature.firstPoint
    firstFeatureLastPoint = firstFeature.lastPoint
    secondFeatureFirstPoint = secondFeature.firstPoint
    secondFeatureLastPoint = secondFeature.lastPoint
    
    fffpX = firstFeatureFirstPoint.X
    fffpY = firstFeatureFirstPoint.Y
    fflpX = firstFeatureLastPoint.X
    fflpY = firstFeatureLastPoint.Y
    sffpX = secondFeatureFirstPoint.X
    sffpY = secondFeatureFirstPoint.Y
    sflpX = secondFeatureLastPoint.X
    sflpY = secondFeatureLastPoint.Y
    
    ##abs() is callable without importing math
    #bothfeatures are backward with respect to one another
    #fffpX, sflpX; fffpY, sflpY match
    if (abs(fffpX - sflpX) <= epsilonValue) and (abs(fffpY - sflpY) <= epsilonValue):
        testResult = True
        return testResult
    #onefeature is backward with respect to the other, can't tell which based on this analysis
    #fffpX, sffpX; fffpY, sffpY match
    elif (abs(fffpX - sffpX) <= epsilonValue) and (abs(fffpY - sffpY) <= epsilonValue):
        testResult = True
        return testResult
    #onefeature is backward with respect to the other, can't tell which based on this analysis
    #fflpX, sflpX; fflpY, sflpY match
    elif (abs(fflpX - sflpX) <= epsilonValue) and (abs(fflpY - sflpY) <= epsilonValue):
        testResult = True
        return testResult
    #bothfeatures are correctly ordered relative to one another
    #fflpX, sffpX; fflpY, sffpY match
    elif (abs(fflpX - sffpX) <= epsilonValue) and (abs(fflpY - sffpY) <= epsilonValue):
        testResult = True
        return testResult
    else:
        print("Test results:")
        print("abs(fffpX - sflpX): " + str(abs(fffpX - sflpX)))
        print("abs(fffpY - sflpY): " + str(abs(fffpY - sflpY)))
        print("abs(fffpX - sffpX): " + str(abs(fffpX - sffpX)))
        print("abs(fffpY - sffpY): " + str(abs(fffpY - sffpY)))
        print("abs(fflpX - sflpX): " + str(abs(fflpX - sflpX)))
        print("abs(fflpY - sflpY): " + str(abs(fflpY - sflpY)))
        print("abs(fflpX - sffpX): " + str(abs(fflpX - sffpX)))
        print("abs(fflpY - sffpY): " + str(abs(fflpY - sffpY)))
    
    # Add logic so that if the firstPoint and lastPoint in a location are the same, the objectID
    # is recorded and later flagged for ghost review, or we just flag one side for ghost review
    # immediately.
    
    # Script improvement:
    # TODO:
    # Since these should be coming in as Polylines, might try adding them to separate feature
    # classes and seeing if they spatially select one another with a small search distance.
    #
    # Then, could also maybe group them into sets so that if the way that I have them
    # ordered causes there to be an incremented unique number where there shouldn't be
    # i.e. a gap between features 1 and 2, but features 1 and 3 are connected and so
    # are 3 and 2, and 2 and 4, but not 5 or with any of them, then there should be
    # 3 groups, with the group that contains the lowest number having the lowest
    # unique id and the group that contains the next lowest number having the
    # next lowest id, etc.
    #
    # Also, this really really needs to be multithreaded and ran on a machine
    # with a lot of cores. Expected duration is currently on the order of
    # 35 hours.
    # Or, make other optimizations, since you already have the features in a list
    # in a dict with their Label as the key.
    # Could get rid of the expensive SQL selection/cursor.
    
    return testResult

def addDistanceAndSort(inputList, geometryColumnLocation):
    ## Calculate a point which is further south and west than any of the other points.
    ## Calculate the distance from each feature to this point. Store the distance in each feature.
    ## Then, sort based on the distance, in ascending order.
    ## Finally, return the list.
    minXCoord = 100000000
    minYCoord = 100000000
    
    for inputFeatureItem in inputList:
        inputFeatureGeom = inputFeatureItem[geometryColumnLocation]
        inputFeatureCentroid = inputFeatureGeom.centroid
        inputFeatureCentroidX = inputFeatureCentroid.X
        inputFeatureCentroidY = inputFeatureCentroid.Y
        ##print inputFeatureGeom
        ##print("X Coord: " + str(inputFeatureGeom.centroid.X) + "  \tY Coord: " + str(inputFeatureGeom.centroid.Y))
        if minXCoord > inputFeatureCentroidX:
            minXCoord = inputFeatureCentroidX
        else:
            pass
        if minYCoord > inputFeatureCentroidY:
            minYCoord = inputFeatureCentroidY
        else:
            pass
    
    ##print("Minimum X Coord = " + str(minXCoord) + "  \tMinimum Y Coord = " + str(minYCoord))
    distStartPointX = minXCoord - 9000
    distStartPointY = minYCoord - 9000
    ##print("distStartPoint X Coord = " + str(distStartPointX) + "  \tdistStartPoint Y Coord = " + str(distStartPointY))
    featureDistance = ((minYCoord - distStartPointY)**2 +  (minXCoord - distStartPointX)**2)
    ##print("Distance from minimum X Coord + minimum Y Coord to the distStartPoint = " + str(math.sqrt(featureDistance)))
    ##print("Unsqrt'd Distance from minimum X Coord + minimum Y Coord to the distStartPoint = " + str(featureDistance))
    ## Get the minimum x and minimum y based on the centroid values for each feature.
    
    for inputFeatureItem in inputList:
        inputFeatureGeom = inputFeatureItem[geometryColumnLocation]
        inputFeatureCentroid = inputFeatureGeom.centroid
        inputFeatureCentroidX = inputFeatureCentroid.X
        inputFeatureCentroidY = inputFeatureCentroid.Y
        
        inputFeatureSortDist = ((inputFeatureCentroidX - distStartPointY)**2 +  (inputFeatureCentroidY - distStartPointX)**2)
        inputFeatureItem.append(inputFeatureSortDist)
    
    sortedLineList = sorted(inputList, key=itemgetter(-1))
    
    for sortedLineItem in sortedLineList:
        print(str(sortedLineItem[-1]))
    
    del inputList
    
    return sortedLineList


def testPolylineStartEndPointsMatchFunction(spatialReferenceToUse):
    testLineList = list()
    print('Trying testLine1')
    testLine1 = Polyline(arcpyArray([Point(10000.38476,22347.18506),Point(235021.997,14251.778)]), spatialReferenceToUse)
    testLineList.append(testLine1)
    
    print('Trying testLine2')
    testLine2 = Polyline(arcpyArray([Point(235021.997,14251.778),Point(779221.8686,925361.04623)]), spatialReferenceToUse)
    testLineList.append(testLine2)
    
    print('Trying testLine3')
    testLine3 = Polyline(arcpyArray([Point(227386.14822, 816234.4438),Point(226001.4771,22347.18506)]), spatialReferenceToUse)
    testLineList.append(testLine3)
    
    print('Trying testLine4')
    testLine4 = Polyline(arcpyArray([Point(18245.9122,44579.8436),Point(10000.38476,22347.18506)]), spatialReferenceToUse)
    testLineList.append(testLine4)
    
    print('Trying testLine5')
    testLine5 = Polyline(arcpyArray([Point(18245.9122,44579.8436),Point(226001.4771,22347.18506)]), spatialReferenceToUse)
    testLineList.append(testLine5)
    
    print('Trying testLine6')
    testLine6 = Polyline(arcpyArray([Point(847224.7665, 241233.9876),Point(779221.8686,925361.04623)]), spatialReferenceToUse)
    testLineList.append(testLine6)
    
    mockXYTolerance = 0.00328083333333
    
    for x1 in xrange(len(testLineList)):
        currentTestLineP1 = testLineList[x1]
        for y1 in xrange(x1 + 1, len(testLineList)):
            currentTestLineP2 = testLineList[y1]
            print("Testing: " + str(x1) + " and " + str(y1) + ".")
            print(polylineStartEndPointsMatch(currentTestLineP1, currentTestLineP2, mockXYTolerance))
    
if __name__ == "__main__":
    print(currentXYTolerance)
    #testPolylineStartEndPointsMatchFunction(currentSR)
    localRouteNumbering()


else:
    pass