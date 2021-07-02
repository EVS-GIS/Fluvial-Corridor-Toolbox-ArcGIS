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
       
#@summary: def__SLEM is an open-source python and arcPy code.
#          SLEM (for Split Line Each Meters) is used in several modules of the FluvialCorridor package.
#          According a user-defined length (m), named "Distance" in the code, it enables to segment a 
#          polyline from upstream to downstream.
#          Four blocks can be identified :
#              - the first one carries-out the disaggregation of raw polylines;
#             - the second one deals the disaggregation of UGOs (with a "Rank_UGO" field);
#              - the third one is for the disaggregation of sequenced UGOs (with a "Order_ID" field);
#              - the fourth one disaggregate AGOs (with a "Rank_AGO" field).

          
#'''


# Import of required librairies
import arcpy
import re
import def__UpToDateShapeLengthField as UPD_SL
import def__Export as Ext

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

#===============================================================================
# CODING
#===============================================================================
def SLEM(Line, Distance, Output, TempFolder, TF):
    
    CopyLine = arcpy.CopyFeatures_management(Line, "%ScratchWorkspace%\CopyLine")
    
    fieldnames = [f.name for f in arcpy.ListFields(CopyLine)]

    #/identification of the polyline type : raw, UGOs, sequenced UGOs, or AGOs
    k = 0
    if "Rank_AGO" in fieldnames :
        k = 3
    elif "Order_ID" in fieldnames :
        k = 2
    elif "Rank_UGO" in fieldnames :
        k = 1
            
    arcpy.AddMessage(k)
    
    if re.search('french', arcpy.GetInstallInfo()['SourceDir'], re.IGNORECASE):
        props = "Rank_UGO Ligne Distance To_M"
    else:
        props = "Rank_UGO LINE Distance To_M"
            

    ################################
    ########## Raw polyline ########
    ################################
    #
    if k == 0 :
        
        #/shaping of the segmented result
        arcpy.AddField_management(CopyLine, "Rank_UGO", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(CopyLine, "Rank_UGO", "!"+fieldnames[0]+"!", "PYTHON_9.3", "")
        arcpy.AddField_management(CopyLine, "From_Measure", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(CopyLine, "From_Measure", "0", "PYTHON_9.3", "")
        arcpy.AddField_management(CopyLine, "To_Measure", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(CopyLine, "To_Measure", "!shape.length!", "PYTHON_9.3", "")
        
        #/conversion in routes
        LineRoutes = arcpy.CreateRoutes_lr(CopyLine, "Rank_UGO", "%ScratchWorkspace%\\LineRoutes", "TWO_FIELDS", "From_Measure", "To_Measure")
        
        #/creation of the event table
        PointEventTEMP = arcpy.CreateTable_management("%ScratchWorkspace%", "PointEventTEMP", "", "")
        arcpy.AddField_management(PointEventTEMP, "Rank_UGO", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(PointEventTEMP, "Distance", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(PointEventTEMP, "To_M", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        
        UPD_SL.UpToDateShapeLengthField(LineRoutes)

        rowslines = arcpy.SearchCursor(LineRoutes)
        rowsevents = arcpy.InsertCursor(PointEventTEMP)
        for line in rowslines:
            tempdistance = float(0)
            while (tempdistance < float(line.Shape_Length)):
                row = rowsevents.newRow()
                row.Rank_UGO = line.Rank_UGO
                row.To_M = tempdistance + float(Distance)
                row.Distance = tempdistance
                rowsevents.insertRow(row)
                tempdistance = tempdistance + float(Distance)
        del rowslines
        del rowsevents

        #/creation of the route event layer
        MakeRouteEventTEMP = arcpy.MakeRouteEventLayer_lr(LineRoutes, "Rank_UGO", PointEventTEMP, props, "%ScratchWorkspace%\\MakeRouteEventTEMP")
        Split = arcpy.CopyFeatures_management(MakeRouteEventTEMP, "%ScratchWorkspace%\\Split", "", "0", "0", "0")
        Sort = arcpy.Sort_management(Split, Output, [["Rank_UGO", "ASCENDING"], ["Distance", "ASCENDING"]])

        arcpy.DeleteField_management(Sort, "To_M")
        
        #/calculation of the "Distance" field
        UPD_SL.UpToDateShapeLengthField(Sort)
        
        rows1 = arcpy.UpdateCursor(Sort)
        rows2 = arcpy.UpdateCursor(Sort)
        line2 = rows2.next()
        line2.Distance = 0
        rows2.updateRow(line2)
        nrows = int(str(arcpy.GetCount_management(Sort)))
        n = 0
        for line1 in rows1 :
            line2 = rows2.next()          
            if n == nrows-1 :
                break
            if n == 0 :
                line1.Distance = 0
            if line2.Rank_UGO == line1.Rank_UGO :
                line2.Distance = line1.Distance + line1.Shape_Length
                rows2.updateRow(line2)
            if line2.Rank_UGO != line1.Rank_UGO :
                line2.Distance = 0
                rows2.updateRow(line2)
            
            n+=1
        
        #/deleting of the temporary files
        if str(TF) == "true" :
            arcpy.Delete_management(Split)
            arcpy.Delete_management(CopyLine)
            arcpy.Delete_management(LineRoutes)
            arcpy.Delete_management(PointEventTEMP)
    
    
         
    
    
    
    
    
    ##################
    ###### UGO #######
    ##################
    if k == 1 :    
        
        #/shaping of the segmented result
        arcpy.AddField_management(CopyLine, "From_Measure", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(CopyLine, "From_Measure", "0", "PYTHON_9.3", "")
        arcpy.AddField_management(CopyLine, "To_Measure", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(CopyLine, "To_Measure", "!shape.length!", "PYTHON_9.3", "")
        
        #/conversion in routes
        LineRoutes = arcpy.CreateRoutes_lr(CopyLine, "Rank_UGO", "%ScratchWorkspace%\\LineRoutes", "TWO_FIELDS", "From_Measure", "To_Measure")
        
        #/creation of the event table
        PointEventTEMP = arcpy.CreateTable_management("%ScratchWorkspace%", "PointEventTEMP", "", "")
        arcpy.AddField_management(PointEventTEMP, "Rank_UGO", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(PointEventTEMP, "Distance", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(PointEventTEMP, "To_M", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        
        UPD_SL.UpToDateShapeLengthField(LineRoutes)

        rowslines = arcpy.SearchCursor(LineRoutes)
        rowsevents = arcpy.InsertCursor(PointEventTEMP)
        for line in rowslines:
            tempdistance = float(0)
            while (tempdistance < float(line.Shape_Length)):
                row = rowsevents.newRow()
                row.Rank_UGO = line.Rank_UGO
                row.To_M = tempdistance + float(Distance)
                row.Distance = tempdistance
                rowsevents.insertRow(row)
                tempdistance = tempdistance + float(Distance)
        del rowslines
        del rowsevents
        
        #/creation of the route event layer
        MakeRouteEventTEMP = arcpy.MakeRouteEventLayer_lr(LineRoutes, "Rank_UGO", PointEventTEMP, props, "%ScratchWorkspace%\\MakeRouteEventTEMP")
        Split = arcpy.CopyFeatures_management(MakeRouteEventTEMP, "%ScratchWorkspace%\\Split", "", "0", "0", "0")
        Sort = arcpy.Sort_management(Split, Output, [["Rank_UGO", "ASCENDING"], ["Distance", "ASCENDING"]])

        arcpy.DeleteField_management(Sort, "To_M")
        
        #/calculation of the "Distance" field
        UPD_SL.UpToDateShapeLengthField(Sort)
        
        rows1 = arcpy.UpdateCursor(Sort)
        rows2 = arcpy.UpdateCursor(Sort)
        line2 = rows2.next()
        line2.Distance = 0
        rows2.updateRow(line2)
        nrows = int(str(arcpy.GetCount_management(Sort)))
        n = 0
        for line1 in rows1 :
            line2 = rows2.next()          
            if n == nrows-1 :
                break
            if n == 0 :
                line1.Distance = 0
            if line2.Rank_UGO == line1.Rank_UGO :
                line2.Distance = line1.Distance + line1.Shape_Length
                rows2.updateRow(line2)
            if line2.Rank_UGO != line1.Rank_UGO :
                line2.Distance = 0
                rows2.updateRow(line2)
            
            n+=1
        
        #/deleting of the temporary files
        if str(TF) == "true" :
            arcpy.Delete_management(Split)
            arcpy.Delete_management(CopyLine)
            arcpy.Delete_management(LineRoutes)
            arcpy.Delete_management(PointEventTEMP)
    
    
    
    
    
    
    
    
    ################################
    ######### Sequenced UGO ########
    ################################
    if k == 2 :    
        
        #/shaping of the segmented result
        arcpy.AddField_management(CopyLine, "From_Measure", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(CopyLine, "From_Measure", "0", "PYTHON_9.3", "")
        arcpy.AddField_management(CopyLine, "To_Measure", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(CopyLine, "To_Measure", "!Shape_Length!", "PYTHON_9.3", "")
          
        #/conversion in routes
        LineRoutes = arcpy.CreateRoutes_lr(CopyLine, "Rank_UGO", "%ScratchWorkspace%\\LineRoutes", "TWO_FIELDS", "From_Measure", "To_Measure")
        arcpy.AddField_management(LineRoutes, "Order_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        Sort = arcpy.Sort_management(Line, "%ScratchWorkspace%\\Sort", [["Rank_UGO", "ASCENDING"]])

        rows1 = arcpy.UpdateCursor(LineRoutes)
        rows2 = arcpy.SearchCursor(Sort)
        
        for line1 in rows1 :
            line2 = rows2.next()
            line1.Order_ID = line2.Order_ID
            rows1.updateRow(line1)
            
        #/creation of the event table
        PointEventTEMP = arcpy.CreateTable_management("%ScratchWorkspace%", "PointEventTEMP", "", "")
        arcpy.AddField_management(PointEventTEMP, "To_M", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(PointEventTEMP, "Order_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(PointEventTEMP, "Rank_UGO", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(PointEventTEMP, "Distance", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
     
        UPD_SL.UpToDateShapeLengthField(LineRoutes)

        
        rowslines = arcpy.SearchCursor(LineRoutes)
        rowsevents = arcpy.InsertCursor(PointEventTEMP)
        for line in rowslines:
            tempdistance = float(0)
            while (tempdistance < float(line.Shape_Length)):
                row = rowsevents.newRow()
                row.To_M = tempdistance + float(Distance)
                row.Order_ID = line.Order_ID
                row.Rank_UGO = line.Rank_UGO
                row.Distance = tempdistance
                rowsevents.insertRow(row)
                tempdistance = tempdistance + float(Distance)
        del rowslines
        del rowsevents
        
        
        MakeRouteEventTEMP = arcpy.MakeRouteEventLayer_lr(LineRoutes, "Rank_UGO", PointEventTEMP, props, "%ScratchWorkspace%\\MakeRouteEventTEMP")
        Split = arcpy.CopyFeatures_management(MakeRouteEventTEMP, "%ScratchWorkspace%\\Split", "", "0", "0", "0")
        Sort = arcpy.Sort_management(Split, Output, [["Rank_UGO", "ASCENDING"], ["Distance", "ASCENDING"]])

        arcpy.DeleteField_management(Sort, "To_M")
        
        #/calculation of the "Distance" field
        UPD_SL.UpToDateShapeLengthField(Sort)
        
        rows1 = arcpy.UpdateCursor(Sort)
        rows2 = arcpy.UpdateCursor(Sort)
        line2 = rows2.next()
        line2.Distance = 0
        rows2.updateRow(line2)
        nrows = int(str(arcpy.GetCount_management(Split)))
        n = 0
        for line1 in rows1 :
            line2 = rows2.next()         
            if n >= nrows-1 :
                break
            if n == 0 :
                line1.Distance = 0
            if line2.Rank_UGO == line1.Rank_UGO :
                line2.Distance = line1.Distance + line1.Shape_Length
                rows2.updateRow(line2)
            if line2.Rank_UGO != line1.Rank_UGO :
                line2.Distance = 0
                rows2.updateRow(line2)
            
            n+=1
        #/deleting of the temporary files
        if str(TF) == "true" :
            arcpy.Delete_management(Split)
            arcpy.Delete_management(CopyLine)
            arcpy.Delete_management(LineRoutes)
            arcpy.Delete_management(PointEventTEMP)

    
    
    
    
    
    
    
    #############
    #### AGO ####
    #############
    if k == 3 :   
        
        #/shaping of the segmented result
        arcpy.AddField_management(CopyLine, "From_Measure", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(CopyLine, "From_Measure", "0", "PYTHON_9.3", "")
        arcpy.AddField_management(CopyLine, "To_Measure", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        try :
            arcpy.CalculateField_management(CopyLine, "To_Measure", "!shape.length!", "PYTHON_9.3", "")
        except :
            arcpy.CalculateField_management(CopyLine, "To_Measure", "!forme.length!", "PYTHON_9.3", "")
        
        #/conversion in routes
        LineRoutes = arcpy.CreateRoutes_lr(CopyLine, "Rank_AGO", "%ScratchWorkspace%\\LineRoutes", "TWO_FIELDS", "From_Measure", "To_Measure")
        arcpy.AddField_management(LineRoutes, "Order_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(LineRoutes, "Rank_UGO", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(LineRoutes, "AGO_Val", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        
        UPD_SL.UpToDateShapeLengthField(LineRoutes)
        

        Ext.Export(CopyLine,TempFolder,"ExportTable")       

        fichier = open(TempFolder+"\\ExportTable.txt", 'r')        
        Order_ID = []
        Rank_UGO = []
        Dist = []
        Rank_AGO = []
        AGO_Val = []
        
        head = fichier.readline().split('\n')[0].split(';')
        iOrder_ID = head.index("Order_ID")
        iRank_UGO = head.index("Rank_UGO")
        iRank_AGO = head.index("Rank_AGO")
        iAGO_Val = head.index("AGO_Val")
        
        for l in fichier:
            Order_ID.append(int(l.split('\n')[0].split(';')[iOrder_ID]))
            Rank_UGO.append(int(l.split('\n')[0].split(';')[iRank_UGO]))
            Rank_AGO.append(float(l.split('\n')[0].split(';')[iRank_AGO]))
            AGO_Val.append(float(l.split('\n')[0].split(';')[iAGO_Val].replace(',','.')))

        p=0
        rows1 = arcpy.UpdateCursor(LineRoutes)
        for line1 in rows1 :
            line1.Order_ID = Order_ID[p]
            line1.Rank_UGO = Rank_UGO[p]
            line1.Rank_AGO = Rank_AGO[p]
            line1.AGO_Val = AGO_Val[p]
            rows1.updateRow(line1)
            p+=1
    
        #/creation of the event table
        PointEventTEMP = arcpy.CreateTable_management("%ScratchWorkspace%", "PointEventTEMP", "", "")
        arcpy.AddField_management(PointEventTEMP, "Distance_From_Start", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(PointEventTEMP, "To_M", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(PointEventTEMP, "Order_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(PointEventTEMP, "Rank_UGO", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(PointEventTEMP, "Rank_AGO", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(PointEventTEMP, "AGO_Val", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

        
        rowslines = arcpy.SearchCursor(LineRoutes)
        rowsevents = arcpy.InsertCursor(PointEventTEMP)
        for line in rowslines:
            tempdistance = float(0)
            while (tempdistance < float(line.Shape_Length)):
                row = rowsevents.newRow()
                row.Distance_From_Start = tempdistance
                row.To_M = tempdistance + float(Distance)
                row.Order_ID = line.Order_ID
                row.Rank_UGO = line.Rank_UGO
                row.Rank_AGO = line.Rank_AGO
                row.AGO_Val = line.AGO_Val
                rowsevents.insertRow(row)
                tempdistance = tempdistance + float(Distance)
        del rowslines
        del rowsevents
        
        if re.search('french', arcpy.GetInstallInfo()['SourceDir'], re.IGNORECASE):
            props2 = "Rank_AGO Ligne Distance_From_Start To_M"
        else:
            props2 = "Rank_AGO LINE Distance_From_Start To_M"

        MakeRouteEventTEMP = arcpy.MakeRouteEventLayer_lr(LineRoutes, "Rank_AGO", PointEventTEMP, props2, "%ScratchWorkspace%\\MakeRouteEventTEMP")
        Split = arcpy.CopyFeatures_management(MakeRouteEventTEMP, "%ScratchWorkspace%\\Split", "", "0", "0", "0")
        arcpy.AddField_management(Split, "Distance", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(Split, "Distance", "!Distance_From_Start!", "PYTHON_9.3", "")
        arcpy.DeleteField_management(Split, ["To_M","Distance_From_Start"])
        Sort = arcpy.Sort_management(Split, Output, [["Order_ID", "ASCENDING"], ["Rank_UGO", "ASCENDING"], ["Rank_AGO", "ASCENDING"], ["Distance", "ASCENDING"]])

        UPD_SL.UpToDateShapeLengthField(Sort)
        
        #/deleting of the temporary files
        if str(TF) == "true" :
            arcpy.Delete_management(Split)
            arcpy.Delete_management(CopyLine)
            arcpy.Delete_management(LineRoutes)
            arcpy.Delete_management(PointEventTEMP)
    
    
    
    
    return Sort
