#!/usr/bin/env python
# -*- coding:utf-8 -*-
# datareviewerchecks_rbjxmlcreation.py
# Created 2016-01-10, by dirktall04
# Updated 2017-01-10, by dirktall04
# Last Updated 2017-02-03, by dirktall04

# Updates the xml paths in the
# data reviewer batch job to match
# the information given in the config
# file for those feature classes.

# Instead of using xml, try making small changes with just changing the text.
# It may be the 4 dash GUID-looking keys that are causing a problem. If that
# is the case, then this is probably not going to be possible to automate unless
# or until Esri releases tools for that purpose.

# Use ElementTree since it's a builtin.
import xml.etree.ElementTree as EleTree

from datareviewerchecks_config import (reviewerBatchJobTemplate, reviewerBatchJob as reviewerBatchJobOutput,
    workspaceToReview, outputRoutes as checkRoutes, dissolvedCalibrationPoints as checkPointsPath,
    gdbBaseName)

from pathFunctions import (returnGDBOrSDEPath,
    returnFeatureClass, returnGDBOrSDEName)
    
#---Testing---#
#---Testing---#
rbjDiffTextLocation1 = reviewerBatchJobOutput[:-4] + '_DiffText.txt'
testingRbjFile = r'C:\GIS\Geodatabases\KHUB\SourceChecks_09C_Prime.rbj'
rbjDiffTextLocation2 = testingRbjFile[:-4] + '_DiffText.txt'
#---Testing---#
#---Testing---#

RoutesMatch = r'RoutesTemplateForReplacement'
RoutesUpdate = returnFeatureClass(checkRoutes)
#RoutesUpdate = r'RoutesTemplateForReplacement'
CalPtsMatch = r'CalPtsTemplateForReplacement'
CalPtsUpdate = returnFeatureClass(checkPointsPath)
#CalPtsUpdate = r'CalPtsTemplateForReplacement'
GeodatabaseMatch = r'GeodatabaseTemplateForReplacement'
GeodatabaseUpdate = workspaceToReview
BatchJobNameTagMatch = r'BatchJobName'
BatchJobNameTextUpdate = reviewerBatchJobOutput
BrowseNameTagMatch = r'BrowseName'
BrowseNameTextUpdate = gdbBaseName

def main():
    
    #---Testing---#
    #---Testing---#
    baseTree2 = EleTree.parse(testingRbjFile)
    xmlRoot2 = baseTree2.getroot()
    #---Testing---#
    #---Testing---#
    
    print("Creating a reviewer batch job from the template: " + str(reviewerBatchJobTemplate) + ".")
    baseTree = EleTree.parse(reviewerBatchJobTemplate)
    xmlRoot = baseTree.getroot()

    UpdatesIter = xmlRoot.iter()

    for UpdatesItem in UpdatesIter:
        if UpdatesItem.text is not None:
            if str(UpdatesItem.text).find(RoutesMatch) > -1:
                #print UpdatesItem.text
                newUpdatesItemText = UpdatesItem.text
                UpdatesItem.text = str.replace(newUpdatesItemText, RoutesMatch, RoutesUpdate)
            else:
                pass
            if str(UpdatesItem.text).find(CalPtsMatch) > -1:
                #print UpdatesItem.text
                newUpdatesItemText = UpdatesItem.text
                UpdatesItem.text = str.replace(newUpdatesItemText, CalPtsMatch, CalPtsUpdate)
            else:
                pass
            if str(UpdatesItem.text).find(GeodatabaseMatch) > -1:
                #print UpdatesItem.text
                newUpdatesItemText = UpdatesItem.text
                UpdatesItem.text = str.replace(newUpdatesItemText, GeodatabaseMatch, GeodatabaseUpdate)
        else:
            pass
        if UpdatesItem.tag is not None:
            if str(UpdatesItem.tag).find(BatchJobNameTagMatch) > -1:
                    #print UpdatesItem.text
                    # No replace necessary, just make the new text what you want it to be.
                    newUpdatesItemText = str(reviewerBatchJobOutput)
                    UpdatesItem.text = newUpdatesItemText
            else:
                pass
            if str(UpdatesItem.tag).find(BrowseNameTagMatch) > -1:
                    #print UpdatesItem.text
                    # No replace necessary, just make the new text what you want it to be.
                    newUpdatesItemText = str(BrowseNameTextUpdate)
                    UpdatesItem.text = newUpdatesItemText
            else:
                pass
        else:
            pass
    
    print("Exporting the reviewer batch job as: " + str(reviewerBatchJobOutput) + ".")
    try:
        baseTree.write(reviewerBatchJobOutput)
        print("Export complete.")
    except:
        print("An error occurred during the export.")
    
    # Uses the base location.
    OutputIter1 = xmlRoot.iter()
    with open(rbjDiffTextLocation1, 'w') as fHandle:
        fHandle.write('\n' + 'OutputIter lines for: ' + rbjDiffTextLocation1 + "'s .rbj." + '\n')
        for OutputItem1 in OutputIter1:
            print OutputItem1.tag, OutputItem1.attrib, OutputItem1.text
            fHandle.write(str(OutputItem1.tag) + ' ' + str(OutputItem1.attrib) + ' ' + str(OutputItem1.text) + '\n')
    
    OutputIter2 = xmlRoot2.iter()
    with open(rbjDiffTextLocation2, 'w') as fHandle:
        fHandle.write('\n' + 'OutputIter lines for: ' + rbjDiffTextLocation2 + "'s .rbj." + '\n')
        for OutputItem2 in OutputIter2:
            print OutputItem2.tag, OutputItem2.attrib, OutputItem2.text
            fHandle.write(str(OutputItem2.tag) + ' ' + str(OutputItem2.attrib) + ' ' + str(OutputItem2.text) + '\n')
    
    print("Printed output files for checking at: " + str(rbjDiffTextLocation1))
    print("and at: " + str(rbjDiffTextLocation2) + ".")
    
if __name__ == "__main__":
    main()
else:
    pass