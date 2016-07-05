#-------------------------------------------------------------------------------

#   ETV_Toolkit.pyt
#
#   Create or update Enjoy the View feature classes (bearings and view polygons)
#   or viewsheds.  Calculate or update visible point areas or scenic inventory
#   values.
#
#
#   Prerequisites/Inputs (vary by tool):
#       ArcGIS 10.2.2 or higher
#       Source ViewBearings database view (Create Bearings, Create View Polygons
#       and CreateViewshed)
#       ViewPolygons feature class (Calculate Visible Point Areas)
#       Source SIV database view (Calculate Scenic Inventory Values)
#
#       XML metadata template in known subfolder (<somewhere>/Templates/Metadata)
#       Output Folder/Workspace
#
#   Outputs (vary by tool):
#       Feature class(es) in the enterprise GDB: ARD_VisualResourceInventory_ViewBearings_ln,
#       ARD_VisualResourceInventory_Views_poly, ARD_VisualResourceInventory_VisiblePointAreas_poly
#       Viewshed rasters (GeoTIFFs) by viewpoint and viewed landscape:
#           ARD_VisualResourceInventory_<ParkCode>_Viewshed_(ViewpointName)_(ViewedLandscapeNumber).tif
#       Scenic Inventory Value summary table: ARD_VisualResourceInventory_ScenicInventoryValues
#
#   Created by:  NPS Inventory and Monitoring Division GIS Staff
#       Update date: 20151216 LN
#       Update date: 20160209 LN - stubbing out CreateBearings
#       Update date: 20160325 LN - started code for CreateViewPolygons
#       Update date: 20160506 LN - fixing bug when viewpoint name has ' and
#                                   added code for ViewBearings tool
#       Update date: 20160526 LN - fixed bug when special chars in viewpoint name
#                                   and added save of source lookup table to ViewBearings tool
#       Update date: 20160609 LN - added logic for visible areas unioning
#
#
#   Credits:
#       View polygon logic adapted from ETV app javascript code
#           ($/ETV/Main/1.1.0/NPS.ETV.Web/Views/Viewpoint/Manage.cshtml)
#
#       Viewshed code adapted from scripts for Great Plains Wind Energy Project
#       written by Kirk Sherrill - IMD contractor (2012-2013)
#-------------------------------------------------------------------------------

import arcpy
import arcpy.da
from arcpy.sa import *

import os, time
from datetime import datetime
import math

EarthRadiusMeters = 6378137.0 # earth's mean radius in meters
ddDisplayField = "UNIT_CODE"

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "ETV_Toolkit"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [CreateBearings, CreateViewedLandscapes, CalculateScenicInventoryValues, CreateViewshed]
        #self.tools = [CreateBearings, CreateViewedLandscapes, CalculateVisiblePointAreas, CalculateScenicInventoryValues, CreateViewshed]

class CreateBearings(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "1 Create View Bearings"
        self.description = "Create View Bearing features from Enjoy the View (Scenic Quality Inventory) database"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName = "Source Viewpoint Table",  # Needs to be the ViewBearings view
            name = "viewpointSource",
            datatype = "DETable",
            parameterType = "Required",
            direction = "Input")
        param0.value = r"Database Connections\ETV_on_INP2300FCVWHIS1_Report_Data_Reader.sde\ETV.web.ViewBearings"

        param1 = arcpy.Parameter(
            displayName = "Choose a park to process",
            name = "parkToProcess",
            datatype = "String",
            parameterType  = "Required",
            direction = "Input")

        param2 = arcpy.Parameter(
            displayName = "Output GeoDatabase",
            name = "outDB",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input")

        param3 = arcpy.Parameter(
            displayName = "View Radius (in meters)",
            name = "viewRadius",
            datatype = "String",
            parameterType = "Required",
            direction = "Input"
            )
        param3.value = r"40000"

        param4 = arcpy.Parameter(
            displayName = "Output Spatial Reference",
            name = "outSR",
            datatype = "GPSpatialReference",
            parameterType = "Required",
            direction = "Input"
            )

        param5 = arcpy.Parameter(
            displayName = "Folder Containing Metadata Template",
            name = "metaFolder",
            datatype = "Folder",
            parameterType = "Optional",
            direction = "Input"
            )
        param5.value = r"X:\ProjectData\NRSS_ARD\EnjoyTheView\Templates\Metadata"

        params = [param0, param1, param2, param3, param4, param5]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        # Modified from the example shown here: http://blogs.esri.com/esri/arcgis/2011/08/25/generating-a-choice-list-from-a-field/
        if parameters[0].value:
            parkList = [str(val) for val in
                                            sorted(
                                              set(
                                                row.getValue(ddDisplayField)
                                                for row in arcpy.SearchCursor(parameters[0].value)
                                                  )
                                               )
                                          ]
            parkList.append("ALL")
            parameters[1].filter.list = parkList

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def getViewpointSource(self, parameters):
        """
        Creates event layer from
        ETV.REPORT_DATA_READER.Viewpoint or ViewBearings
        """
        pass

    def createBearingFeatures(self, sourceFeatureClass, sourceField, outSR, outputFeatureClass):
        """
        Creates left or right bearing features from
        ETV.REPORT_DATA_READER.Viewpoint  or ViewBearings
        """
        arcpy.BearingDistanceToLine_management(sourceFeatureClass, outputFeatureClass, "Longitude", "Latitude", "Distance", "METERS", sourceField, "DEGREES", "GEODESIC", "ViewConeID", outSR)
        arcpy.RepairGeometry_management(outputFeatureClass)
        arcpy.AddMessage('\n Created '  + outputFeatureClass)

    def createViewPolygons(self, sourceCursor, isCircle = False):
        pass

    def projectDataset(self, sourceDataset, outputDataset, outputSpatialRef, transform=None):
        """
            Re-projects and repairs source dataset
        """
        arcpy.Project_management(sourceDataset, outputDataset, outputSpatialRef, transform)
        arcpy.RepairGeometry_management(outputDataset)
        arcpy.AddMessage('\n Re-projected to '  + outputDataset)


    def execute(self, parameters, messages):
        message = ""
        today=datetime.now()
        datestamp = str(today.isoformat()).replace('-','')[0:8]
        metadataTemplates = ["ETVviewcones.xml"]

        arcpy.env.overwriteOutput = 1
        tempLayer = "tempLayer"
        newTempLayer = "tempLayer2"

        outputInitTempFCName0 = r"ViewpointSource0"
        outputInitTempFCName = r"ViewpointSource"
        outputLeftBearingFCName = r"ViewBearingLeft"
        outputRightBearingFCName = r"ViewDearingRight"
        outputBearingMergeFCName = r"ViewBearingsMerge"
        outputBearingFCName = "ARD_VIEW_"  +parameters[1].valueAsText + "_ViewBearings_ln" #r"ViewBearings"
        outputBearingProjectedFCName = "ARD_VIEW_"  +parameters[1].valueAsText + "_ViewBearings_projected_ln"
        outputLookupTableName = r"ARD_VIEW_"  +parameters[1].valueAsText + "_ViewpointSourceLookup"
        bearingLayer = r'bearingLayer'
        outputTempCircularName = r'tempCircular'
        outputNonCircularTempName = r'tempNonCircular'

        whereClause = "UNIT_CODE = '" + parameters[1].valueAsText + "'"
        addFieldList = ["ViewpointID","ViewID","UNIT_CODE","ViewpointName", "ViewedLandscapeNumber", "ViewNumber","Longitude","Latitude","LeftBearing", "RightBearing","Distance"]

        selectCircularCones = 'LeftBearing = 359 AND RightBearing = 0'
        selectNonCircularCones = 'LeftBearing <> 359 AND RightBearing <> 0'
        viewDistance = int(parameters[3].valueAsText)

        sourceView = parameters[0].valueAsText
        outputGDBFCInitTemp0 = os.path.join(parameters[2].valueAsText, outputInitTempFCName0)
        outputGDBFCInitTemp = os.path.join(parameters[2].valueAsText, outputInitTempFCName)
        outputGDBFCLeftBearing = os.path.join(parameters[2].valueAsText, outputLeftBearingFCName)
        outputGDBFCRightBearing = os.path.join(parameters[2].valueAsText, outputRightBearingFCName)
        outputGDBFCMergeBearing = os.path.join(parameters[2].valueAsText, outputBearingMergeFCName)
        outputGDBFCBearing = os.path.join(parameters[2].valueAsText, outputBearingFCName)
        outputGDBFCBearingProjected = os.path.join(parameters[2].valueAsText, outputBearingProjectedFCName)
        outputTempCircular = os.path.join(parameters[2].valueAsText, outputTempCircularName)
        #outputTempNonCircular = os.path.join(parameters[2].valueAsText, outputTempNonCircularNonCircularName)

        WGSSpatialRef = arcpy.SpatialReference(4326)
        outputSpatialReference = parameters[4].valueAsText

        # Get records from producton database and create temporary point feature class and lookup table
        arcpy.MakeXYEventLayer_management(sourceView, "Longitude", "Latitude", tempLayer); messages.addGPMessages()
        arcpy.CopyFeatures_management(tempLayer, outputGDBFCInitTemp0); messages.addGPMessages()
        arcpy.RepairGeometry_management(outputGDBFCInitTemp0); messages.addGPMessages()
        arcpy.MakeFeatureLayer_management(outputGDBFCInitTemp0, newTempLayer); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(newTempLayer, "NEW_SELECTION", whereClause); messages.addGPMessages()
        arcpy.CopyFeatures_management(newTempLayer, outputGDBFCInitTemp); messages.addGPMessages()
        arcpy.RepairGeometry_management(outputGDBFCInitTemp); messages.addGPMessages()
        arcpy.CopyRows_management(outputGDBFCInitTemp, os.path.join(parameters[2].valueAsText,outputLookupTableName)); messages.addGPMessages()

        arcpy.Delete_management(outputGDBFCInitTemp0); messages.addGPMessages()

        # Create left and right bearing polyline feature classes, merge and dissolve
        CreateBearings.createBearingFeatures(self, outputGDBFCInitTemp, "LeftBearing", WGSSpatialRef, outputGDBFCLeftBearing)
        CreateBearings.createBearingFeatures(self, outputGDBFCInitTemp, "RightBearing", WGSSpatialRef, outputGDBFCRightBearing)

        arcpy.Merge_management([outputGDBFCLeftBearing, outputGDBFCRightBearing], outputGDBFCMergeBearing); messages.addGPMessages()
        arcpy.Dissolve_management(outputGDBFCMergeBearing, outputGDBFCBearing, "ViewConeID", "", "MULTI_PART", "DISSOLVE_LINES"); messages.addGPMessages()

        # Join to lookup table to populate bearing values
        arcpy.JoinField_management(outputGDBFCBearing, "ViewConeID", os.path.join(parameters[2].valueAsText,outputLookupTableName), "ViewConeID", addFieldList); messages.addGPMessages()
        arcpy.Project_management(outputGDBFCBearing, outputGDBFCBearingProjected, outputSpatialReference); messages.addGPMessages()
        arcpy.RepairGeometry_management(outputGDBFCBearingProjected); messages.addGPMessages()

##        # Select and Cursor through bearing features, creating view bearing line features
##        arcpy.MakeFeatureLayer_management(outputGDBFCBearing, bearingLayer); messages.addGPMessages()
##        # Get circular views and create polygons:
##        arcpy.SelectLayerByAttribute_management(bearingLayer, selectCircularCones); messages.addGPMessages()
##        arcpy.Buffer_analysis(bearingLayer, outputTempCircular, viewDistance); messages.addGPMessages()
##        arcpy.RepairGeometry_management(outputTempCircular); messages.addGPMessages()
##        arcpy.SelectLayerByAttribute_management(bearingLayer, "CLEAR_SELECTION"); messages.addGPMessages()
##        #circularBearingCursor = arcpy.SearchCursor(outputGDBFCBearing, selectCircularCones); messages.addGPMessages()
##        #for row in circularBearingCursor:
##        #    viewPointID = row.getValue("ViewpointID")
##            #arcpy.SelectLayerByAttribute_management(bearingLayer, )
##        #    arcpy.Buffer_analysis(row@SHAPE, )
##        #del row, circularBearingCursor
##
##        # Get non-circular views
##        if (initialBearing == 359):  # For some non-circular views, initial bearings are > than final, hence the explicit logic
##                deltaBearing = 360 #finalBearing = 360
##            else:
##                deltaBearing = finalBearing - initialBearing
##            #arcpy.AddMessage("\n DELTA BEARING = " + str(deltaBearing) + " and initialBearing = " + str(initialBearing) + "\n")
##
##        deltaBearingCheck = abs(deltaBearing)
##        #arcpy.SelectLayerByAttribute_management(bearingLayer, selectNonCircularCones); messages.addGPMessages()
##        noncircularBearingCursor = arcpy.SearchCursor(bearingLayer, selectNonCircularCones); messages.addGPMessages()
##        for row in noncircularBearingCursor:
##            coneID = row.getValue("ViewConeID")
##            feat = row.getValue("SHAPE")
##            lBearing = row.getValue("LeftBearing")
##            rBearing = row.getValue("RightBearing")
##            if (rBearing - lBearing) > 180:
##                isConvex = True
##            else:  isConvex = False
##            arcpy.Buffer_analysis(feat, outputTempNonCircular, viewDistance); messages.addGPMessages()
##            arcpy.FeatureToPolygon_management([], ); messages.addGPMessages()
##            arcpy.RepairGeometry_management(); messages.addGPMessages()
##
##        del row, noncircularBearingCursor

        # Import metadata
        if (parameters[5].valueAsText <> None):
            arcpy.MetadataImporter_conversion(os.path.join(parameters[5].valueAsText, metadataTemplates[0]), outputGDBFCBearing); messages.addGPMessages()
            arcpy.MetadataImporter_conversion(os.path.join(parameters[5].valueAsText, metadataTemplates[0]), outputGDBFCBearingProjected); messages.addGPMessages()

        # Delete items
        itemsToDelete = [outputGDBFCLeftBearing, outputGDBFCRightBearing, outputGDBFCMergeBearing, outputGDBFCInitTemp, tempLayer, newTempLayer]
        for item in itemsToDelete:
            if arcpy.Exists(item):
                arcpy.Delete_management(item); messages.addGPMessages()



class CreateViewedLandscapes(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "2 Create Viewed Landscape Polygons"
        self.description = "Create or update Viewed Landscape features from Enjoy the View (Scenic Quality Inventory) database"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName = "Source Viewpoint Table",  # Needs to be the ViewBearings view
            name = "viewpointSource",
            datatype = "DETable",
            parameterType = "Required",
            direction = "Input")
        param0.value = r"Database Connections\ETV_on_INP2300FCVWHIS1_Report_Data_Reader.sde\ETV.web.ViewBearings"

        param1 = arcpy.Parameter(
            displayName = "Output GeoDatabase",
            name = "outDB",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input")
        param1.value = r"D:\Workspace\Default.gdb"

        param2 = arcpy.Parameter(
            displayName = "Choose a park to process",
            name = "parkToProcess",
            datatype = "String",
            parameterType  = "Required",
            direction = "Input")

        param3 = arcpy.Parameter(
            displayName = "View Radius (in meters)",
            name = "viewRadius",
            datatype = "String",
            parameterType = "Required",
            direction = "Input"
            )
        param3.value = r"40000"

        param4 = arcpy.Parameter(
            displayName = "Output Spatial Reference",
            name = "outSR",
            datatype = "GPSpatialReference",
            parameterType = "Required",
            direction = "Input"
            )

        param5 = arcpy.Parameter(
            displayName = "Folder Containing Metadata Template",
            name = "metaFolder",
            datatype = "Folder",
            parameterType = "Optional",
            direction = "Input"
            )
        param5.value = r"X:\ProjectData\NRSS_ARD\EnjoyTheView\Templates\Metadata"

        params = [param0, param1, param2, param3, param4, param5]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        # Modified from the example shown here: http://blogs.esri.com/esri/arcgis/2011/08/25/generating-a-choice-list-from-a-field/
        if parameters[0].value and parameters[1].value:
            parkList = [str(val) for val in
                                            sorted(
                                              set(
                                                row.getValue(ddDisplayField)
                                                for row in arcpy.SearchCursor(parameters[0].value)
                                                  )
                                               )
                                          ]
            parkList.append("ALL")
            parameters[2].filter.list = parkList
##            parameters[2].filter.list = [str(val) for val in
##                                            sorted(
##                                              set(
##                                                row.getValue(ddDisplayField)
##                                                for row in arcpy.SearchCursor(parameters[0].value)
##                                                  )
##                                               )
##                                          ]
##        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def calculateLatLong(self, bearing, dist, cenX, cenY):
        R = EarthRadiusMeters
        brng = bearing * (math.pi / 180)
        lat1 = cenY * (math.pi / 180) # Convert lat to radians
        lon1 = cenX * (math.pi / 180) # Convert long to radians
        lat2 = math.asin( math.sin(lat1)*math.cos(dist/R) +
                                math.cos(lat1)*math.sin(dist/R)*math.cos(brng) )
        lon2 = lon1 + math.atan2(math.sin(brng)*math.sin(dist/R)*math.cos(lat1),
                                        math.cos(dist/R)-math.sin(lat1)*math.sin(lat2))

        DestinationPoint = [lon2 * (180 / math.pi), lat2 * (180 / math.pi)]
        return DestinationPoint


    def execute(self, parameters, messages):
        message = ""
        today=datetime.now()
        datestamp = str(today.isoformat()).replace('-','')[0:8]
        metadataTemplates = ["ETVviewcones.xml"]
        viewpointSource = "viewpointSource"

        arcpy.env.overwriteOutput = 1

        EarthRadiusMeters = 6378137.0 # earth's mean radius in meters

        WGSSpatialRef = arcpy.SpatialReference(4326)
        outputSpatialReference = parameters[4].valueAsText
        #ServiceSpatialRef = 'PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.017453292519943295]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],PARAMETER["Auxiliary_Sphere_Type",0.0],UNIT["Meter",1.0]]'

        joinField = "ViewConeID"
        fieldList = ["ViewpointID","ViewConeID","ViewID","UNIT_CODE","ViewpointName", "ViewedLandscapeNumber", "ViewNumber", "Longitude","Latitude","LeftBearing", "RightBearing","Distance"]
        addfieldList = ["ViewpointID","ViewID","UNIT_CODE","ViewpointName", "ViewedLandscapeNumber", "ViewNumber","Longitude","Latitude","LeftBearing", "RightBearing","Distance"]
        if parameters[2].valueAsText <> "ALL":
            fullFCName = "ARD_VIEW_"  +parameters[2].valueAsText + "_ViewedLandscapes_py" # Park-specific "ARD_<UNIT_CODE>_VIEW_ViewedLandscapes_py"
            fullFCNameOutputSR = "ARD_VIEW_" + parameters[2].valueAsText + "_ViewedLandscapes_projected_py"
            whereClause = "UNIT_CODE = '" + parameters[2].valueAsText + "'"
        else:
            fullFCName = "ARD_VIEW_ViewedLandscapes_py"
            fullFCNameOutputSR = "ARD_VIEW_ViewedLandscapes_projected_py"

        arcpy.CopyRows_management(parameters[0].value, os.path.join(parameters[1].valueAsText,"tempTable")); messages.addGPMessages()

        # Calculate helper variables
        d2r = math.pi / 180  # degrees to radians
        r2d = 180 / math.pi # radians to degrees

        points = 32; # arcline points
        radius = int(parameters[3].valueAsText)

        # find the radius in lat/lon
        #rlat = (radius / EarthRadiusMeters) * r2d;
        #rlng = rlat / math.cos(center.Y * d2r);

        # Define array (list) for lat/long points using radius - becomes input for cone polygon
        radialPts = []
        count =  0

        if parameters[2].valueAsText <> "ALL":
            cursor = arcpy.SearchCursor(parameters[0].valueAsText, whereClause)
        else:
            cursor = arcpy.SearchCursor(parameters[0].valueAsText)
        for row in cursor: # Each view
            count = count + 1
            outputFCName = "View_" + str(row.getValue(fieldList[0])) + "_" + str(row.getValue(fieldList[1]))
            initialBearing = int(row.getValue(fieldList[9]))
            finalBearing = int(row.getValue(fieldList[10]))
            arcpy.AddMessage("\nLeftBearing: " + str(initialBearing) + " Right Bearing: " + str(finalBearing))
            centerX = row.getValue(fieldList[7])
            centerY = row.getValue(fieldList[8])
            # Cursor through bearing records and create point array for building cone polygon
            #if (initialBearing > finalBearing):
            if (initialBearing == 359):  # For some non-circular views, initial bearings are > than final, hence the explicit logic
                deltaBearing = 360 #finalBearing = 360
            else:
                deltaBearing = finalBearing - initialBearing
            arcpy.AddMessage("\n DELTA BEARING = " + str(deltaBearing) + " and initialBearing = " + str(initialBearing) + "\n")

            deltaBearingCheck = abs(deltaBearing)
            deltaBearing = abs(deltaBearing/points)
            arcpy.AddMessage("\n deltaBearing: " + str(deltaBearing))

            # Add center point to array if not a 360 degree view
            if deltaBearingCheck <> 360:
                radialPts.append([centerX, centerY])
                arcpy.AddMessage("\n Center Point: " +str(centerX)+ ", " + str(centerY) )
                #arcpy.AddMessage("\n\n DELTA BEARING: " + str(deltaBearingCheck) + "\n")
                #arcpy.AddMessage("\n\n ADDED CENTER to " + row.getValue(fieldList[4]) + "\n")
                outPt = CreateViewedLandscapes.calculateLatLong(self, initialBearing, radius, centerX, centerY)
                radialPts.append([outPt[0], outPt[1]])
            for i in range(1, points):
                 # Determine 'direction' of increment
##                if (initialBearing == 359) or (initialBearing < finalBearing): # clockwise/positive
##                    increment = initialBearing + i*deltaBearing
##                else: # counter-clockwise/negative
##                    increment = initialBearing + i*deltaBearing
                if (initialBearing + i*deltaBearing) < 360:  # need to account for radians, not degrees to compensate for left > right bearings
                    outPt = CreateViewedLandscapes.calculateLatLong(self, (initialBearing + i*deltaBearing), radius, centerX, centerY)
                else:
                    outPt = CreateViewedLandscapes.calculateLatLong(self, (0 + i*deltaBearing), radius, centerX, centerY)
                outPt = CreateViewedLandscapes.calculateLatLong(self, increment, radius, centerX, centerY)
                #outPt = CreateViewedLandscapes.calculateLatLong(self, (initialBearing + i*deltaBearing), radius, centerX, centerY)
                radialPts.append([outPt[0], outPt[1]])
                arcpy.AddMessage("\n Output Point: " +str(outPt[0])+ ", " + str(outPt[1]) )

            # Create polygon object from point array
            conePoly = arcpy.Polygon(
                arcpy.Array([arcpy.Point(*coords) for coords in radialPts]), WGSSpatialRef); messages.addGPMessages()

            # Add polygon feature to interim and final feature class(es), repairing geometry and joining fields
            arcpy.CopyFeatures_management(conePoly, os.path.join(parameters[1].valueAsText,outputFCName)); messages.addGPMessages()
            arcpy.RepairGeometry_management(os.path.join(parameters[1].valueAsText,outputFCName)); messages.addGPMessages()
            arcpy.AddField_management(os.path.join(parameters[1].valueAsText,outputFCName), fieldList[1], "SHORT", "", "", "", "", "NULLABLE"); messages.addGPMessages()
            arcpy.CalculateField_management(os.path.join(parameters[1].valueAsText,outputFCName), fieldList[1], row.getValue(fieldList[1])); messages.addGPMessages()
            arcpy.JoinField_management(os.path.join(parameters[1].valueAsText,outputFCName), joinField, os.path.join(parameters[1].valueAsText,"tempTable"), joinField, addfieldList); messages.addGPMessages()
            arcpy.AddField_management(os.path.join(parameters[1].valueAsText,outputFCName), "DateCreated", "TEXT", "", "", "8", "", "NULLABLE"); messages.addGPMessages()
            arcpy.CalculateField_management(os.path.join(parameters[1].valueAsText,outputFCName), "DateCreated", datestamp); messages.addGPMessages()

            if (parameters[5].valueAsText <> None):
                arcpy.MetadataImporter_conversion(os.path.join(parameters[5].valueAsText, metadataTemplates[0]), os.path.join(parameters[1].valueAsText,outputFCName)); messages.addGPMessages()
            if count == 1:
                arcpy.CopyFeatures_management(os.path.join(parameters[1].valueAsText,outputFCName), os.path.join(parameters[1].valueAsText,fullFCName)); messages.addGPMessages()
            else:
                arcpy.Append_management(os.path.join(parameters[1].valueAsText,outputFCName), os.path.join(parameters[1].valueAsText,fullFCName), "NO_TEST"); messages.addGPMessages()

            # Delete interim feature class
            arcpy.Delete_management(os.path.join(parameters[1].valueAsText,outputFCName)); messages.addGPMessages()
            radialPts = [] # Re-initialize array

        # Re-project to output spatial reference
        arcpy.RepairGeometry_management(os.path.join(parameters[1].valueAsText,fullFCName)); messages.addGPMessages()
        arcpy.AlterField_management(os.path.join(parameters[1].valueAsText,fullFCName), "Distance", "Radius_m", "Radius_m"); messages.addGPMessages()
        arcpy.CalculateField_management(os.path.join(parameters[1].valueAsText,fullFCName), "Radius_m", parameters[3].valueAsText); messages.addGPMessages()
        arcpy.Project_management(os.path.join(parameters[1].valueAsText, fullFCName), os.path.join(parameters[1].valueAsText, fullFCNameOutputSR), outputSpatialReference); messages.addGPMessages()
        #arcpy.Project_management(os.path.join(parameters[1].valueAsText, fullFCName), os.path.join(parameters[1].valueAsText, fullFCNameWebMerc), ServiceSpatialRef); messages.addGPMessages()
        arcpy.RepairGeometry_management(os.path.join(parameters[1].valueAsText, fullFCNameOutputSR)); messages.addGPMessages()

        itemsToDelete = [os.path.join(parameters[1].valueAsText, "tempTable")]
        for item in itemsToDelete:
            if arcpy.Exists(item):
                arcpy.Delete_management(item); messages.addGPMessages()

class CalculateVisiblePointAreas(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "5 Calculate Visible Point Areas"
        self.description = "Create polygon feature class with counts of viewpoints visible from Viewed Landscape viewshed surface."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

##        param0 = arcpy.Parameter(
##            displayName = "Webmercator Unit Bounds Feature Class",
##            name = "unitBounds",
##            datatype = "GPFeatureLayer",
##            parameterType = "Required",
##            direction = "Input")
##        param0.value = r"X:\ProjectData\Data_Processing\Bounds_Processing\Data\IMD_Bounds.gdb\imd_unit_bounds_webmercator"
##
##        param1 = arcpy.Parameter(
##            displayName = "Replace Feature",
##            name = "APPA",
##            datatype = "GPFeatureLayer",
##            parameterType = "Required",
##            direction = "Input")
##        param1.value = r"X:\ProjectData\Data_Processing\Bounds_Processing\Data\UnitBound_Processing.gdb\appa_simplified_forServices"
##
##        param2 = arcpy.Parameter(
##            displayName = "Convex Hulls Unit Bounds Feature Class",
##            name = "unitBoundsCH",
##            datatype = "GPFeatureLayer",
##            parameterType = "Required",
##            direction = "Input")
##        param2.value = r"X:\ProjectData\Data_Processing\Bounds_Processing\Data\IMD_Bounds.gdb\imd_unit_bounds_webmercator_convexhulls"
##
##        param3 = arcpy.Parameter(
##            displayName = "Output GeoDatabase",
##            name = "outDB",
##            datatype = "DEWorkspace",
##            parameterType = "Required",
##            direction = "Input")
##        #param3.value = "X:\ProjectData\Data_Processing\Bounds_Processing\Metadata_Templates"
##
##        params = [param0, param1, param2, param3]
##        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return


    def execute(self, parameters, messages):
        message = ""
        today=datetime.now()
        datestamp = str(today.isoformat()).replace('-','')[0:8]

        arcpy.env.overwriteOutput = 1
        GDBFeatureClassName = "imd_unit_bounds"
        GDBFeatureClassWebMerc = (parameters[0].valueAsText)
        GDBFeatureClassConvexHulls = (parameters[2].valueAsText)
        outputSDEFeatureClassWebMerc = ("Database Connections\\GDB_NRSS.DBO.INPNISCVDBNRSST_IMDGIS.sde\\" + GDBFeatureClassName + "_webmercator")
        outputSDEFeatureClassConvexHulls = ("Database Connections\\GDB_NRSS.DBO.INPNISCVDBNRSST_IMDGIS.sde\\" + GDBFeatureClassName + "_webmercator_convexhulls")
        outputSDEFeatureClassWebMerc1 = ("Database Connections\\GDB_NRSS.DBO.INPNISCVDBNRSST_IMDGIS.sde\\" + GDBFeatureClassName + "_webmercator")
        outputSDEFeatureClassConvexHulls1 = ("Database Connections\\GDB_NRSS.DBO.INPNISCVDBNRSST_IMDGIS.sde\\" + GDBFeatureClassName + "_webmercator_convexhulls")
        outputSDEFeatureClassNPSData = ("Database Connections\\NPSData.DBO.INPNISCVDBNRSST_IMDGIS.sde\\" + GDBFeatureClassName + "_webmercator")
        APPA_generalized = (parameters[1].valueAsText)
        temp = r"X:\ProjectData\Data_Processing\Bounds_Processing\Data\Scratch.gdb\Temp"
        tempLayer = r"X:\ProjectData\Data_Processing\Bounds_Processing\Data\Scratch.gdb\webmercatorTemp"
        tempFeature = r"X:\ProjectData\Data_Processing\Bounds_Processing\Data\Scratch.gdb\TempFeature"

        arcpy.CopyFeatures_management(GDBFeatureClassWebMerc, temp); messages.addGPMessages()
        arcpy.MakeFeatureLayer_management(temp, tempLayer); messages.addGPMessages()

        arcpy.SelectLayerByAttribute_management(tempLayer, "NEW_SELECTION", "UNIT_CODE = 'APPA'"); messages.addGPMessages()
        if int(arcpy.GetCount_management(tempLayer).getOutput(0)) > 0:
            arcpy.DeleteFeatures_management(tempLayer); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(tempLayer, "CLEAR_SELECTION"); messages.addGPMessages()

        arcpy.Merge_management([tempLayer,APPA_generalized],tempFeature); messages.addGPMessages()
        arcpy.RepairGeometry_management(tempFeature); messages.addGPMessages()

        arcpy.DeleteFeatures_management(outputSDEFeatureClassWebMerc); messages.addGPMessages()
        arcpy.DeleteFeatures_management(outputSDEFeatureClassConvexHulls); messages.addGPMessages()
        arcpy.DeleteFeatures_management(outputSDEFeatureClassNPSData); messages.addGPMessages()

        arcpy.CopyFeatures_management(tempFeature, outputSDEFeatureClassWebMerc1); messages.addGPMessages()
        arcpy.CopyFeatures_management(GDBFeatureClassConvexHulls, outputSDEFeatureClassConvexHulls1); messages.addGPMessages()
        arcpy.CopyFeatures_management(tempFeature, outputSDEFeatureClassNPSData); messages.addGPMessages()

        itemsToDelete = [temp, tempLayer, tempFeature] #tempLayer, tempFeature
        for item in itemsToDelete:
            if arcpy.Exists(item):
                arcpy.Delete_management(item); messages.addGPMessages()

class CalculateScenicInventoryValues(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "3 Calculate Scenic Inventory Values"
        self.description = "Calculate Scenic Inventory values (individual and composite) for Viewed Landscape polygons from Enjoy the View (Scenic Quality Inventory) database"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
            displayName = "Viewed Landscape Feature Class",
            name = "viewedLandscapes",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input")
        #param0.value = r"D:\Workspace\Default.gdb\ARD_VIEW_ViewedLandscapes_py"

        param1 = arcpy.Parameter(
            displayName = "Source Enjoy the View Database",
            name = "sivSource",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input")

        params = [param0, param1]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
##        if parameters[0].value and parameters[1].value:
##            parameters[2].filter.list = [str(val) for val in
##                                            sorted(
##                                              set(
##                                                row.getValue(ddDisplayField)
##                                                for row in arcpy.SearchCursor(parameters[1].value)
##                                                  )
##                                               )
##                                          ]

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def addSIVFields(self, targetFC, fieldName, fieldType, fieldLength, messages):
        arcpy.AddField_management(targetFC, fieldName, fieldType, "", "", fieldLength, "", "NULLABLE"); messages.addGPMessages()


    def execute(self, parameters, messages):
        message = ""
        today=datetime.now()
        datestamp = str(today.isoformat()).replace('-','')[0:8]

        arcpy.env.overwriteOutput = 1

        viewedLandscapeFCName = "ARD_VIEW_ViewedLandscapes_py" # Park-specific "ARD_<UNIT_CODE>_VIEW_ViewedLandscapes_py"
        viewedLandscapeFCNameWebMerc = "ARD_VIEW_ViewedLandscapes_webmerc_py"

        viewedLandscapeFC = parameters[0].valueAsText
        idField = "ViewID"
        fieldList = ["ScenicQualityRating","ViewImportanceRating","ScenicInventoryValue","ScenicInventoryRanking"]
        sql = r'select ViewID, SSRS.View_SQRating(ViewID) ScenicQualityRating, SSRS.View_ImportanceRating(ViewID) ViewImportanceRating, SSRS.View_SQRating(ViewID) + SSRS.View_ImportanceRating(ViewID) ScenicInventoryValue from web.ViewBearings'
        ScenicInventoryRankings = {'A1': 'VH','A2': 'VH','A3': 'VH','A4': 'H','A5': 'M','B1': 'VH','B2': 'VH','B3': 'H','B4': 'M','B5': 'L','C1': 'H','C2': 'H','C3': 'M','C4': 'L','C5': 'L','D1': 'H','D2': 'M','D3': 'L','D4': 'VL','D5': 'VL','E1': 'M','E2': 'L','E3': 'VL','E4': 'VL','E5': 'VL'}

        # Add fields to feature class
        # Cursor through features, calculating fields:
        for field in fieldList:
            CalculateScenicInventoryValues.addSIVFields(self, viewedLandscapeFC, field, "TEXT", 5, messages)
        # Add placeholder fields for composite SIV and ranking
        #for field in ["CompositeScenicInventoryValue","CompositeScenicInventoryRanking"]:
         #   CalculateScenicInventoryValues.addSIVFields(self, viewedLandscapeFC, field, "TEXT", 5, messages)

        # Get SQ, VI, and SIV from database
        sdeConn = arcpy.ArcSDESQLExecute(parameters[1].valueAsText)
        #arcpy.AddMessage('\n\t'+ sql)
        sdeReturn = sdeConn.execute(sql)

        # Cursor through rows, updating attributes
        if isinstance(sdeReturn, list):
            for i in sdeReturn:
                viewID = int(i[0]) # First column
                nullVal = 'Missing'
                with arcpy.da.UpdateCursor(viewedLandscapeFC, fieldList, 'ViewID = ' + str(int(i[0]))) as cursor:
                    for row in cursor:
                        if i[1] is not '':
                            row[0] = i[1] # Scenic quality rating
                        else: row[0] = nullVal
                        if i[2] is not '':
                            row[1] = i[2] # View importance rating
                        else: row[1] = nullVal
                        if i[2] is not '':
                            row[2] = i[3] # Scenic inventory value
                        else: row[2] = nullVal
                        if i[2] is not '':
                            row[3] = ScenicInventoryRankings.get(i[3])
                        else: row[3] = nullVal
                        cursor.updateRow(row); messages.addGPMessages()
                del cursor


class CreateViewshed(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "4 Create Viewsheds and Visible Areas"
        self.description = "Given a DEM, a set of viewpoints, and a view distance, output viewsheds for each viewpoint plus a composite viewshed, an observer visbility surface, and a visible areas polygon feature class."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
            displayName = "Source DEM",
            name = "demLayer",
            datatype = "GPRasterLayer",
            parameterType = "Required",
            direction = "Input")
        #param0.value = r"X:\NRSSData\ReferenceData\NRCS_DEM_30m_Fall_2012\CONUS\DEM_NED_Float.gdb\DEM_CONUS_Albers_Flt"

        param1 = arcpy.Parameter(
            displayName = "Source Viewpoint Table",  # Needs to be the ViewBearings view
            name = "viewpointSource",
            datatype = "DETable",
            parameterType = "Required",
            direction = "Input")
        #param1.value = r"Database Connections\ETV_on_INP2300FCVWHIS1_Report_Data_Reader.sde\ETV.web.ViewBearings"

        param2 = arcpy.Parameter(
            displayName = "Choose a park to extract",
            name = "parkToExtract",
            datatype = "String",
            parameterType  = "Required",
            direction = "Input")

        param3 = arcpy.Parameter(
            displayName = "View Distance (in meters)",
            name = "viewDist",
            datatype = "String",
            parameterType = "Required",
            direction = "Input"
            )
        param3.value = r"40000"

        param4 = arcpy.Parameter(
            displayName = "Output GeoDatabase",
            name = "outDB",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input")
        param4.value = r"D:\Workspace\Default.gdb"

##        param5 = arcpy.Parameter(
##            displayName = "Output folder for viewshed rasters",
##            name = "outputFolder",
##            datatype = "Folder",
##            parameterType = "Required",
##            direction = "Input"
##        )
##        param5.value = r"D:\temp\trash\ETVTests"

##        param6 = arcpy.Parameter(
##            displayName = "Viewed Landscape Feature Class",
##            name = "viewedLandscapes",
##            datatype = "GPFeatureLayer",
##            parameterType = "Required",
##            direction = "Input")
##        param6.value = r"D:\Workspace\Default.gdb\ARD_VIEW_ViewedLandscapes_py"

        params = [param0, param1, param2, param3, param4]
        #params = [param0, param1, param2, param3, param4, param5, param6]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        # Modified from the example shown here: http://blogs.esri.com/esri/arcgis/2011/08/25/generating-a-choice-list-from-a-field/
        if parameters[0].value and parameters[1].value:
            parameters[2].filter.list = [str(val) for val in
                                            sorted(
                                              set(
                                                row.getValue(ddDisplayField)
                                                for row in arcpy.SearchCursor(parameters[1].value)
                                                  )
                                               )
                                          ]

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return


##    def addSIVFields(self, targetFC, fieldName, fieldType, fieldLength, messages):
##        arcpy.AddField_management(targetFC, fieldName, fieldType, "", "", fieldLength, "", "NULLABLE"); messages.addGPMessages()

    def execute(self, parameters, messages):
        message = ""
        today=datetime.now()
        datestamp = str(today.isoformat()).replace('-','')[0:8]

        arcpy.env.overwriteOutput = 1
        arcpy.env.snapRaster = parameters[0].valueAsText
        arcpy.CheckOutExtension("3D")
        arcpy.CheckOutExtension("Spatial")

        # Variables specific to park and viewed landscapes
        viewPoints = []
        viewPointFeatures = []
        whereClause = "UNIT_CODE = '" + parameters[2].valueAsText + "'"
        sourceView = "sourceView"
        tempTable = "tempTable"
        tempLayer = "tempLayer"
        viewshedRoot = "ARD_VIEW_" + parameters[2].valueAsText + "_Viewshed"
        viewshedRootClipped = "ARD_VIEW_" + parameters[2].valueAsText + "_Clipped_Viewshed"
        viewshedRootClippedTemp = "ARD_VIEW_" + parameters[2].valueAsText + "_ClippedTemp_Viewshed"
        viewshedRootVisibleArea = "ARD_VIEW_" + parameters[2].valueAsText + "_VisibleArea"
        tempFeatureClass = os.path.join(parameters[4].valueAsText, "viewPoints")
        tempFeatureClassOutput = os.path.join(parameters[4].valueAsText, viewshedRoot + "_ObserverPoints_projected_pt")
        #tempFeatureClassAlbers = os.path.join(parameters[4].valueAsText, viewshedRoot + "_ObserverPoints_albers_pt")
        #tempPtClass = os.path.join(parameters[4].valueAsText, "ptAlbers0")
        tempPtClassOutput = os.path.join(parameters[4].valueAsText, "ptProj")
        #tempPtClassAlbers = os.path.join(parameters[4].valueAsText, "ptAlbers")
        tempClipped = os.path.join(parameters[4].valueAsText,"tempClipped")

        outViewshed = ""
        compositeViewshed = "ARD_VIEW_" +parameters[2].valueAsText + "_VisibleAreas" # "_VisibleAreas"
        compositeViewshedPolys = "ARD_VIEW_" +parameters[2].valueAsText + "_VisibleAreas_py"
        unionedVisibleAreas = "ARD_VIEW_" +parameters[2].valueAsText + "_UnionedVisibleAreas"
        intersectedVisibleAreas = "ARD_VIEW_" +parameters[2].valueAsText + "_IntersectedVisibleAreas"
        outVisibility = "ARD_VIEW_" +parameters[2].valueAsText + "_Visibility_byObserver"

        joinFields = ["ViewpointID","ViewConeID","ViewID","UNIT_CODE","ViewedLandscapeNumber","ViewNumber", "Longitude","Latitude","LeftBearing", "RightBearing","ScenicQualityRating","ViewImportanceRating","ScenicInventoryValue"]

        WGSSpatialRef = arcpy.SpatialReference(4326)
        AlbersSpatialRef = arcpy.SpatialReference(102039)
        # Match output spatial reference to input DEM
        desc = arcpy.Describe(parameters[0].valueAsText)
        outputSpatialRef = desc.SpatialReference


        # Use event layer to make observer (view) points feature class
        # Direct MakeTableView does not honor the whereClause
##        with arcpy.da.SearchCursor(parameters[1].valueAsText, "*", whereClause) as cursor:
##            for row in cursor:
##                # Write rows to temp table
##                arcpy.CopyRows_management(row ,os.path.join(parameters[4].valueAsText,sourceView)); messages.addGPMessages()


##        with arcpy.da.SearchCursor(parameters[1].value, "*", whereClause) as cursor: #valueAsText
##            for row in cursor:
##                # Get viewpoints for park  from database
##                viewPoints.append([row[7], row[8]])
##
##        arcpy.AddMessage("\nviewPoints: " + str(viewPoints))
##
##        # Create point feature class from viewpoint array
##        for vp in viewPoints:
##            arcpy.AddMessage("\nvp: " + str(vp))
##            arcpy.AddMessage("\ncoords in vp:" + str(vp[0]) + "," + str(vp[1]))
##            viewPointFeatures.append(arcpy.PointGeometry(arcpy.Point(vp[0], vp[1]), WGSSpatialRef))

        arcpy.CopyRows_management(parameters[1].value, os.path.join(parameters[4].valueAsText,tempTable)); messages.addGPMessages()
        arcpy.TableSelect_analysis(os.path.join(parameters[4].valueAsText,tempTable), os.path.join(parameters[4].valueAsText,sourceView), whereClause); messages.addGPMessages()

        arcpy.MakeXYEventLayer_management(os.path.join(parameters[4].valueAsText, sourceView), "Longitude", "Latitude", os.path.join(parameters[4].valueAsText, tempLayer), WGSSpatialRef); messages.addGPMessages()
        arcpy.CopyFeatures_management(os.path.join(parameters[4].valueAsText, tempLayer), tempFeatureClass); messages.addGPMessages()
        arcpy.RepairGeometry_management(tempFeatureClass); messages.addGPMessages()
        arcpy.Project_management(tempFeatureClass, tempFeatureClassOutput, outputSpatialRef); messages.addGPMessages()
        #arcpy.Project_management(tempFeatureClass, tempFeatureClassOutput, AlbersSpatialRef); messages.addGPMessages()
        arcpy.RepairGeometry_management(tempFeatureClassOutput); messages.addGPMessages()

        # Set processing extent to view point feature class extent +/- 60000 meters
        # Clip source DEM to park extent
        arcpy.MinimumBoundingGeometry_management(tempFeatureClassOutput, os.path.join(parameters[4].valueAsText, "mbr"), "RECTANGLE_BY_AREA", "ALL"); messages.addGPMessages()
        fcExtent = arcpy.Describe(os.path.join(parameters[4].valueAsText, "mbr")).extent
        # Assumes source DEM spatial reference is projected (in meters)
        arcpy.env.extent = arcpy.Extent(fcExtent.XMin - 60000, fcExtent.YMin - 60000, fcExtent.XMax + 60000, fcExtent.YMax + 60000)
        arcpy.AddMessage("\nProcessing extent: " + str(arcpy.env.extent))
        arcpy.Clip_management(parameters[0].valueAsText, str(arcpy.env.extent), os.path.join(parameters[4].valueAsText, "tempRaster") ,"#", "#", "NONE", "NO_MAINTAIN_EXTENT")

        # Create Viewsheds
        viewPolygons = arcpy.MakeFeatureLayer_management(os.path.join(parameters[4].valueAsText,"ARD_VIEW_" + parameters[2].valueAsText + "_ViewedLandscapes_projected_py"))
        # Loop through park viewpoints, creating binary viewsheds using clipped DEM
        with arcpy.da.SearchCursor(parameters[1].valueAsText, "*", whereClause) as cursor:
            for row in cursor:
                ptFeature = []
                arcpy.AddMessage("\n\nPoint for viewshed: " + str(row[7]) + ", "  + str(row[8]))
                newPt = arcpy.PointGeometry(arcpy.Point(row[7], row[8]), WGSSpatialRef) # setting explicit variable required
                ptFeature.append(newPt)
                #arcpy.AddMessage("\n\nPoints in ptFeature: " + ptFeature[0].WKT)

                # Project to Albers and make it a feature class
                newPtOutput = newPt.projectAs(outputSpatialRef); messages.addGPMessages()
                #newPtAlbers = newPt.projectAs(AlbersSpatialRef); messages.addGPMessages()
                arcpy.CopyFeatures_management(newPtOutput, tempPtClassOutput); messages.addGPMessages()
                arcpy.RepairGeometry_management(tempPtClassOutput); messages.addGPMessages()

                outViewshed = os.path.join(parameters[4].valueAsText, viewshedRoot + "_" + (row[4].replace(' ','_')).replace("'", '').replace(".","").replace("-","").replace("/","_") + "_View" + str(row[6]))
                arcpy.Viewshed_3d(os.path.join(parameters[4].valueAsText, "tempRaster"), tempPtClassOutput, outViewshed, "1", "CURVED_EARTH"); messages.addGPMessages()

                # Clip viewshed to view
                clippedViewshed = os.path.join(parameters[4].valueAsText, viewshedRootClipped + "_" + (row[4].replace(' ','_')).replace("'", '').replace(".","").replace("-","").replace("/","_") + "_View" + str(row[6]))
                clippedViewshedTemp = os.path.join(parameters[4].valueAsText, viewshedRootClippedTemp + "_" + (row[4].replace(' ','_')).replace("'", '').replace(".","").replace("-","").replace("/","_") + "_View" + str(row[6]))
                arcpy.SelectLayerByAttribute_management(viewPolygons, "NEW_SELECTION", "ViewpointName = '" + row[4] + "'"); messages.addGPMessages()
                #arcpy.Clip_management(outViewshed, viewPolygons, clippedViewshed, )
                clippedOutput = ExtractByMask(outViewshed, viewPolygons); messages.addGPMessages()
                clippedOutput.save(clippedViewshedTemp)
                clippedOutput2 = ExtractByAttributes(clippedOutput, "Value > 0"); messages.addGPMessages()
                clippedOutput2.save(clippedViewshed); messages.addGPMessages()

                # Create visible area polygons and attribute them
                viewPoly = os.path.join(parameters[4].valueAsText, viewshedRootVisibleArea + "_" + (row[4].replace(' ','_')).replace("'", '').replace(".","").replace("-","").replace("/","_") + "_View" + str(row[6])) + "_py"
                arcpy.RasterToPolygon_conversion(clippedViewshed, tempClipped, "NO_SIMPLIFY", "Value"); messages.addGPMessages()
                arcpy.RepairGeometry_management(tempClipped); messages.addGPMessages()
                arcpy.Dissolve_management(tempClipped, viewPoly, "gridcode"); messages.addGPMessages()
                arcpy.RepairGeometry_management(viewPoly); messages.addGPMessages()
                arcpy.AddField_management(viewPoly,"ViewpointName","TEXT", "", "", 255, "ViewpointName", "NULLABLE"); messages.addGPMessages()
                arcpy.CalculateField_management(viewPoly, "ViewpointName", "'" + row[4] + "'", "PYTHON_9.3"); messages.addGPMessages()
                arcpy.JoinField_management(viewPoly,"ViewpointName",viewPolygons,"ViewpointName", joinFields); messages.addGPMessages()
                arcpy.DeleteField_management(viewPoly,["Id","gridcode"]); messages.addGPMessages()

                arcpy.SelectLayerByAttribute_management(viewPolygons, "CLEAR_SELECTION"); messages.addGPMessages()

                arcpy.Delete_management(tempPtClassOutput); messages.addGPMessages()
                arcpy.Delete_management("in_memory"); messages.addGPMessages()
        #del cursor, row

        # Create visible areas raster (i.e. composite viewshed) and combined polygons
        arcpy.env.workspace = parameters[4].valueAsText
        valueTable = arcpy.ValueTable()
        ratExists = True
        pointCount = arcpy.GetCount_management(tempFeatureClassOutput); messages.addGPMessages()

        if int(pointCount.getOutput(0)) > 1: # Multiple viewpoints
            count = 1
            #rasterSearchString = viewshedRoot + "_*"
            rasterSearchString = viewshedRootClippedTemp + "_*"
            visibleAreasSearchString = "ARD_VIEW_" + parameters[2].valueAsText + "_VisibleArea_*_py"
            #rasterSearchString = "*"+parameters[2].valueAsText+"_Viewshed_*"
            rasters = arcpy.ListRasters(rasterSearchString)
            arcpy.AddMessage("\nSearched for " + rasterSearchString + " and processing " + str(len(rasters))+ " to create " + compositeViewshed)
            for ras in rasters:
                if count == 1: cv = arcpy.Raster(ras); arcpy.AddMessage("\nStarted visible areas raster: added "+ ras + " with count: " + str(count))
                else: cv = Plus(cv, arcpy.Raster(ras)); arcpy.AddMessage("\nAdded " + ras + " to visible areas raster" + " with count: " + str(count))
                #else: cv = cv + arcpy.Raster(ras); arcpy.AddMessage("\nAdded " + ras + " to visible areas raster")
                count = count + 1
            cv.save(compositeViewshed)
            #cv.save(os.path.join(parameters[4].valueAsText, compositeViewshed))
            for ras in rasters:
                arcpy.Delete_management(ras)
            #ratExists = cv.hasRAT

            visAreas = arcpy.ListFeatureClasses(visibleAreasSearchString)
            arcpy.AddMessage("\nSearched for " + visibleAreasSearchString + " and processing " + str(len(visAreas))+ " to create unioned visible areas")
            for visArea in visAreas:
                valueTable.addRow(visArea); messages.addGPMessages()
        else: # Only one viewpoint (like SCBL)
            arcpy.CopyRaster_management(clippedViewshed, os.path.join(parameters[4].valueAsText, compositeViewshed)); messages.addGPMessages()

        #if ratExists == True:
        tempViz = ExtractByAttributes(compositeViewshed, "Value > 0"); messages.addGPMessages()
        #tempViz = ExtractByAttributes(os.path.join(parameters[4].valueAsText, compositeViewshed), "Value > 0"); messages.addGPMessages()
        tempViz.save(os.path.join(parameters[4].valueAsText, "tempViz"))
        arcpy.RasterToPolygon_conversion(os.path.join(parameters[4].valueAsText, "tempViz"), os.path.join(parameters[4].valueAsText, "tempVizPolys"), "NO_SIMPLIFY", "Value"); messages.addGPMessages()
        arcpy.RepairGeometry_management(os.path.join(parameters[4].valueAsText, "tempVizPolys")); messages.addGPMessages()
        arcpy.Dissolve_management(os.path.join(parameters[4].valueAsText, "tempVizPolys"), os.path.join(parameters[4].valueAsText, compositeViewshedPolys), "gridcode"); messages.addGPMessages()
        arcpy.AlterField_management(os.path.join(parameters[4].valueAsText, compositeViewshedPolys), "gridcode", "VisiblePointCount", "VisiblePointCount"); messages.addGPMessages()
        arcpy.RepairGeometry_management(os.path.join(parameters[4].valueAsText, compositeViewshedPolys)); messages.addGPMessages()

        #arcpy.AddMessage("\nValueTable: "+str(valueTable))

        arcpy.Union_analysis(valueTable, unionedVisibleAreas); messages.addGPMessages()
        arcpy.RepairGeometry_management(unionedVisibleAreas); messages.addGPMessages()
        arcpy.env.extent = arcpy.Describe(unionedVisibleAreas).extent
        arcpy.Intersect_analysis(valueTable, intersectedVisibleAreas, "ALL"); messages.addGPMessages()
        arcpy.RepairGeometry_management(intersectedVisibleAreas); messages.addGPMessages()

##        # Compute composite Scenic Inventory Values (cSIV) by unioning viewshed polygons and populating value based on unioned scenic inventory value
##        polySearchString = viewshedRoot + "_*_py"
##        polys = arcpy.ListFeatureClasses(polySearchString)
##        arcpy.AddMessage("\nSearched for " + polySearchString + " and processing " + str(len(polys))+ " to calculate cSIV)
##        for poly in polys:
##            # Add fields and populate
##            #for field in fieldList:
##            #    CreateViewshed.addSIVFields(self, poly, field, "TEXT", 5, messages)
##            CreateViewshed.addSIVFields(self, poly, "ViewConeID", "SHORT", None, messages)
##
##            # Lookup ViewConeID from viewed landscapes feature class based on name (viewshed raster/poly name)
##
##            # Populate ViewConeID in individual polygon
##
##            # Join to viewed landscape feature class and grab SQ and VI values

        # Union polys and use lookup matrix to populate cSIV (in individual polygon feature class and in viewed landscapes feature class

        # Compute visibility by observer
        if int(pointCount.getOutput(0)) < 17:
            tempRaster = os.path.join(parameters[4].valueAsText, "tempRaster")
            arcpy.Visibility_3d(tempRaster, tempFeatureClassOutput, os.path.join(parameters[4].valueAsText, outVisibility), "#", "OBSERVERS", "NODATA", 1, "CURVED_EARTH"); messages.addGPMessages()

        # Clean up
        itemsToDelete = [tempFeatureClass, os.path.join(parameters[4].valueAsText, tempTable), os.path.join(parameters[4].valueAsText, sourceView), os.path.join(parameters[4].valueAsText, "tempVizPolys"), os.path.join(parameters[4].valueAsText, "tempViz"),os.path.join(parameters[4].valueAsText,"tempClipped")] #tempLayer, tempFeature
        #itemsToDelete = [tempFeatureClass, os.path.join(parameters[4].valueAsText, "tempRaster"), os.path.join(parameters[4].valueAsText, tempTable), os.path.join(parameters[4].valueAsText, sourceView), os.path.join(parameters[4].valueAsText, "tempVizPolys"), os.path.join(parameters[4].valueAsText, "tempViz")] #tempLayer, tempFeature
        #itemsToDelete = [tempFeatureClass] #tempLayer, tempFeature
        for item in itemsToDelete:
            if arcpy.Exists(item):
                arcpy.Delete_management(item); messages.addGPMessages()


##def main():
##
##    param0 = arcpy.Parameter(
##            displayName = "Source DEM",
##            name = "demLayer",
##            datatype = "GPRasterLayer",
##            parameterType = "Required",
##            direction = "Input")
##    param0.value = r"X:\NRSSData\ReferenceData\NRCS_DEM_30m_Fall_2012\CONUS\DEM_NED_Float.gdb\DEM_CONUS_Albers_Flt"
##
##    param1 = arcpy.Parameter(
##            displayName = "Source Viewpoint Table",  # Needs to be the ViewBearings view
##            name = "viewpointSource",
##            datatype = "DETable",
##            parameterType = "Required",
##            direction = "Input")
##    param1.value = r"Database Connections\ETV_on_INP2300FCVWHIS1_Report_Data_Reader.sde\ETV.web.ViewBearings"
##
##    param2 = arcpy.Parameter(
##        displayName = "Choose a park to extract",
##        name = "parkToExtract",
##        datatype = "String",
##        parameterType  = "Required",
##        direction = "Input")
##
##    param3 = arcpy.Parameter(
##        displayName = "View Distance (in meters)",
##        name = "viewDist",
##        datatype = "String",
##        parameterType = "Required",
##        direction = "Input"
##        )
##    param3.value = r"40000"
##
##    param4 = arcpy.Parameter(
##        displayName = "Output GeoDatabase",
##        name = "outDB",
##        datatype = "DEWorkspace",
##        parameterType = "Required",
##        direction = "Input")
##    param4.value = r"D:\Workspace\Default.gdb"
##
##    param5 = arcpy.Parameter(
##        displayName = "Output folder for viewshed rasters",
##        name = "outputFolder",
##        datatype = "Folder",
##        parameterType = "Required",
##        direction = "Input"
##    )
##    param5.value = r"D:\temp\trash\ETVTests"
##
##    params = [param0, param1, param2, param3, param4, param5]
##    vs = CreateViewshed()
##    CreateViewshed.execute(vs, params, "")
##
##if __name__ == '__main__':
##    main()
