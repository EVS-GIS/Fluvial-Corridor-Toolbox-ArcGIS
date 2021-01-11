# -*- coding: utf-8 -*-

'''
Created on 21 fev. 2013
Last update on 07 fev. 2014

@author: Clement Roux

@contact: samuel.dunesme@ens-lyon.fr
          CNRS - UMR5600 Environnement Ville Societe
          15 Parvis Ren� Descartes, BP 7000, 69342 Lyon Cedex 07, France
         
@note: For each use of the FluvialCorridor toolbox leading to a publication, report, presentation or any other
       document, please refer the following article :
       Roux, C., Alber, A., Bertrand, M., Vaudor, L., Piegay, H., submitted. "FluvialCorridor": A new ArcGIS 
       package for multiscale riverscape exploration. Geomorphology
       
@summary: def__Export is an open-source python and arcPy code.
          This script enables to write the attribute table of an ArcGIS layer into a .txt file.
          
'''


# Import of required librairies
import arcpy
from arcpy import env

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True



#===============================================================================
# CODING
#===============================================================================
def Export (inFC, ScratchW, outTableName):
    fields = arcpy.ListFields(inFC)
    rows = arcpy.SearchCursor(inFC)
    i = 1
    f = open(ScratchW + "\\" + outTableName + ".txt",'w')
    for field in fields:
        if i < len(fields):
            f.write('%s;' % field.name)
            i += 1
        else:
            f.write('%s\n' % field.name)
    
    for row in rows:
        i = 1
        for field in fields:
            if i < len(fields):
                f.write('%s;' % row.getValue(field.name))
                i += 1
            else:
                f.write('%s\n' % row.getValue(field.name))
    del rows
    f.close
