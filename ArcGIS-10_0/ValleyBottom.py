# -*- coding: utf-8 -*-

'''
Created on 21 fev. 2013
Last update on 07 fev. 2014

@author: Clement Roux

@contact: aurelie.antonio@ens-lyon.fr
          CNRS - UMR5600 Environnement Ville Societe
          15 Parvis René Descartes, BP 7000, 69342 Lyon Cedex 07, France
         
@note: For each use of the FluvialCorridor toolbox leading to a publication, report, presentation or any other
       document, please refer the following article :
       Roux, C., Alber, A., Bertrand, M., Vaudor, L., Piegay, H., submitted. "FluvialCorridor": A new ArcGIS 
       package for multiscale riverscape exploration. Geomorphology
       
@summary: Valley bottom is an open-source python and arcPy code.
          This script is used to extract the valley bottom related to a hydrographic network.
          
'''


# Import of required librairies
import arcpy
from arcpy import env
import def__ScratchWPathName as SWPN
import def__SLEM as dS

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

# Inputs
Boolean = arcpy.GetParameterAsText(0)
Network = arcpy.GetParameterAsText(1)
DEM = arcpy.GetParameterAsText(2)
SmoothingNetwork = arcpy.GetParameterAsText(3)
LargeBufferSize = arcpy.GetParameterAsText(4)
SmallBufferSize = arcpy.GetParameterAsText(5)
DisaggregationStep = arcpy.GetParameterAsText(6)
ThresholdMIN = arcpy.GetParameterAsText(7)
ThresholdMAX = arcpy.GetParameterAsText(8)
UncleanedPolygonVB_USER = arcpy.GetParameterAsText(9)
AggregationDist = arcpy.GetParameterAsText(10)
MinimumArea = arcpy.GetParameterAsText(11)
MinimumHoleSize = arcpy.GetParameterAsText(12)
SmoothingVB = arcpy.GetParameterAsText(13)
Output = arcpy.GetParameterAsText(14)
DeleteTF = arcpy.GetParameterAsText(15)

# Dervied variable from inputs
ScratchW = SWPN.ScratchWPathName ()



#===============================================================================
# CODING
#===============================================================================
    ################################
    ### Valley bottom extraction ###
    ################################
    ## The box "Only Execute the CleanStep of the Polygonal Valley Bottom" is not checked

if str(Boolean) == "false" :
    
    # Number of steps
    if str(DeleteTF) == "true" :
        nstep = 18
        if str(SmoothingVB) != "0" :
            nstep += 1
    else :
        nstep = 17
        if str(SmoothingVB) != "0" :
            nstep += 1
    ncurrentstep=1
   
    #/copying the DEM into a usable format
    DEMprop = arcpy.GetRasterProperties_management(DEM, 'VALUETYPE')
    if (DEMprop == 9) :
        ProcessDEM = arcpy.CopyRaster_management(DEM, "%ScratchWorkspace%\\ProcessDEM", "DEFAULTS", "", "", "", "", "32_BIT_UNSIGNED")
    else :
        ProcessDEM = DEM

    #/smoothing of the stream network
    arcpy.AddMessage("Smoothing the Stream Network - Step " + str(ncurrentstep) + "/" + str(nstep))
    SmoothedNetwork = arcpy.SmoothLine_cartography(Network, "%scratchWorkspace%\\SmoothedNetwork", "PAEK", SmoothingNetwork, "FIXED_CLOSED_ENDPOINT", "NO_CHECK")

    #/creation of buffers
    ncurrentstep+=1
    arcpy.AddMessage("Creating Large Buffer - Step " + str(ncurrentstep) + "/" + str(nstep))
    LargeBuffer = arcpy.Buffer_analysis(Network, "%scratchWorkspace%\\LargeBuffer", LargeBufferSize, "FULL", "ROUND", "NONE", "")

    ncurrentstep+=1
    arcpy.AddMessage("Creating Small Buffer- Step " + str(ncurrentstep) + "/" + str(nstep))
    SmallBuffer=arcpy.Buffer_analysis(Network, "%scratchWorkspace%\\SmallBuffer", SmallBufferSize, "FULL", "ROUND", "NONE", "")


    #/creation of thiessen polygons
    ncurrentstep+=1
    arcpy.AddMessage("Splitting the network - Step " + str(ncurrentstep) + "/" + str(nstep))
    SplitNetwork = dS.SLEM(SmoothedNetwork, DisaggregationStep, "%ScratchWorkspace%\\SplitNetwork", ScratchW, "true")

    ncurrentstep+=1
    arcpy.AddMessage("Converting Split network to points - Step " + str(ncurrentstep) + "/" + str(nstep))
    SplitNetworkToPoints = arcpy.FeatureVerticesToPoints_management(SplitNetwork, "%scratchWorkspace%\\SplitNetworkToPoints", "MID")

    ncurrentstep+=1
    arcpy.AddMessage("Creating Thiessen polygons - Step  " + str(ncurrentstep) + "/" + str(nstep))
    ThiessenPolygons = arcpy.CreateThiessenPolygons_analysis(SplitNetworkToPoints, "%scratchWorkspace%\\ThiessenPolygons", "ALL")


    #/creation of the reference DEM
    ncurrentstep+=1
    arcpy.AddMessage("Clipping Thiessen polygons with Large Buffer - Step " + str(ncurrentstep) + "/" + str(nstep))
    ClippedThiessenPolygons = arcpy.Clip_analysis(ThiessenPolygons, LargeBuffer, "%scratchWorkspace%\\ClippedThiessenPolygons", "")

    ncurrentstep+=1
    arcpy.AddMessage("Creating DEM with the Small Buffer - Step " + str(ncurrentstep) + "/" + str(nstep))
    MinDEM = arcpy.gp.ExtractByMask_sa(ProcessDEM, SmallBuffer, "%scratchWorkspace%\\MinDEM")


    #/extraction of the polygon extent
    ncurrentstep+=1
    arcpy.AddMessage("Getting the treatment extent - Step  " + str(ncurrentstep) + "/" + str(nstep))
    desc = arcpy.Describe(ClippedThiessenPolygons)
    extent = desc.extent
    
    ext = str(extent).split(" ")
    Xmin = float(ext[0].replace(",","."))
    Ymin = float(ext[1].replace(",","."))
    Xmax = float(ext[2].replace(",","."))
    Ymax = float(ext[3].replace(",","."))
    
    chaine = str(Xmin) + " " + str(Ymin) + " " + str(Xmax) + " " + str(Ymax)
    arcpy.AddMessage("        Extent : Xmin=" + str(Xmin) + " ; Ymin=" + str(Ymin))
    arcpy.AddMessage("                 Xmax=" + str(Xmax) + " ; Ymax=" + str(Ymax))

    #/creation of the relative DEM
    ncurrentstep+=1
    arcpy.AddMessage("Zonal Statistics - Step " + str(ncurrentstep) + "/" + str(nstep))
    arcpy.env.extent = chaine
    ReferenceDEM = arcpy.gp.ZonalStatistics_sa(ClippedThiessenPolygons, "Input_FID", MinDEM, "%scratchWorkspace%\\ReferenceDEM", "MINIMUM", "DATA")
    arcpy.env.extent = chaine

    ncurrentstep+=1
    arcpy.AddMessage("Creating Relative DEM - Step " + str(ncurrentstep) + "/" + str(nstep))
    RelativeDEM = arcpy.gp.Minus_sa(ProcessDEM, ReferenceDEM, "%scratchWorkspace%\\RelativeDEM")


    #/extraction of a raw valley bottom as raster
    ncurrentstep+=1
    arcpy.AddMessage("Building attribute table for the relative DEM - Step " + str(ncurrentstep) + "/" + str(nstep))
    arcpy.BuildRasterAttributeTable_management(RelativeDEM, "NONE")

    ncurrentstep+=1 
    arcpy.AddMessage("Extracting Valley Bottom - Step " + str(ncurrentstep) + "/" + str(nstep))
    Expression = "\"Value\" <= " + str(ThresholdMAX) + " and \"Value\" >= " + str(ThresholdMIN)

    arcpy.AddMessage("All values contains in : " + Expression + " are selected")
    RasterVB = arcpy.gp.ExtractByAttributes_sa(RelativeDEM, Expression, "%scratchWorkspace%\\RasterVB")


    #/conversion into a polygon layer
    VBminusVB = arcpy.gp.Minus_sa(RasterVB, RasterVB, "%scratchWorkspace%\\VBminusVB")

    ncurrentstep+=1
    arcpy.AddMessage("Converting Raster Valley Bottom into a polygon feature - Step " + str(ncurrentstep) + "/" + str(nstep))
    RasterVBToPolygon = arcpy.RasterToPolygon_conversion(VBminusVB, "%scratchWorkspace%\\RasterVBToPolygon", "SIMPLIFY", "VALUE")
    arcpy.AddField_management(RasterVBToPolygon, "TEMP", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    ncurrentstep+=1
    arcpy.AddMessage("Dissolving the Polygon Valley Bottom - Step " + str(ncurrentstep) + "/" + str(nstep))
    UncleanedPolygonVB = arcpy.Dissolve_management(RasterVBToPolygon, "%scratchWorkspace%\\UncleanedPolygonVB", "TEMP", "", "MULTI_PART", "DISSOLVE_LINES")
    ncurrentstep+=1

  
  
    ################################
    #### Valley bottom cleaning ####
    ################################
    ## The box "Only Execute the CleanStep of the Polygonal Valley Bottom" is checked

else :
    # Number of steps
    if str(DeleteTF) == "true" :
        nstep = 3
    else : 
        nstep = 2
    if str(SmoothingVB) != "0" :
            nstep += 1
    else :
        nstep = 17
    ncurrentstep = 1
    
    #/definition of the valley bottom to be cleaned
    UncleanedPolygonVB = UncleanedPolygonVB_USER


    
    
#/cleaning of the valley bottom polygon
arcpy.AddMessage("Aggregating and Deleting Holes | CleanStep 1 - Step " + str(ncurrentstep) + "/" + str(nstep))
AggregatedVB = arcpy.AggregatePolygons_cartography(UncleanedPolygonVB, "%scratchWorkspace%\\AggregatedVB", AggregationDist, MinimumArea, MinimumHoleSize, "NON_ORTHOGONAL")


if str(SmoothingVB) != "0" :
    
    ncurrentstep+=1
    arcpy.AddMessage("Eliminating Polygon Parts | CleanStep 2 - Step " + str(ncurrentstep) + "/" + str(nstep))
    EliminatedVB = arcpy.EliminatePolygonPart_management(AggregatedVB, "%scratchWorkspace%\\EliminatedVB", "AREA", MinimumHoleSize, "", "ANY")

    ncurrentstep+=1
    arcpy.AddMessage("Smoothing Valley Bottom | CleanStep 3 - Step " + str(ncurrentstep) + "/" + str(nstep))
    VB = arcpy.SmoothPolygon_cartography(EliminatedVB, Output, "PAEK", SmoothingVB, "FIXED_ENDPOINT", "NO_CHECK")

else :
    ncurrentstep+=1
    arcpy.AddMessage("Eliminating Polygon Part | CleanStep 2 - Step " + str(ncurrentstep) + "/" + str(nstep))
    VB = arcpy.EliminatePolygonPart_management(AggregatedVB, Output, "AREA", MinimumHoleSize, "", "ANY")








#===============================================================================
# DELETING TEMPORARY FILES
#=============================================================================== 
if str(DeleteTF) == "true" :
    ncurrentstep+=1
    arcpy.AddMessage("Delete temporary files - Step " + str(ncurrentstep) + "/" + str(nstep))
    if str(Boolean) == "false" :
        if (DEMprop == 9) :
            arcpy.Delete_management(ProcessDEM)
        arcpy.Delete_management(SmoothedNetwork)
        arcpy.Delete_management(LargeBuffer)
        arcpy.Delete_management(SmallBuffer)
        arcpy.Delete_management(SplitNetwork)
        arcpy.Delete_management(SplitNetworkToPoints)
        arcpy.Delete_management(ThiessenPolygons)
        arcpy.Delete_management(ClippedThiessenPolygons)
        arcpy.Delete_management(MinDEM)
        arcpy.Delete_management(ReferenceDEM)
        arcpy.Delete_management(RelativeDEM)
        arcpy.Delete_management(RasterVB)
        arcpy.Delete_management(VBminusVB)
        arcpy.Delete_management(RasterVBToPolygon)
    arcpy.Delete_management(AggregatedVB)
    if str(SmoothingVB) != "0" :
        arcpy.Delete_management(EliminatedVB)





#===============================================================================
# WARNING MESSAGE
#===============================================================================
#/display a warning message if the final VB is a multi-part polygon
rowCount = arcpy.GetCount_management(VB)
arcpy.AddMessage(str(rowCount))
if int(str(rowCount)) > int(1) :
    arcpy.AddWarning("Output feature : " + Output + " is a multi-part entity. This is not consistent with inputs. You can re-work clean parameters by clicking the 'Only execute the CleanSteps of the polygonal Fdv' box.")
