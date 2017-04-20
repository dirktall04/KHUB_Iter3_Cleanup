#!/usr/bin/env python
# -*- coding:utf-8 -*-
#duplicate_ramp_check.py
# Created 2016-12-13
# by dirktall04

# The SHARED.INTERCHANGE_RAMPS feature class has 20 more ramps than
# the feature class that I used which was in the outgoing\TSS folder's
# Data_Transmit.gdb.
# Do a quick check to see if any of the ramps are multipart/have
# duplicate LRS_KEY values -- then find out if that's
# supposed to be the case.

from arcpy.da import SearchCursor

print 'Check starting...'

rampFeatures = r'C:\GIS\Geodatabases\KHUB\Data_Mirroring_02_Prime.gdb\Export_Ramps'
rampFields = ['LRS_KEY', 'OBJECTID']

lrsKeyList = list()

newCursor = SearchCursor(rampFeatures, rampFields)

# Read all of the LRS_Keys in a feature class.
for rampItem in newCursor:
    rampLRSKey = str(rampItem[0])
    # If there is a duplicate LRS_Key, complain to the user.
    if rampLRSKey in lrsKeyList:
        print 'The LRS_KEY: ' + rampLRSKey + ' is a duplicate!'
    else:
        pass
    lrsKeyList.append(rampLRSKey)

try:
    del newCursor
except:
    pass

print 'Check completed.'