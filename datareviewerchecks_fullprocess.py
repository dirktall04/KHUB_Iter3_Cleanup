#!/usr/bin/env python
# -*- coding:utf-8 -*-
# datareviewerchecks_fullprocess.py
# Created 2016-12-30
# Updated 2017-01-027 by dirktall04
# Last Updated 2017-02-06 by dirktall04

# Run ALL the things!
# To change the location of the inputs/outputs
# please visit/modify datareviewerchecks_config.py

# With the KDOTProcess, ramps are not currently showing up in the output.
# Fix next.

import datetime
import time

import datareviewerchecks_config as configsettings
import datareviewerchecks_routessourcecreation as createtheroutessource
import datareviewerchecks_kdotprocessimprovements_iter2 as kdotprocesstocreatetheroutesource
### Can't create from template due to hashed values with unknown algorithm in .rbj files. ###
###import datareviewerchecks_rbjxmlcreation as rbjxmlcreation
# Source dissolve should happen after simplification and flipping, but before ... ghost route detection?
# Means it needs to be inside the kdotprocessimprovements_iter2 script.
###import datareviewerchecks_sourcedissolve as sourcedissolve
import datareviewerchecks_exportfeatures as exportthefeatures
import datareviewerchecks_lrsroutecreation as createtheroutes
import datareviewerchecks_runchecks as runthechecks
import datareviewerchecks_nonmonoroadsandhighways as nonmonorandhcheck
###import datareviewerchecks_grabconflationdata as grabconflationdata

startTime = datetime.datetime.now()

if __name__ == "__main__":
    print('Starting the full process of importing centerlines from ' + str(configsettings.inputCenterlines))
    print('then exporting them as routes to ' + str(configsettings.outputRoutes))
    print('next running the data reviewer checks from ' + str(configsettings.reviewerBatchJob))
    print('and exporting the error features to ' + str(configsettings.errorFeaturesGDB))
    print('at: ' + str(startTime))
    #if configsettings.importNewConflationData == True:
    #    grabconflationdata.main()
    #else:
    #    pass
    if configsettings.routeSourceCreationOption.lower() == 'base':
        print('Creating the routesSource from centerlines & ramps.')
        createtheroutessource.main()
    elif configsettings.routeSourceCreationOption.lower() == 'kdot':
        print("Using KDOT's improvements to create the routesSource from centerlines & ramps.")
        kdotprocesstocreatetheroutesource.main()
    else:
        print("The routeSourceCreationOption is neither 'base' nor 'kdot'. Will not recreate the routeSource.")
        pass
    if configsettings.recreateTheRoutes == True:
        time.sleep(25)
        print('Recreating the LRS Routes from the routesSource.')
        createtheroutes.main()
    else:
        print('Skipping route creation.')
        pass
    if configsettings.runDataReviewerChecks == True:
        ### Can't create .rbj from template due to hashed values with unknown algorithm in .rbj files. ###
        ###rbjxmlcreation.main()
        print('Running the Data reviewer checks. This will take a while.')
        print('Seriously though... check back in an hour or so.')
        runthechecks.main()
    else:
        pass
    if configsettings.useRAndHCheck == True:
        print('Running the Roads and Highways Non-Monotonicity check.')
        nonmonorandhcheck.main()
    else:
        pass
    if configsettings.exportFeatures == True:
        exportthefeatures.main()
    else:
        print("Not exporting the error features because the exportFeatures setting for errors is False.")
    print('Full process completed')
    completeTime = datetime.datetime.now()
    print('at approximately: ' + str(completeTime))
    durationTime = completeTime - startTime
    print('and taking ' + str(durationTime))
    print('The completed GDBs can be found in ' + str(configsettings.mainFolder) + '.')

else:
    pass

#Next steps:
# Include the Ghost Route detection script.
# Exclude the routes which are detected to have Ghost Route status.

#Then, recreate the lrs routes and run all of the checks to see how much error reduction has taken place.