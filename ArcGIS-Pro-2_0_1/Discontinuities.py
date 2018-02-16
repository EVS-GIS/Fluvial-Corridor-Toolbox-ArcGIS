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
       
@summary: Discontinuities is an open-source python and arcPy code.
          This script provides spatial discontinuities of a DGO or AGO-scale database. Between each homogeneous 
          reach, a break point is created containing the downstream ratio of a given metric. The input AGO-scale
          database can be either a polygon (e.g. valley bottom) or a polyline (e.g. hydrographic network).  
          
'''


# Import of required librairies
import arcpy
from arcpy import env
import os
import def__ScratchWPathName as SWPN

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

# Inputs
TypeOfEntity = arcpy.GetParameterAsText(0)
TypeOfGO = arcpy.GetParameterAsText(1)
InputFC = arcpy.GetParameterAsText(2)
Metric = arcpy.GetParameterAsText(3)
Centerline = arcpy.GetParameterAsText(4)
setNoData = arcpy.GetParameterAsText(5)
OutputFC = arcpy.GetParameterAsText(6)
DeleteTF = arcpy.GetParameterAsText(7)

# Dervied variable from inputs
ScratchW = SWPN.ScratchWPathName ()
(pathIN, nameIN) = os.path.split(InputFC)   
(pathOUT, nameOUT) = os.path.split(OutputFC)
(pathRef, nameRef) = os.path.split(Centerline)
name = os.path.splitext(os.path.split(Centerline)[1])[0]

# Number of steps
if str(DeleteTF) == "true" :
    nstep = 5
else :
    nstep = 4
ncurrentstep = 1



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

    
    #######################
    #### Polygon input ####
    #######################
if str(TypeOfEntity) == "Polygon" :
    #/creation of the spatial discontinuities for a DGO-scale database
    if str(TypeOfGO) == "DGO" :
        arcpy.AddMessage("Creating breaks points - Step " + str(ncurrentstep) + "/" + str(nstep)) 
        TEMPinFC = arcpy.CopyFeatures_management(InputFC, "%ScratchWorkspace%\\TEMPinFC")
        Intersect = arcpy.Intersect_analysis([TEMPinFC, Centerline], "%ScratchWorkspace%\\Intersect", "ONLY_FID", "", "POINT")
        arcpy.AddXY_management(Intersect)
        arcpy.DeleteIdentical_management(Intersect, ["POINT_X", "POINT_Y"])
        
        ncurrentstep+=1
        arcpy.AddMessage("Generating near table between break points and the input polygon - Step " + str(ncurrentstep) + "/" + str(nstep)) 
        NearTable_TEMP = arcpy.GenerateNearTable_analysis(Intersect, [TEMPinFC], "%ScratchWorkspace%\\NearTable_TEMP", "0", "NO_LOCATION", "NO_ANGLE", "ALL", "3")
        arcpy.JoinField_management(NearTable_TEMP, "NEAR_FID", TEMPinFC, "OBJECTID", ["Order_ID", "Rank_UGO", "Rank_DGO", "Distance", Metric])
        
        NearTable = arcpy.Sort_management(NearTable_TEMP, "%ScratchWorkspace%\\NearTable", [["IN_FID", "ASCENDING"], ["Distance", "ASCENDING"]])
        arcpy.AddField_management(NearTable, "Ratio", "FLOAT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(NearTable, "Type", "TEXT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(NearTable, "Up_DGO", "SHORT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(NearTable, "Down_DGO", "SHORT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")

    #/creation of the spatial discontinuities for an AGO-scale database
    elif str(TypeOfGO) == "AGO" :
        arcpy.AddMessage("Creating breaks points - Step " + str(ncurrentstep) + "/" + str(nstep)) 
        TEMPinFC = arcpy.Dissolve_management(InputFC, "%ScratchWorkspace%\\TEMPinFC", ["Rank_AGO"], [["Order_ID", "MIN"], ["Rank_UGO", "MIN"], ["Distance", "MIN"], [Metric, "MEAN"]])
        arcpy.AddField_management(TEMPinFC, "Order_ID", "SHORT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(TEMPinFC, "Rank_UGO", "SHORT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(TEMPinFC, "Distance", "FLOAT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(TEMPinFC, Metric, "FLOAT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(TEMPinFC, "Order_ID", "!MIN_Order_ID!", "PYTHON_9.3")
        arcpy.CalculateField_management(TEMPinFC, "Rank_UGO", "!MIN_Rank_UGO!", "PYTHON_9.3")
        arcpy.CalculateField_management(TEMPinFC, "Distance", "!MIN_Distance!", "PYTHON_9.3")
        arcpy.CalculateField_management(TEMPinFC, Metric, "!MEAN_"+str(Metric)+"!", "PYTHON_9.3")
        arcpy.DeleteField_management(TEMPinFC, ["MIN_Order_ID", "MIN_Rank_UGO", "MIN_Distance", "MEAN_"+str(Metric)])
        
        Intersect = arcpy.Intersect_analysis([TEMPinFC, Centerline], "%ScratchWorkspace%\\Intersect", "ONLY_FID", "", "POINT")
        arcpy.AddXY_management(Intersect)
        arcpy.DeleteIdentical_management(Intersect, ["POINT_X", "POINT_Y"])
        
        ncurrentstep+=1
        arcpy.AddMessage("Generating near table between break points and the input polygon - Step " + str(ncurrentstep) + "/" + str(nstep)) 
        NearTable_TEMP = arcpy.GenerateNearTable_analysis(Intersect, [TEMPinFC], "%ScratchWorkspace%\\NearTable_TEMP", "0", "NO_LOCATION", "NO_ANGLE", "ALL", "3")
        arcpy.JoinField_management(NearTable_TEMP, "NEAR_FID", TEMPinFC, "OBJECTID", ["Order_ID", "Rank_UGO", "Distance", "Rank_AGO", Metric])


        NearTable = arcpy.Sort_management(NearTable_TEMP, "%ScratchWorkspace%\\NearTable", [["IN_FID", "ASCENDING"], ["Distance", "ASCENDING"]])
        arcpy.AddField_management(NearTable, "Ratio", "FLOAT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(NearTable, "Type", "TEXT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(NearTable, "Up_AGO", "SHORT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(NearTable, "Down_AGO", "SHORT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")

    #/calculation of the Ratio field ...
    ncurrentstep+=1
    arcpy.AddMessage("Calculating fields into the near table - Step " + str(ncurrentstep) + "/" + str(nstep)) 
    rows1 = arcpy.UpdateCursor(NearTable)
    rows2 = arcpy.UpdateCursor(NearTable)
    line2 = next(rows2)
    nrows = int(str(arcpy.GetCount_management(NearTable)))
    n = 0
    k = 0
    
    #/... for a DGO-scale input
    if str(TypeOfGO) == "DGO" :
        for line1 in rows1 :
            if n >= nrows-1 :
                break
            line2 = next(rows2)
            
            if line1.IN_FID != line2.IN_FID and k == 0 :
                line1.Type = "extreme point"
                line1.Up_DGO = -1
                if line1.Order_ID != 1 :
                    line1.Down_DGO = line1.Rank_DGO
                else : 
                    line1.Down_DGO = -1
                rows1.updateRow(line1)
                k = 0
                n += 1
                continue
            if line1.IN_FID != line2.IN_FID and k == 1 :
                n += 1
                continue 
            if line1.IN_FID == line2.IN_FID :
                if line1.Rank_UGO != line2.Rank_UGO :
                    line1.Up_DGO = -1
                    line1.Down_DGO = -1
                    line1.Type = "confluence"
                    line2.Type = "2"
                    
                    rows1.updateRow(line1)
                    rows2.updateRow(line2)
                    
                if line1.Rank_UGO == line2.Rank_UGO :
                    line2.Type = "contact"
                    
                    line2.Up_DGO = line1.Rank_DGO
                    line2.Down_DGO = line2.Rank_DGO
                    
                    try :
                        if line1.getValue(Metric) != noData and line2.getValue(Metric) != noData :
                            line2.Ratio = line1.getValue(Metric) / line2.getValue(Metric)
                    except : 
                        pass
                    line1.Type = "2"
                    
                    rows1.updateRow(line1)
                    rows2.updateRow(line2)
                k = 1
            n += 1

    #/... for an AGO-scale input
    elif str(TypeOfGO) == "AGO" :
        for line1 in rows1 :
            if n >= nrows-1 :
                break
            line2 = next(rows2)
            
            if line1.IN_FID != line2.IN_FID and k == 0 :
                line1.Type = "extreme point"
                line1.Up_AGO = -1
                if line1.Order_ID != 1 :
                    line1.Down_AGO = line1.Rank_AGO
                else : 
                    line1.Down_AGO = -1
                rows1.updateRow(line1)
                k = 0
                n += 1
                continue
            if line1.IN_FID != line2.IN_FID and k == 1 :
                n += 1
                continue 
            if line1.IN_FID == line2.IN_FID :
                if line1.Rank_UGO != line2.Rank_UGO :
                    line1.Up_AGO = -1
                    line1.Down_AGO = -1
                    line1.Type = "confluence"
                    line2.Type = "2"
                    
                    rows1.updateRow(line1)
                    rows2.updateRow(line2)
                    
                if line1.Rank_UGO == line2.Rank_UGO :
                    line2.Type = "contact"
                    
                    line2.Up_AGO = line1.Rank_AGO
                    line2.Down_AGO = line2.Rank_AGO
                    
                    try :
                        if line1.getValue(Metric) != noData and line2.getValue(Metric) != noData :
                            line2.Ratio = line1.getValue(Metric) / line2.getValue(Metric)
                    except : 
                        pass
                    line1.Type = "2"
                    
                    rows1.updateRow(line1)
                    rows2.updateRow(line2)
                k = 1
            n += 1


          
    #/transfer of the Ratio field and shaping of the spatial discontinuities layer
    ncurrentstep+=1
    arcpy.AddMessage("Transferring fields into the output break points - Step " + str(ncurrentstep) + "/" + str(nstep))       
    NearTableView = arcpy.MakeTableView_management(NearTable, "NearTable_View")
    Selection = arcpy.SelectLayerByAttribute_management(NearTableView, "NEW_SELECTION", "\"Type\" = '2'")
    
    arcpy.DeleteRows_management(Selection)

    if str(TypeOfGO) == "DGO" : 
        arcpy.JoinField_management(Intersect, "OBJECTID", NearTable, "IN_FID", ["Order_ID", "Rank_UGO", "Distance", "Ratio", "Type", "Up_DGO", "Down_DGO", ])
   
    elif str(TypeOfGO) == "AGO" :    
        arcpy.JoinField_management(Intersect, "OBJECTID", NearTable, "IN_FID", ["Order_ID", "Rank_UGO", "Distance", "Ratio", "Type", "Up_AGO", "Down_AGO", ])

    arcpy.DeleteField_management(Intersect, ["FID_TEMPinFC", "FID_"+str(nameRef)])
    try :
        arcpy.DeleteField_management(Intersect, ["POINT_M"])
    except :
        pass
    
    OutputPoints = arcpy.Sort_management(Intersect, OutputFC, [["Order_ID", "ASCENDING"], ["Rank_UGO", "ASCENDING"], ["Distance", "ASCENDING"], ["Type", "ASCENDING"]])
    Make = arcpy.MakeFeatureLayer_management(OutputPoints, "%ScratchWorkspace%\\Make")
    arcpy.SelectLayerByAttribute_management(Make, "NEW_SELECTION", "\"Order_ID\" IS NULL")
    arcpy.DeleteFeatures_management(Make)
    
    try :
        arcpy.DeleteField_management(OutputPoints, ["FID_" + str(name)])
    except :
        pass
    try :
        arcpy.DeleteField_management(OutputPoints, ["FID_" + str(name[0:6])])
    except :
        pass
    try : 
        arcpy.DeleteField_management(OutputPoints, ["Point_Z"])
    except :
        pass
    
    
    
    
    
    
    
    
    ########################
    #### Polyline input ####
    ########################
if str(TypeOfEntity) == "Polyline" :
    #/creation of the spatial discontinuities for a DGO-scale database
    if str(TypeOfGO) == "DGO" :
        arcpy.AddMessage("Creating breaks points - Step " + str(ncurrentstep) + "/" + str(nstep))
        TEMPinFC = arcpy.CopyFeatures_management(InputFC, "%ScratchWorkspace%\\TEMPinFC") 
        Sort = arcpy.Sort_management(TEMPinFC, "%ScratchWorkspace%\\Sort", [["Order_ID", "ASCENDING"], ["Rank_UGO", "ASCENDING"], ["Distance", "ASCENDING"]])
    
        OutputPoints = arcpy.FeatureVerticesToPoints_management(Sort, OutputFC, "START")
        
        ncurrentstep+=1
        arcpy.AddMessage("Generating near table between break points and the input linear feature - Step " + str(ncurrentstep) + "/" + str(nstep))
        NearTable = arcpy.GenerateNearTable_analysis(OutputPoints, [TEMPinFC], "%ScratchWorkspace%\\NearTable", "0", "NO_LOCATION", "NO_ANGLE", "ALL", "3")
        arcpy.JoinField_management(NearTable, "NEAR_FID", TEMPinFC, "OBJECTID", ["Order_ID", "Rank_UGO", "Rank_DGO", "Distance", Metric])
        
        arcpy.AddField_management(NearTable, "Ratio", "FLOAT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(NearTable, "Type", "TEXT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(NearTable, "Down_DGO", "LONG", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(NearTable, "Up_DGO_1", "LONG", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(NearTable, "Up_DGO_2", "LONG", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")

    #/creation of the spatial discontinuities for an AGO-scale database
    elif str(TypeOfGO) == "AGO" :
        arcpy.AddMessage("Creating breaks points - Step " + str(ncurrentstep) + "/" + str(nstep)) 
        TEMPinFC = arcpy.Dissolve_management(InputFC, "%ScratchWorkspace%\\TEMPinFC", ["Rank_AGO"], [["Order_ID", "MIN"], ["Rank_UGO", "MIN"], ["Distance", "MIN"], [Metric, "MEAN"]])
        arcpy.AddField_management(TEMPinFC, "Order_ID", "SHORT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(TEMPinFC, "Rank_UGO", "SHORT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(TEMPinFC, "Distance", "FLOAT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(TEMPinFC, Metric, "FLOAT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(TEMPinFC, "Order_ID", "!MIN_Order_ID!", "PYTHON_9.3")
        arcpy.CalculateField_management(TEMPinFC, "Rank_UGO", "!MIN_Rank_UGO!", "PYTHON_9.3")
        arcpy.CalculateField_management(TEMPinFC, "Distance", "!MIN_Distance!", "PYTHON_9.3")
        arcpy.CalculateField_management(TEMPinFC, Metric, "!MEAN_"+str(Metric)+"!", "PYTHON_9.3")
        arcpy.DeleteField_management(TEMPinFC, ["MIN_Order_ID", "MIN_Rank_UGO", "MIN_Distance", "MEAN_"+str(Metric)])
        Sort = arcpy.Sort_management(TEMPinFC, "%ScratchWorkspace%\\Sort", [["Order_ID", "ASCENDING"], ["Rank_UGO", "ASCENDING"], ["Distance", "ASCENDING"]])
    
        OutputPoints = arcpy.FeatureVerticesToPoints_management(Sort, OutputFC, "START")
        
        ncurrentstep+=1
        arcpy.AddMessage("Generating near table between break points and the input linear feature - Step " + str(ncurrentstep) + "/" + str(nstep))
        NearTable = arcpy.GenerateNearTable_analysis(OutputPoints, [Sort], "%ScratchWorkspace%\\NearTable", "0", "NO_LOCATION", "NO_ANGLE", "ALL", "3")
        arcpy.JoinField_management(NearTable, "NEAR_FID", Sort, "OBJECTID", ["Order_ID", "Rank_UGO", "Distance", "Rank_AGO", Metric])
        
        

        arcpy.AddField_management(NearTable, "Ratio", "FLOAT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(NearTable, "Type", "TEXT", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(NearTable, "Down_AGO", "LONG", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(NearTable, "Up_AGO_1", "LONG", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(NearTable, "Up_AGO_2", "LONG", "", "", "", "" , "NULLABLE", "NON_REQUIRED", "")


    #/calculation of the Ratio field ...
    ncurrentstep+=1
    arcpy.AddMessage("Calculating fields into the near table - Step " + str(ncurrentstep) + "/" + str(nstep)) 
    rows1 = arcpy.UpdateCursor(NearTable)
    rows2 = arcpy.UpdateCursor(NearTable)
    rows3 = arcpy.UpdateCursor(NearTable)
    line2 = next(rows2)
    line3 = next(rows3)
    line3 = next(rows3)
    nrows = int(str(arcpy.GetCount_management(NearTable)))
    n = 0
    k = 0
    
    
    #/... for a DGO-scale input
    if str(TypeOfGO) == "DGO" :
        for line1 in rows1 :
            n += 1
            line2 = next(rows2)
            line3 = next(rows3)
            
            if line3.OBJECTID >= nrows :
                
                if k == 2 and line2.IN_FID == line3.IN_FID :
                    line3.Type = "contact"
                    
                    try :
                        if line2.getValue(Metric) != noData and line3.getValue(Metric) != noData :
                            line3.Ratio = line2.getValue(Metric) / line3.getValue(Metric)
                    except :
                        pass
                    
                    l1 = [line2.getValue("Order_ID"),line3.getValue("Order_ID")]
                    l2 = [line2.getValue("Rank_DGO"),line3.getValue("Rank_DGO")]
                    line3.Down_DGO = l2[l1.index(min(l1))]
                    del l2[l1.index(min(l1))]
                    line3.Up_DGO_1 = l2[0]
                    line2.Up_DGO_2 = -1
                    
                    line2.Type = "2"
                    
                    rows2.updateRow(line2)
                    rows3.updateRow(line3)
                
                if k == 1 and line1.IN_FID != line2.IN_FID and line2.IN_FID != line3.IN_FID :
                    line1.Type = "extreme point"
                    line2.Type = "extreme point"
                    line3.Type = "extreme point"
                    
                    line1.Down_DGO = line1.Rank_DGO
                    line2.Down_DGO = line2.Rank_DGO
                    line3.Down_DGO = line3.Rank_DGO
                    
                    line1.Up_DGO_1 = -1
                    line2.Up_DGO_1 = -1
                    line3.Up_DGO_1 = -1
                    
                    line1.Up_DGO_2 = -1
                    line2.Up_DGO_2 = -1
                    line3.Up_DGO_2 = -1
                    
                    rows1.updateRow(line1)
                    rows2.updateRow(line2)
                    rows3.updateRow(line3)
                    
                    
                if k == 3 :
                    line3.Type = "2"
                    rows3.updateRow(line3)
                
                break
    
            if k == 3 or k == 2 : 
                k = k - 1
                continue    
            
            
            if line1.IN_FID == line2.IN_FID and line2.IN_FID == line3.IN_FID :
                line1.Type = "confluence"
                l1 = [line1.getValue("Order_ID"),line2.getValue("Order_ID"),line3.getValue("Order_ID")]
                l2 = [line1.getValue("Rank_DGO"),line2.getValue("Rank_DGO"),line3.getValue("Rank_DGO")]
                line1.Down_DGO = l2[l1.index(min(l1))]
                del l2[l1.index(min(l1))]
                line1.Up_DGO_1 = l2[0]
                line1.Up_DGO_2 = l2[1]
                
                line2.Type ="2"
                line3.Type = "2"
                
                rows1.updateRow(line1)
                rows2.updateRow(line2)
                rows3.updateRow(line3)
                
                k = 3
                continue
                
            if line1.IN_FID == line2.IN_FID and line2.IN_FID != line3.IN_FID and line1.Rank_UGO == line2.Rank_UGO :
                line2.Type = "contact"

                try :
                    if line1.getValue(Metric) != noData and line2.getValue(Metric) != noData :
                        line2.Ratio = line1.getValue(Metric) / line2.getValue(Metric)
                except : 
                    pass
                
                l1 = [line1.getValue("Distance"),line2.getValue("Distance")]
                l2 = [line1.getValue("Rank_DGO"),line2.getValue("Rank_DGO")]
                line2.Down_DGO = l2[l1.index(max(l1))]
                del l2[l1.index(max(l1))]
                line2.Up_DGO_1 = l2[0]
                line2.Up_DGO_2 = -1
                
                line1.Type = "2"
                
                rows1.updateRow(line1)
                rows2.updateRow(line2)
                
                k = 2
                continue
                
            if line1.IN_FID != line2.IN_FID and line1.Distance == 0 :
                line1.Type = "extreme point"
                line1.Down_DGO = line1.Rank_DGO
                line1.Up_DGO_1 = -1
                line1.Up_DGO_2 = -1
                rows1.updateRow(line1)
                continue
    
    
    
    
    
    
    #/... for an AGO-scale input
    elif str(TypeOfGO) == "AGO" :    
        for line1 in rows1 :
            n += 1
            line2 = next(rows2)
            line3 = next(rows3)
            
            if line3.OBJECTID >= nrows :
                
                if k == 2 and line2.IN_FID == line3.IN_FID :
                    line3.Type = "contact"
                    try :
                        if line2.getValue(Metric) != noData and line3.getValue(Metric) != noData :
                            line3.Ratio = line2.getValue(Metric) / line3.getValue(Metric)
                    except :
                        pass
                    
                    l1 = [line2.getValue("Order_ID"),line3.getValue("Order_ID")]
                    l2 = [line2.getValue("Rank_AGO"),line3.getValue("Rank_AGO")]
                    line3.Down_AGO = l2[l1.index(min(l1))]
                    del l2[l1.index(min(l1))]
                    line3.Up_AGO_1 = l2[0]
                    line2.Up_AGO_2 = -1
                    
                    line2.Type = "2"
                    
                    rows2.updateRow(line2)
                    rows3.updateRow(line3)
                
                if k == 1 and line1.IN_FID != line2.IN_FID and line2.IN_FID != line3.IN_FID :
                    line1.Type = "extreme point"
                    line2.Type = "extreme point"
                    line3.Type = "extreme point"
                    
                    line1.Down_AGO = line1.Rank_AGO
                    line2.Down_AGO = line2.Rank_AGO
                    line3.Down_AGO = line3.Rank_AGO
                    
                    line1.Up_AGO_1 = -1
                    line2.Up_AGO_1 = -1
                    line3.Up_AGO_1 = -1
                    
                    line1.Up_AGO_2 = -1
                    line2.Up_AGO_2 = -1
                    line3.Up_AGO_2 = -1
                    
                    rows1.updateRow(line1)
                    rows2.updateRow(line2)
                    rows3.updateRow(line3)
                    
                    
                if k == 3 :
                    line3.Type = "2"
                    rows3.updateRow(line3)
                
                break
    
            if k == 3 or k == 2 : 
                k = k - 1
                continue    
            
            
            if line1.IN_FID == line2.IN_FID and line2.IN_FID == line3.IN_FID :
                line1.Type = "confluence"
                l1 = [line1.getValue("Order_ID"),line2.getValue("Order_ID"),line3.getValue("Order_ID")]
                l2 = [line1.getValue("Rank_AGO"),line2.getValue("Rank_AGO"),line3.getValue("Rank_AGO")]
                line1.Down_AGO = l2[l1.index(min(l1))]
                del l2[l1.index(min(l1))]
                line1.Up_AGO_1 = l2[0]
                line1.Up_AGO_2 = l2[1]
                
                line2.Type ="2"
                line3.Type = "2"
                
                rows1.updateRow(line1)
                rows2.updateRow(line2)
                rows3.updateRow(line3)
                
                k = 3
                continue
                
            if line1.IN_FID == line2.IN_FID and line2.IN_FID != line3.IN_FID and line1.Rank_UGO == line2.Rank_UGO :
                line2.Type = "contact"
                try :
                    if line1.getValue(Metric) != noData and line2.getValue(Metric) != noData :
                        line2.Ratio = line1.getValue(Metric) / line2.getValue(Metric)
                except : 
                    pass
                
                l1 = [line1.getValue("Distance"),line2.getValue("Distance")]
                l2 = [line1.getValue("Rank_AGO"),line2.getValue("Rank_AGO")]
                line2.Down_AGO = l2[l1.index(max(l1))]
                del l2[l1.index(max(l1))]
                line2.Up_AGO_1 = l2[0]
                line2.Up_AGO_2 = -1
                
                line1.Type = "2"
                
                rows1.updateRow(line1)
                rows2.updateRow(line2)
                
                k = 2
                continue
                
            if line1.IN_FID != line2.IN_FID and line1.Distance == 0 :
                line1.Type = "extreme point"
                line1.Down_AGO = line1.Rank_AGO
                line1.Up_AGO_1 = -1
                line1.Up_AGO_2 = -1
                rows1.updateRow(line1)
                continue
        

    #/transfer of the Ratio field and shaping of the spatial discontinuities layer
    ncurrentstep+=1
    arcpy.AddMessage("Transferring fields into the output break points - Step " + str(ncurrentstep) + "/" + str(nstep))       
    NearTableView = arcpy.MakeTableView_management(NearTable, "NearTable_View")
    Selection = arcpy.SelectLayerByAttribute_management(NearTableView, "NEW_SELECTION", "\"Type\" = '2'")
    
    arcpy.DeleteRows_management(Selection)

    fieldname = [f.name for f in arcpy.ListFields(OutputPoints)]

    if str(TypeOfGO) == "DGO" :    
        arcpy.JoinField_management(OutputPoints, str(fieldname[0]), NearTable, "IN_FID", ["Ratio", "Type", "Down_DGO", "Up_DGO_1", "Up_DGO_2" ])
    elif str(TypeOfGO) == "AGO" :    
        arcpy.JoinField_management(OutputPoints, str(fieldname[0]), NearTable, "IN_FID", ["Ratio", "Type", "Down_AGO", "Up_AGO_1", "Up_AGO_2" ])

    arcpy.AddXY_management(OutputPoints)
    arcpy.DeleteField_management(OutputPoints, ["ORIG_FID", str(Metric), "POINT_M"])








#===============================================================================
# DELETING TEMPORARY FILES
#=============================================================================== 
if str(DeleteTF) == "true" :
    ncurrentstep += 1
    arcpy.AddMessage("Deleting temporary files - Step " + str(ncurrentstep) + "/" + str(nstep))
    
    if str(TypeOfEntity) == "Polygon" :
        arcpy.Delete_management(TEMPinFC)
        arcpy.Delete_management(Intersect)
        arcpy.Delete_management(NearTable_TEMP)
        arcpy.Delete_management(NearTable)
        arcpy.Delete_management(NearTableView)
                    
    if str(TypeOfEntity) == "Polyline" :
        arcpy.Delete_management(TEMPinFC)
        arcpy.Delete_management(Sort)
        arcpy.Delete_management(NearTable)
            