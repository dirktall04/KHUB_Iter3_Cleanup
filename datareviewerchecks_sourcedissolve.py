#!/usr/bin/env python
# -*- coding:utf-8 -*-
# datareviewerchecks_sourcedissolve.py
# Created 2017-02-08, by dirktall04, with contributions from KyleG

#From Kyle:
'''I think these dissolve settings worked to resolve all the overlapping line segment issues, outputting a single line from the Conflation r6 geodatabase.  I think it would be even cleaner if I flip the segments before running this dissolve, and then don’t include the flip flag in the dissolve.  From this, along with some of the other processes we’ve been working on (I possibly need to incorporate the segment calibration… or possibly that is unnecessary with this, or possibly that process will be different with this), I think we can build routes a little cleaner.  

I just ran this on a layer with LRS_ROUTE_PREFIX in ('I', 'U', 'K')

arcpy.Dissolve_management(in_features="State System", out_feature_class="C:/temp/dissolces.gdb/DissolveSHSTest3_split_nonmulti", dissolve_field="STATE_FLIP_FLAG;KDOT_DIRECTION_CALC;KDOT_LRS_KEY;LRS_COUNTY_PRE;LRS_ROUTE_PREFIX;LRS_ROUTE_SUFFIX;LRS_UNIQUE_IDENT", statistics_fields="BEG_NODE MIN;BEG_NODE MAX;END_NODE MAX;END_NODE MIN;COUNTY_BEGIN_MP MIN;COUNTY_END_MP MAX", multi_part="SINGLE_PART", unsplit_lines="DISSOLVE_LINES")
'''

from arcpy import (CopyFeatures_management, Dissolve_management, env,
    GetCount_management,
    MakeFeatureLayer_management, SelectLayerByAttribute_management)

from datareviewerchecks_config import (gdbForSourceCreation, routesSourceCenterlines,
    routesSourceDissolveOutput, routesSourcePreDissolveOutput)

env.workspace = gdbForSourceCreation
env.overwriteOutput = True

def main():
    print("Starting to dissolve the routes source.")
    stateSystemSelectedFeatures = 'StateSystem_Features'
    selectQuery1 = '''LRS_ROUTE_PREFIX in ('I', 'U', 'K')'''
    MakeFeatureLayer_management (routesSourceCenterlines, stateSystemSelectedFeatures, selectQuery1)
    CopyFeatures_management(stateSystemSelectedFeatures, routesSourcePreDissolveOutput)
    
    #GetCount on the features in the layer here.
    countResult = GetCount_management(stateSystemSelectedFeatures)
    intCount = int(countResult.getOutput(0))
    print('Found ' + str(intCount) + ' state system features to be dissolved.')
    
    # Removed STATE_FLIP_FLAG because we've already flipped the data prior to this process.
    dissolveFields = "KDOT_DIRECTION_CALC;KDOT_LRS_KEY;LRS_COUNTY_PRE;LRS_ROUTE_PREFIX;LRS_ROUTE_SUFFIX;LRS_UNIQUE_IDENT"
    statisticsFields = "BEG_NODE MIN;BEG_NODE MAX;END_NODE MAX;END_NODE MIN;COUNTY_BEGIN_MP MIN;COUNTY_END_MP MAX"
    multipart = "SINGLE_PART"
    unsplitLines = "DISSOLVE_LINES"
    ## Use a selection for the state system so that it will work the first time.
    ## Then, later expand the selection and the amount of routes that are attempted for
    ## the dissolve.
    Dissolve_management(stateSystemSelectedFeatures, routesSourceDissolveOutput, dissolveFields, statisticsFields, multipart, unsplitLines)
    print("Completed dissolving the routes source.")

if __name__ == "__main__":
    main()
else:
    pass