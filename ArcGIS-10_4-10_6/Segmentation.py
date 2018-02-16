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
       
@summary: Segmentation is an open-source python and arcPy code.
          This module is mainly based on the SLEM script. The segmentation can be done either for polylines
          or for polygons. For polylines, the input is simply segmented thanks to the SLEM script. For polygons,
          the centerline is segmented with the SLEM script and then a thiessen polygonization is done. The 
          segmentation is then done by intersecting the input polygon with the Thiessen polygons.        
          
'''


# Import of required librairies
import arcpy
from arcpy import env
import def__ScratchWPathName as SWPN
import def__SLEM as dS

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

# Inputs
inFCtype = arcpy.GetParameterAsText(0)
inFC = arcpy.GetParameterAsText(1)
Centerline = arcpy.GetParameterAsText(2)
SegmentationStep = arcpy.GetParameterAsText(3)
OutputSeg = arcpy.GetParameterAsText(4)
DeleteTF = arcpy.GetParameterAsText(5)

# Dervied variable from inputs
ScratchW = SWPN.ScratchWPathName ()



#===============================================================================
# CODING
#===============================================================================
    ############
    ### Line ###
    ############
if str(inFCtype) == "Line" :
    # Number of steps
    nstep=2
    if str(DeleteTF) == "true" :
        nstep += 1
    ncurrentstep = 1
    
    #/segmentation of the polyline
    arcpy.AddMessage("Using the SLEM script to segment the in-polyline feature - Step " + str(ncurrentstep) + "/" + str(nstep))
    SplitLine = dS.SLEM(inFC, SegmentationStep, "%ScratchWorkspace%\\SplitLine", ScratchW, DeleteTF)
    
    ncurrentstep+=1
    arcpy.AddMessage("Sorting the segmented line - Step " + str(ncurrentstep) + "/" + str(nstep))
    Sort = arcpy.Sort_management(SplitLine, OutputSeg, [["Rank_UGO", "ASCENDING"], ["Distance", "ASCENDING"]])
    
    arcpy.AddField_management(Sort, "Rank_DGO", "LONG", "", "", "", "","NULLABLE", "NON_REQUIRED")
    fieldname = [f.name for f in arcpy.ListFields(Sort)]
    arcpy.CalculateField_management(Sort, "Rank_DGO", "!" + str(fieldname[0]) + "!", "PYTHON_9.3")

    
    #===============================================================================
    # DELETING TEMPORARY FILES
    #===============================================================================
    if str(DeleteTF) == "true" :
        ncurrentstep+=1
        arcpy.AddMessage("Deleting Temporary Files - Step " + str(ncurrentstep) + "/" + str(nstep))
        arcpy.Delete_management(SplitLine)



    ###############
    ### Polygon ###
    ###############
if str(inFCtype) == "Polygon" :
    # Number of steps
    if str(DeleteTF) == "true" :
        nstep=8
    else :
        nstep=7
    ncurrentstep = 1
    
    #/segmentation of the centerline
    CenterlineMTS = arcpy.MultipartToSinglepart_management(Centerline, "%ScratchWorkspace%\\CenterlineMTS")
    
    arcpy.AddMessage("Splitting the centerline with the SLEM script - Step  " + str(ncurrentstep) + "/" + str(nstep))
    SplitCenterline = dS.SLEM(CenterlineMTS, SegmentationStep, "%ScratchWorkspace%\\SplitCenterline", ScratchW, DeleteTF)

    ncurrentstep+=1
    arcpy.AddMessage("Converting all the segments into point (MID point of each reach) - Step  " + str(ncurrentstep) + "/" + str(nstep))
    SplitCenterlineToPoint = arcpy.FeatureVerticesToPoints_management(SplitCenterline, "%ScratchWorkspace%\\SplitCenterlineToPoint", "MID")
    
    
    #/extraction of the polygon extent
    ncurrentstep+=1
    arcpy.AddMessage("Getting the extent of the in polygon feature - Step  " + str(ncurrentstep) + "/" + str(nstep))
    desc = arcpy.Describe(inFC)
    extent = desc.extent
    
    ext = str(extent).split(" ")
    Xmin = float(ext[0].replace(",","."))
    Ymin = float(ext[1].replace(",","."))
    Xmax = float(ext[2].replace(",","."))
    Ymax = float(ext[3].replace(",","."))
    
    chaine = str(Xmin) + " " + str(Ymin) + " " + str(Xmax) + " " + str(Ymax)
    arcpy.AddMessage("        Extent : Xmin=" + str(Xmin) + " ; Ymin=" + str(Ymin))
    arcpy.AddMessage("                 Xmax=" + str(Xmax) + " ; Ymax=" + str(Ymax))

    #/creation of the Thiessen polygons
    ncurrentstep+=1
    arcpy.AddMessage("Creating Thiessen polygons - Step  " + str(ncurrentstep) + "/" + str(nstep))
    arcpy.env.extent = chaine
    ThiessenPolyCenterline = arcpy.CreateThiessenPolygons_analysis(SplitCenterlineToPoint, "%ScratchWorkspace%\\ThiessenPolyCenterline", "ALL")
    arcpy.env.extent = chaine
    
    #/extraction of the Thiessen polygons overlaying the polygon 
    ncurrentstep+=1
    arcpy.AddMessage("Clipping Thiessen polygons with the in polygon feature - Step  " + str(ncurrentstep) + "/" + str(nstep))
    Segmentation_TEMP = arcpy.Clip_analysis(ThiessenPolyCenterline, inFC, "%ScratchWorkspace%\\Segmentation_TEMP", "")

    
    #/transfer of the ordination information
        # ordination fields are contained in the split centerline 
    ncurrentstep+=1
    arcpy.AddMessage("Transferring the ordination information from the sequenced and split centerline into the segmented polygon - Step  " + str(ncurrentstep) + "/" + str(nstep))
    Make = arcpy.MakeFeatureLayer_management(Segmentation_TEMP, "%ScratchWorkspace%\\Make", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
    
    Join_TEMP = arcpy.AddJoin_management(Make, "Input_FID", SplitCenterlineToPoint, "OBJECTID")
    Join = arcpy.CopyFeatures_management(Join_TEMP, "%ScratchWorkspace%\\Join")

    arcpy.AddField_management(Join, "Order_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(Join, "Rank_UGO", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(Join, "Distance", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    
    try :
        arcpy.CalculateField_management(Join, "Order_ID", "!SplitCenterlineToPoint_Order_ID!", "PYTHON_9.3", "")
    except :
        arcpy.AddMessage("      No Order_ID field")
    try :
        arcpy.CalculateField_management(Join, "Rank_UGO", "!SplitCenterlineToPoint_Rank_UGO!", "PYTHON_9.3", "")
    except :
        arcpy.AddMessage("      No Rank_UGO field")
    try :
        arcpy.CalculateField_management(Join, "Distance", "!SplitCenterlineToPoint_Distance!", "PYTHON_9.3", "")
    except :
        arcpy.AddMessage("      No Distance field")

    arcpy.DeleteField_management(Join, ["Segmentation_TEMP_Input_FID", "SplitCenterlineToPoint_OBJECTID", "SplitCenterlineToPoint_Rank_UGO", "SplitCenterlineToPoint_Order_ID", "SplitCenterlineToPoint_Distance", "SplitCenterlineToPoint_ORIG_FID"])

    ncurrentstep+=1
    arcpy.AddMessage("Sorting the segmented polygon - Step  " + str(ncurrentstep) + "/" + str(nstep))
    Sort = arcpy.Sort_management(Join, OutputSeg, [["Rank_UGO", "ASCENDING"], ["Distance", "ASCENDING"]])

    arcpy.AddField_management(Sort, "Rank_DGO", "SHORT", "", "", "", "","NULLABLE", "NON_REQUIRED")
    fieldname = [f.name for f in arcpy.ListFields(Sort)]
    arcpy.CalculateField_management(Sort, "Rank_DGO", "!" + str(fieldname[0]) + "!", "PYTHON_9.3")








#===============================================================================
# DELETING TEMPORARY FILES
#=============================================================================== 
    if str(DeleteTF) == "true" : 
        ncurrentstep+=1
        arcpy.AddMessage("Deleting temporary files - Step " + str(ncurrentstep) + "/" + str(nstep))
        
        arcpy.Delete_management(CenterlineMTS)
        arcpy.Delete_management(SplitCenterline)
        arcpy.Delete_management(SplitCenterlineToPoint)
        arcpy.Delete_management(ThiessenPolyCenterline)
        arcpy.Delete_management(Segmentation_TEMP)
        arcpy.Delete_management(Join)
