#!/usr/bin/env python
# -*- coding:utf-8 -*-
# r1r5tor6comparison.py
# Created 2017-02-07

#Load the All_Road_Centerlines from R1-R5 and from R6
# and compare their fields to see which ones don't match.

# Then, see which ones are populated in R1-R5 that aren't
# populated in R6, if the fieldnames mostly match.

from arcpy import (Describe, env)

r1Tor5 = r'C:\GIS\Geodatabases\KHUB\Data_Mirroring_09C_Prime_Source.gdb\All_Road_Centerlines'
r6Only = r'C:\GIS\Geodatabases\KHUB\Data_Mirroring_09F_Region6_Source.gdb\All_Road_Centerlines'

r1Tor5Fields = Describe(r1Tor5).fields
r1Tor5FieldNames = [x.name for x in r1Tor5Fields]
r6OnlyFields = Describe(r6Only).fields
r6OnlyFieldNames = [y.name for y in r6OnlyFields]

fieldsInR1ToR5NotInR6 = [z for z in r1Tor5FieldNames if z not in r6OnlyFieldNames]
fieldsInR6NotInR1ToR5 = [vv for vv in r6OnlyFieldNames if vv not in r1Tor5FieldNames]

print("fieldsInR1ToR5NotInR6:")
print(str(fieldsInR1ToR5NotInR6))

print("fieldsInR6NotInR1ToR5:")
print(str(fieldsInR6NotInR1ToR5))