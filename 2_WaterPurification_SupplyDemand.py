##Script to run supply-demand water purification analysis
##To run this script, you must have an NLCD for each year of your analysis named "NLCD_[year]" and a flow direction raster with streams set to null stored in a geodatabase
##You must run script 1_WaterPurification_SupplyOnly.py before running this script

# Import modules, reset environments
import arcpy
arcpy.CheckOutExtension("spatial")
arcpy.ResetEnvironments()

from tkinter import filedialog

# Select geodatabase where input NLCD dataset is stored
inputFolder = filedialog.askdirectory(initialdir="/", title='Please select the geodatabase where the NLCD is stored.')

#Get states dataset
#If study area different input study area here
states = inputFolder+"/studystates30m_census.tif"

arcpy.env.mask = states

# Set years of analysis
years = input("Enter years of analysis separated by spaces:")
years_list = years.split()

#Set output folder (where results will be stored)
outputFolder = filedialog.askdirectory(initialdir="/", title='Please select the directory where output files should be saved. This must be the same output directory used for script 1')

#Set intermediates folder (where intermediate datasets will be stored) and set it as working directory
intFolder = filedialog.askdirectory(initialdir="/", title='Please select the directory where intermediate files should be stored.')
arcpy.env.workspace = intFolder

#Locate flow direction raster with streams set to null
if arcpy.Exists(inputFolder+"/FlowDir_NullStrm_census.tif"):
    FlowDir = inputFolder+"/FlowDir_NullStrm_census.tif"
    FlowDirsize = arcpy.GetRasterProperties_management(FlowDir, "CELLSIZEX")
else:
    raise Exception('Flow direction raster does not exist.')

#Loop rest of processing through each year of analysis
for year in years_list:
    # Set input datasets
    if arcpy.Exists(inputFolder + "/NLCD_" + year + ".tif"):
        NLCD = inputFolder + "/NLCD_" + year + ".tif"
    else:
        raise Exception('NLCD dataset does not exist.')

    # Locate supply-only buffer dataset
    if arcpy.Exists(outputFolder+"/Buffer_"+year+".tif"):
        SOBuff = outputFolder+"/Buffer_"+year+".tif"
    else:
        raise Exception('Supply-only buffer dataset does not exist.  Run script 1 to create it.')

    # Identify nonpoint-source pollution sources
    output = "NPS_"+year+".tif"
    remap = arcpy.sa.RemapValue([[21, 1], [22, 1], [23, 1], [24, 1], [82, 1]])  #remap by value to ID NPS classes
    Reclass = arcpy.sa.Reclassify(NLCD, "Value", remap, "NODATA")   #Reclassify using remap table; values not in table reclassed as NoData
    Reclass.save(output)    #save output

    #Resample NPS to match FlowDir raster,
    #use as weight for flow length tool, set 0 to NoData in result
    NPS = "NPS_" + year+".tif"
    NPSsize = arcpy.GetRasterProperties_management(NPS, "CELLSIZEX")
    if NPSsize != FlowDirsize:
          out_coor_sys = arcpy.Describe(FlowDir).spatialReference
          arcpy.env.outputCoordinateSystem = out_coor_sys
          arcpy.env.snapRaster = FlowDir
          NPS = arcpy.Resample_management(NPS, "NPS_"+year+"_rsmp", FlowDirsize, "NEAREST")
    FlowAcc = arcpy.sa.FlowAccumulation(FlowDir, NPS)
    where = """Value = 0"""
    FlowAccFinal = arcpy.sa.SetNull(FlowAcc, FlowAcc, where)
    output = outputFolder + "/NPSFlow_" + year + ".tif"
    FlowAccFinal.save(output)

    # Tabulate Area of PH by landocver type for each state (or study area)
    # if change study area need to update zone data and zone field
    #Flowpath = "NPSFlow_" + year + ".tif"
    #output = "Flowpath" + year + ".dbf"
    #TabArea = arcpy.sa.TabulateArea(in_zone_data=states, zone_field="STATE_NAME", in_class_data=Flowpath,
     #                               class_field="VALUE", out_table=output, processing_cell_size=states, classes_as_rows="CLASSES_AS_FIELDS")

    # Table To Excel
    #Flowpath_A = "Flowpath" + year + ".dbf"
    #output = outputFolder + "/Flowpath_" + year + ".xls"
    #arcpy.conversion.TableToExcel(Input_Table=Flowpath_A, Output_Excel_File=output, Use_field_alias_as_column_header="NAME", Use_domain_and_subtype_description="CODE")

    #Identify buffer areas in the flowpath between NPS and streams
    Flowpath = "NPSFlow_" + year + ".tif"
    Flowpathsize = arcpy.GetRasterProperties_management(Flowpath, "CELLSIZEX")
    Buffersize = arcpy.GetRasterProperties_management(SOBuff, "CELLSIZEX")
    if Buffersize != Flowpathsize:
        out_coor_sys = arcpy.Describe(Flowpath).spatialReference
        arcpy.env.outputCoordinateSystem = out_coor_sys
        arcpy.env.snapRaster = Flowpath
        SOBuff = arcpy.Resample_management(SOBuff, "Buff"+year+"_rsmp", Flowpathsize, "NEAREST")
    SDBuff = arcpy.sa.ExtractByMask(SOBuff, Flowpath)
    output = outputFolder + "/SDBuffer_"+year + ".tif"
    SDBuff.save(output)

    # Combine data set with landcover dataset to get pollinator habitat by landcover type
    Combine = arcpy.sa.Combine(in_rasters=[SDBuff, NLCD])
    output = "SD_byLC" + year + ".tif"
    Combine.save(output)

    # Tabulate Area of PH by landocver type for each state (or study area)
    # if change study area need to update zone data and zone field
    SD_byLC = "SD_byLC" + year + ".tif"
    output = "SDBuff_A" + year + ".dbf"
    TabArea = arcpy.sa.TabulateArea(in_zone_data=states, zone_field="STATE_ABBR", in_class_data=SD_byLC,
                                       class_field="NLCD_"+year, out_table=output,
                                       processing_cell_size=states, classes_as_rows="CLASSES_AS_FIELDS")

    # Table To Excel
    Table_A = "SDBuff_A" + year + ".dbf"
    output = outputFolder + "/SDBuff_" + year + ".xls"
    arcpy.conversion.TableToExcel(Input_Table=Table_A, Output_Excel_File=output,
                                  Use_field_alias_as_column_header="NAME", Use_domain_and_subtype_description="CODE")

#Check in spatial analyst extension
arcpy.CheckInExtension("spatial")
