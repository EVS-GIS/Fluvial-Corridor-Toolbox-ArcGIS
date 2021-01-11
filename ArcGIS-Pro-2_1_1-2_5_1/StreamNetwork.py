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
       
#@summary: Streamnetwork is an open-source python and arcPy code.
#          This script works with a DEM or derived raster layers and provides a related hydrographic network
#          layer. The module can be launched from a raw DEM (a streamburning step is then available thanks to
#          the ArcHydroTools ESRI package) or from derived rasters such as the flow direction or flow accumulation
#          rasters.
          
#'''


# Import of required librairies
import arcpy
from arcpy.sa import *
import os
import def__UpToDateShapeLengthField as UPD_SL 

# AA
import archydro 
arcpy.CheckOutExtension('Spatial')

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

# Inputs
Version = arcpy.GetParameterAsText(0)
StepDEM = arcpy.GetParameterAsText(1)
IncludeStreamBurning = arcpy.GetParameterAsText(2)
Dir = arcpy.GetParameterAsText(3)
UserDEM = arcpy.GetParameterAsText(4)
NetworkForNurning = arcpy.GetParameterAsText(5)
NumberOfCellsForStreamBuffer = arcpy.GetParameterAsText(6)
SmoothDropInZUnits = arcpy.GetParameterAsText(7)
SharpDropinZUnits = arcpy.GetParameterAsText(8)
ThresholdDrainage = arcpy.GetParameterAsText(9)
Output = arcpy.GetParameterAsText(10)
KeepRasters = arcpy.GetParameterAsText(11)
DeleteTF = arcpy.GetParameterAsText(12)

# Dervied variable from inputs
ThresholdDrainage = float(ThresholdDrainage.replace(',', '.'))

# Number of steps
if str(StepDEM) == "Original DEM" :
    nstep = 6
if str(StepDEM) == "Burned DEM" :
    nstep = 6
if str(StepDEM) == "Filled DEM" :
    nstep = 5
if str(StepDEM) == "Flow Dir raster" :
    nstep = 4
if str(StepDEM) == "Flow Acc raster" :
    nstep = 3

if str(DeleteTF) == "true" :
    nstep+=1
ncurrentstep=1



#===============================================================================
# CODING
#===============================================================================
#/extraction of the flow accumulation raster ...
if str(StepDEM) == "Original DEM" :
    if str(IncludeStreamBurning) == "true" :
        nstep+=1
        arcpy.AddMessage("Burning the DEM - Step " + str(ncurrentstep) + "/" + str(nstep))
        (path, name) = os.path.split(UserDEM)
        out = os.path.join(path, "BurnedDEM")
        CopyNetworkForBurning = arcpy.CopyFeatures_management(NetworkForNurning, "%ScratchWorkspace%\\CopyNetworkForBurning")
        FLOATUserDEM = Float(UserDEM)
        FLOATUserDEM.save(str(path) + "\\FLOATUserDEM")
        #DEM = arcpy.gp.DEMReconditioning_archydro(FLOATUserDEM, CopyNetworkForBurning, NumberOfCellsForStreamBuffer, SmoothDropInZUnits, SharpDropinZUnits, out, "NEGATIVE_NO")
 
        #AA
        oProcessor = archydro.demreconditioning.DEMReconditioning()
        oProcessor.bCallFromPYT = False
        params = (FLOATUserDEM, CopyNetworkForBurning, NumberOfCellsForStreamBuffer, SmoothDropInZUnits, SharpDropinZUnits, out, "NEGATIVE_NO")
        str_defres = oProcessor.execute(params, None)
        DEM = arcpy.Copy_management(out, "%ScratchWorkspace%\\BurnedDEM")
        
                 
        ncurrentstep+=1
    elif str(IncludeStreamBurning) == "false" :
        DEM = UserDEM
        

    arcpy.AddMessage("Filling the DEM - Step " + str(ncurrentstep) + "/" + str(nstep))
    FilledDEM = arcpy.gp.Fill_sa(DEM, "%ScratchWorkspace%\\FilledDEM")
    ncurrentstep+=1
    arcpy.AddMessage("Generating the Flow Direction raster - Step " + str(ncurrentstep) + "/" + str(nstep))
    FlowDir = arcpy.gp.FlowDirection_sa(FilledDEM, "%ScratchWorkspace%\\FlowDirRaster", "NORMAL", "%ScratchWorkspace%\\FlowDirOutput")
    arcpy.Delete_management("%ScratchWorkspace%\\FlowDirOutput")
    ncurrentstep+=1
    arcpy.AddMessage("Generating the Flow Accumulation raster - Step " + str(ncurrentstep) + "/" + str(nstep))
    FlowAcc = arcpy.gp.FlowAccumulation_sa(FlowDir, "%ScratchWorkspace%\\FlowAccRaster", "", "FLOAT")

## From the Burned DEM
if str(StepDEM) == "Burned DEM" : 
    arcpy.AddMessage("Filling the DEM - Step " + str(ncurrentstep) + "/" + str(nstep))
    FilledDEM = arcpy.gp.Fill_sa(UserDEM, "%ScratchWorkspace%\\FilledDEM")
    ncurrentstep+=1
    arcpy.AddMessage("Generating the Flow Direction raster - Step " + str(ncurrentstep) + "/" + str(nstep))
    FlowDir = arcpy.gp.FlowDirection_sa(FilledDEM, "%ScratchWorkspace%\\FlowDirRaster", "NORMAL", "%ScratchWorkspace%\\FlowDirOutput")
    arcpy.Delete_management("%ScratchWorkspace%\\FlowDirOutput")
    ncurrentstep+=1
    arcpy.AddMessage("Generating the Flow Accumulation raster - Step " + str(ncurrentstep) + "/" + str(nstep))
    FlowAcc = arcpy.gp.FlowAccumulation_sa(FlowDir, "%ScratchWorkspace%\\FlowAccRaster", "", "FLOAT")

## From the Filled DEM
if str(StepDEM) == "Filled DEM" :
    arcpy.AddMessage("Generating the Flow Direction raster - Step " + str(ncurrentstep) + "/" + str(nstep))
    FlowDir = arcpy.gp.FlowDirection_sa(UserDEM, "%ScratchWorkspace%\\FlowDirRaster", "NORMAL", "%ScratchWorkspace%\\FlowDirOutput")
    arcpy.Delete_management("%ScratchWorkspace%\\FlowDirOutput")
    ncurrentstep+=1
    arcpy.AddMessage("Generating the Flow Accumulation raster - Step " + str(ncurrentstep) + "/" + str(nstep))
    FlowAcc = arcpy.gp.FlowAccumulation_sa(FlowDir, "%ScratchWorkspace%\\FlowAccRaster", "", "FLOAT")

## From the Flow Direction raster
if str(StepDEM) == "Flow Dir raster" :
    arcpy.AddMessage("Generating the Flow Accumulation raster - Step " + str(ncurrentstep) + "/" + str(nstep))
    FlowDir = UserDEM
    FlowAcc = arcpy.gp.FlowAccumulation_sa(UserDEM, "%ScratchWorkspace%\\FlowAccRaster", "", "FLOAT")

## From the Flow Accumulation raster
if str(StepDEM) == "Flow Acc raster" :
    ncurrentstep = 0
    FlowDir = Dir
    FlowAcc = UserDEM

#/application of a drainage area threshold
CellS = arcpy.GetRasterProperties_management(UserDEM, "CELLSIZEX")
CellA = float(str(CellS))*float(str(CellS))/1000000
nbCell = float(str(ThresholdDrainage))/CellA
Expression = "\"Value\" >= " + str(int(nbCell))
ncurrentstep+=1
arcpy.AddMessage("Thresholding : keep cells with a drainage area >= " + str(ThresholdDrainage) + "km2 - Step " + str(ncurrentstep) + "/" + str(nstep))
ThresholdStep = arcpy.gp.Con_sa(FlowAcc, FlowAcc, "%ScratchWorkspace%\\ThresholdStep", "", Expression)

#/linking of the streamnetwork
ncurrentstep+=1
arcpy.AddMessage("Linking Stream Network - Step " + str(ncurrentstep) + "/" + str(nstep))
StreamLink = arcpy.gp.StreamLink_sa(ThresholdStep, FlowDir, "%ScratchWorkspace%\\StreamLink")

#/conversion of the raster streamnetwork into a polyline layer
ncurrentstep+=1
arcpy.AddMessage("Converting into a polyline feature - Step " + str(ncurrentstep) + "/" + str(nstep))
Network = arcpy.gp.StreamToFeature_sa(StreamLink, FlowDir, Output, "NO_SIMPLIFY")

#/updating fields
try :
    UPD_SL.UpToDateShapeLengthField(Network)
except :
    try :
        arcpy.AddField_management(Network, "Length", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(Network, "Length", "!shape.length!", "PYTHON_9.3", "")
    except :
        pass

try :
    arcpy.DeleteField_management(Network, ["GRID_CODE"])
except :
    pass








#===============================================================================
# DELETING TEMPORARY FILES
#=============================================================================== 
if str(KeepRasters) == "false" :
    if str(StepDEM) == "Original DEM" :
        if str(IncludeStreamBurning) == "true" :
            arcpy.Delete_management(DEM)
        arcpy.Delete_management(FilledDEM)
        arcpy.Delete_management(FlowDir)
        arcpy.Delete_management(FlowAcc)
    if str(StepDEM) == "Burned DEM" : 
        arcpy.Delete_management(FilledDEM)
        arcpy.Delete_management(FlowDir)
        arcpy.Delete_management(FlowAcc)
    if str(StepDEM) == "Filled DEM" :
        arcpy.Delete_management(FlowDir)
        arcpy.Delete_management(FlowAcc)
    if str(StepDEM) == "Flow Dir raster" :
        arcpy.Delete_management(FlowAcc)

    
if str(DeleteTF) == "true" :
    ncurrentstep+=1
    arcpy.AddMessage("Deleting temporary files - Step " + str(ncurrentstep) + "/" + str(nstep))
    if str(StepDEM) == "Original DEM" and str(IncludeStreamBurning) == "true" :
        arcpy.Delete_management(CopyNetworkForBurning)
        arcpy.Delete_management(str(path) + "\\FLOATUserDEM")
    arcpy.Delete_management(ThresholdStep)
    arcpy.Delete_management(StreamLink)
