#!/usr/bin/env python
# -*- coding:utf-8 -*-
#copyMissingDomainsFromGDBtoGDB.py
# Created by dirktall04 on 02/23/2017

import os
from arcpy import (DomainToTable_management, Exists, Delete_management,
    TableToDomain_management)

from arcpy.da import (ListDomains)

sourceGDB = r'Database Connections\Conflation2012_sde.sde'
targetGDB = r'Database Connections\ConflationProd_sde.sde'
##targetGDB = r'C:\GIS\Geodatabases\domainTransferTest.gdb'
tableStorageGDB = r'C:\GIS\Geodatabases\domainTransfer.gdb'

def main():
    sourceGDBDomains = ListDomains(sourceGDB)
    sourceGDBDomainNames = [x.name for x in sourceGDBDomains]
    targetGDBDomains = ListDomains(targetGDB)
    targetGDBDomainNames = [x.name for x in targetGDBDomains]
    missingDomainNames = [x for x in sourceGDBDomainNames if x not in targetGDBDomainNames]
    missingDomainNameAndDescDict = dict()
    
    for sourceDomain in sourceGDBDomains:
        if sourceDomain.name in missingDomainNames:
            missingDomainNameAndDescDict[sourceDomain.name] = sourceDomain.description
        else:
            pass
    
    codeField = 'Code'
    descField = 'Description'
    
    for domainToCopyName in missingDomainNames:
        print("Copying the domain named: " + domainToCopyName + ".")
        domainStorageTable = os.path.join(tableStorageGDB, domainToCopyName)
        #Check if the table already exists in the storageTableLocation, if so
        #then delete it before trying to copy the data out from the source
        #table.
        if Exists(domainStorageTable):
            try:
                Delete_management(domainStorageTable)
            except:
                print("Could not delete the table located at " + domainStorageTable + ".")
        else:
            pass
        
        DomainToTable_management(sourceGDB, domainToCopyName, domainStorageTable, codeField, descField)
        domainDescription = missingDomainNameAndDescDict[domainToCopyName]
        TableToDomain_management(domainStorageTable, codeField, descField, targetGDB, domainToCopyName, domainDescription)

if __name__ == "__main__":
    main()

else:
    pass