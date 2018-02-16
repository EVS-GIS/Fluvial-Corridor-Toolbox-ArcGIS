# -*- coding: utf-8 -*-

#'''
#Created on 21 fev. 2013
#Last update on 07 fev. 2014

#@author: Clement Roux

#@contact: aurelie.antonio@ens-lyon.fr
#          CNRS - UMR5600 Environnement Ville Societe
#          15 Parvis René Descartes, BP 7000, 69342 Lyon Cedex 07, France
         
#@note: For each use of the FluvialCorridor toolbox leading to a publication, report, presentation or any other
#       document, please refer the following article :
#       Roux, C., Alber, A., Bertrand, M., Vaudor, L., Piegay, H., submitted. "FluvialCorridor": A new ArcGIS 
#       package for multiscale riverscape exploration. Geomorphology
       
#@summary: Morphometry is an open-source python and arcPy code.
#          This script provides a characterization of linear UGO or DGO-scale databases (e.g. hydrographic
#          network, centerline). A set of morphometric metrics is calculated thanks to the input feature and its
#          inflection line (provided by the Polyline disaggregation module). Results can be transferred into the
#          input database or into the inflection line (or into both of them). Four metrics are calculated : the 
#          sinuosity, the half-amplitude, the half-length and the bend length.
        
#'''


# Import of required librairies
import arcpy
from arcpy import env
import math
import def__UpToDateShapeLengthField as UPD_SL
 
# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

# Inputs
inFC = arcpy.GetParameterAsText(0)
InflectionLine = arcpy.GetParameterAsText(1)
InflectionPts = arcpy.GetParameterAsText(2)
Report = arcpy.GetParameterAsText(3)
outInflLine = arcpy.GetParameterAsText(4)
outinFC = arcpy.GetParameterAsText(5)
DeleteTF = arcpy.GetParameterAsText(6)

# Number of steps
if str(DeleteTF) == "true" :
    nstep = 6
else :
    nstep = 5
ncurrentstep = 1



#===============================================================================
# CODING
#===============================================================================
#/segmentation of the inFC with the inflection points
arcpy.AddMessage("Segmentation of the inFC according to the inflection points - Step " + str(ncurrentstep) + "/" + str(nstep))
CopyinFC = arcpy.CopyFeatures_management(inFC, "%ScratchWorkspace%\\CopyinFC")

UPD_SL.UpToDateShapeLengthField(CopyinFC)

arcpy.AddField_management(CopyinFC, "Start", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(CopyinFC, "End", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.CalculateField_management(CopyinFC, "Start", "0", "PYTHON_9.3", "")
arcpy.CalculateField_management(CopyinFC, "End", "!Shape_Length!", "PYTHON_9.3", "")

Routes = arcpy.CreateRoutes_lr(CopyinFC, "Rank_UGO", "%ScratchWorkspace%\\Routes", "TWO_FIELDS", "Start", "End")
UPD_SL.UpToDateShapeLengthField(Routes)

LocateTABLE = arcpy.LocateFeaturesAlongRoutes_lr(InflectionPts, Routes, "Rank_UGO", "1", "%ScratchWorkspace%\\LocateTABLE", "RID POINT MEAS")
arcpy.LocateFeaturesAlongRoutes_lr(InflectionPts, Routes, "Rank_UGO", "1", "%ScratchWorkspace%\\LocateTABLE1", "RID POINT MEAS")

rows1 = arcpy.UpdateCursor(LocateTABLE)
rows2 = arcpy.UpdateCursor(LocateTABLE)
rows3 = arcpy.SearchCursor(Routes)
line2 = next(rows2)
nrows = int(str(arcpy.GetCount_management(LocateTABLE)))
n = 0
for line1 in rows1 : 
    if n >= nrows - 1 :
        line3 = next(rows3)
        line2.MEAS = line3.Shape_Length
        rows2.updateRow(line2)
        break
    line2 = next(rows2)
    if n == 0 :
        line1.MEAS = 0
        rows1.updateRow(line1)
    if line1.Rank_UGO != line2.Rank_UGO :
        line3 = next(rows3)
        line1.MEAS = line3.Shape_Length
        line2.MEAS = 0
        rows1.updateRow(line1)
        rows2.updateRow(line2)

    n += 1


rows1 = arcpy.UpdateCursor(LocateTABLE)
rows2 = arcpy.UpdateCursor(LocateTABLE)
line2 = next(rows2)
nrows = int(str(arcpy.GetCount_management(LocateTABLE)))

n = 0
for line1 in rows1 :
    if n >= nrows - 1 :
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
    
MakeRouteEventTEMP = arcpy.MakeRouteEventLayer_lr(Routes, "Rank_UGO", LocateTABLE, "Rank_UGO LINE MEAS Distance", "%ScratchWorkspace%\\MakeRouteEventTEMP")
SplitinFC = arcpy.Sort_management(MakeRouteEventTEMP, "%ScratchWorkspace%\\SplitinFC", [["Rank_UGO", "ASCENDING"], ["Distance", "ASCENDING"]])
CopyInflLine = arcpy.CopyFeatures_management(InflectionLine, "%ScratchWorkspace%\\CopyInflLine")

#/creation of the new fields
fieldnames = [f.name for f in arcpy.ListFields(SplitinFC)]
arcpy.AddField_management(SplitinFC, "Rank_DGO", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(SplitinFC, "Sinuosity", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(SplitinFC, "Half_Amplitude", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(SplitinFC, "Half_Length", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(SplitinFC, "Bend_Length", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")


arcpy.AddField_management(CopyInflLine, "Sinuosity", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(CopyInflLine, "Half_Amplitude", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(CopyInflLine, "Half_Length", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(CopyInflLine, "Bend_Length", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

arcpy.CalculateField_management(SplitinFC, "Distance", "!MEAS!", "PYTHON_9.3", "" )
arcpy.CalculateField_management(SplitinFC, "Rank_DGO", "!" + fieldnames[0] + "!", "PYTHON_9.3", "" )
arcpy.DeleteField_management(SplitinFC, ["RID", "MEAS", "POINT_X", "POINT_Y"])


UPD_SL.UpToDateShapeLengthField(SplitinFC)
UPD_SL.UpToDateShapeLengthField(CopyInflLine)








    #######################
    ###### Sinuosity ######
    #######################
#/calculation of the sinuosity ... 
ncurrentstep+=1
arcpy.AddMessage("Assessment of the Sinuosity - Step " + str(ncurrentstep) + "/" + str(nstep))
#/... into the inFC and the inflection line
if str(Report) == "On both" :
    rows0 = arcpy.UpdateCursor(CopyInflLine)
    rows1 = arcpy.UpdateCursor(SplitinFC)
    for line1 in rows1 :
        line0 = next(rows0)
        line0.Sinuosity = line1.Shape_Length/line0.Shape_Length
        line1.Sinuosity = line1.Shape_Length/line0.Shape_Length
        rows0.updateRow(line0)
        rows1.updateRow(line1)

#/... into the inFC
if str(Report) == "Only on the polyline" :
    rows0 = arcpy.UpdateCursor(CopyInflLine)
    rows1 = arcpy.UpdateCursor(SplitinFC)
    for line1 in rows1 :
        line0 = next(rows0)
        line1.Sinuosity = line1.Shape_Length/line0.Shape_Length
        rows1.updateRow(line1)
        
#/... into the inflection line
if str(Report) == "Only on the inflection line" :
    rows0 = arcpy.UpdateCursor(CopyInflLine)
    rows1 = arcpy.UpdateCursor(SplitinFC)
    for line1 in rows1 :
        line0 = next(rows0)
        line0.Sinuosity = line1.Shape_Length/line0.Shape_Length
        rows0.updateRow(line0)








    ######################
    ### Half-amplitude ###
    ######################
#/calculation of the half-amplitude 
ncurrentstep+=1
arcpy.AddMessage("Assessment of the Half-Amplitude - Step " + str(ncurrentstep) + "/" + str(nstep))
SplitinFCtoPts = arcpy.FeatureVerticesToPoints_management(SplitinFC, "%ScratchWorkspace%\\SplitinFCtoPts")
NearTable = arcpy.GenerateNearTable_analysis(SplitinFCtoPts, InflectionLine, "%ScratchWorkspace%\\NearTable", "", "", "NO_ANGLE", "")
HalfAmplitudeTable = arcpy.Statistics_analysis(NearTable, "%ScratchWorkspace%\\HalfAmplitudeTable", [["NEAR_DIST", "MAX"]] , "NEAR_FID")




Sort = arcpy.Sort_management(NearTable, "%ScratchWorkspace%\\Sort", [["NEAR_FID", "ASCENDING"]])
rows1 = arcpy.SearchCursor(Sort)
rows2 = arcpy.SearchCursor(Sort)
line2 = next(rows2)

err = []
for line1 in rows1 : 
    try :
        line2 = next(rows2)
        if (line2.NEAR_FID - line1.NEAR_FID) > 1 :
            err.append(line2.NEAR_FID)
    except :
        break

if len(err) > 0 :
    MakeInflectionLine = arcpy.MakeFeatureLayer_management(InflectionLine, "%ScratchWorkspace%\\MakeInflectionLine", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
    MakeSplitinFCtoPts = arcpy.MakeFeatureLayer_management(SplitinFCtoPts, "%ScratchWorkspace%\\MakeSplitinFCtoPts", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
    for i in err :
        SelectionInfl = arcpy.SelectLayerByAttribute_management(MakeInflectionLine, "NEW_SELECTION", "\"Rank_DGO\" = " + str(i))
        SelectionPts = arcpy.SelectLayerByAttribute_management(MakeSplitinFCtoPts, "NEW_SELECTION", "\"Rank_DGO\" = " + str(i))
        NearTable_TEMP = arcpy.GenerateNearTable_analysis(SelectionPts, SelectionInfl, "%ScratchWorkspace%\\NearTable_TEMP", "", "", "NO_ANGLE", "")
        HalfAmplitudeTable_TEMP = arcpy.Statistics_analysis(NearTable_TEMP, "%ScratchWorkspace%\\HalfAmplitudeTable_TEMP", [["NEAR_DIST", "MAX"]] , "NEAR_FID")
        
        rowsTEMP = arcpy.SearchCursor(HalfAmplitudeTable_TEMP)
        rows = arcpy.InsertCursor(HalfAmplitudeTable)
        lineTEMP = next(rowsTEMP)
      
        line = rows.newRow()
        line.setValue("NEAR_FID", lineTEMP.NEAR_FID)
        line.setValue("FREQUENCY", lineTEMP.FREQUENCY)
        line.setValue("MAX_NEAR_DIST", lineTEMP.MAX_NEAR_DIST)
        rows.insertRow(line)


    SortHalfAmplitudeTable = arcpy.Sort_management(HalfAmplitudeTable, "%scratchWorkspace%\\SortHalfAmplitudeTable", [["NEAR_FID", "ASCENDING"]])
    HalfAmplitude = SortHalfAmplitudeTable
else:
    HalfAmplitude = HalfAmplitudeTable

#/transfer of the half-amplitude into the inFC and the inflection line
if str(Report) == "On both" :
    rows0 = arcpy.UpdateCursor(CopyInflLine)
    rows1 = arcpy.UpdateCursor(SplitinFC)
    rows2 = arcpy.SearchCursor(HalfAmplitude)
    for line1 in rows1 :
        line0 = next(rows0)
        line2 = next(rows2)
        line0.Half_Amplitude = line2.MAX_NEAR_DIST
        line1.Half_Amplitude = line2.MAX_NEAR_DIST
        rows0.updateRow(line0)
        rows1.updateRow(line1)
     
        
#/transfer of the half-amplitude into the inFC
if str(Report) == "Only on the polyline" :
    rows1 = arcpy.UpdateCursor(SplitinFC)
    rows2 = arcpy.SearchCursor(HalfAmplitude)
    for line1 in rows1 :
        line2 = next(rows2)
        line1.Half_Amplitude = line2.MAX_NEAR_DIST
        rows1.updateRow(line1)
        
#/transfer of the half-amplitude into the inflection line
if str(Report) == "Only on the inflection line" :
    rows0 = arcpy.UpdateCursor(CopyInflLine)
    rows2 = arcpy.SearchCursor(HalfAmplitude)
    for line0 in rows0 :
        line2 = next(rows2)
        line0.Half_Amplitude = line2.MAX_NEAR_DIST
        rows0.updateRow(line0)








    #####################
    #### Half-length ####
    #####################
#/calculation of the half-length ...
ncurrentstep+=1
arcpy.AddMessage("Assessment of the Half-Length - Step " + str(ncurrentstep) + "/" + str(nstep))
InflectionPtsXY = arcpy.CopyFeatures_management(InflectionPts, "%ScratchWorkspace%\\InflectionPtsXY")
arcpy.AddXY_management(InflectionPtsXY)

#/... into the inFC and the inflection line
if str(Report) == "On both" :
    rows0 = arcpy.UpdateCursor(CopyInflLine)
    rows1 = arcpy.UpdateCursor(SplitinFC)
    rows2 = arcpy.SearchCursor(InflectionPtsXY)
    rows3 = arcpy.SearchCursor(InflectionPtsXY)
    line2 = next(rows2)
    line3 = next(rows3)
    line3 = next(rows3)
    for line1 in rows1 :
        line0 = next(rows0)       
        if line2.Rank_UGO != line3.Rank_UGO :
            line2 = next(rows2)
            line3 = next(rows3)
        if line2.Rank_UGO == line3.Rank_UGO :
            line0.Half_Length = ( (line3.POINT_X-line2.POINT_X)**2 + (line3.POINT_Y - line2.POINT_Y)**2 )**0.5
            line1.Half_Length = ( (line3.POINT_X-line2.POINT_X)**2 + (line3.POINT_Y - line2.POINT_Y)**2 )**0.5
            rows0.updateRow(line0)
            rows1.updateRow(line1)
        line2 = next(rows2)
        line3 = next(rows3)

#/... into the inFC
if str(Report) == "Only on the polyline" :
    rows1 = arcpy.UpdateCursor(SplitinFC)
    rows2 = arcpy.SearchCursor(InflectionPtsXY)
    rows3 = arcpy.SearchCursor(InflectionPtsXY)
    line2 = next(rows2)
    line3 = next(rows3)
    line3 = next(rows3) 
    for line1 in rows1 :
        if line2.Rank_UGO != line3.Rank_UGO :
            line2 = next(rows2)
            line3 = next(rows3)
        if line2.Rank_UGO == line3.Rank_UGO :
            line1.Half_Length = math.sqrt((line3.POINT_X - line2.POINT_X) ** 2 + (line3.POINT_Y - line2.POINT_Y) ** 2)
            rows1.updateRow(line1)
        line2 = next(rows2)
        line3 = next(rows3)

#/... into the inflection line
if str(Report) == "Only on the inflection line" :
    rows0 = arcpy.UpdateCursor(CopyInflLine)
    rows2 = arcpy.SearchCursor(InflectionPtsXY)
    rows3 = arcpy.SearchCursor(InflectionPtsXY)
    line2 = next(rows2)
    line3 = next(rows3)
    line3 = next(rows3)
    for line0 in rows0 :
        if line2.Rank_UGO != line3.Rank_UGO :
            line2 = next(rows2)
            line3 = next(rows3)
        if line2.Rank_UGO == line3.Rank_UGO :
            line0.Half_Length = math.sqrt((line3.POINT_X - line2.POINT_X) ** 2 + (line3.POINT_Y - line2.POINT_Y) ** 2)
            rows0.updateRow(line0)
        line2 = next(rows2)
        line3 = next(rows3)








    #####################
    #### Bend-length ####
    #####################
#/calculation of the bend-length ...
ncurrentstep+=1
arcpy.AddMessage("Assessment of the Bend-Length - Step " + str(ncurrentstep) + "/" + str(nstep))

#/... into the inFC and the inflection line
if str(Report) == "On both" :
    rows0 = arcpy.UpdateCursor(CopyInflLine)
    rows1 = arcpy.UpdateCursor(SplitinFC)
    for line1 in rows1 :
        line0 = next(rows0)
        line0.Bend_Length = line1.Shape_Length
        line1.Bend_Length = line1.Shape_Length
        rows0.updateRow(line0)
        rows1.updateRow(line1)
        
#/... into the inFC        
if str(Report) == "Only on the polyline" :
    rows1 = arcpy.UpdateCursor(SplitinFC)
    for line1 in rows1 :
        line1.Bend_Length = line1.Shape_Length
        rows1.updateRow(line1)
        
#/... into the inflection line
if str(Report) == "Only on the inflection line" :
    rows0 = arcpy.UpdateCursor(CopyInflLine)
    rows1 = arcpy.SearchCursor(SplitinFC)
    for line1 in rows1 :
        line0 = next(rows0)
        line0.Bend_Length = line1.Shape_Length
        rows0.updateRow(line0)


#/creation of the final output(s)
try :
    arcpy.DeleteField_management(SplitinFC, ["Distance2"])
except :
    pass
if str(Report) == "On both" :
    arcpy.CopyFeatures_management(SplitinFC, outinFC)
    arcpy.CopyFeatures_management(CopyInflLine, outInflLine)
if str(Report) == "Only on the polyline" :
    arcpy.CopyFeatures_management(SplitinFC, outinFC)
if str(Report) == "Only on the inflection line" :
    arcpy.CopyFeatures_management(CopyInflLine, outInflLine)








#===============================================================================
# DELETING TEMPORARY FILES
#=============================================================================== 
if str(DeleteTF) == "true" :
    ncurrentstep+=1
    arcpy.AddMessage("Deleting temporary files - Step " + str(ncurrentstep) + "/" + str(nstep))

    arcpy.Delete_management(Sort)
    arcpy.Delete_management(CopyinFC)
    arcpy.Delete_management(Routes)
    arcpy.Delete_management(LocateTABLE)
    arcpy.Delete_management(SplitinFCtoPts)
    arcpy.Delete_management(HalfAmplitudeTable)
    arcpy.Delete_management(SplitinFC)
    arcpy.Delete_management(CopyInflLine)
    arcpy.Delete_management(InflectionPtsXY)
    
    if len(err) > 0 :
        arcpy.Delete_management(NearTable_TEMP)
        arcpy.Delete_management(HalfAmplitudeTable_TEMP)
        try :
            arcpy.Delete_management(SortHalfAmplitudeTable)
        except : 
            pass
