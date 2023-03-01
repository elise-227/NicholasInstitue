##Script to run supply-only water purification analysis
##To run this script, you must have an NLCD for each year of your analysis named "NLCD_[year]" stored in a geodatabase

# Import modules, reset environments
import arcpy
arcpy.CheckOutExtension("spatial")
arcpy.ResetEnvironments()

from tkinter import filedialog

# Select gepdatabase where input NLCD dataset is stored
inputFolder = filedialog.askdirectory(initialdir="/", title='Please select the geodatabase where the NLCD is stored.')

arcpy.env.mask = inputFolder + "/studystates30m_census.tif"

# Set years of analysis
years = input("Enter years of analysis separated by spaces:")
years_list = years.split()

#Set output folder (where results will be stored)
outputFolder = filedialog.askdirectory(initialdir="/", title='Please select the directory where output files should be saved.')

#Set output folder as working directory
arcpy.env.workspace = outputFolder

#Loop rest of processing through each year of analysis
for year in years_list:
    # Set input datasets
    if arcpy.Exists(inputFolder + "/NLCD_" + year + ".tif"):
        NLCD = inputFolder + "/NLCD_" + year + ".tif"
    else:
        raise Exception('NLCD dataset does not exist.')
    output = "Buffer_"+year+".tif"    #set output using year variable
    remap = arcpy.sa.RemapValue([[41, 1], [42, 1], [43, 1], [71, 1], [90, 1], [95, 1]])  #remap by value to ID NPS classes
    Reclass = arcpy.sa.Reclassify(NLCD, "Value", remap, "NODATA")   #Reclassify using remap table; values not in table reclassed as NoData
    Reclass.save(output)    #save output


#Check in spatial analyst extension
arcpy.CheckInExtension("spatial")

                                