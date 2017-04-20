import os

def returnGDBOrSDEPath(inputPath):
    gdbStrCount = -1
    sdeStrCount = -1
    if inputPath is not None:
        if inputPath != '':
            loweredPath = str(inputPath).lower()
            gdbStrCount = loweredPath.find('.gdb')
            sdeStrCount = loweredPath.find('.sde')
        else:
            return ''
        
        if gdbStrCount != -1:
            return inputPath[:gdbStrCount] + '.gdb'
        else:
            pass
        if sdeStrCount != -1:
            return inputPath[:sdeStrCount] + '.sde'
        else:
            pass
        
    else:
        pass
        
    return ''

def returnFeatureClass(inputPath):
    pathParts = os.path.split(inputPath)
    lastPart = pathParts[-1]
    priorParts = list(pathParts[:-1])
    
    if len(priorParts) > 1:
        strPriorParts = os.path.join(priorParts)
    else:
        strPriorParts = str(priorParts)
    ##priorParts = os.path.join(list(pathParts[:-1]))
    
    if lastPart.find('.shp') != -1:
        return lastPart
    else:
        pass
    
    gdbStrCount = -1
    sdeStrCount = -1
    if lastPart is not None:
        if strPriorParts is not None:
            loweredPath = strPriorParts.lower()
            gdbStrCount = loweredPath.find('.gdb')
            sdeStrCount = loweredPath.find('.sde')
        else:
            return ''
        
        if gdbStrCount != -1:
            return lastPart
        else:
            pass
        if sdeStrCount != -1:
            return lastPart
        else:
            pass
        
    else:
        pass
        
    return ''
    
''' Unused:
def returnGDBOrSDEPath(inputPath):
    gdbStrCount = -1
    sdeStrCount = -1
    if inputPath is not None:
        if inputPath != '':
            loweredPath = str(inputPath).lower()
            gdbStrCount = loweredPath.find('.gdb')
            sdeStrCount = loweredPath.find('.sde')
        else:
            return ''
            
        if gdbStrCount != -1:
            return inputPath[:gdbStrCount] + '.gdb'
        else:
            pass
        if sdeStrCount != -1:
            return inputPath[:sdeStrCount] + '.sde'
        else:
            pass
        
    else:
        return ''
        

def returnPortionOfPath(inputPath, portionToReturn):
    portionToReturn = str(portionToReturn).lower()
    inputPLower = str(inputPath).lower()
    shpString = '.shp'
    gdbString = '.gdb'
    sdeString = '.sde'
    shpResult = inputPLower.find(shpString)
    gdbResult = inputPLower.find(gdbString)
    sdeResult = inputPLower.find(sdeString)'
    
    if shpResult == -1 and gdbResult == -1 and sdeResult == -1:
        print 'inputPath was not a valid gis feature path.'
        return ''
    else:
        pass
    
    if portionToReturn == 'feature_class':
        pass
    elif portionToReturn == 'feature_dataset':
        pass
    elif portionToReturn == 'gdb_path':
        pass
    elif portionToReturn == 'gdb_name':
        pass
    elif portionToReturn == 'gdb_containing_folder':
        pass
    elif portionToReturn == 'sde_path':
        pass
    elif portionToReturn == 'sde_name':
        pass
    elif portionToReturn == 'sde_containing_folder':
        pass
    else:
        print 'portionToReturn parameter did not match a valid case.'
        return ''
    pass
    
    return parsedPathResult
'''

if __name__ == "__main__":
    print returnGDBOrSDEPath(r'C:\test.gdb')
    print returnGDBOrSDEPath(r'C:\sdeTest.sde')
    print returnGDBOrSDEPath('C:\\user\\other\\arcgdb.gdb')
    print returnGDBOrSDEPath('C:\\user\\other\\arcsde.sde')
    print returnGDBOrSDEPath(r'C:\this\is\a\shapefile.shp')

    print returnFeatureClass(r'C:\test.gdb\testFeature')
    print returnFeatureClass(r'C:\sdeTest.sde\sdeRoads')
    print returnFeatureClass('C:\\user\\other\\arcgdb.gdb\\arcFeature')
    print returnFeatureClass('C:\\user\\other\\arcsde.sde\\arcFeature2')
    print returnFeatureClass(r'C:\this\is\a\shapefile.shp')
else:
    pass