# -*- coding: utf-8 -*-

'''
Created on 21 fev. 2013
Last update on 22 dec 2017

@author: Aurelie Antonio

@contact: samuel.dunesme@ens-lyon.fr
          CNRS - UMR5600 Environnement Ville Societe
          15 Parvis Ren� Descartes, BP 7000, 69342 Lyon Cedex 07, France
         
@note: For each use of the FluvialCorridor toolbox leading to a publication, report, presentation or any other
       document, please refer the following article :
       Roux, C., Alber, A., Bertrand, M., Vaudor, L., Piegay, H., submitted. "FluvialCorridor": A new ArcGIS 
       package for multiscale riverscape exploration. Geomorphology
       
@summary: ElevationAndSlope is an open-source python and arcPy code.
          This script provides a characterization of linear UGO, DGO or AGO-scale databases with a set of topologic 
          metrics. From a DEM, five metrics are extracted : the upstream, downstream and mean elevations, the
          slope and the 3D slope. The slope is directly calculated as the ratio between the difference of elevation
          and the euclidean distance from up to downstream. The 3D slope is the ratio between the difference 
          of elevation and the river course length from up to downstream. 
          
'''


# Import of required librairies
import arcpy
from arcpy import env
from arcpy.sa import *
import def__UpToDateShapeLengthField as UPD_SL

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

# Inputs
inFC = arcpy.GetParameterAsText(0)
DEM = arcpy.GetParameterAsText(1)
Output = arcpy.GetParameterAsText(2)
DeleteTF = arcpy.GetParameterAsText(3)

# Number of steps
if str(DeleteTF) == "true" :
    nstep = 5
else :
    nstep = 4
ncurrentstep = 1



#===============================================================================
# CODING
#===============================================================================
#/creation of the output with the new fields
arcpy.AddMessage("Creating output with new fields - Step " + str(ncurrentstep) + "/" + str(nstep)) 

Out = arcpy.CopyFeatures_management(inFC, "%ScratchWorkspace%\\OutTemp")
arcpy.AddField_management(Out, "Z_Up", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(Out, "Z_Down", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
UPD_SL.UpToDateShapeLengthField(Out)

ncurrentstep+=1
arcpy.AddMessage("Converting input line into points and adding surface information - Step " + str(ncurrentstep) + "/" + str(nstep)) 
Pts = arcpy.FeatureVerticesToPoints_management(Out, "%ScratchWorkspace%\\Pts", "BOTH_ENDS")
arcpy.AddXY_management(Pts)

#/extraction and calculation of the topologic metrics
# Ajout Aurelie
arcpy.CheckOutExtension("3D")
# Fin Ajout Aurelie
arcpy.AddSurfaceInformation_3d(Out, DEM, "Z_MEAN", "BILINEAR")
arcpy.AddSurfaceInformation_3d(Pts, DEM, "Z", "BILINEAR")
arcpy.AddField_management(Out, "Slope", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(Out, "Slope3D", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")


ncurrentstep+=1
arcpy.AddMessage("Calculating metrics - Step " + str(ncurrentstep) + "/" + str(nstep)) 
rows1 = arcpy.UpdateCursor(Out)
rows2 = arcpy.SearchCursor(Pts)
rows3 = arcpy.SearchCursor(Pts)
line2 = rows2.next()
line3 = rows3.next()
line3 = rows3.next()


for line1 in rows1 :
    
    line1.Z_Up = line2.Z
    line1.Z_Down = line3.Z
    

    line1.Slope = (line1.Z_Up - line1.Z_Down) / (((line3.POINT_X-line2.POINT_X)**2 + (line3.POINT_Y-line2.POINT_Y)**2)**0.5)
    line1.Slope3D = (line1.Z_Up - line1.Z_Down) / line1.Shape_Length
    rows1.updateRow(line1)
    
    line2 = rows2.next()
    line2 = rows2.next()
    line3 = rows3.next()
    line3 = rows3.next()

    
arcpy.CopyFeatures_management(Out, Output)

#/removing of the residual fields
ncurrentstep+=1
arcpy.AddMessage("Removing the residual fields - Step " + str(ncurrentstep) + "/" + str(nstep))
fieldnamesfromFC = [f.name for f in arcpy.ListFields(Output)]
fieldnamestoFC = [f.name for f in arcpy.ListFields(inFC)]
for field in fieldnamesfromFC :
    if field not in fieldnamestoFC and field != "Z_Up" and field != "Z_Down" and field != "Z_Mean" and field != "Slope" and field != "Slope3D" :
        try :
            arcpy.DeleteField_management(Output, str(field))
        except :
            continue








#===============================================================================
# DELETING TEMPORARY FILES
#=============================================================================== 
if str(DeleteTF) == "true" :
    ncurrentstep+=1
    arcpy.AddMessage("Deleting temporary files - Step " + str(ncurrentstep) + "/" + str(nstep))
    arcpy.Delete_management(Pts)
    arcpy.Delete_management(Out)
