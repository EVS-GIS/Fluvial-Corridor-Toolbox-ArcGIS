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
       
@summary: Sequencing is an open-source python and arcPy code.
          This script has been developed to ensure a good orientation and and to sequence the network from 
          upstream to downstream. The code start from the outlet and go upstream. The first stream is attributed
          with an "Order_ID" of 1. Next up stream with an "Order_ID" of 2 and so on. For each stream, the
          orientation is checked and eventually corrected. Computation time of this module directly depends on
          the drainage density.
          
'''


# Import of required librairies
import arcpy
import os

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

# Inputs
InputFC = arcpy.GetParameterAsText(0)
OutStreamPt = arcpy.GetParameterAsText(1)
OutFP = arcpy.GetParameterAsText(2)
OutSeq = arcpy.GetParameterAsText(3)
DeleteTF = arcpy.GetParameterAsText(4)

# Dervied variable from inputs
(path, name) = os.path.split(OutFP)
size = len(path)



#===============================================================================
# CODING
#===============================================================================
#/creation of the final stream network
    # The sequencing module will operate on this layer
arcpy.AddMessage("Creating final shp - Step 0")
InputFCMTS_TEMP = arcpy.MultipartToSinglepart_management(InputFC, "%ScratchWorkspace%\\InputFCMTS_TEMP")
InputFCMTS = arcpy.Intersect_analysis([InputFCMTS_TEMP, InputFCMTS_TEMP], "%ScratchWorkspace%\\InputFCMTS", "", "", "")

fieldnamesInFC = [f.name for f in arcpy.ListFields(InputFCMTS_TEMP)]
fieldnamesOutFC = [f.name for f in arcpy.ListFields(InputFCMTS)]
for fieldOut in fieldnamesOutFC :
    if  str(fieldOut) not in str(fieldnamesInFC) :
            arcpy.DeleteField_management(InputFCMTS, str(fieldOut))
            
arcpy.AddField_management(InputFCMTS, "Rank_UGO", "SHORT", "", "", "", "","NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(InputFCMTS, "NextDownID", "SHORT", "", "", "", "","NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(InputFCMTS, "NextUpID", "SHORT", "", "", "", "","NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(InputFCMTS, "From_X", "DOUBLE", "", "", "", "","NULLABLE", "NON_REQUIRED")

#/creation of the up and down points 
if path[size-4:size] == ".gdb" :
    UDPts = arcpy.FeatureVerticesToPoints_management(InputFCMTS, OutFP, "BOTH_ENDS")
else :
    UDPts = arcpy.FeatureVerticesToPoints_management(InputFCMTS, "%ScratchWorkspace%\\UDPts", "BOTH_ENDS")

fieldnamesUDPts = [f.name for f in arcpy.ListFields(UDPts)]
for field in fieldnamesUDPts :
    try :
        arcpy.DeleteField_management(UDPts, [field])
    except :
        continue

arcpy.AddField_management(UDPts, "Join_Field", "LONG", "", "", "", "","NULLABLE", "NON_REQUIRED")
arcpy.CalculateField_management(UDPts, "Join_Field", "[OBJECTID]", "VB", "")
arcpy.AddXY_management(UDPts)
arcpy.DeleteIdentical_management(UDPts, ["POINT_X", "POINT_Y"])

MakeUDPts = arcpy.MakeFeatureLayer_management(UDPts, "%ScratchWorkspace%\\MakeUDPts", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")



#/couting of the sreams number
nbParts = arcpy.GetCount_management(InputFCMTS)

# Number of steps
if str(nbParts) == str(1) :
    nstep = 4
else : 
    nstep = 7
if str(DeleteTF) == "true" :
    nstep+=1 
ncurrentstep = 1




#/creation of the "Order_ID" field
arcpy.AddMessage("Adding Order_ID field - Step "  + str(ncurrentstep) + "/" + str(nstep))
arcpy.AddField_management(InputFCMTS, "Order_ID", "LONG", "", "", "", "","NULLABLE", "NON_REQUIRED")
arcpy.CalculateField_management(InputFCMTS, "Order_ID", "0", "VB", "")



    #####################
    ## One stream case ##
    #####################
if str(nbParts) == str(1) :
    #/work on the extreme downstream branch
    ncurrentstep+=1
    arcpy.AddMessage("Extracting and flipping, if it is needed, the direction of the extreme downstream branch - Step "  + str(ncurrentstep) + "/" + str(nstep))
    arcpy.CalculateField_management(InputFCMTS, "Order_ID", "1", "VB", "")

        # Cursor on the streamline
    rows1 = arcpy.SearchCursor(InputFCMTS)
    line = rows1.next()
    shapeName1 = arcpy.Describe(InputFCMTS).shapeFieldName
    SpatialRef = arcpy.Describe(InputFCMTS).spatialReference
    Obj1 = line.getValue(shapeName1)
    
        # Last point of the streamline as a PointGeometry
    end = Obj1.lastPoint
    endPt = arcpy.PointGeometry(end, SpatialRef)
    EPt = arcpy.CopyFeatures_management(endPt,"%ScratchWorkspace%\\EPt")
    
        # First point of the streamline as a PointGeometry
    start = Obj1.firstPoint
    startPt = arcpy.PointGeometry(start, SpatialRef)
    SPt = arcpy.CopyFeatures_management(startPt,"%ScratchWorkspace%\\SPt")
    
        # Cursor on the OutStreamPoint
    rows2 = arcpy.SearchCursor(OutStreamPt)
    point = rows2.next()
    shapeName2 = arcpy.Describe(OutStreamPt).shapeFieldName
    Obj2 = point.getValue(shapeName2)
    
        # OutStreamPoint as an PointGeometry
    Pt = Obj2.lastPoint
    OutPt = arcpy.PointGeometry(Pt, SpatialRef)

        # Distance between the OutStreamPoint and the first and last point of the streamline (dS and DE)
    dS = startPt.distanceTo(OutPt)
    dE = endPt.distanceTo(OutPt)


    #/orientation of the streamline
    if dS < dE :
        arcpy.AddMessage("   Wrong Direction")
        arcpy.FlipLine_edit(InputFCMTS)
        rows = arcpy.SearchCursor(InputFCMTS)
        line = rows.next()
    
        ncurrentstep+=1
        arcpy.AddMessage("Extracting the new first point - Step "  + str(ncurrentstep) + "/" + str(nstep))
        shapeName = arcpy.Describe(InputFCMTS).shapeFieldName
        SpatialRef = arcpy.Describe(InputFCMTS).spatialReference
      
        Obj = line.getValue(shapeName)
        first = Obj.firstPoint
        end = Obj.lastPoint
        firstPt = arcpy.PointGeometry(first, SpatialRef)
        endPt = arcpy.PointGeometry(end, SpatialRef)
        
    else :
        arcpy.AddMessage("      Good Direction")
        rows = arcpy.SearchCursor(InputFCMTS)
        line = rows.next()
    
        ncurrentstep+=1
        arcpy.AddMessage("Extracting the new first point - Step "  + str(ncurrentstep) + "/" + str(nstep))
        shapeName = arcpy.Describe(InputFCMTS).shapeFieldName
        SpatialRef = arcpy.Describe(InputFCMTS).spatialReference
      
        Obj = line.getValue(shapeName)
        first = Obj.firstPoint
        end = Obj.lastPoint
        firstPt = arcpy.PointGeometry(first, SpatialRef)
        endPt = arcpy.PointGeometry(end, SpatialRef)
        
        
    #/extraction of NextDownID and NextUpID information
        # We get the OBJECTID of the new first and end points from the UDPts to store it into the output shp. 
        # This enable to get the NextDown and NextUp information
    ncurrentstep+=1
    arcpy.AddMessage("Storing the new first point - Step "  + str(ncurrentstep) + "/" + str(nstep))
    FPt = arcpy.CopyFeatures_management(firstPt, "%ScratchWorkspace%\\FPt")
    EPt = arcpy.CopyFeatures_management(endPt, "%ScratchWorkspace%\\EPt")

    MakeFPt = arcpy.MakeFeatureLayer_management(FPt, "%ScratchWorkspace%\\MakeFPt", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
    MakeEPt = arcpy.MakeFeatureLayer_management(EPt, "%ScratchWorkspace%\\MakeEPt", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
    
    rowsOut = arcpy.UpdateCursor(InputFCMTS)
    lineOut = rowsOut.next()
    
    SelecStart = arcpy.SelectLayerByLocation_management(MakeUDPts, "ARE_IDENTICAL_TO", MakeFPt, "", "NEW_SELECTION")
    rowsStart = arcpy.SearchCursor(SelecStart)
    lineStart = rowsStart.next()
    lineOut.NextUpID = lineStart.OBJECTID
    lineOut.From_X = lineStart.POINT_X
    rowsOut.updateRow(lineOut)
    
    SelecEnd = arcpy.SelectLayerByLocation_management(MakeUDPts, "ARE_IDENTICAL_TO", MakeEPt, "", "NEW_SELECTION")
    rowsEnd = arcpy.SearchCursor(SelecEnd)
    lineEnd = rowsEnd.next()
    lineOut.NextDownID = lineEnd.OBJECTID
    lineOut.Rank_UGO = 1
    rowsOut.updateRow(lineOut)
    
    





    ####################
    ### Network case ###
    ####################
else :
    #/extraction of the distance between the outlet and the network
    ncurrentstep+=1
    arcpy.AddMessage("Generating NearTable between the network and its outlet - Step "  + str(ncurrentstep) + "/" + str(nstep))
    NearTable = arcpy.GenerateNearTable_analysis(OutStreamPt, InputFCMTS, "NearTable", "", "LOCATION", "NO_ANGLE", "")
    rows = arcpy.SearchCursor(NearTable)
    line = rows.next()
    Distance = float(line.NEAR_DIST)
    if Distance == 0 :
        Distance+=1
    
    #/selection of the most downstream branch
    #/addition of the first order "1" to the "Order_ID" field.
    ncurrentstep+=1
    arcpy.AddMessage("Extracting extreme aval branch - Step "  + str(ncurrentstep) + "/" + str(nstep))
    MakeCopy = arcpy.MakeFeatureLayer_management(InputFCMTS, "%ScratchWorkspace%\\MakeCopy", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
    MakeOutStreamPt = arcpy.MakeFeatureLayer_management(OutStreamPt, "%ScratchWorkspace%\\MakeOutStreamPt", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
    BrancheAvale = arcpy.SelectLayerByLocation_management(MakeCopy, "INTERSECT", MakeOutStreamPt, Distance, "NEW_SELECTION")

    arcpy.CalculateField_management(BrancheAvale, "Order_ID", "1", "VB", "")
    
    #/orientation of the downstream branch
        # Looking for the point which is considered as the final point "lastPt".
    rows = arcpy.SearchCursor(BrancheAvale)
    line = rows.next()
    
    ncurrentstep+=1
    arcpy.AddMessage("Extracting the direction of the extreme aval branch - Step "  + str(ncurrentstep) + "/" + str(nstep))
    shapeName = arcpy.Describe(BrancheAvale).shapeFieldName
    SpatialRef = arcpy.Describe(BrancheAvale).spatialReference
      
    Obj = line.getValue(shapeName)
    end = Obj.lastPoint
    
        # "endPt" contains the lastPt, with the same spatial reference of the network.
    endPt = arcpy.PointGeometry(end, SpatialRef)
    EPt = arcpy.CopyFeatures_management(endPt,"%ScratchWorkspace%\\EPt")

        # Selection of the branches adjacent to the EPt.
    ncurrentstep+=1
    arcpy.AddMessage("If it needed, flipping the extreme downstream branch and setting its Order_ID - Step "  + str(ncurrentstep) + "/" + str(nstep))
    MakeCopy = arcpy.MakeFeatureLayer_management(InputFCMTS, "%ScratchWorkspace%\\MakeCopy", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
    Selection = arcpy.SelectLayerByLocation_management(MakeCopy, "BOUNDARY_TOUCHES", EPt, "", "NEW_SELECTION")
    MakeSelection = arcpy.MakeFeatureLayer_management(Selection, "%ScratchWorkspace%\\MakeSelection", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
        
        # If there is only one branch connected to the "endPt", it means that the downstream branch is 
        # correctly oriented. 
        # If there is more than one branch, the "endPt" of the downstream branch is wrongly defined and the
        # branch need to be re-oriented.
    Counter = arcpy.GetCount_management(MakeSelection)
    if int(str(Counter)) > int(1) :
        arcpy.AddMessage("    wrong direction")
        SelectionTEMP = arcpy.SelectLayerByAttribute_management(Selection, "NEW_SELECTION", "\"Order_ID\" = 1")
        arcpy.FlipLine_edit(SelectionTEMP)
    else :
        arcpy.AddMessage("    Good direction")
        SelectionTEMP = arcpy.SelectLayerByAttribute_management(Selection, "NEW_SELECTION", "\"Order_ID\" = 1")
    
    
    #/extraction of NextDownID and NextUpID information
        # In any case, the new "FirstPt" and his "Order_ID" are stored into "FirstsPts".
        # Finally, "FirstsPts" will contains all the first points.
    ncurrentstep+=1
    arcpy.AddMessage("Getting the NextDownID and NextUpID fields - Step "  + str(ncurrentstep) + "/" + str(nstep))
    rows = arcpy.SearchCursor(SelectionTEMP)
    line = rows.next()
    
    shapeName = arcpy.Describe(SelectionTEMP).shapeFieldName
    
    Obj = line.getValue(shapeName)
    firstPt = Obj.firstPoint
    endPt = Obj.lastPoint
    
    first = arcpy.PointGeometry(firstPt, SpatialRef)
    end = arcpy.PointGeometry(endPt, SpatialRef)
    
      

        # We get the OBJECTID of the new first and end points from the UDPts to store it
        # into the output shp. This enable to get the NextDown and NextUp information
    FPt = arcpy.CopyFeatures_management(first, "%ScratchWorkspace%\\FPt")
    FPtoSelect = arcpy.CopyFeatures_management(first, "%ScratchWorkspace%\\FPtoSelect")
    EPt = arcpy.CopyFeatures_management(end, "%ScratchWorkspace%\\EPt")

    MakeFPt = arcpy.MakeFeatureLayer_management(FPt, "%ScratchWorkspace%\\MakeFPt", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
    MakeEPt = arcpy.MakeFeatureLayer_management(EPt, "%ScratchWorkspace%\\MakeEPt", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
    
    rowsOut = arcpy.UpdateCursor(SelectionTEMP)
    lineOut = rowsOut.next()
    
    SelecStart = arcpy.SelectLayerByLocation_management(MakeUDPts, "ARE_IDENTICAL_TO", MakeFPt, "", "NEW_SELECTION")
    rowsStart = arcpy.SearchCursor(SelecStart)
    lineStart = rowsStart.next()
    lineOut.NextUpID = lineStart.OBJECTID
    lineOut.From_X = lineStart.POINT_X
    rowsOut.updateRow(lineOut)
    
    SelecEnd = arcpy.SelectLayerByLocation_management(MakeUDPts, "ARE_IDENTICAL_TO", MakeEPt, "", "NEW_SELECTION")
    rowsEnd = arcpy.SearchCursor(SelecEnd)
    lineEnd = rowsEnd.next()
    lineOut.NextDownID = lineEnd.OBJECTID
    lineOut.Rank_UGO = 1
    rowsOut.updateRow(lineOut)
    
    
    #/deleting of the NearTable
    arcpy.Delete_management(NearTable)
    
    
    
    
    
    ###### Process iteration downstream #######
    ncurrentstep+=1
    arcpy.AddMessage("Iterative loop (flipping and updating Order_ID) from downstream to upstream - Step "  + str(ncurrentstep) + "/" + str(nstep))
    n = 2       # "n" relates to the order in treatment.
    C = 1       # "C" is the number of the branches of the current order.
                # When C=0, it means that the process have assessed the upper branches of the network : is done.
    k = 2       # k will be the unique ID "Rank_UGO" of each line.
    
    
    while int(str(C)) > int(0) :
        #/selection of the n and n+1 Order_ID
        arcpy.AddMessage("    Order_ID  : " + str(n))
            # We select the branches touching a point in "FirstPts". Those streams are the  ones already processed 
            # (lower Order_ID than the current Order_ID) and the ones with a n+1 order, unprocessed.
        arcpy.AddMessage("        Selecting branches")
        MakeCopy = arcpy.MakeFeatureLayer_management(InputFCMTS, "%ScratchWorkspace%\\MakeCopy", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
        MakeFPtoSelect = arcpy.MakeFeatureLayer_management(FPtoSelect, "%ScratchWorkspace%\\MakeFPtoSelect", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
        Selection1 = arcpy.SelectLayerByLocation_management(MakeCopy, "BOUNDARY_TOUCHES", MakeFPtoSelect, "", "NEW_SELECTION")
        MakeSelection = arcpy.MakeFeatureLayer_management(Selection1, "%ScratchWorkspace%\\MakeSelection2", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
        
        #/selection of the unprocessed branches
            # We limit the selection to the unprocessed branches : thoses which do not have a Order_ID yet.
        Selection2 = arcpy.SelectLayerByAttribute_management(Selection1, "SUBSET_SELECTION", "\"Order_ID\" = 0 ")
        MakeSelection2 = arcpy.MakeFeatureLayer_management(Selection2, "%ScratchWorkspace%\\MakeSelection2", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")

        #/updating of C    
        C = arcpy.GetCount_management(Selection2)
        
        #/setting the new "Order_ID" order
        arcpy.AddMessage("        Writting the field Order_ID")
        arcpy.CalculateField_management(Selection2, "Order_ID", str(n), "VB", "")
        
        #/initialization of the SearchCursor over the unprocessed selection
        shapeName = arcpy.Describe(Selection2).shapeFieldName
        rows = arcpy.SearchCursor(Selection2)
        
        #/orientation of each line within the selection
        arcpy.AddMessage("        Iterative loop on each branch of order " + str(n) + " to redefine the direction, if it is needed")
        for line in rows :      
                # The loop is done for each unprocessed branch of the current selection.
                # The most downstream point is stored in "lastPt" and then copied in "endPt".
            Obj = line.getValue(shapeName)
            end = Obj.lastPoint
            endPt = arcpy.PointGeometry(end, SpatialRef)
            EPt = arcpy.CopyFeatures_management(endPt, "%ScratchWorkspace%\\EPt")
            
                # For each branch in the current selection, we look if the end point is identical to one
                # in the "FirstPts" layer.
                # If this is the case, the branch is correctly oriented and "counter" will not zero
                # If the branch is not correctly oriented, "Counter"=0.
            MakeFPtoSelect = arcpy.MakeFeatureLayer_management(FPtoSelect, "%ScratchWorkspace%\\MakeFPtoSelect", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
            Selection = arcpy.SelectLayerByLocation_management(MakeFPtoSelect, "ARE_IDENTICAL_TO", EPt, "", "NEW_SELECTION")
            MakeSelection = arcpy.MakeFeatureLayer_management(Selection, "%ScratchWorkspace%\\MakeSelection", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
            Counter = arcpy.GetCount_management(MakeSelection)
            
           
            if int(str(Counter)) == int(0) :
                # If the branch is wrongly oriented :
                #     --> Selection of the branch and flipping it.
                arcpy.AddMessage("          Wrong direction")
                MakeSelection2 = arcpy.MakeFeatureLayer_management(Selection2, "%ScratchWorkspace%\\MakeSelection2", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
                SelectionTEMP = arcpy.SelectLayerByLocation_management(MakeSelection2, "BOUNDARY_TOUCHES", EPt, "", "NEW_SELECTION")
                arcpy.FlipLine_edit(SelectionTEMP)
                
                # The branch is now correctly oriented :
                #    --> We set the Order_ID order and store the new and correct first point in FirstPts.
                rows = arcpy.SearchCursor(SelectionTEMP)
                line = rows.next()
                shapeName = arcpy.Describe(SelectionTEMP).shapeFieldName
                Obj = line.getValue(shapeName)
                first = Obj.firstPoint
                end = Obj.lastPoint
                
                firstPt = arcpy.PointGeometry(first, SpatialRef)
                endPt = arcpy.PointGeometry(end, SpatialRef)
                FPt = arcpy.CopyFeatures_management(firstPt, "%ScratchWorkspace%\\FPt")
                EPt = arcpy.CopyFeatures_management(endPt, "%ScratchWorkspace%\\EPt")

                arcpy.Append_management(FPt, FPtoSelect, "TEST", "", "")
                
                
                
            else :
                    # If the branch is correctly oriented :
                    #     --> selection of the branch.
                arcpy.AddMessage("          Good direction")
                first = Obj.firstPoint
                firstPt = arcpy.PointGeometry(first, SpatialRef)
                FPt = arcpy.CopyFeatures_management(firstPt, "%ScratchWorkspace%\\FPt")
                MakeSelection2 = arcpy.MakeFeatureLayer_management(Selection2, "%ScratchWorkspace%\\MakeSelection2", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
                SelectionTEMP = arcpy.SelectLayerByLocation_management(MakeSelection2, "BOUNDARY_TOUCHES", FPt, "", "NEW_SELECTION")
                
                    # Setting the "Order_ID" order and getting the first point.
                rows = arcpy.SearchCursor(SelectionTEMP)
                line = rows.next()
                shapeName = arcpy.Describe(SelectionTEMP).shapeFieldName
                Obj = line.getValue(shapeName)
                first = Obj.firstPoint
                end = Obj.lastPoint
                
                firstPt = arcpy.PointGeometry(first, SpatialRef)
                endPt = arcpy.PointGeometry(end, SpatialRef)
                FPt = arcpy.CopyFeatures_management(firstPt, "%ScratchWorkspace%\\FPt")
                EPt = arcpy.CopyFeatures_management(endPt, "%ScratchWorkspace%\\EPt")

                arcpy.Append_management(FPt, FPtoSelect, "TEST", "", "")


            #/extraction of NextDownID and NextUpID information
                # We get the OBJECTID of the new first and end points from the UDPts to store it
                # into the output shp. This enable to get the NextDown and NextUp IDs.
            MakeFPt = arcpy.MakeFeatureLayer_management(FPt, "%ScratchWorkspace%\\MakeFPt", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
            MakeEPt = arcpy.MakeFeatureLayer_management(EPt, "%ScratchWorkspace%\\MakeEPt", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
    
            rowsOut = arcpy.UpdateCursor(SelectionTEMP)
            lineOut = rowsOut.next()

            SelecStart = arcpy.SelectLayerByLocation_management(MakeUDPts, "INTERSECT", MakeFPt, "", "NEW_SELECTION")
            rowsStart = arcpy.SearchCursor(SelecStart)
            lineStart = rowsStart.next()
            lineOut.NextUpID = lineStart.OBJECTID
            lineOut.From_X = lineStart.POINT_X
            rowsOut.updateRow(lineOut)
            
            SelecEnd = arcpy.SelectLayerByLocation_management(MakeUDPts, "INTERSECT", MakeEPt, "", "NEW_SELECTION")
            rowsEnd = arcpy.SearchCursor(SelecEnd)
            lineEnd = rowsEnd.next()
            lineOut.NextDownID = lineEnd.OBJECTID
            lineOut.Rank_UGO = k
            rowsOut.updateRow(lineOut)
            

            #/selection of  the next branch in the selection
            k += 1
        
        #/selection of the next "Order_ID"
        n+=1

#finalization of the outputs
if path[size-4:size] != ".gdb" :
    arcpy.CopyFeatures_management(UDPts, OutFP)
 
Sort = arcpy.Sort_management(InputFCMTS, OutSeq, [["Order_ID", "ASCENDING"],["From_X", "ASCENDING"]])
arcpy.AddField_management(Sort, "Rank_UGO", "SHORT", "", "", "", "","NULLABLE", "NON_REQUIRED")
rows1 = arcpy.UpdateCursor(Sort)
n = 1
for line1 in rows1 :
    line1.Rank_UGO = n
    rows1.updateRow(line1)
    n+=1
try :
    arcpy.DeleteField_management(Sort, ["From_X", "ORIG_FID"])
except :
    pass
try :
    arcpy.DeleteField_management(Sort, ["Shape_Le_1"])
except:
    pass








#===============================================================================
# DELETING TEMPORARY FILES
#=============================================================================== 
arcpy.DeleteField_management(InputFCMTS, ["ORIG_FID"])
arcpy.Delete_management(InputFCMTS_TEMP)
if str(DeleteTF) == "true" : 
    ncurrentstep+=1
    arcpy.AddMessage("Deleting temporary files - Step " + str(ncurrentstep) + "/" + str(nstep))
    arcpy.Delete_management(FPt)
    arcpy.Delete_management(EPt)
    arcpy.Delete_management(InputFCMTS)
    try :
        arcpy.Delete_management(FPtoSelect)
    except :
        pass
    if path[size-4:size] != ".gdb" :
        arcpy.Delete_management("%ScratchWorkspace%\\UDPts")
