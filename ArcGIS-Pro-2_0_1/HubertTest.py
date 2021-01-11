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
       
@summary: HubertTest is an open-source python and arcPy code.
          This script uses the def__PackHubert function in order to proceed the statistical test of Hubert over
          one metric of a characterized DGO-scale database. The attribute table of the DGO database is exported
          into a .txt file. The test is then run and results of the segmentation are finally transferred into
          the attribute table of the output DGO database.          
          
'''


# Import of required librairies
import arcpy
from arcpy import env
import os
import def__ScratchWPathName as SWPN
import def__Export as Ext
import def__PackHubert as dPH

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

# Inputs
table = arcpy.GetParameterAsText(0)
metric = arcpy.GetParameterAsText(1)
alpha = arcpy.GetParameterAsText(2)
setNoData = arcpy.GetParameterAsText(3)
outHReach = arcpy.GetParameterAsText(4)

# Dervied variable from inputs
alpha = float(alpha.replace(',', '.'))
ScratchW = SWPN.ScratchWPathName ()

# Number of steps
nstep = 6
ncurrentstep=1



#===============================================================================
# CODING
#===============================================================================
#/setting of the NoData values
if setNoData :
    if setNoData.find(".") == -1 :
        noData = str(setNoData)+".0"
    else :
        noData = str(setNoData).replace(',','.')
else : 
    noData = "None"

#/sorting of the DGO-scale database
arcpy.AddMessage("Sorting the attribute table - Step " + str(ncurrentstep) + "/" + str(nstep))
SortedTable = arcpy.Sort_management(table, "%ScratchWorkspace%\\outHReach", [["Order_ID","ASCENDING"],["Rank_UGO","ASCENDING"],["Distance","ASCENDING"]])

#/export of the attribute table of DGO-scale database into a. txt file  
ncurrentstep+=1
arcpy.AddMessage("Exporting the attribute table into 'ExportTable.txt' - Step " + str(ncurrentstep) + "/" + str(nstep))
Ext.Export(SortedTable,ScratchW,"ExportTable")  

#/extraction of lists from the .txt file
    # 1- one with the OBJECTID of each DGO
    # 2- one with the Order_ID of each DGO
    # 3- one with the Rank_UGO of each DGO
    # 4- one with the metric value of each DGO
ncurrentstep+=1
arcpy.AddMessage("Writing the OBJECTID, Order_ID, Rank_UGO and " + str(metric) + " fields into the .txt file - Step " + str(ncurrentstep) + "/" + str(nstep))
fichier = open(ScratchW + "\\ExportTable.txt", 'r')
ObjectID = []
Order_ID = []
Rank_UGO = []
Metric = []

head = fichier.readline().split('\n')[0].split(';')
iObjectID = head.index("OBJECTID")
iOrder_ID = head.index("Order_ID")
iRank_UGO = head.index("Rank_UGO")
iMetric = head.index(metric)

for l in fichier:
    if str(l.split('\n')[0].split(';')[iMetric]) == noData or str(l.split('\n')[0].split(';')[iMetric]) == "None" :
        ObjectID.append(int(l.split('\n')[0].split(';')[iObjectID]))
        Order_ID.append(int(l.split('\n')[0].split(';')[iOrder_ID]))
        Rank_UGO.append(int(l.split('\n')[0].split(';')[iRank_UGO]))
        Metric.append(None)
    else: 
        ObjectID.append(int(l.split('\n')[0].split(';')[iObjectID]))
        Order_ID.append(int(l.split('\n')[0].split(';')[iOrder_ID]))
        Rank_UGO.append(int(l.split('\n')[0].split(';')[iRank_UGO]))
        Metric.append(float(l.split('\n')[0].split(';')[iMetric].replace(',','.')))
        
#/counting of the number of segments (Rank_UGO) and identification of their boundaries        
ncurrentstep+=1
arcpy.AddMessage("Counting the number of Rank_UGO in the network - Step " + str(ncurrentstep) + "/" + str(nstep))
NbUGO = 1         #number of segment
elem = [0]        #list with the start and end OID of each UGO
UGO = Rank_UGO[0]

for i in range (0, len(Rank_UGO)) :
    if Rank_UGO[i] != UGO  :
        UGO = Rank_UGO[i]
        NbUGO+=1
        elem.append(ObjectID[i]-1)
        continue
    if i == 0 and Metric[i] == None :
        continue
    elif Rank_UGO[i] == UGO and Metric[i-1] != None and Metric[i] == None :
        elem.append(ObjectID[i]-1)
    elif Rank_UGO[i] == UGO and Metric[i-1] == None and Metric[i] != None and i != 0 :
        elem.append(ObjectID[i]-1)
             
elem.append(len(Rank_UGO))


#/Hubert test
    # for each segment, we process the Hubert Test
breaks = []     #List with the discontinuities
                #    - it contains as many elements as segments
                #    - each element contains :
                #        1. a list of the discontinuities position (identified by the Hubert Test.
                #        2. an information about the accuracy of the segmentation proposed by the Hubert Test.
                #           For each homogeneous reach, the resulting metric value is the mean of DGO metric 
                #           values contained in the homogeneous reach. 

HReach = []     #List with the estimated model. It contains :
                #    - all the disaggregated reaches with their own metric value
                #    - the value estimated by the Hubert Test : 'AGO_Val'
                #    - a unique id, 'Rank_AGO', related to the homogeneous reach
                #It is a .txt file which will be used to create the output shapefile. 

ncurrentstep+=1
arcpy.AddMessage("Processing the Hubert Test for each segment ('Rank_UGO') - Step " + str(ncurrentstep) + "/" + str(nstep))
UGO = Rank_UGO[0]
for i in range(0, len(elem)-1) :
    if Rank_UGO[elem[i]] != UGO or i == 0:
        UGO = Rank_UGO[elem[i]]
        arcpy.AddMessage("        Hubert Test in processing : UGO " + str(UGO) + "/" + str(NbUGO))
    if Metric[elem[i]:elem[i+1]][0] == None :
        breaks.append([[elem[i], elem[i+1]],[None]])
        HReach [breaks[i][0][0]:breaks[i][0][-1]] = [None]*len(Metric[elem[i]:elem[i+1]])
    else :
        breaks.append(dPH.Hubert_segmentation(Metric[elem[i]:elem[i+1]], alpha))
        breaks[i][0][:] = [x+elem[i] for x in breaks[i][0]]
        model = dPH.model_signal(Metric[breaks[i][0][0]:breaks[i][0][-1]], breaks[i][0])
        HReach [breaks[i][0][0]:breaks[i][0][-1]] = model[:]




#/back to ArcGIS : transfer of Rank_AGO and AGO_Val fields into the DGO-scale database 
ncurrentstep+=1
arcpy.AddMessage("Transferring the 'Rank_AGO' and  'AGO_Val' - Step " + str(ncurrentstep) + "/" + str(nstep))
arcpy.AddField_management(SortedTable, "Rank_AGO", "SHORT")
arcpy.AddField_management(SortedTable, "AGO_Val", "FLOAT")

p=0
rows1 = arcpy.UpdateCursor(SortedTable)
rows2 = arcpy.SearchCursor(SortedTable)
line2 = next(rows2)
AGOval = HReach[p]
AGORankUGO = Rank_UGO[p]
HReachID = 1

for line1 in rows1 :
    line2 = next(rows2)
    line1.Rank_AGO = HReachID
    line1.AGO_Val = HReach[p]
    rows1.updateRow(line1)
    p+=1
    if p < len(HReach) :
        if HReach[p] != AGOval or Rank_UGO[p] != AGORankUGO  :
            AGOval = HReach[p]
            AGORankUGO= Rank_UGO[p]
            HReachID+=1








#===============================================================================
# DELETING TEMPORARY FILES
#=============================================================================== 
arcpy.CopyFeatures_management(SortedTable, outHReach)
arcpy.Delete_management(SortedTable)
