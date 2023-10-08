#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert SuperCycle rides' data (stored in a SQLite) to GPX files

@author: rcassani

Relevant SuperCycle SQLite Tables:
  bike:         Information for bikes
  ride:         Summary information for rides
  ride_detail:  Localization resolved 1s for each ride
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
# SuperCycle database file
argParser = argparse.ArgumentParser()
argParser.add_argument("-f", "--file", help="SuperCycle database file")
args = argParser.parse_args(args=None if sys.argv[1:] else ['--help'])
#args.file = 'SuperCycle-20230904-1159.scbak'
db_sc = args.file

# Check that file exists
if not os.path.isfile(os.path.abspath(args.file)):
    print("File '{}' does not exist".format(args.file))
    sys.exit(2)


# Create output dir
output_dir = 'rides_gpx_' + datetime.now().strftime('%Y_%m_%dT%H_%M_%S')
os.mkdir(output_dir)

#%% From DB to GPX files
# Info for GPX files
xmlns          = "http://www.topografix.com/GPX/1/1"
xsi            = "http://www.w3.org/2001/XMLSchema-instance"
schemaLocation = "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
version        = "1.1"
creator        = 'SuperCycle2GPX'

# Get all bikes
cnx_db = sqlite3.connect(db_sc)
df_bikes = pd.read_sql_query('SELECT id, name FROM bike', cnx_db)
for ix_bike in df_bikes.index:
    # Make bike folder (not ASCII characters in name are replaced)
    name_bike = df_bikes['name'][ix_bike].encode('ascii', 'replace').decode("utf-8", "ignore")
    name_bike = name_bike.replace(' ', '_')
    dir_bike = output_dir + '/{:03d}_{}'.format(df_bikes['id'][ix_bike], name_bike)
    os.mkdir(dir_bike)
    # Get all rides
    df_rides = pd.read_sql_query('SELECT id,bikeId FROM ride WHERE bikeId ={}'.format(df_bikes['id'][ix_bike]), cnx_db)
    # Create a GPX file for each ride
    for ix_ride in df_rides.index:
        # Start GPX (XML tree)
        root = ET.Element("gpx", creator=creator, attrib={"{" + xsi + "}schemaLocation" : schemaLocation}, version=version, xmlns=xmlns)
        tree = ET.ElementTree(root)
        # Get all ride points for ride
        df_points = pd.read_sql_query('SELECT lat,lon,timestamp FROM ride_detail WHERE rideId ={}'.format(df_rides['id'][ix_ride]), cnx_db)
        # Change UNIX time to 2023-09-15T22:08:06Z, uses system TimeZone
        df_points['time'] = df_points['timestamp'].apply(lambda x: datetime.fromtimestamp(x/1000, tz=None).strftime('%Y-%m-%dT%H:%M:%SZ'))
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
        with open(dir_bike + '/{:03d}_ride.gpx'.format(df_rides['id'][ix_ride]), "wb") as f:
            f.write(xmlstr)
cnx_db.close()
