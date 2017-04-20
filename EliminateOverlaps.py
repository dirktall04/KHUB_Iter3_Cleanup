'''
Created on Feb 7, 2017
This script prepares the conflation data for route creation
conflation road data representing the state highway system is copied toin-memory for fast processing 
field are formatted for route creating based on the LRS flagging for flips and non-primary directions
make all changes in the source conflation data

LRS Keys are structured in the source format and can also be outputted in the destination LRS key format 
The dissolve settings should eliminate overlapping geometries

The results table can be sorted and reviewed to find additional non-primary directions, bad conflation route keys, ghost routes, and other issues

@author: kyleg
'''

if __name__ == '__main__':
    pass

from arcpy import FeatureClassToFeatureClass_conversion,FlipLine_edit,SelectLayerByAttribute_management,CalculateField_management, AddField_management, Dissolve_management

roadcenterlines  ="Database Connections/Conflation2012_ADuser.sde/Conflation.SDE.NG911/Conflation.SDE.RoadCenterlines"
output = r"C:/temp/dissolces.gdb/CountyMakeRoutes2"

def StateHighwaySystemDissolve():
    # Create an in-memory copy of state highay system routes based on LRS Route Prefix
    FeatureClassToFeatureClass_conversion(roadcenterlines, "in_memory", "State_System", "LRS_ROUTE_PREFIX in ('I', 'U', 'K')")
    #about 941 records in Southwest Kansas had reverse mileages and need to be flipped
    #this should be corrected in the final conflation delivery
    #if it is not corrected, these route segments should be explored in more detail

    SelectLayerByAttribute_management("State_System", "NEW_SELECTION", """("COUNTY_BEGIN_MP" > "COUNTY_END_MP" OR "STATE_BEGIN_MP" > "STATE_END_MP") AND "STATE_FLIP_FLAG" IS NULL""")
    CalculateField_management("State_System", "STATE_FLIP_FLAG", """'Y'""", "PYTHON_9.3", "")
    
    SelectLayerByAttribute_management("State_System", "NEW_SELECTION", """"STATE_FLIP_FLAG" = 'Y' """)
    FlipLine_edit("State_System")
    #need to flip mileages where geometry was flipped so add fields
    AddField_management("State_System", "F_CNTY_2", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    AddField_management("State_System", "T_CNTY_2", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    AddField_management("State_System", "F_STAT_2", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    AddField_management("State_System", "T_STAT_2", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        
    #check if there are any state system segments where the to is greater than the from and flag them for review
    AddField_management("State_System", "MileFlipCheck", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
      
    CalculateField_management("State_System", "F_CNTY_2", "!COUNTY_END_MP!", "PYTHON_9.3", "")
    CalculateField_management("State_System", "T_CNTY_2", "!COUNTY_BEGIN_MP!", "PYTHON_9.3", "")
    CalculateField_management("State_System", "F_STAT_2", "!STATE_END_MP!", "PYTHON_9.3", "")
    CalculateField_management("State_System", "T_STAT_2", "!STATE_BEGIN_MP!", "PYTHON_9.3", "")
    
    # Switch selection and calculate mileages

    SelectLayerByAttribute_management(in_layer_or_view="State_System", selection_type="SWITCH_SELECTION", where_clause="")

    CalculateField_management("State_System", "F_CNTY_2", "!COUNTY_BEGIN_MP!", "PYTHON_9.3", "")
    CalculateField_management("State_System", "T_CNTY_2", "!COUNTY_END_MP!", "PYTHON_9.3", "")
    CalculateField_management("State_System", "F_STAT_2", "!STATE_BEGIN_MP!", "PYTHON_9.3", "")
    CalculateField_management("State_System", "T_STAT_2", "!STATE_END_MP!", "PYTHON_9.3", "")
    #KDOT Direction should already be calculated, by running "DualCarriagweayIdentity.py" and updating the KDOT_DIRECTION_CALC to 1 where dual carriagway is found
    #Validation_CheckOverlaps can also help do identify sausage link/parallel geometries that may indicate dual carriagway, but that script does not yet 
    #identify and calculate the KDOT_DIRECTION_CALC flag.  It probably could with more development
    # Select the EB routes and change the LRS_Direction to WB
    
    SelectLayerByAttribute_management("State_System", "NEW_SELECTION", """"KDOT_DIRECTION_CALC" = '1' AND "LRS_DIRECTION" = 'EB'""")
    CalculateField_management("State_System", "LRS_DIRECTION", "'WB'", "PYTHON_9.3", "")
    #Select the SB routes to chante hte LRS direction to SB
    SelectLayerByAttribute_management("State_System", "NEW_SELECTION", """"KDOT_DIRECTION_CALC" = '1' AND "LRS_DIRECTION" = 'NB'""")
    CalculateField_management("State_System", "LRS_DIRECTION", "'SB'", "PYTHON_9.3", "")
    # Clear the selections
    SelectLayerByAttribute_management("State_System", "CLEAR_SELECTION", "")

    #Calculate County LRS Key in CountyKey1 field for State Highway system
    #Need to add CountyKey2 for iteration 2, also go ahead and add new LRS Key format
    CalculateField_management("State_System", "CountyKey1", """[LRS_COUNTY_PRE] + [LRS_ROUTE_PREFIX] + [LRS_ROUTE_NUM] + [LRS_ROUTE_SUFFIX] + [LRS_UNIQUE_IDENT] +"-" + [LRS_DIRECTION]""", "VB")
    CalculateField_management("State_System", "StateKey1", """[LRS_ROUTE_PREFIX] + [LRS_ROUTE_NUM] + [LRS_ROUTE_SUFFIX] + [LRS_UNIQUE_IDENT] +"-" + [LRS_DIRECTION]""", "VB")
    
    #this is the dissolve - the output of this is a feature class which is clean for route creation of the state highway system
    Dissolve_management("State_System", output+"dissolve", "CountyKey1;LRS_COUNTY_PRE;LRS_ROUTE_PREFIX;LRS_ROUTE_NUM;LRS_ROUTE_SUFFIX;LRS_UNIQUE_IDENT;LRS_DIRECTION", "F_CNTY_2 MIN;T_CNTY_2 MAX", "SINGLE_PART", "DISSOLVE_LINES")
    Dissolve_management("State_System", output+"unsplit", "CountyKey1;LRS_COUNTY_PRE;LRS_ROUTE_PREFIX;LRS_ROUTE_NUM;LRS_ROUTE_SUFFIX;LRS_UNIQUE_IDENT;LRS_DIRECTION", "F_CNTY_2 MIN;T_CNTY_2 MAX", "SINGLE_PART", "UNSPLIT_LINES")
    # Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
    # The following inputs are layers or table views: "State_System"
    #review the dissolve output, go back and flag the input data 
    #
    
def main():
    StateHighwaySystemDissolve()
    
main()