# -*- coding: utf-8 -*-

#'''
#Created on 21 fev. 2013
#Last update on 07 fev. 2014

#@author: Clement Roux

#@contact: samuel.dunesme@ens-lyon.fr
#
#          15 Parvis Ren� Descartes, BP 7000, 69342 Lyon Cedex 07, France
         
#@note: For each use of the FluvialCorridor toolbox leading to a publication, report, presentation or any other
#       document, please refer the following article :
#       Roux, C., Alber, A., Bertrand, M., Vaudor, L., Piegay, H., submitted. "FluvialCorridor": A new ArcGIS 
#       package for multiscale riverscape exploration. Geomorphology
       
#@summary: def__ScratchWPathName is an open-source python and arcPy code.
#          This script extract the path of the ArcGIS default geodatabase. 
          
#'''


# Import of required librairies
import arcpy
from arcpy import env

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True



#===============================================================================
# CODING
#===============================================================================
def ScratchWPathName ():
    SW = env.scratchWorkspace
    SWW = SW.split("\\")
    n = len(SWW)
    ScratchWPathName = str()
    for i in range(0,n-1) :
        ScratchWPathName = ScratchWPathName + SWW[i] + "\\"
    return ScratchWPathName
