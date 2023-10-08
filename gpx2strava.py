#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload GPX files to Strava, using its API

@author: rcassani
"""

import argparse
import sys
import os
import requests
import json

#%% Parameters
# SuperCycle database file
argParser = argparse.ArgumentParser()
argParser.add_argument("-d", "--dir", help="Directory with GPX files")
args = argParser.parse_args(args=None if sys.argv[1:] else ['--help'])
gpx_dir = args.dir

# Check that dir exists
if not os.path.isdir(os.path.abspath(gpx_dir)):
    print("Directory '{}' does not exist".format(args.dir))
    sys.exit(2)

# Get GPX files
gpx_files = []
for file in os.listdir(gpx_dir):
    if file.endswith('.gpx'):
        gpx_files.append(file)
gpx_files.sort()

# Read CLIENT_ID and CLIENT_SECRET
f = open('api_info.json')
api_info = json.load(f)
f.close()

#%%
# Display info in terminal with link

print('Authenticate yourself, so you can grant the permissions')
print('that the app is requesting for the uploading.')
print('Authenticate yourself, so you can grant the permissions')
print('Required permission ' + "'activity:write'")
print('')
print('Open the link below, log in, and copy the value of ' + "'code'" +'from the URL:')
print('')

auth_url = ('https://www.strava.com/oauth/authorize?client_id=' +
            str(api_info['client_id']) +
            '&response_type=code' +
            '&redirect_uri=http://localhost/exchange_token&approval_prompt=force' +
            '&scope=activity:write')

print(auth_url)
print('')

val = input('Enter the value of ' + "'code': ")
print('')

# Request code
api_info['code'] = val
api_info['grant_type'] = 'authorization_code'

# Solicit a token (with the permissions accepted by the user)
# In Bash:
# curl -X POST https://www.strava.com/oauth/token \
#  -F client_id=[REPLACE_WITH_YOUR_CLIENT_ID] \
#  -F client_secret=[REPLACE_WITH_YOUR_CLIENT_SECRET] \
#  -F code=[REPLACE_WITH_YOUR_CODE]
#  -F grant_type=authorization_code
response = requests.post('https://www.strava.com/oauth/token', json=api_info)
response_data = json.loads(response.text)

# Upload GPX files
print('Uploading...')
for gpx_file in gpx_files:
    # In Bash
    # curl -X 'POST' \
    #  'https://www.strava.com/api/v3/uploads' \
    #  -H 'accept: application/json' \
    #  -H 'authorization: Bearer [REPLACE_WITH_ACCESS_TOKEN]' \
    #  -H 'Content-Type: multipart/form-data' \
    #  -F 'file=@[REPLACE WITH FILENAME.GPX];type=application/gpx+xml' \
    #  -F 'name=[REPLACE WITH RIDE_NAME]' \
    #  -F 'data_type=gpx'

    # Headers: do not include Content-Type, this is handled by providing 'files' arg in resquests.post
    headers = {'authorization' : 'Bearer {}'.format(response_data['access_token'])}
    files = {'file'      : open(os.path.abspath(gpx_dir + '/' + gpx_file), 'r')}
    data  = {'name'      : gpx_file,
             'data_type' : 'gpx'}
    res_up = requests.post('https://www.strava.com/api/v3/uploads', files=files, data=data, headers=headers)
    res_up_data = json.loads(res_up.text)
    print(res_up_data)
