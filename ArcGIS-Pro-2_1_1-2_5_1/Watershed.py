# -*- coding: utf-8 -*-

#'''
#Created on 21 fev. 2013
#Last update on 07 fev. 2014

#@author: Clement Roux

#@contact: samuel.dunesme@ens-lyon.fr
#          CNRS - UMR5600 Environnement Ville Societe
#          15 Parvis Ren� Descartes, BP 7000, 69342 Lyon Cedex 07, France
         
#@note: For each use of the FluvialCorridor toolbox leading to a publication, report, presentation or any other
#       document, please refer the following article :
#       Roux, C., Alber, A., Bertrand, M., Vaudor, L., Piegay, H., submitted. "FluvialCorridor": A new ArcGIS 
#       package for multiscale riverscape exploration. Geomorphology
       
#@summary: Watershed is an open-source python and arcPy code.
#          This script provides a characterization of linear or polygon  UGO, DGO or AGO-scale database. For each
#          component of the database, a set of points with the drained surface (m�) is extracted from a flow 
#          accumulation raster. It can be then join to the original database thanks to a "Join_Field" field.
          
#'''


# Import of required librairies
import arcpy
from arcpy.sa import *

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

# Inputs
inFC = arcpy.GetParameterAsText(0)
FAC = arcpy.GetParameterAsText(1)
Output = arcpy.GetParameterAsText(2)
DeleteTF = arcpy.GetParameterAsText(3)

# Number of steps
if str(DeleteTF) == "true" :
    nstep=4
else :
    nstep=3
ncurrentstep=1



#===============================================================================
# CODING
#===============================================================================
#/creation of the set of points
Shape = arcpy.Describe(inFC).shapeType
fieldname = [f.name for f in arcpy.ListFields(inFC)]
# CopyinFC = arcpy.CopyFeatures_management(inFC, "%ScratchWorkspace%\\CopyinFC")

arcpy.AddMessage("Converting inFC into raster - Step " + str(ncurrentstep) + "/" + str(nstep)) 
CellSize = str(arcpy.GetRasterProperties_management(FAC, "CELLSIZEX"))
arcpy.env.snapRaster = FAC
if str(Shape) == "Polyline" :
    inFCtoRaster = arcpy.PolylineToRaster_conversion(inFC, fieldname[0], "%ScratchWorkspace%\\inFCtoRaster", "", "", CellSize)
elif str(Shape) == "Polygon" :
    inFCtoRaster = arcpy.PolygonToRaster_conversion(inFC, fieldname[0], "%ScratchWorkspace%\\inFCtoRaster", "MAXIMUM_AREA", "", CellSize)


ncurrentstep+=1
arcpy.AddMessage("Converting raster into points - Step " + str(ncurrentstep) + "/" + str(nstep)) 
RasterToPts = arcpy.RasterToPoint_conversion(inFCtoRaster, "%ScratchWorkspace%\\RasterToPts", "")


#/extraction of the number of cells drained into each points
ncurrentstep+=1
arcpy.AddMessage("Extracting FlowAcc values into a point shapefile - Step " + str(ncurrentstep) + "/" + str(nstep)) 
FACpts = ExtractValuesToPoints(RasterToPts, FAC, Output, "", "")

arcpy.AddField_management(FACpts, "Join_Field", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(FACpts, "Watershed", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.CalculateField_management(FACpts, "Join_Field", "!grid_code!", "PYTHON_9.3")
arcpy.CalculateField_management(FACpts, "Watershed", "!RASTERVALU!*" + str(CellSize) + "*" + str(CellSize) + "/1000000.0", "PYTHON_9.3")
arcpy.DeleteField_management(FACpts, ["pointid", "grid_code", "RASTERVALU"])
try :
    arcpy.DeleteField_management(FACpts, ["OBJECTID"])
except :
    pass








#===============================================================================
# DELETING TEMPORARY FILES
#=============================================================================== 
if str(DeleteTF) == "true" :
    ncurrentstep+=1
    arcpy.AddMessage("Deleting temporary files - Step " + str(ncurrentstep) + "/" + str(nstep))
#     arcpy.Delete_management(CopyinFC)
    arcpy.Delete_management(inFCtoRaster)
    arcpy.Delete_management(RasterToPts)
