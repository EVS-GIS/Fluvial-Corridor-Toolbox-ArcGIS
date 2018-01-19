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
       
@summary: Centerline is an open-source python and arcPy code.
          This script has been implemented to extract the centerline line of "long" polygon features (i.e. with
          one larger dimension compared to the other). It is based on a Thiessen polygonization of the input
          polygon boundaries. 
          
'''


# Import of required librairies
import arcpy
from arcpy import env
import os
import def__ExtremePoints as ExtPts
import def__SLEM as dS
import def__UpToDateShapeLengthField as UPD_SL
import def__ScratchWPathName as SWPN

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

# Inputs
Polygon = arcpy.GetParameterAsText(0)
Polyline = arcpy.GetParameterAsText(1)
DisaggregationStep = arcpy.GetParameterAsText(2)
Smoothing = arcpy.GetParameterAsText(3)
Output = arcpy.GetParameterAsText(4)
DeleteTF = arcpy.GetParameterAsText(5)

# Dervied variable from inputs
name = os.path.split(os.path.splitext(Polygon)[0])[1]
ScratchW = SWPN.ScratchWPathName ()

# Number of steps
nstep = 12
if str(DeleteTF) == "false" :
    nstep+=-1
ncurrentstep=1



#===============================================================================
# CODING
#===============================================================================
#/creation of the extreme points
arcpy.AddMessage("Looking for the extreme points of the input polyline - Step "  + str(ncurrentstep) + "/" + str(nstep))

ExtremePoints = arcpy.FeatureVerticesToPoints_management(Polyline, "%ScratchWorkspace%\\ExtremePoints", "BOTH_ENDS")
arcpy.AddXY_management(ExtremePoints)
arcpy.AddField_management(ExtremePoints, "Del", "SHORT")
ExtPts.ExtremePoints(ExtremePoints)

Make = arcpy.MakeFeatureLayer_management(ExtremePoints, "%ScratchWorkspace%\\Make")
Selection = arcpy.SelectLayerByAttribute_management(Make, "NEW_SELECTION", "\"Del\" = 1")

arcpy.DeleteFeatures_management(Selection)


#/splitting of the polygon with extreme points
ncurrentstep+=1
arcpy.AddMessage("Converting the input polygon to line - Step " + str(ncurrentstep) + "/" + str(nstep))
PolyToLine = arcpy.FeatureToLine_management(Polygon, "%ScratchWorkspace%\\PolyToLine", "", "ATTRIBUTES")

ncurrentstep+=1
arcpy.AddMessage("Looking for the longer distance between extreme points and the polygon - Step " + str(ncurrentstep) + "/" + str(nstep))
NearTable = arcpy.GenerateNearTable_analysis(ExtremePoints, PolyToLine, "NearTable", "", "LOCATION", "NO_ANGLE")
rows = arcpy.SearchCursor(NearTable)
Counter = 0
for row in rows :
    if row.NEAR_DIST > Counter :
        Counter = row.NEAR_DIST
Counter+=1

ncurrentstep+=1
arcpy.AddMessage("Splitting polygon with the extreme points - Step " + str(ncurrentstep) + "/" + str(nstep))
FracTEMP = arcpy.SplitLineAtPoint_management(PolyToLine, ExtremePoints, "%ScratchWorkspace%\\FracTEMP", Counter)


ncurrentstep+=1
arcpy.AddMessage("Deleting residual segments - Step " + str(ncurrentstep) + "/" + str(nstep))
FracTEMPToPoints = arcpy.FeatureVerticesToPoints_management(FracTEMP, "%ScratchWorkspace%\\FracTEMPToPoints", "BOTH_ENDS")

arcpy.AddXY_management(FracTEMPToPoints)
arcpy.DeleteIdentical_management(FracTEMPToPoints, ["POINT_X", "POINT_Y"])

arcpy.AddField_management(FracTEMP, "Fusion", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
fieldnames = [f.name for f in arcpy.ListFields(FracTEMP)]
arcpy.CalculateField_management(FracTEMP, "Fusion", "["+fieldnames[0]+"]", "VB", "")

SpatialRef = arcpy.Describe(Polygon).spatialReference
XY = arcpy.MakeXYEventLayer_management(NearTable, "NEAR_X", "NEAR_Y", "%ScratchWorkspace%\\XY", SpatialRef, "")

fieldnames = [f.name for f in arcpy.ListFields(FracTEMPToPoints)]
NearTable2 = arcpy.GenerateNearTable_analysis(XY, FracTEMPToPoints, "NearTable2", "", "LOCATION", "NO_ANGLE", "CLOSEST", "")
arcpy.JoinField_management(FracTEMPToPoints, fieldnames[0], NearTable2, "NEAR_FID", ["NEAR_FID"])

MakeFracTEMPToPoints = arcpy.MakeFeatureLayer_management(FracTEMPToPoints, "%ScratchWorkspace%\\MakeFracTEMPToPoints", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
MakeFracTEMP = arcpy.MakeFeatureLayer_management(FracTEMP, "%ScratchWorkspace%\\MakeFracTEMP", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")

SelectionPoints = arcpy.SelectLayerByAttribute_management(MakeFracTEMPToPoints, "NEW_SELECTION", "\"NEAR_FID\" IS NULL")
SelectLine = arcpy.SelectLayerByLocation_management(MakeFracTEMP, "BOUNDARY_TOUCHES", SelectionPoints, "", "NEW_SELECTION")
arcpy.CalculateField_management(SelectLine, "Fusion", "10000", "VB", "")

FracPoly_TEMP = arcpy.Dissolve_management(FracTEMP, "%ScratchWorkspace%\\FracPoly_TEMP", "Fusion", "", "MULTI_PART", "DISSOLVE_LINES")

FracPoly = arcpy.MultipartToSinglepart_management(FracPoly_TEMP, "%ScratchWorkspace%\\FracPoly")
arcpy.DeleteField_management(FracPoly, "Fusion")

ncurrentstep+=1
arcpy.AddMessage("Split the input polygon - Step " + str(ncurrentstep) + "/" + str(nstep))
PolySplitTEMP = dS.SLEM(FracPoly, DisaggregationStep, "%ScratchWorkspace%\\PolySplitTEMP", ScratchW, "true")
PolySplit = arcpy.Sort_management(PolySplitTEMP, "%ScratchWorkspace%\\PolySplit", [["Rank_UGO", "ASCENDING"],["Distance","ASCENDING"]])

ncurrentstep+=1
arcpy.AddMessage("Converting Split polygon to points - Step " + str(ncurrentstep) + "/" + str(nstep))
PolySplitToPoint = arcpy.FeatureToPoint_management(PolySplit, "%ScratchWorkspace%\\PolySplitToPoint", "INSIDE")


#/creating the Thiessen polygons and the centerline
ncurrentstep+=1
arcpy.AddMessage("Creating Thiessen polygons - Step  " + str(ncurrentstep) + "/" + str(nstep))
ThiessenPoly = arcpy.CreateThiessenPolygons_analysis(PolySplitToPoint, "%ScratchWorkspace%\\ThiessenPoly", "ALL")

JoinTEMP = arcpy.SpatialJoin_analysis(ThiessenPoly, PolySplitToPoint, "%ScratchWorkspace%\\JoinTEMP", "JOIN_ONE_TO_ONE", "KEEP_ALL", "Rank_UGO \"Rank_UGO\" true true false 4 Long 0 0 ,First,#, %ScratchWorkspace%\\PolySplitToPoint,Rank_UGO,-1,-1; Distance \"Distance\" true true false 4 Long 0 0 ,First,#,%ScratchWorkspace%\\PolySplitToPoint,Distance,-1,-1", "INTERSECT", "", "")
Join = arcpy.Sort_management(JoinTEMP, "%ScratchWorkspace%\\Join", [["Rank_UGO", "ASCENDING"],["Distance","ASCENDING"]])

ncurrentstep+=1
arcpy.AddMessage("Merging Thiessen polygons - Step  " + str(ncurrentstep) + "/" + str(nstep))
Dissolve1 = arcpy.Dissolve_management(Join, "%ScratchWorkspace%\\Dissolve1", "Rank_UGO", "", "MULTI_PART", "DISSOLVE_LINES")

ncurrentstep+=1
arcpy.AddMessage("Finalizing the centerline - Step  " + str(ncurrentstep) + "/" + str(nstep))
Dissolve1ToLine = arcpy.Intersect_analysis([Dissolve1,Dissolve1], "%ScratchWorkspace%\\Dissolve1ToLine", "", "", "LINE")
UPD_SL.UpToDateShapeLengthField(Dissolve1ToLine)
arcpy.DeleteIdentical_management(Dissolve1ToLine, ["Shape_Length"])

RawCenterline = arcpy.Intersect_analysis([Dissolve1ToLine, Polygon], "%ScratchWorkspace%\\RawCenterline", "ALL", "", "INPUT")

ncurrentstep+=1
arcpy.AddMessage("Smoothing centerline - Step " + str(ncurrentstep) + "/" + str(nstep))
Centerline = arcpy.SmoothLine_cartography(RawCenterline, Output, "PAEK", Smoothing, "FIXED_CLOSED_ENDPOINT", "NO_CHECK")


#/deleting residual fields
try :
    arcpy.DeleteField_management(Centerline, ["FID_Dissolve1ToLine", "FID_Dissolve1", "FID_Dissolve1_1", "ORIG_FID", "Rank_UGO", "Rank_UGO_1", "FID_"+str(name)])
except:
    pass
try : 
    arcpy.DeleteField_management(Centerline, ["FID_Dissol", "FID_Diss_1", "FID_Diss_2", "FID_"+str(name)[0:6], "ORIG_FID", "Rank_UGO", "Rank_UGO_1", "Shape_Leng", "Shape_Le_1"])
except :
    pass








#===============================================================================
# DELETING TEMPORARY FILES
#===============================================================================
if str(DeleteTF) == "true" : 
    ncurrentstep+=1
    arcpy.AddMessage("Deleting temporary files - Step " + str(ncurrentstep) + "/" + str(nstep))
    arcpy.Delete_management(ExtremePoints)
    arcpy.Delete_management(PolyToLine)
    arcpy.Delete_management(NearTable)
    arcpy.Delete_management(NearTable2)
    arcpy.Delete_management(FracTEMP)
    arcpy.Delete_management(FracTEMPToPoints)
    arcpy.Delete_management(FracPoly_TEMP)
    arcpy.Delete_management(FracPoly)
    arcpy.Delete_management(PolySplitTEMP)
    arcpy.Delete_management(PolySplit)
    arcpy.Delete_management(PolySplitToPoint)
    arcpy.Delete_management(ThiessenPoly)
    arcpy.Delete_management(JoinTEMP)
    arcpy.Delete_management(Join)
    arcpy.Delete_management(Dissolve1)
    arcpy.Delete_management(Dissolve1ToLine)
    arcpy.Delete_management(RawCenterline)
