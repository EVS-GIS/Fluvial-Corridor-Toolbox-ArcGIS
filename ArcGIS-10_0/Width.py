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
       
@summary: Width is an open-source python and arcPy code.
          This script is used to extract the fluvial width. It can provides the valley bottom width from a valley
          bottom layer or the active channel width from an active channel layer.
          
'''


# Import of required librairies
import arcpy
import def__SLEM as dS
from arcpy import env
import def__ScratchWPathName as SWPN
import def__UpToDateShapeLengthField as UPD_SL

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

# Inputs
TypeOfWidth = arcpy.GetParameterAsText(0)
Polygon = arcpy.GetParameterAsText(1)
Centerline = arcpy.GetParameterAsText(2)
DisaggregationStepForWidth = arcpy.GetParameterAsText(3)
Output = arcpy.GetParameterAsText(4)
DeleteTF = arcpy.GetParameterAsText(5)

# Dervied variable from inputs
ScratchW = SWPN.ScratchWPathName ()

# Number of steps
if str(TypeOfWidth) == "Valley Bottom" :
    nstep = 8
if str(TypeOfWidth) == "Active Channel" :
    nstep = 9

if str(DeleteTF) == "false" :
    nstep+=-1
ncurrentstep=1



#===============================================================================
# CODING
#===============================================================================
    ###########################
    ### Valley bottom width ###
    ###########################
if str(TypeOfWidth) == "Valley Bottom" : 
    #/conversion of the polygon into a polyline
    arcpy.AddMessage("Converting to line - Step " + str(ncurrentstep) + "/" + str(nstep))
    PolygonToLine = arcpy.FeatureToLine_management(Polygon, "%ScratchWorkspace%\\PolygonToLine", "", "ATTRIBUTES")

    ncurrentstep+=1
    arcpy.AddMessage("Up to date the \"Shape_Length\" field - Step " + str(ncurrentstep) + "/" + str(nstep))
    UPD_SL.UpToDateShapeLengthField(PolygonToLine)

    #/disaggregation of the polygon boundaries
    ncurrentstep+=1
    arcpy.AddMessage("Splitting the Polygon contour - Step " + str(ncurrentstep) + "/" + str(nstep))
    SplitLine = dS.SLEM(PolygonToLine, DisaggregationStepForWidth, "%ScratchWorkspace%\\SplitLine", ScratchW, "true")
    
    #/calculation of the valley bottom width
    ncurrentstep+=1
    arcpy.AddMessage("Converting to points - Step " + str(ncurrentstep) + "/" + str(nstep))
    SplitLineToPoints = arcpy.FeatureVerticesToPoints_management(SplitLine, "%ScratchWorkspace%\\SplitLineToPoints","MID")
    
    ncurrentstep+=1
    arcpy.AddMessage("ProxyTable between Points and Centerline - Step " + str(ncurrentstep) + "/" + str(nstep))
    ProxyTable = arcpy.GenerateNearTable_analysis(SplitLineToPoints, Centerline, "ProxyTable", "", "LOCATION", "NO_ANGLE", "")
    
    ncurrentstep+=1
    arcpy.AddMessage("Generating XY layer - Step " + str(ncurrentstep) + "/" + str(nstep))
    SpatialRef = arcpy.Describe(Polygon).spatialReference
    ProxyPtsTEMP = arcpy.MakeXYEventLayer_management("ProxyTable", "NEAR_X", "NEAR_Y", "ProxyPtsTEMP", SpatialRef, "")

    ncurrentstep+=1
    arcpy.AddMessage("Final point shapefile with width information - Step " + str(ncurrentstep) + "/" + str(nstep))
    WidthPts = arcpy.CopyFeatures_management(ProxyPtsTEMP, Output)
    arcpy.AddField_management(WidthPts, "Width", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.CalculateField_management(WidthPts, "Width", "!NEAR_DIST!*2", "PYTHON_9.3", "")
    arcpy.DeleteField_management(WidthPts, "NEAR_DIST")

    #/deleting residual fields
    try :
        arcpy.DeleteField_management(WidthPts, ["IN_FID"])
    except : 
        pass


    #===============================================================================
    # DELETING TEMPORARY FILES
    #=============================================================================== 
    if str(DeleteTF) == "true" :
        ncurrentstep+=1
        arcpy.AddMessage("Deleting temporary files - Step " + str(ncurrentstep) + "/" + str(nstep))
        arcpy.Delete_management(PolygonToLine)
        arcpy.Delete_management(SplitLine)
        arcpy.Delete_management(SplitLineToPoints)
        arcpy.Delete_management(ProxyTable)








    ###########################
    ### Active channel width ##
    ###########################
if str(TypeOfWidth) == "Active Channel" : 
    #/disaggregation of the centerline
    arcpy.AddMessage("Splitting the Centerline - Step " + str(ncurrentstep) + "/" + str(nstep))
    SplitCenterline = dS.SLEM(Centerline, DisaggregationStepForWidth, "%ScratchWorkspace%\\SplitCenterline", ScratchW, "true")
    
    #/creation of thiessen polygons
    ncurrentstep+=1
    arcpy.AddMessage("Converting to points - Step " + str(ncurrentstep) + "/" + str(nstep))
    SplitCenterlineToPoints = arcpy.FeatureVerticesToPoints_management(SplitCenterline, "%ScratchWorkspace%\\SplitCenterlineToPoints","MID")
    
    ncurrentstep+=1
    arcpy.AddMessage("Create Thiessen polygons - Step  " + str(ncurrentstep) + "/" + str(nstep))
    ThiessenPoly = arcpy.CreateThiessenPolygons_analysis(SplitCenterlineToPoints, "%ScratchWorkspace%\\ThiessenPoly", "ALL")
    
    #/creation of active channel transects
    ncurrentstep+=1
    arcpy.AddMessage("Converting to line - Step  " + str(ncurrentstep) + "/" + str(nstep)) 
    PolygonToLine = arcpy.FeatureToLine_management(ThiessenPoly, "%ScratchWorkspace%\\PolygonToLine", "", "ATTRIBUTES")

    ncurrentstep+=1
    arcpy.AddMessage("Clip Line with Polygon - Step  " + str(ncurrentstep) + "/" + str(nstep)) 
    LineWidth_TEMP = arcpy.Intersect_analysis([PolygonToLine, Polygon], "%ScratchWorkspace%\\LineWidth_TEMP", "ALL", "", "LINE")
    arcpy.DeleteIdentical_management(LineWidth_TEMP, ["Shape_Length"])
      
    ncurrentstep+=1
    arcpy.AddMessage("Up to date the \"Shape_Length\" field - Step " + str(ncurrentstep) + "/" + str(nstep))
    UPD_SL.UpToDateShapeLengthField(LineWidth_TEMP)
    
    #/calculation of the active channel width
    arcpy.AddField_management(LineWidth_TEMP, "Width", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.CalculateField_management(LineWidth_TEMP, "Width", "!shape.length!", "PYTHON_9.3", "")

    LineWidth = arcpy.Dissolve_management(LineWidth_TEMP, "%ScratchWorkspace%\\LineWidth", ["FID_PolygonToLine"], [["Width", "SUM"]])
    arcpy.AddField_management(LineWidth, "Width", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.CalculateField_management(LineWidth, "Width", "!SUM_Width!", "PYTHON_9.3", "")


    #/transfert of the width values into the output set of points
    ncurrentstep+=1
    arcpy.AddMessage("Transfering width information into the points of the split centerline - Step " + str(ncurrentstep) + "/" + str(nstep))
        # Spatial Join between LineWidth and ThiessenPoly
    fieldmappings = arcpy.FieldMappings()
    fieldmappings.addTable(LineWidth)
    fieldmappings.addTable(ThiessenPoly)
    
    MetricFieldIndex = fieldmappings.findFieldMapIndex("Width")
    fieldmap = fieldmappings.getFieldMap(MetricFieldIndex)       
    fieldmap.mergeRule = "mean"
    fieldmappings.replaceFieldMap(MetricFieldIndex, fieldmap)
    
    JoinThiessen = arcpy.SpatialJoin_analysis(ThiessenPoly, LineWidth, "%ScratchWorkspace%\\JoinThiessen", "JOIN_ONE_TO_ONE", "KEEP_ALL", fieldmappings)
    
        # Spatial Join between previous JoinThiessen and SplitCenterlineToPoints
    fieldmappings = arcpy.FieldMappings()
    fieldmappings.addTable(JoinThiessen)
    fieldmappings.addTable(SplitCenterlineToPoints)
    
    MetricFieldIndex = fieldmappings.findFieldMapIndex("Width")
    fieldmap = fieldmappings.getFieldMap(MetricFieldIndex)       
    fieldmap.mergeRule = "mean"
    fieldmappings.replaceFieldMap(MetricFieldIndex, fieldmap)
    
    Width = arcpy.SpatialJoin_analysis(SplitCenterlineToPoints, JoinThiessen, Output, "JOIN_ONE_TO_ONE", "KEEP_ALL", fieldmappings, "WITHIN")

    #/removing of the residual fields
    ncurrentstep+=1
    arcpy.AddMessage("Removing the residual fields created during the Spatial Join - Step " + str(ncurrentstep) + "/" + str(nstep))
    fieldnamesPoints = [f.name for f in arcpy.ListFields(SplitCenterlineToPoints)]
    fieldnamesWidth = [f.name for f in arcpy.ListFields(Width)]
    for field in fieldnamesWidth :
        if field not in fieldnamesPoints and field != "Width" :
            try : 
                arcpy.DeleteField_management(Width, str(field))
            except :
                continue

    
    #===============================================================================
    # DELETING TEMPORARY FILES
    #=============================================================================== 
    if str(DeleteTF) == "true" :
        ncurrentstep+=1
        arcpy.AddMessage("Deleting temporary files - Step " + str(ncurrentstep) + "/" + str(nstep))
        arcpy.Delete_management(SplitCenterline)
        arcpy.Delete_management(SplitCenterlineToPoints)
        arcpy.Delete_management(ThiessenPoly)
        arcpy.Delete_management(PolygonToLine)
        arcpy.Delete_management(LineWidth_TEMP)
        arcpy.Delete_management(LineWidth)
        arcpy.Delete_management(JoinThiessen)
