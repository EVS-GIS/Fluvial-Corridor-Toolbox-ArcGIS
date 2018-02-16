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
       
@summary: PolylineDisaggregation is an open-source python and arcPy code.
          This script has been developed to provide a disaggregation of polyline according their inflection
          points. Over a linear UGO-scale database (e.g. hydrographic network, centerlines), inflection points
          are located where the angle between three successive nodes changes. The inflection line is thus the 
          Bezier curve linking all those points.
          
'''


# Import of required librairies
import arcpy
import math
import os
import def__UpToDateShapeLengthField as UPD_SL 

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

# Inputs
inFC = arcpy.GetParameterAsText(0)
Offset = arcpy.GetParameterAsText(1)
outInflectionPt = arcpy.GetParameterAsText(2)
outInflLine = arcpy.GetParameterAsText(3)
DeleteTF = arcpy.GetParameterAsText(4)

# Dervied variable from inputs
(pathInflectionPt, nameInflectionPt) = os.path.split(outInflectionPt)
(pathInflLine, nameInflLine) = os.path.split(outInflLine)

# Number of steps
if str(DeleteTF) == "true" :
    nstep=7
else :
    nstep=6
ncurrentstep=1



#===============================================================================
# CODING
#===============================================================================
#/preparation of the used features
arcpy.AddMessage("Smoothing the input polyline to apply the lateral offset tolerance - Step " + str(ncurrentstep) + "/" + str(nstep)) 
SmoothedLine = arcpy.SmoothLine_cartography(inFC, "%Scratchworkspace%\\SmoothedLine", "PAEK", Offset)


ncurrentstep+=1
arcpy.AddMessage("Creating features used during the process - Step " + str(ncurrentstep) + "/" + str(nstep)) 
ToPts = arcpy.FeatureVerticesToPoints_management(SmoothedLine, "%ScratchWorkspace%\\ToPts", "ALL")

arcpy.AddXY_management(ToPts)
arcpy.AddField_management(ToPts, "Inflection", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(ToPts, "Angle", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")


#/assessment of the angle between three successive nodes
ncurrentstep+=1
arcpy.AddMessage("Iterative process to determine the angle between three successive nodes - Step " + str(ncurrentstep) + "/" + str(nstep))

rows0 = arcpy.UpdateCursor(ToPts)
rows1 = arcpy.UpdateCursor(ToPts)
rows2 = arcpy.UpdateCursor(ToPts)
rows3 = arcpy.UpdateCursor(ToPts)
line2 = next(rows2)
line3 = next(rows3)
line3 = next(rows3)
n = -1
k = 0
nrows = int(str(arcpy.GetCount_management(ToPts)))

    # Each point of the smoothed (i.e. lateral offset tolerance) in-line has 
    #     - an "Angle" field : angle with the two next points
    #     - an "Inflection" field : set at "1" if the point is an inflection point
    # --> a point is an inflection point is the angle sign changes.
for line1 in rows1 :
    if k >= (nrows-2) :
        # At the end of the table, set the last point as an inflection point and stop the process 
        line3.Inflection = 1
        rows3.updateRow(line3)
        break
    k += 1
    
    line2 = next(rows2)
    line3 = next(rows3)

    if n == -1 :
        # At the beginning of the table, set the first point as an inflection point
        line1.Inflection = 1
        rows1.updateRow(line1)

    if line2.ORIG_FID != line1.ORIG_FID :
        # At each new UGO, set the last point of the previous UGO and the first point of the new UGO as
        # inflection points
        line1.Inflection = 1
        line2.Inflection = 1
        rows1.updateRow(line1)
        rows2.updateRow(line2)    
        
    if line3.ORIG_FID != line1.ORIG_FID :
        n += 1
        line0 = next(rows0)
        continue

    # Calculation of the angle and its sign
    a = ((line2.POINT_X-line1.POINT_X)**2 + (line2.POINT_Y-line1.POINT_Y)**2)**0.5
    b = ((line3.POINT_X-line2.POINT_X)**2 + (line3.POINT_Y-line2.POINT_Y)**2)**0.5
    c = ((line3.POINT_X-line1.POINT_X)**2 + (line3.POINT_Y-line1.POINT_Y)**2)**0.5
    signe = (line2.POINT_X-line1.POINT_X)*(line3.POINT_Y-line1.POINT_Y)-(line3.POINT_X-line1.POINT_X)*(line2.POINT_Y-line1.POINT_Y)

    alpha = math.copysign(math.acos((a*a+c*c-b*b)/(2*a*c)), signe)
    
    line1.Angle = alpha
    rows1.updateRow(line1)
    
    if n == 0 :
    # if n=0 (i.e. line0, line1, line2 and line3 in a same UGO), compare two successive
    # angles and set the "inflection" field
        if line1.Angle * line0.Angle < 0  :
            line0.Inflection = 1
        rows0.updateRow(line0)
    
    line0 = next(rows0)
    n = 0


#/creation of the inflection points
    # Fix the inflection points of the smoothed line (i.e. lateral offset tolerance) on the inFC line.
ncurrentstep+=1
arcpy.AddMessage("Creating temporary inflection points feature - Step " + str(ncurrentstep) + "/" + str(nstep))

MakeToPts = arcpy.MakeFeatureLayer_management(ToPts, "%ScratchWorkspace%\\MakeToPts")
Selection = arcpy.SelectLayerByAttribute_management(MakeToPts, "NEW_SELECTION", "\"Inflection\" = 1")
NearTable = arcpy.GenerateNearTable_analysis(Selection, inFC, "%ScratchWorkspace%\\NearTable", "", "LOCATION", "NO_ANGLE", "")

SpatialRef = arcpy.Describe(inFC).spatialReference
ProxyPtsTEMP = arcpy.MakeXYEventLayer_management(NearTable, "NEAR_X", "NEAR_Y", "ProxyPtsTEMP", SpatialRef, "")


PtsForInflLine = arcpy.CopyFeatures_management(ProxyPtsTEMP, "%ScratchWorkspace%\\PtsForInflLine")
PtsForSplitting = arcpy.CopyFeatures_management(ProxyPtsTEMP, "%ScratchWorkspace%\\PtsForSplitting")
arcpy.JoinField_management(PtsForInflLine, "IN_FID", ToPts, "OBJECTID", ["Order_ID", "ORIG_FID", "NEAR_X", "NEAR_Y"])
arcpy.JoinField_management(PtsForSplitting, "IN_FID", ToPts, "OBJECTID", ["Order_ID", "ORIG_FID", "NEAR_X", "NEAR_Y"])


    # Shaping the inflection points
ncurrentstep+=1
arcpy.AddMessage("Formating inflection points feature in order to create the final inflection line - Step " + str(ncurrentstep) + "/" + str(nstep))

arcpy.AddField_management(PtsForInflLine, "Rank_UGO", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(PtsForSplitting, "Rank_UGO", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(PtsForInflLine, "END_X", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(PtsForInflLine, "END_Y", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.CalculateField_management(PtsForInflLine, "Rank_UGO", "!ORIG_FID!", "PYTHON_9.3", "")
arcpy.CalculateField_management(PtsForSplitting, "Rank_UGO", "!ORIG_FID!", "PYTHON_9.3", "")
arcpy.DeleteField_management(PtsForInflLine, ["ORIG_FID"])


nrows = int(str(arcpy.GetCount_management(PtsForInflLine)))
rowsS = arcpy.UpdateCursor(PtsForInflLine)
rowsE = arcpy.SearchCursor(PtsForInflLine)
lineE = next(rowsE)
n = 0

for lineS in rowsS :
    
    if n >= (nrows-1) :
        rowsS.deleteRow(lineS)
        rowsS.updateRow(lineS)
        break
    lineE = next(rowsE)
    if lineS.Rank_UGO == lineE.Rank_UGO :
        lineS.END_X = lineE.NEAR_X
        lineS.END_Y = lineE.NEAR_Y
    else :
        rowsS.deleteRow(lineS)
    rowsS.updateRow(lineS)
    n += 1

#/creation of the inflection line
ncurrentstep+=1
arcpy.AddMessage("Creating the final Inflection line - Step " + str(ncurrentstep) + "/" + str(nstep))

arcpy.AddMessage("    Connecting inflection point by straight lines - 1/9")
InflToLine = arcpy.XYToLine_management(PtsForInflLine, "%ScratchWorkspace%\\InflToLine", "NEAR_X", "NEAR_Y", "END_X", "END_Y", "GEODESIC", "Rank_UGO", SpatialRef)

arcpy.AddMessage("    Dissolving all lines with the same \"Rank_UGO\" field - 2/9")
Dissolve = arcpy.Dissolve_management(InflToLine, "%ScratchWorkspace%\\Dissolve", "Rank_UGO", "", "MULTI_PART", "DISSOLVE_LINES")

arcpy.AddMessage("    Smoothing by Bezier interpolation - 3/9")
Bezier = arcpy.SmoothLine_cartography(Dissolve, "%ScratchWorkspace%\\Bezier", "BEZIER_INTERPOLATION")
arcpy.AddField_management(Bezier, "Start", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(Bezier, "End", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.CalculateField_management(Bezier, "Start", "0", "PYTHON_9.3", "")
arcpy.CalculateField_management(Bezier, "End", "!Shape_Length!", "PYTHON_9.3", "")

arcpy.AddMessage("    Converting in routes - 4/9")
BezierRoutes = arcpy.CreateRoutes_lr(Bezier, "Rank_UGO", "%ScratchWorkspace%\\BezierRoutes", "TWO_FIELDS", "Start", "End")

arcpy.AddMessage("    Up to date the \"Shape_Length\" field - 5/9")
UPD_SL.UpToDateShapeLengthField(BezierRoutes)

arcpy.AddMessage("    Locate inflection points on Bezier routes - 6/9")
InflectionPtTABLE = arcpy.LocateFeaturesAlongRoutes_lr(PtsForSplitting, BezierRoutes, "Rank_UGO", "1", "%ScratchWorkspace%\\InflectionPtTABLE", "RID POINT MEAS")


#/correction of the table : some errors have occured at confluences
rows1 = arcpy.UpdateCursor(InflectionPtTABLE)
rows2 = arcpy.UpdateCursor(InflectionPtTABLE)
rows3 = arcpy.SearchCursor(BezierRoutes)
line2 = next(rows2)
nrows = int(str(arcpy.GetCount_management(InflectionPtTABLE)))
    # Each inflection point has a MEAS field (distance from upstream)
n = 0
for line1 in rows1 : 
    if n >= nrows-1:
        # At the end of the table set the MEAS as the UGO (line3) length and stop the process
        line3 = next(rows3)
        line2.MEAS = line3.Shape_Length
        rows2.updateRow(line2)
        break
    line2 = next(rows2)
    if n == 0 :
        # At the beginning of the table set the MEAS as 0
        line1.MEAS = 0
        rows1.updateRow(line1)
    if line1.Rank_UGO != line2.Rank_UGO :
        # At the end of an UGO, set the last point of this UGO as the UGO (line3) length and the first
        # point of the next UGO as 0
        line3 = next(rows3)
        line1.MEAS = line3.Shape_Length
        line2.MEAS = 0
        rows1.updateRow(line1)
        rows2.updateRow(line2)
    
    n += 1

#/split of the inflection line at inflection points
arcpy.AddMessage("    Preparing the split at inflection points of the final inflection line - 7/9")
PtsForInflLineDisaggregationTABLE = arcpy.CopyRows_management(InflectionPtTABLE, "%ScratchWorkspace%\\PtsForInflLineDisaggregationTABLE")
rows1 = arcpy.UpdateCursor(PtsForInflLineDisaggregationTABLE)
rows2 = arcpy.UpdateCursor(PtsForInflLineDisaggregationTABLE)
line2 = next(rows2)
nrows = int(str(arcpy.GetCount_management(PtsForInflLineDisaggregationTABLE)))

n = 0
for line1 in rows1 :
    if n >= nrows-1 :
        rows1.deleteRow(line1)
        rows1.updateRow(line1)
        break
    line2 = next(rows2)
    if line1.Rank_UGO != line2.Rank_UGO :
        rows1.deleteRow(line1)
        rows1.updateRow(line1)
    if line1.Rank_UGO == line2.Rank_UGO :
        line1.Distance = line2.MEAS
        rows1.updateRow(line1)
    
    n += 1

arcpy.AddMessage("    Creation of the final inflection points output - 8/9")
PtsTEMP = arcpy.MakeXYEventLayer_management(InflectionPtTABLE, "NEAR_X", "NEAR_Y", "PtsTEMP", SpatialRef, "")
InflectionPt = arcpy.CopyFeatures_management(PtsTEMP, outInflectionPt)

arcpy.DeleteField_management(InflectionPt, ["RID", "MEAS", "Distance", "IN_FID", "NEAR_FID", "NEAR_DIST", "NEAR_X", "NEAR_Y", "End_X", "End_Y"])

arcpy.AddMessage("    Creation of the final inflection line output - 9/9")
MakeRouteEventTEMP = arcpy.MakeRouteEventLayer_lr(BezierRoutes, "Rank_UGO", PtsForInflLineDisaggregationTABLE, "Rank_UGO LINE MEAS Distance", "%ScratchWorkspace%\\MakeRouteEventTEMP")
InflectionLine = arcpy.Sort_management(MakeRouteEventTEMP, "%ScratchWorkspace%\\InflectionLine", [["Rank_UGO", "ASCENDING"], ["Distance", "ASCENDING"]])
fieldnames = [f.name for f in arcpy.ListFields(InflectionLine)]

arcpy.AddField_management(InflectionLine, "Rank_DGO", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.CalculateField_management(InflectionLine, "Rank_DGO", "!"+fieldnames[0]+"!", "PYTHON_9.3", "")
arcpy.CalculateField_management(InflectionLine, "Distance", "!MEAS!", "PYTHON_9.3", "")
arcpy.DeleteField_management(InflectionLine, ["RID", "MEAS", "IN_FID", "NEAR_FID", "NEAR_DIST", "NEAR_X", "NEAR_Y", "END_X", "END_Y"])

arcpy.AddField_management(InflectionPt, "Distance", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
UPD_SL.UpToDateShapeLengthField(InflectionLine)
rows0 = arcpy.UpdateCursor(InflectionPt)
rows1 = arcpy.UpdateCursor(InflectionPt)
line1 = next(rows1)
rows2 = arcpy.SearchCursor(InflectionLine)
rows3 = arcpy.SearchCursor(BezierRoutes)
nrows = int(str(arcpy.GetCount_management(InflectionPt)))
n = 0

for line0 in rows0 :
    if n >= nrows -1 :
        line0.Distance = line2.Distance + line2.Shape_Length
        rows0.updateRow(line0)
        break
    n += 1
    line1 = next(rows1)
    if line0.Rank_UGO == line1.Rank_UGO :
        line2 = next(rows2)
        line0.Distance = line2.Distance
        rows0.updateRow(line0)
    if line0.Rank_UGO != line1.Rank_UGO :
        line0.Distance = line2.Distance + line2.Shape_Length
        rows0.updateRow(line0)
    
arcpy.CopyFeatures_management(InflectionLine, outInflLine)


#/removing of residual fields
try :
    arcpy.DeleteField_management(outInflectionPt, ["ORIG_FID"])
except:
    pass
try :
    arcpy.DeleteField_management(outInflLine, ["ORIG_FID"])
except:
    pass








#===============================================================================
# DELETING TEMPORARY FILES
#=============================================================================== 
if str(DeleteTF) == "true" :
    ncurrentstep+=1
    arcpy.AddMessage("Deleting temporary files - Step " + str(ncurrentstep) + "/" + str(nstep))
    arcpy.Delete_management(SmoothedLine)
    arcpy.Delete_management(ToPts)
    arcpy.Delete_management(NearTable)
    arcpy.Delete_management(PtsForInflLine)
    arcpy.Delete_management(PtsForSplitting)
    arcpy.Delete_management(InflToLine)
    arcpy.Delete_management(Dissolve)
    arcpy.Delete_management(Bezier)
    arcpy.Delete_management(BezierRoutes)
    arcpy.Delete_management(InflectionPtTABLE)
    arcpy.Delete_management(PtsForInflLineDisaggregationTABLE)
    arcpy.Delete_management(InflectionLine)
    