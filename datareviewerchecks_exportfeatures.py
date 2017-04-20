#!/usr/bin/env python
# -*- coding:utf-8 -*-
#datareviewerchecks_exportfeatures.py
# Created 2016-12-22
# Last Updated 2017-01-30
# by dirktall04

# Use the OBJECTID field from the reviewer table
# to select by ObjectId  in the source feature
# class. Group the output by the Check Title field.

# Get a list of the unique types of Check Titles

# Then, condense the list by removing the spaces
# and dashes.

# Next, create feature classes (based on the Source
# type) with the names of those checks, and transfer
# the matching ObjectIDs into those feature classes.

# Table to read is REVTABLEMAIN in the Reviewer_Sessions GDB
# The "RecordID" for this table is actually its OID.
# The "ObjectID" field for this table is the ObjectID for the
# originating feature class.

# "ORIGINTABLE" is the name of the table that the feature
# comes from.

# "CHECKTITLE" is the name of what the output should be called
# though it needs to be modified a bit, to remove spaces and
# dashes (if any exist).

# Need to create a list of the unique checktitles.

# Then, for each checktitle, get the origintable that it
# applies to, and get a list of the objectIds in that
# table that it applies to. -- Possibility for one
# checktitle to have more than one origintable, so guard
# against that -- even though it probably doesn't occur
# in this dataset.

# Need to create lists of the ObjectIds for each origintable
# then, create a list of the unique checktitles.

# Start with the base gdb location for the features
# then use concatenation to build the Feature class
# name with the origintable field.

# REVTABLEMAIN is the name of the table that holds the error records
# that are of interest.

import os
import time

from arcpy import (AddField_management, AddJoin_management, CopyFeatures_management,
    CreateFileGDB_management, Delete_management, Exists, env,
    GetCount_management, MakeFeatureLayer_management,
    MakeTableView_management, SelectLayerByAttribute_management,)

from arcpy.da import SearchCursor as daSearchCursor

from pathFunctions import (returnGDBOrSDEName, returnFeatureClass)

from datareviewerchecks_config import (revTable, originTablesGDB, errorFeaturesGDB,
    mainFolder, errorReportCSVName, errorReportCSV, useRAndHCheck,
    nonMonotonicOutputFC, errorReportRowsOrder, nullable)

def formatCheckTitle(nameToBeUnderscorified):
    newName = nameToBeUnderscorified
    newName = str(newName).replace(' ', '')
    newName = str(newName).replace('-', '')
    return newName


class tableAndCheckData:
    def __init__(self, tableName, checkTitle):
        self.tableName = tableName
        self.checkTitle = checkTitle
        self.listOfOIDsToUse = list()


def exportErrorsToFeatureClasses(reviewTable, originGDB, errorOutputGDB, errorOutputGDBFolder):
    # Checking to see if the output already exists.
    # If so, remove it.
    if Exists(errorOutputGDB):
        Delete_management(errorOutputGDB)
    else:
        pass
    
    CreateFileGDB_management(errorOutputGDBFolder, returnGDBOrSDEName(errorOutputGDB))
    
    previousWorkspace = env.workspace
    env.workspace = errorOutputGDB
    
    tableFields = ['ORIGINTABLE', 'CHECKTITLE', 'OBJECTID']
    newCursor = daSearchCursor(reviewTable, tableFields)
    
    revRows = list()
    
    for rowItem in newCursor:
        revRows.append(list(rowItem))
    
    try:
        del newCursor
    except:
        pass
    
    originTableList = list()
    checkTitleList = list()
    
    for revRowItem in revRows:
        originTableList.append(revRowItem[0])
        checkTitleList.append(revRowItem[1])
    
    print ('Creating sets from the originTable and checkTitle lists.')
    originTableSet = set(originTableList)
    checkTitleSet = set(checkTitleList)
    print ('Finished set creation.')
    
    originTableList = list(originTableSet)
    checkTitleList = list(checkTitleSet)
    
    tableAndCheckDataObjects = list()
    csvDictOfErrorFeatures = dict()
    
    for originTableItem in originTableList:
        print('Origin table = ' + originTableItem + '.')
        completeOriginTablePath = os.path.join(originGDB, originTableItem)
        print('The full path to the origin table is ' + str(completeOriginTablePath) + '.')
        tableViewName = "ReviewTable_View_" + str(originTableItem)
        originTableWhereClause = """"ORIGINTABLE" = '""" + str(originTableItem) +  """'"""
        MakeTableView_management(reviewTable, tableViewName, originTableWhereClause)
        
        for checkTitleItem in checkTitleList:
            print('Check title = ' + checkTitleItem + '.')
            selectionWhereClause = """"CHECKTITLE" = '""" + str(checkTitleItem) + """'"""
            SelectLayerByAttribute_management(tableViewName, "NEW_SELECTION", selectionWhereClause)
            countResult = GetCount_management(tableViewName)
            intCount = int(countResult.getOutput(0))
            
            if intCount >= 1:
                tempTableAndCheckData = tableAndCheckData(originTableItem, checkTitleItem)
                tableViewFields = ["RECORDID", "OBJECTID"]
                
                newCursor = daSearchCursor(tableViewName, tableViewFields, selectionWhereClause)
                
                newOIDList = list()
                
                for cursorItem in newCursor:
                    newOIDList.append(cursorItem[1])
                    
                try:
                    del newCursor
                except:
                    pass
                
                tempTableAndCheckData.listOfOIDsToUse = newOIDList
                
                tableAndCheckDataObjects.append(tempTableAndCheckData)
            else:
                print("There were no features selected for the " + tableViewName + " table.")
    
    print("There are " + str(len(tableAndCheckDataObjects)) + " different items in the tableAndCheckDataObjects list.")
    
    for listObject in tableAndCheckDataObjects:
        
        featureLayerForErrorOutput = 'FeatureClassAsFeatureLayer'
        
        if Exists(featureLayerForErrorOutput):
            Delete_management(featureLayerForErrorOutput)
        else:
            pass
        
        fullPathToFeatureClass = os.path.join(originTablesGDB, listObject.tableName)
        
        MakeFeatureLayer_management(fullPathToFeatureClass, featureLayerForErrorOutput)
        
        # build the selection list & select up to but not more than 999 features at at time
        OIDTotalCounter = 0
        errorOutputWhereClause = """ "OBJECTID" IN ("""
        
        for errorOID in listObject.listOfOIDsToUse:
            if OIDTotalCounter <= 998:
                errorOutputWhereClause = errorOutputWhereClause + str(errorOID) + """, """
                OIDTotalCounter += 1
            else:
                # Remove the trailing ", " and add a closing parenthesis.
                errorOutputWhereClause = errorOutputWhereClause[:-2] + """) """ 
                SelectLayerByAttribute_management(featureLayerForErrorOutput, "ADD_TO_SELECTION", errorOutputWhereClause)
                
                OIDTotalCounter = 0
                errorOutputWhereClause = """ "OBJECTID" IN ("""
                errorOutputWhereClause = errorOutputWhereClause + str(errorOID) + """, """
        
        # Remove the trailing ", " and add a closing parenthesis.
        errorOutputWhereClause = errorOutputWhereClause[:-2] + """) """
        SelectLayerByAttribute_management(featureLayerForErrorOutput, "ADD_TO_SELECTION", errorOutputWhereClause)
        
        ##print "Counting..."
        selectedErrorsResult = GetCount_management(featureLayerForErrorOutput)
        selectedErrorsCount = int(selectedErrorsResult.getOutput(0))
        
        # export the selected data with the correct tableName & checkTitle
        outputFeatureClassName = formatCheckTitle(listObject.checkTitle) + "ErrorsFrom_" + listObject.tableName
        fullPathToOutputFeatureClass = os.path.join(errorOutputGDB, outputFeatureClassName)
        
        csvDictOfErrorFeatures[outputFeatureClassName] = str(selectedErrorsCount)
        
        print(str(selectedErrorsCount) + "\t features will be written to \t" + outputFeatureClassName)
        if selectedErrorsCount >= 1:
            CopyFeatures_management(featureLayerForErrorOutput, fullPathToOutputFeatureClass)
            time.sleep(25)
            AddField_management(outputFeatureClassName, "OptionalInfo", "TEXT", "", "", 250, "ReviewingInfo", nullable)
        else:
            pass
    
    # Need to write a short CSV here that tells the number and type of errors.
    print('Writing error information to an error reports file called' + str(errorReportCSVName) + '.')
    
    with open(errorReportCSV, 'w') as fHandle:
        for errorFeature in errorReportRowsOrder:
            if errorFeature in csvDictOfErrorFeatures:
                errorFeatureCount = csvDictOfErrorFeatures[errorFeature]
                fHandle.write(str(errorFeature) + ', ' + str(errorFeatureCount) + '\n')
            else:
                fHandle.write(str(errorFeature) + ', ' + str(0) + '\n')
    
    # Modify this so that it just checks for the existence of the roads
    # and highways check output, rather than relying on the config
    # file for whether or not this should be ran.
    # The config file can tell the full process whether or not
    # to run the R&H check, but the error report should give
    # details on the R&H check whether or not the config file
    # currently states that the R&H check should be ran again
    # were the full process to run.
    
    env.workspace = previousWorkspace
    
    reportExtensionForRAndHCheck(nonMonotonicOutputFC)


def reportExtensionForRAndHCheck(featuresToCheck):
    if Exists(featuresToCheck):
        featuresName = returnFeatureClass(featuresToCheck)
        errorsFromRAndH = 'RAndHErrorsAsFeatureLayer'
        MakeFeatureLayer_management(featuresToCheck, errorsFromRAndH)
        errorsFromRAndHResult = GetCount_management(errorsFromRAndH)
        errorsFromRAndHCount = int(errorsFromRAndHResult.getOutput(0))
        
        print("Roads & Highways Non-Monotonic Check output was found.")
        print("Extending the errors report with information from the Roads & Highways Non-Monotonicity Check.")
        
        with open(errorReportCSV, 'a') as fHandle:
            fHandle.write('\n' + 'Roads & Highways checks follow: ' + '\n')
            fHandle.write(featuresName + ', ' + str(errorsFromRAndHCount) + '\n')
        
        #errorsRHGDB = returnGDBOrSDEName(featuresToCheck)
        #errorsFeatureClass = returnFeatureClass(featuresToCheck)
        #previousWorkspace = env.workspace
        #env.workspace = errorsRHGDB
        
        #time.sleep(25)
        #print("Also adding ReviewUser and ReviewInfo text fields to the")
        #print("Roads & Highways Non-Monotonicity Check error output feature class.")
        #AddField_management(errorsFeatureClass, "OptionalInfo", "TEXT", "", "", 250, "ReviewingInfo", nullable)
        
        #env.workspace = previousWorkspace
        
    else:
        print("No Roads & Highways Non-Monotonic Check output found.")
        print("Will not add additional information to the errors report csv.")


def main():
    print 'Error exports starting...'
    exportErrorsToFeatureClasses(revTable, originTablesGDB, errorFeaturesGDB, mainFolder)
    print 'Error exports complete.'
# To get the multipart point errors, you can join the REVTABLEPOINT.LINKID to the REVTABLEMAIN.RECORDID.
# Need a script that won't mess up when dissolving this for this:
#    SB         NB
#     *         *
#   /| |\       |\
#  / | | \      | \
#  | | | |      | |
#  | | | |      | |
#  | | | |      | |
#  \ | | /      | /
#   \| |/       |/
#     *         *

if __name__ == "__main__":
    main()

else:
    pass