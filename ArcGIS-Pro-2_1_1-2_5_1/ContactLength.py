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
       
#@summary: ContactLength is an open-source python and arcPy code.
#          This script carries out the assessment of the contact length along a river course and within an 
#          alluvial valley. The contact length refers to the ecotone concept; i.e. the boundary shared by 
#          to adjacent ecosystems. This tool extract the contact length of the active channel for each 
#          valley segment.
          
#'''


# Import of required librairies
import arcpy
from arcpy import env
import def__UpToDateShapeLengthField as UPD_SL
import def__ScratchWPathName as SWPN

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

# Inputs
ActiveChannel = arcpy.GetParameterAsText(0)
DisaggregatedValleyBottom = arcpy.GetParameterAsText(1)
Output = arcpy.GetParameterAsText(2)
DeleteTF = arcpy.GetParameterAsText(3)

# Dervied variable from inputs
ScratchW = SWPN.ScratchWPathName ()

# Number of steps
if str(DeleteTF) == "true" :
    nstep = 7
else :
    nstep = 6
ncurrentstep = 1



#===============================================================================
# CODING
#===============================================================================
#/conversion of the active channel polygons to lines
arcpy.AddMessage("Converting active channel to lines - Step " + str(ncurrentstep) + "/" + str(nstep)) 
ACtoLine = arcpy.FeatureToLine_management(ActiveChannel, "%ScratchWorkspace%\\ACtoLine", "", "ATTRIBUTES")

ncurrentstep+=1
arcpy.AddMessage("Deleting identical - Step " + str(ncurrentstep) + "/" + str(nstep))
arcpy.DeleteIdentical_management(ACtoLine, ["Shape_Length"])


#/processing the contact length
ncurrentstep+=1
arcpy.AddMessage("Intersecting active channel lines with the disaggregated valley bottom - Step " + str(ncurrentstep) + "/" + str(nstep)) 
Intersect = arcpy.Intersect_analysis([DisaggregatedValleyBottom, ACtoLine], "%ScratchWorkspace%\\Intersect", "ALL", "", "LINE")

ncurrentstep+=1
arcpy.AddMessage("Up to date the \"Shape_Length\" field - Step " + str(ncurrentstep) + "/" + str(nstep))
UPD_SL.UpToDateShapeLengthField(Intersect)

arcpy.AddField_management(Intersect, "contactL", "DOUBLE", "", "9", "", "" , "NULLABLE", "NON_REQUIRED", "")
arcpy.CalculateField_management(Intersect, "contactL", "!Shape_Length!", "PYTHON_9.3", "")



#/transfer of the contact length values into the disaggregated valley bottom
ncurrentstep+=1
arcpy.AddMessage("Transferring the information thanks to a Spatial join - Step " + str(ncurrentstep) + "/" + str(nstep))
fieldmappings = arcpy.FieldMappings()
fieldmappings.addTable(Intersect)
fieldmappings.addTable(DisaggregatedValleyBottom)

MetricFieldIndex = fieldmappings.findFieldMapIndex("contactL")
fieldmap = fieldmappings.getFieldMap(MetricFieldIndex)       
fieldmap.mergeRule = "sum"
fieldmappings.replaceFieldMap(MetricFieldIndex, fieldmap)

Transfer = arcpy.SpatialJoin_analysis(DisaggregatedValleyBottom, Intersect, Output, "JOIN_ONE_TO_ONE", "KEEP_ALL", fieldmappings, "CONTAINS")


#/removing of the residual fields
ncurrentstep+=1
arcpy.AddMessage("Removing the residual fields - Step " + str(ncurrentstep) + "/" + str(nstep))
fieldnamesfromFC = [f.name for f in arcpy.ListFields(Transfer)]
fieldnamestoFC = [f.name for f in arcpy.ListFields(DisaggregatedValleyBottom)]
for field in fieldnamesfromFC :
    if field not in fieldnamestoFC and field != "contactL" :
        try :
            arcpy.DeleteField_management(Transfer, str(field))
        except :
            continue








#===============================================================================
# DELETING TEMPORARY FILES
#===============================================================================
if str(DeleteTF) == "true" :
    ncurrentstep+=1
    arcpy.AddMessage("Deleting temporary files - Step " + str(ncurrentstep) + "/" + str(nstep))
    arcpy.Delete_management(ACtoLine)
    arcpy.Delete_management(Intersect)
