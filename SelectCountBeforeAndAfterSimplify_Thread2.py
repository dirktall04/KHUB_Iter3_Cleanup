#SelectCountBeforeAndAfterSimplify.py
# -*- coding:utf-8 -*-
# By: Dirk Talley
# Created: 2016-11-29

from arcpy import  GetCount_management, MakeFeatureLayer_management, SelectLayerByAttribute_management

from arcpy.da import SearchCursor as daSearchCursor

originalPointsSource = r'C:\GIS\Geodatabases\KHUB\Testing\R6_For_Vertex_Simplification.gdb\RoadCenterlines_Unsimplified_Points'
simplifiedPointsSource = r'C:\GIS\Geodatabases\KHUB\Testing\R6_For_Vertex_Simplification_05Ft.gdb\RoadCenterlines_05Ft_Points'
originalPointsAsLayer = 'OrgPoints'
simplifiedPointsAsLayer = 'SimPoints'

selectionTypeToUse = "NEW_SELECTION"

outputFile = 'stewardPointCountsR6_5FT.txt'

def writeStewardPointCounts():
    MakeFeatureLayer_management(originalPointsSource, originalPointsAsLayer)
    MakeFeatureLayer_management(simplifiedPointsSource, simplifiedPointsAsLayer)
    
    allStewardsDict = dict()
    
    #Programatically grab the stewards instead of manually listing them here
    newCursor = daSearchCursor(originalPointsAsLayer, ["OID@", "STEWARD"])
    
    for cursorItem in newCursor:
        allStewardsDict[cursorItem[1]] = 'True'
    
    if 'newCursor' in locals():
        try:
            del newCursor
        except:
            print("The cursor exists, but it could not be successfully removed.")
    else:
        print("The cursor has already been removed.")
    
    
    try:
        wHandle = open(outputFile,'w')
        columnNames = "StewardID , OriginalCount , SimplifiedCount\n"
        wHandle.write(columnNames)
        
        # For each steward in the list, get a count of all of the original centerline
        # points and the the simplified road centerlines points.
        # Next, write the data out to a text file in comma separated form.
        for stewardItem in allStewardsDict.keys():
            if stewardItem is not None:
                selectionQuery = """ "STEWARD" = '""" + stewardItem + """' """
                SelectLayerByAttribute_management(originalPointsAsLayer, selectionTypeToUse, selectionQuery)
                oCountResult = GetCount_management(originalPointsAsLayer)
                originalCount = int(oCountResult.getOutput(0))
                SelectLayerByAttribute_management(simplifiedPointsAsLayer, selectionTypeToUse, selectionQuery)
                sCountResult = GetCount_management(simplifiedPointsAsLayer)
                simplifiedCount = int(sCountResult.getOutput(0))
                strToWrite = "'" + stewardItem + "'" + ", " + str(originalCount) + ", " + str(simplifiedCount) + "\n"
                print("Writing " + strToWrite + " to the file: " + outputFile + ".")
                wHandle.write(strToWrite)
            else:
                print("The stewardItem is None, so it will be skipped.")
    
    except:
        errorInfo = sys.exc_info()[0]
        errorInfo1 = sys.exc_info()[1]
        print("An error occurred: " + str(errorInfo) + str(errorInfo1))
        try:
            wHandle.close()
        except:
            raise
        try:
            del errorInfo
            del errorInfo1
        except:
            pass

# Then, import the CSV into Excel for further manipulation/sharing.

if __name__ == "__main__":
    writeStewardPointCounts()
else:
    pass