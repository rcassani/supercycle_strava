# Supercycle > GPX > Strava
Scripts to help the migration of rides data from [SuperCycle](http://www.osborntech.com/) to [Strava](https://www.strava.com/).

More details about this codes in:

https://www.castoriscausa.com/posts/2023/10/07/supercycle_strava/

## Usage
### 1. SuperCycle > GPX files
The script `supercycle2gpx.py` reads the SuperCycle database and generates a GPX for each ride in the database.

**Execution:**  
`./supercyle2gpx.py --file SuperCycle-20230813-1549.scbak`

### 2. GPX files > Strava
Run the `gpx2strava.py` Python script and follow the instructions in the terminal to upload the GPX files to Strava using its API

**Execution:**  
`./gpx2strava.py --dir ./rides_gpx_2023_10_02T09_15_20/001_bike/`

⚠️ You need to have a `client_id` and `client_secret` to use the Strava API. More info [here](https://developers.strava.com/docs/getting-started/).
