#!/usr/bin/env python
# -*- coding:utf-8 -*-
# datareviewerchecks_runchecks.py
# Created 2016-12-22
# Last Updated 2017-01-30
# by dirktall04

# Modify the data reviewer checks to point to the correct data sources.
# Run the data reviewer checks.

# Third check seems to be the monotonicity check, but
# if we're using the R&H check, we might not need
# to have it enabled most of the time.
# Build a separate reviwer checks batch job that doesn't
# include the data reviewer check for monotonicty
# and then specify in the config file which one is which
# and whether we want to use the data reviewer check
# for a particular run through or not.


from pathFunctions import (returnFeatureClass,
    returnGDBOrSDEName, returnGDBOrSDEPath)

from arcpy import (CheckExtension, CheckInExtension, CheckOutExtension,
    CreateFileGDB_management, CreateReviewerSession_Reviewer,
    Delete_management, EnableDataReviewer_Reviewer, env,
    ExecuteReviewerBatchJob_Reviewer, Exists)

from datareviewerchecks_config import (workspaceToReview,
    reviewerSessionGDBFolder, reviewerSessionGDB,
    reviewerSession, sessionReviewerSession, reviewerBatchJob)


def reviewData():
    try:
        print 'Data Reviewer batch job starting.'
        print 'If one of the feature classes, Routes or CalPts, does not exist in the place that the'
        print 'data reviewer batch job looks for it, then you will get an "Unknown Error".'
        print "This can be remedied by updating the data reviewer batch job's workspace settings."
        # Test the data reviewer part:
        if CheckExtension("datareviewer") == 'Available':
            print("Test complete.")
            CheckOutExtension("datareviewer")

            # Checking to see if the output already exists.
            # If so, remove it so that it can be recreated. -- For the errors, might need a better process, so that
            # it's possible to track where the errors were at the start and how things progressed.
            if Exists(reviewerSessionGDB):
                Delete_management(reviewerSessionGDB)
            else:
                pass

            # Create new geodatabase
            # Replace with returnGDBOrSDEPath(reviewerSessionGDB), returnGDBOrSDEName(reviewerSessionGDB)
            # or similar functions
            CreateFileGDB_management(reviewerSessionGDBFolder, returnGDBOrSDEName(reviewerSessionGDB))

            # Execute EnableDataReviewer
            EnableDataReviewer_Reviewer(reviewerSessionGDB, "#", "#", "DEFAULTS")

            # Create a new Reviewer session
            CreateReviewerSession_Reviewer(reviewerSessionGDB, reviewerSession, "#")

            # execute the batch job
            batchJobResult = ExecuteReviewerBatchJob_Reviewer(reviewerSessionGDB, sessionReviewerSession, reviewerBatchJob, workspaceToReview)

            print "Data Reviewer batch job complete."

            # get the output table view from the result object
            outputTable = batchJobResult.getOutput(0)

            print "The output table is called " + str(outputTable.name) + "." # prints REVBATCHRUNTABLE

            CheckInExtension("datareviewer")
        
        else:
            print("The 'datareviewer' extension is not available. Skipping checks.")


    except Exception as Exception1:
        # If an error occurred, print line number and error message
        import traceback, sys
        tb = sys.exc_info()[2]
        print "Line %i" % tb.tb_lineno
        print Exception1.message
        try:
            del Exception1
        except:
            pass        
    finally:
        CheckInExtension("datareviewer")


def main():    
    reviewData()


if __name__ == "__main__":
    main()

else:
    pass