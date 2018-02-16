# -*- coding: utf-8 -*-

#Created on 21 fev. 2013
#Last update on 07 fev. 2014

#@author: Clement Roux

#@contact: aurelie.antonio@ens-lyon.fr
#          CNRS - UMR5600 Environnement Ville Societe
#          15 Parvis René Descartes, BP 7000, 69342 Lyon Cedex 07, France
        
#@note: For each use of the FluvialCorridor toolbox leading to a publication, report, presentation or any other
#       document, please refer the following article :
#       Roux, C., Alber, A., Bertrand, M., Vaudor, L., Piegay, H., submitted. "FluvialCorridor": A new ArcGIS
#      package for multiscale riverscape exploration. Geomorphology
      
#@summary: def__UpToDateShapeLengthField is an open-source python and arcPy code.
#          Some GIS operations modifies the Shape_Length field names, preventing further generic functions.
#          Thus, this script is called in most of the FluvialCorridor modules to update the Shape_Length field.


# Import of required librairies
import arcpy
from arcpy import env
import math
import os

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True



#===============================================================================
# CODING
#===============================================================================
def UpToDateShapeLengthField (a):

    x = 0
    fieldnames = [f.name for f in arcpy.ListFields(a)]
    for i in range(0, len(fieldnames)) :
        if fieldnames[i] == "Shape_Length" :
            x = 1  
    if x == 0 :
        arcpy.AddField_management(a, "Shape_Length", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        try :
            arcpy.CalculateField_management(a, "Shape_Length", "!shape.length!", "PYTHON_9.3", "")
        except :
            arcpy.CalculateField_management(a, "Shape_Length", "!forme.length!", "PYTHON_9.3", "")
    
    return a
