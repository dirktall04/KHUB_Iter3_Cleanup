#!/usr/bin/env python
# datareviewerchecks_multithreadedfeaturesimplification.py
# -*- coding: utf-8 -*-
# Created 2017-01-11, by dirktall04


#-------------------------------------------------------------------------
### IMPORTANT:
### When this script is called, you must call it with
### the exact same capitalization
### that the script is saved with.
### Windows and Python will run it just fine
### without matching capitalization, but the
### multiprocessing module's fork script WILL NOT.
#-------------------------------------------------------------------------

## The purpose of this script is to provide
## flow control and related logic for the
## feature simplification process.

import os
import sys
import shutil
import time

import arcpy
import arcpy.da as da
from arcpy import (Append_management, CreateFeatureclass_management,
    CreateFileGDB_management, CopyFeatures_management,
    Delete_management, env, Exists, GetCount_management,
    GetMessages, MakeFeatureLayer_management,
    Result, SelectLayerByAttribute_management,
    SimplifyLine_cartography)

import multiprocessing as mp
from multiprocessing import Process, Manager

import datetime

from pathFunctions import returnFeatureClass, returnGDBOrSDEPath

from datareviewerchecks_config import (featureSimplificationInput,
    featureSimplificationOutput,
    mainFolder, maxFeatures, mirrorBaseName, 
    simplifyAlgorithm, simplifyDistance)

simplifyInputName = 'simplificationInput'
simplifyOutputName = 'simplificationOutput'
simplifyTempLayer = 'layerForSelection'


def FindDuration(endTime, startTime):
    #Takes two datetime.datetime objects, subtracting the 2nd from the first
    #to find the duration between the two.
    duration = endTime - startTime
    
    dSeconds = int(duration.seconds)
    durationp1 = str(int(dSeconds // 3600)).zfill(2)
    durationp2 = str(int((dSeconds % 3600) // 60)).zfill(2)
    durationp3 = str(int(dSeconds % 60)).zfill(2)
    durationString = durationp1 + ':' +  durationp2 + ':' + durationp3
    
    return durationString


def subProcessFeatureSimplification(processInfoList):
    """ Multiprocessing version of feature simplification. 
        Uses multiple cores to simplify features. Should be
        significantly faster than waiting on one core to do all
        of the processing work on its own. Also, shouldn't run
        into memory limits as easily."""
    
    folderToCreateGDBsIn = processInfoList[0]
    subprocessGDB = processInfoList[1]
    simplificationRoutine = processInfoList[2]
    simplificationDistance = processInfoList[3]
    simplificationInput = os.path.join(subprocessGDB, simplifyInputName)
    simplificationOutput = os.path.join(subprocessGDB, simplifyOutputName)
    
    ### Improvement: All of the print statements in this need to be
    ### messages passed to the main function so that there are
    ### not situations where more than one subfunction is attempting
    ### to write to the terminal window at once.
    
    try:
        SimplifyLine_cartography(simplificationInput, simplificationOutput,
        simplificationRoutine, simplificationDistance, "RESOLVE_ERRORS",
        "KEEP_COLLAPSED_POINTS", "CHECK")
        
        
    except Exception as Exception1:
        # If an error occurred, print line number and error message
        tb = sys.exc_info()[2]
        print "Line %i" % tb.tb_lineno
        print Exception1.message
        print "An error occurred." # Need to get the error from the arcpy object or result to figure out what's going on.
        print arcpy.GetMessages()
    
    


def mainProcessFeatureSimplification(inputFeatures, maxCount, outputFeatures):

    # Split the input features into intermediary features:
    # Add each intermediary feature class to a list and
    # pass one feature class of the intermediary features
    # to each subprocess.
    
    # When all of the subprocesses complete, use the
    # list of the intermediary feature classes to append
    # the data into the output features.
    
    countResult = GetCount_management(inputFeatures)
    intCount = int(countResult.getOutput(0))
    # debug print
    print("Counted " + str(intCount) + " features in the " + inputFeatures + " feature class.")
    
    if maxCount > 25000:
        pass
    else:
        maxCount = 25000
    
    neededMirrors = intCount / maxCount + 1
    
    # debug print
    print("Will create " + str(neededMirrors) + " reflection gdbs.")
    
    infoForSubprocess = list()
    gdbToCreateList = list()
    
    for countItem in xrange(0, neededMirrors):
        gdbMirrorName = mirrorBaseName + '_' + '0' + str(countItem) + '.gdb'
        gdbMirrorFullPath = os.path.join(mainFolder, gdbMirrorName)
        gdbToCreateList.append(gdbMirrorFullPath)
        try:
            if Exists(gdbMirrorFullPath):
                try:
                    Delete_management(gdbMirrorFullPath)
                except:
                    pass
            else:
                pass
        except:
            pass
        
        CreateFileGDB_management(mainFolder, gdbMirrorName)
        
        # do a selection on the input features here
        # then copyfeatures to get the selected features
        # output to the target gdb.
        
        if Exists(simplifyTempLayer):
            try:
                Delete_management(simplifyTempLayer)
            except:
                pass
        else:
            pass
        
        MakeFeatureLayer_management(inputFeatures, simplifyTempLayer)
        
        currentSelectMin = int(countItem * maxCount) 
        currentSelectMax = int((countItem + 1) * maxCount)
        
        dynSelectClause = """"OBJECTID" >= """ + str(currentSelectMin) + """ AND "OBJECTID" < """ + str(currentSelectMax) + """"""
        
        SelectLayerByAttribute_management(simplifyTempLayer, "NEW_SELECTION", dynSelectClause)
        
        selectedSimplifyFeatures = os.path.join(gdbMirrorFullPath, simplifyInputName)
        
        CopyFeatures_management(simplifyTempLayer, selectedSimplifyFeatures)
        
        subprocessInfoItem = [mainFolder, gdbMirrorFullPath, simplifyAlgorithm, simplifyDistance]
        
        infoForSubprocess.append(subprocessInfoItem)
    
    # Predivide the list of data driven pages that each process needs to run
    # and pass it as a list of exportItems.
    
    coreCount = mp.cpu_count()
    
    # To support running this on the slow AR60, reduce the coreCount used to try to keep
    # this script from crashing there.
    if coreCount >= 3:
        coreCount = coreCount - 2
    else:
        coreCount = 1
    
    print("Starting a multi-threaded job which will use (up to) " + str(coreCount) + " cores at once.")
    
    workPool = mp.Pool(processes=coreCount)
    # Note: This is a different usage of the word map than the one generally used in GIS.
    workPool.map(subProcessFeatureSimplification, infoForSubprocess)
    print("Multi-threaded job's done!")
    
    print("Waiting a few moments before closing down the worker processes...")
    time.sleep(20)
    workPool.close()
    time.sleep(20)
    workPool.join()
    
    print("Worker processes closed.")
    
    # Delete the output target prior to recreating it and appending data into it.
    if Exists(outputFeatures):
        try:
            Delete_management(outputFeatures)
        except:
            pass
    else:
        pass
    
    # Need the gdb and fc name here from outputFeatures.
    outGDB = returnGDBOrSDEPath(outputFeatures)
    outFCName = returnFeatureClass(outputFeatures)
    
    # Use the inputFeatures as a template.
    CreateFeatureclass_management(outGDB, outFCName, "", inputFeatures)
    
    appendOutputFCList = list()
    
    for gdbToCreate in gdbToCreateList:
        appendOutputFC = os.path.join(gdbToCreate, 'simplificationOutput')
        appendOutputFCList.append(appendOutputFC)
    
    # Do appends here, then sleep again for a bit.
    # Shouldn't need a field mapping since they should all be the same.
    Append_management(appendOutputFCList, outputFeatures, "NO_TEST")
    
    print "Waiting a few moments to be sure that all of the locks have been removed prior to deleting the reflection gdbs..."
    time.sleep(20)
    
    # Then remove the mirror gdbs.
    for gdbToCreate in gdbToCreateList:
        try:
            if Exists(gdbToCreate):
                try:
                    Delete_management(gdbToCreate)
                except:
                    pass
            else:
                pass
        except:
            pass


def main():
    startingTime = datetime.datetime.now()
    print "Feature simplification starting time: " + str(startingTime)
    
    mainProcessFeatureSimplification(featureSimplificationInput, maxFeatures, featureSimplificationOutput)
    
    endingTime = datetime.datetime.now()
    scriptDuration = FindDuration(endingTime, startingTime)
    
    print "For the main thread of feature simplification..."
    print "Feature simplification ending time: " + str(endingTime)
    print "Feature simplification elapsed time: " + scriptDuration


if __name__ == "__main__":
    main()
    
else:
    pass