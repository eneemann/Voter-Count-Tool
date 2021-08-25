# -*- coding: utf-8 -*-
"""
Created on Thu Aug 5 11:47:04 2021
@author: eneemann
Script to count voters within each feature of a polygon layer
"""

import arcpy
import os
import time

#: Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
arcpy.AddMessage(f"The script start time is: {readable_start}")
today = time.strftime("%Y%m%d")

#: Get inputs from the GUI
precinct_polygons = arcpy.GetParameterAsText(0)
county = arcpy.GetParameterAsText(1)
working_dir = arcpy.GetParameterAsText(2)

arcpy.AddMessage(f"Selected counties: {county}")
arcpy.AddMessage(f"Output geodatabase: {working_dir}")

#: Create dictionary to convert county names into county numbers for voter data
county_dict = {"Beaver": 1,
        "Box Elder": 2,
        "Cache": 3,
        "Carbon": 4,
        "Daggett": 5,
        "Davis": 6,
        "Duchesne": 7,
        "Emery": 8,
        "Garfield": 9,
        "Grand": 10,
        "Iron": 11,
        "Juab": 12,
        "Kane": 13,
        "Millard": 14,
        "Morgan": 15,
        "Piute": 16,
        "Rich": 17,
        "Salt Lake": 18,
        "San Juan": 19,
        "Sanpete": 20,
        "Sevier": 21,
        "Summit": 22,
        "Tooele": 23,
        "Uintah": 24,
        "Utah": 25,
        "Wasatch": 26,
        "Washington": 27,
        "Wayne": 28,
        "Weber": 29}

#: Build SQL query depending on number of counties selected
if ';' in county:
    county_list = county.split(';')
    county_list = [item.replace("'", "").strip() for item in county_list]
    numbers = [county_dict[f'{county}'] for county in county_list]
    where_clause = f'COUNTY_ID in ({",".join([str(num) for num in numbers])})'
else:
    county = county.replace("'", "").strip()
    county_list = county
    numbers = county_dict[f'{county}']
    where_clause = f'COUNTY_ID = {numbers}'

arcpy.AddMessage(f'Final county list: {county_list}')
arcpy.AddMessage(f"County numbers: {numbers}")


#: Check for existing fields and delete, if necessary
field_list = arcpy.ListFields(precinct_polygons)
field_names = [field.name for field in field_list]

if 'sum_voters' in field_names:
    arcpy.AddMessage('Deleting existing sum_voters field ...')
    arcpy.management.DeleteField(precinct_polygons, 'sum_voters')
if 'Point_Count' in field_names:
    arcpy.AddMessage('Deleting existing Point_Count field ...')
    arcpy.management.DeleteField(precinct_polygons, 'Point_Count')

#: Get timestamp for FC name
now = time.strftime("%Y%m%d_%H%M%S")

#: Set up data variables
scratch_db = arcpy.env.scratchGDB
arcpy.AddMessage(f'Scratch database: {scratch_db}')
voter_points = r'https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/Utah_Voter_Counts_by_Addresses/FeatureServer/0'
out_name = os.path.join(working_dir, f'voter_counts_output_{now}')

#: Make layer from AGOL feature layer by applying county query
#: Delete layer ahead of time, if it already exists
if arcpy.Exists("voter_lyr"):
    arcpy.AddMessage('Deleting "voter_lyr" ...')
    arcpy.management.Delete("voter_lyr")

arcpy.AddMessage(f"Making a feature layer with query: {where_clause} ...")
arcpy.management.MakeFeatureLayer(voter_points, "voter_lyr", where_clause)

#: Copy layer to temporary fc in scratch gdb to improve performance
temp_fc = 'temp_voter_fc'
temp_path = os.path.join(scratch_db, temp_fc)
arcpy.conversion.FeatureClassToFeatureClass("voter_lyr", scratch_db, temp_fc)

#: Perform Summarize Within to count up voters
arcpy.AddMessage("Starting 'Summarize Within' ...")
arcpy.analysis.SummarizeWithin(precinct_polygons, temp_path, out_name, "KEEP_ALL", "VOTERS Sum", "ADD_SHAPE_SUM")
arcpy.AddMessage(f"Output FC named: {out_name} ...")

#: Join sum_voters field back to the original data layer
arcpy.management.JoinField(precinct_polygons, 'OBJECTID', out_name, 'OBJECTID', ['sum_voters', 'Point_Count'])

#: Delete temp_voter_fc
if arcpy.Exists(temp_path):
    arcpy.AddMessage(f'Deleting {temp_path} ...')
    arcpy.management.Delete(temp_path)
    
arcpy.AddMessage("Script shutting down ...")
#: Stop timer and print end time in UTC
readable_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
arcpy.AddMessage(f"The script end time is: {readable_end}")
arcpy.AddMessage("Time elapsed: {:.2f}s".format(time.time() - start_time))