#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert Zeopoxa rides' data (stored in a SQLite) to GPX files

@author: rcassani

Relevant Zeopoxa SQLite Tables:
  main_table:     Information for rides
  bicycle_table:  Information for bikes

It is possible to have rides with a BICYCLE_ID that is not in bycicle_table

"""

import argparse
import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime
import xml.etree.cElementTree as ET
from xml.dom import minidom

#%% Parameters
# Zeopoxa database file
argParser = argparse.ArgumentParser()
argParser.add_argument("-f", "--file", help="Zeopoxa database file")
args = argParser.parse_args(args=None if sys.argv[1:] else ['--help'])
#args.file = '2023-10-16-10-54-49_Database_Zeopoxa_Cycling.db'
db_ze = args.file

# Check that file exists
if not os.path.isfile(os.path.abspath(args.file)):
    print("File '{}' does not exist".format(args.file))
    sys.exit(2)


# Create output dir
output_dir = 'rides_zeopoxa_gpx_' + datetime.now().strftime('%Y_%m_%dT%H_%M_%S')
os.mkdir(output_dir)

#%% From DB to GPX files
# Info for GPX files
xmlns          = "http://www.topografix.com/GPX/1/1"
xsi            = "http://www.w3.org/2001/XMLSchema-instance"
schemaLocation = "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
version        = "1.1"
creator        = 'Zeopoxa2GPX'


cnx_db = sqlite3.connect(db_ze)
# Get all rides
df_rides = pd.read_sql_query('SELECT ID,YEAR,MONTH,DAY,START_TIME,LATLON_ARRAY,BICYCLE_ID FROM main_table', cnx_db)
# Create a GPX file for each ride
for ix_ride in df_rides.index:
    # Get its bycicle
    df_bycicle = pd.read_sql_query('SELECT BICYCLE_NAME FROM bicycle_table WHERE ID = {}'.format(df_rides['BICYCLE_ID'][ix_ride]), cnx_db)
    if df_bycicle.empty:
        name_bike = 'bike_{}'.format(df_rides['BICYCLE_ID'][ix_ride])
    else:
        name_bike = df_bycicle['BICYCLE_NAME'][0]
    # Create folder if it does not exist
    name_bike = name_bike.replace(' ', '_')
    dir_bike = output_dir + '/' + name_bike
    if not os.path.isdir(os.path.abspath(dir_bike)):
        os.mkdir(dir_bike)
    # Get all ride points for ride
    #latlon = evaluate df_rides['LATLON_ARRAY'][ix_ride]
    points = None
    exec('points = ' + df_rides['LATLON_ARRAY'][ix_ride])
    if len(points) == 0:
        continue
    # Start GPX (XML tree)
    root = ET.Element("gpx", creator=creator, attrib={"{" + xsi + "}schemaLocation" : schemaLocation}, version=version, xmlns=xmlns)
    tree = ET.ElementTree(root)
    # Create dataframe
    df_points = pd.DataFrame(points)
    df_points = df_points.rename(columns={'latitude':'lat', 'longitude':'lon'})
    # Add column with seconds, as points are 1s resolution
    df_points['seconds'] = range(len(df_points))
    # Generte timestamp for year_mont_day
    datetime_str = '{:04d}-{:02d}-{:02d}T{}:00Z'.format(df_rides['YEAR'][ix_ride],
                                                        df_rides['MONTH'][ix_ride],
                                                        df_rides['DAY'][ix_ride],
                                                        df_rides['START_TIME'][ix_ride])
    formated_datetime = datetime.strptime(datetime_str,"%Y-%m-%dT%H:%M:%SZ")
    timestamp = datetime.timestamp(formated_datetime)
    # Add second to timestamp
    df_points['timestamp'] = timestamp + df_points['seconds']
    # Change UNIX time to 2023-09-15T22:08:06Z, uses system TimeZone
    df_points['time'] = df_points['timestamp'].apply(lambda x: datetime.fromtimestamp(x, tz=None).strftime('%Y-%m-%dT%H:%M:%SZ'))
    # Metadata
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "time").text = df_points['time'][0]

    # Track
    trk = ET.SubElement(root, "trk")
    ET.SubElement(trk, "name").text = 'WOW!'
    ET.SubElement(trk, "type").text = 'cycling'
    trkseg = ET.SubElement(trk, "trkseg")

    # Write each ride point
    for point in df_points.index:
        trkpt = ET.SubElement(trkseg, "trkpt", lat= str(df_points['lat'][point]), lon=str(df_points['lon'][point]))
        ET.SubElement(trkpt, "time").text = df_points['time'][point]
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent=" ", encoding="utf-8")

    # Write GPX file
    with open(dir_bike + '/{:03d}_ride.gpx'.format(df_rides['ID'][ix_ride]), "wb") as f:
        f.write(xmlstr)
cnx_db.close()

