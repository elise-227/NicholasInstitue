#Before beginning, NLCD, CDL and Study area rasters should be in one folder in which you want to retrive from
#If doing SE region analysis, use DataPrep_PollinationAnalysis.py to prepare NLCD and CDL data
#Also have a folder for outputs ready

import arcpy
import os

# Check out any necessary licenses.
arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("ImageAnalyst")
arcpy.ResetEnvironments()

from tkinter import filedialog

# Select folder where input datasets (NLCD, CDL, and state rasters) are stored
inputFolder = filedialog.askdirectory(initialdir="/", title='Please select the directory where data is stored.')

#Set input folder as working directory
arcpy.env.workspace = inputFolder

# Set years of analysis
years = input("Enter years of analysis separated by spaces:")
years_list = years.split()

#Get states dataset
#If study area different input study area here
states = inputFolder+"/studystates30m_census.tif"


#Set output folder (where results will be stored)
outputFolder = filedialog.askdirectory(initialdir="/", title='Please select the directory where output files should be saved.')

#Loop rest of processing through each year of analysis
#Make sure file names correct, spelling is important
for year in years_list:
    # Set input datasets
    CDL = inputFolder+"/CDL_" + year + ".tif"
    NLCD = inputFolder+"/NLCD_" + year + ".tif"

# Create geodatabase to store intermediate datasets

    root = os.path.split(outputFolder)[0]
    if arcpy.Exists(root + "/" + year + "Intermediates.gdb") == False:
        arcpy.CreateFileGDB_management(root, year + "Intermediates.gdb")
    arcpy.env.workspace = root + "/" + year + "Intermediates.gdb"


    #Set agricultural areas in CDL to agriculture class in NLCD (So agriculture class the same across the two datasets)
    output = "NLCD_NEW"
    query = 'Value IN (5, 6, 242, 250, 221, 72, 212, 50, 209, 213, 229, 222, 48, 69, 10, 239, 240, 241, 254, 26, 75, 34, 68, 223, 66, 218, 211, 67, 77, 220, 210)'
    NLCD_reclass = arcpy.sa.Con(CDL, 82, NLCD, query)
    NLCD = NLCD_reclass
    NLCD.save(output)

    # Extract NLCD classes that provide pollinator habitat
    PollHab = arcpy.sa.Con(NLCD, "1", "", "Value IN (41, 42, 43, 52, 71, 90, 95)")
    output = outputFolder+"/TotalPH_"+year + ".tif"
    PollHab.save(output)

# Step 1: Identify pollinator-dependent crops in the study area
    # Reclassify CDL into directly pollinator-dependent crops (=1), all other classes (=NODATA)
    output = "CropReclass"
    remap = arcpy.sa.RemapValue([[0,"NODATA"],[5,1],[6,1],[242,1], [250, 1], [221, 1], [72, 1], [212, 1], [50, 1], [209, 1], [213, 1],
                             [229, 1], [222, 1], [48, 1], [69, 1], [10, 1], [239, 1], [240, 1], [241, 1], [254, 1], [26, 1], [75, 1], [34, 1], [68, 1], [223, 1],
                             [66, 1], [218, 1], [211, 1], [67, 1], [77, 1], [220, 1], [210, 1], [55, 1]])
    Reclass = arcpy.sa.Reclassify(CDL, "Value", remap, "NODATA")
    Reclass.save(output)

    # Region Group reclassified crop layer to identify patches greater than 12 pixels
    RG_output = "RegionGroup"
    RG = arcpy.sa.RegionGroup(Reclass, "EIGHT", "CROSS", "ADD_LINK", "0")
    RG.save(RG_output)
    cutoff = "45"
    Con_output = "CropPatch"
    whereClause = "COUNT >= %s AND VALUE > 0" %cutoff
    CropPatch = arcpy.sa.Con(RG, "1", "", whereClause)
    CropPatch.save(Con_output)

    #Use resulting layer as a mask to extract the reclassified cropland layer (to exclude patches < 10 acres)Extract by Mask
    output = "FinalCrop"
    FinalCrop = arcpy.sa.ExtractByMask(Reclass, CropPatch)
    FinalCrop.save(output)

    # Step 2: Create pollinator range "buffer" around pollinator-dependent crops
    # Create a mask of areas within pollinator distance of pollinator-dependent crops
    output = "EucDist"
    EucDist = arcpy.sa.EucDistance(FinalCrop, 1308, 30)
    EucDist.save(output)

    # Create a mask of areas within pollinator distance of pollinator-dependent crops, excluding the crops themselves
    output = "PollDistMask"
    PollDistMask = arcpy.sa.Con(EucDist, "1", "", "Value > 0")
    PollDistMask.save(output)

    # Extract potential pollinator habitat that is within pollinator distance of PDCs
    arcpy.env.snapRaster = PollHab
    output = outputFolder+"/PHNearPDC" + year + ".tif"
    PDCPollHab = arcpy.sa.ExtractByMask(PollHab, PollDistMask)
    PDCPollHab.save(output)

    # Combine data set with landcover dataset to get pollinator habitat by landcover type
    CombineDist = arcpy.sa.Combine(in_rasters=[PDCPollHab, NLCD])
    output = "PH2PDC_Lc"
    CombineDist.save(output)

    # Tabulate Area of PH by landocver type for each state (or study area)
    # if change study area need to update zone data and zone field
    output = outputFolder + "/PH_A" + year + ".dbf"
    TabAreaPH = arcpy.sa.TabulateArea(in_zone_data=states, zone_field="STATE_ABBR", in_class_data=CombineDist, class_field="NLCD_NEW", out_table=output, processing_cell_size=states, classes_as_rows="CLASSES_AS_FIELDS")

    # Table To Excel
    output = outputFolder + "/PH_A" + year + ".xls"
    arcpy.conversion.TableToExcel(Input_Table=TabAreaPH, Output_Excel_File=output, Use_field_alias_as_column_header="NAME", Use_domain_and_subtype_description="CODE")

    # Step 3: Create pollinator range "buffer" around pollinator habitat
    # Create a mask of areas within pollinator distance of pollinator habitat
    PH_mask_reclass = arcpy.sa.SetNull(PollHab, PollHab, "Value = 0")
    output = "EucDistPH"
    EucDist2 = arcpy.sa.EucDistance(PH_mask_reclass, 1308, 30)
    EucDist2.save(output)

    # Create a mask of areas within pollinator distance of pollinator-dependent crops, excluding the crops themselves
    output = "PHDistMask"
    PHDistMask = arcpy.sa.Con(EucDist2, "1", "", "Value > 0")
    PHDistMask.save(output)

    # Extract PDCs that are within pollinator distance of pollinator habitat
    arcpy.env.snapRaster = PollHab
    output = outputFolder+"/PDCNearPH"+year + ".tif"
    PDCNearPH = arcpy.sa.ExtractByMask(FinalCrop, PHDistMask)
    PDCNearPH.save(output)

    # Tabulate Area of PDCs within pollinator distance of pollinator habitat by state (or study area)
    # If update study area need to update zone data and zone field
    output = outputFolder + "/PDC_A" + year + ".dbf"
    TabAreaPDC = arcpy.sa.TabulateArea(in_zone_data=states, zone_field="STATE_ABBR", in_class_data=PDCNearPH,
                                      class_field="VALUE", out_table=output,
                                      processing_cell_size=states, classes_as_rows="CLASSES_AS_FIELDS")

    # Table To Excel
    output = outputFolder + "/PDC_A" + year + ".xls"
    arcpy.conversion.TableToExcel(Input_Table=TabAreaPDC, Output_Excel_File= output, Use_field_alias_as_column_header = "NAME", Use_domain_and_subtype_description = "CODE")


