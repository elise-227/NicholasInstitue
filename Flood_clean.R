
## install and load packages
require(nhdplusTools)
require(sf)
require(mapview)
require(tidyverse)
require(dplyr)
require(ggplot2)
mapviewOptions(fgb = FALSE)

#read in catchment data for AOI from GIS analysis
catchwdata <- read_sf("./huc_2019_gis/fra_wet_percatch_byNCHUC.shp")

#clean data from gis
catchwdata <- catchwdata %>% 
  mutate(clean_wet = ifelse(WetA > Shape_Area, Shape_Area, WetA)) %>%
  mutate(clean_fra = ifelse(FRA > Shape_Area, Shape_Area, FRA))

#get list of feature ids to filter flowline data with
featureids <- catchwdata$featurd

#filter flowline data from previous script (not recommended to save and reload)
#if reloading need to do read_sf() of shapefile first
flowdata <- filter(final_flow, comid %in% featureids)

#Subset data into usable parts
#get comids
comids <- flowdata$comid
#and not spatial data frame for catchment data
catch <- data.frame(catchwdata)

#to check if outputs working
for (x in comids) {
  result <- get_DD(flowdata, comid = x , distance = 4)
  print(result)
}

#run code below for results for each catchment

df <- data.frame(matrix(ncol = 2, nrow = length(comids)))
colnames(df) <- c('comid', 'FRA_tot')
df[,1] <- comids
for (x in comids) {
  result <- get_DD(flowdata, comid = x , distance = 4)
  df2 <- data.frame(matrix(ncol = 2, nrow = length(result)))
  colnames(df2) <- c('comid', 'FRA')
  df2[,1] <- result
  area <- for (y in result) {
    catch_fra <- as.numeric(catch %>%
                               filter(featurd == y) %>%
                               select(clean_fra))
    df2[df2$comid == y,2] <- catch_fra
  }
  tot <- sum(df2$FRA)
  print(tot)
  df[df$comid == x,2] <- tot
}

#save results from dataframe
write.csv(df, "fra_downstream_hucs_2019.csv", row.names = FALSE)

#reload or work from dataframe output
data_2019 <- read.csv("fra_downstream_hucs_2019.csv")

#attach results to original catchment spatial data frame
all_2019 <- left_join(catchwdata, data_2019, by = c("featurd" = "comid"))

#calculate percent wetlands for each catchment
all_2019 <- all_2019 %>%
  mutate(wet_per = ((clean_wet)/Shape_Area)*100)

#save final spatial data set 
st_write(all_2019, "final_2019_flood_hucs.shp", driver = "ESRI Shapefile")

#summary statistics
summary(all_2019$wet_per)




comids
   
22130729        

get_DD(flowdata, comid = "22130729" , distance = 4)

