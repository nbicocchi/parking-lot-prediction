# IoT – enabled Predictive Parking project
The projects aims at developing an industrial-grade testbed for smart parking technologies. 
Bosch provides the physical sensors, while LGH and a2a groups provide LoraWAN connectivity and competences within the multi-utility sector. 
UNIMORE provides expertise in data management, visualization and predictive analysis.

# Application server repository
This repository contains the code of UNIMORE application server.

## Requirements
* Tested on Debian 4.9.30 (but it should work also on other Linux distros).
* Tested on Python 3.5.6 (but it should work also on newer 3.x versions).
* MySQL database.

## Installation
1. Create a folder named `bosch_pls` in your home and clone this repository there.
2. Create a folder named `.bosch_pls` in your home.
3. Copy the network server private key file in `$HOME/.bosch_pls/` folder and rename it as `keyfile.crt`.
4. Modify `auth_EXAMPLE.yaml` file and save it as `auth.yaml` in `$HOME/.bosch_pls/` folder.
5. Execute (in this order!) `app_tables.sql` and `sensors_tables.sql` to create the necessary tables.
6. Install the required modules using requirements.txt: `pip3 install -r requirements.txt`.
7. Add to crontab these two lines: <pre>*/5 * * * * bash $HOME/bosch_pls/check_running.sh > /dev/null 2>&1
*/5 * * * * nohup python3 $HOME/bosch_pls/resample_data.py --rule=5 > /dev/null 2>&1</pre>
8. Wait up to 5 minutes and check if `main.py` is running executing `pgrep -a "python3"`.

## Documentation

### main.py
Subscribe to the network server using MQTT protocol to gather and save sensors' messages (default saved in `messages` table in the database).
#### Usage
<pre>python3 main.py [--park_id=P] [--log_to_sysout] [--save_to_file]</pre>
* `--park_id=P`: if set save `P` as `park_id` in the messages (default `0`)
* `--log_to_sysout`: if set log to sysout, otherwise log to `$HOME/.bosch_pls/log/main.log`
* `--save_to_file`: if set save the messages in `$HOME/.bosch_pls/data.csv`, otherwise save the messages in `messages` table in the database

### resample_data.py
Resample sensors' messages into `rule`-minutely data and compute sensors data matrix and occupancy data (default saved in `occupancy` table in the database).
#### Usage
<pre>python3 resample_data.py [--park_id=P] [--start_date=SD] [--rule=R] [--log_to_sysout] [--occupancy_to_file]</pre>
* `--park_id=P`: if set load only messages with `park_id=P` (default `0`)
* `--start_date=SD`: if set resample from `SD` date (in `YYYY-MM-DD` format)
* `--rule=R`: if set resample sensors' messages into `R`-minutely data, otherwise resample sensors' messages into 5-minutely data
* `--log_to_sysout`: if set log to sysout, otherwise log to `$HOME/.bosch_pls/log/resample_data.log`
* `--occupancy_to_file`: if set save the occupancy data in `$HOME/.bosch_pls/occupancy.csv`, otherwise save the occupancy data in `occupancy` table in the database

Note: truncate/drop `occupancy` table before changing the parameters to avoid inconsistent data.

### show_plots.py
Show plots about occupancy and other data (between `start_date` and `end_date` if set):
* Activity plot: how many sensors are active and how many messages are sent every day
* Occupancy plot: occupancy percentage over time (to show only last data set `--days` parameter)
* Occupancy heatmap: occupancy percentage over time (to show only last data set `--days` parameter)
* Free parking week boxplot: show the distribution of free parking lots by week
* Free parking day plot: show the average number of free parking lots by day
#### Usage
<pre>python3 show_plots.py [--park_id=P] [--days=D] [--start_date=SD] [--end_date=ED]</pre>
* `--park_id=P`: if set load only messages with `park_id=P` (default `0`)
* `--days=D`: if set show only last `D` days of data, otherwise show all data
* `--start_date=SD`: if set show data from `SD` date (in `YYYY-MM-DD` format)
* `--end_date=ED`: if set show data until `ED` date (in `YYYY-MM-DD` format)

**Note:** if `days`, `start_date` and `end_date` are all set, `start_date` and `end_date` have the priority over `days`.

### train_nn.py
Tune hyperparameters to select the best Neural Network architecture and train it to predict occupancy and free parkings (8-hours-ahead prediction given the last 24 hours of data). 
Save the best model to `$HOME/.bosch_pls/model.h5` (NN architecture and weights) and `$HOME/.bosch_pls/model_architecture.json` (only NN architecture).
#### Usage (on local machine)
<pre>python3 train_nn.py [--path] [--plot]</pre>
* `--path`: if set look for `occupancy.csv` file and save the model here
* `--plot`: if set show prediction plots
#### Usage (on Google Colaboratory)
1. Create a folder named `bosch_pls` in your Google Drive
2. Copy `neural_network` package and `train_nn.py` script in `bosch_pls` folder
3. Change the configuration in `neural_network/config.py` file
4. Run `resample_data.py --occupancy_to_file` and upload the output file in `bosch_pls` folder
5. Upload `train_nn_colab.ipynb` in your Google Drive and open it with Google Colaboratory
6. In order to use a GPU with the notebook, select the Runtime → Change runtime type menu, and then set the hardware accelerator dropdown to GPU.
7. Run the notebook and look for the model files in `bosch_pls` folder
8. Copy `model.h5` file in `$HOME/.bosch_pls` directory

### Queries on the database
There are some useful queries to see the status of the system at first glance:
* Last `N` messages: <pre>SELECT * FROM bosch_pls.messages ORDER BY time DESC LIMIT <i>N</i>;</pre>
* Last `N` occupancy: <pre>SELECT * FROM bosch_pls.occupancy ORDER BY time DESC LIMIT <i>N</i>;</pre>
* Number of active sensors on the last `N` hours: <pre>SELECT count(DISTINCT dev_eui) FROM bosch_pls.messages WHERE TIME >= DATE_SUB(CURDATE(), INTERVAL <i>N</i> HOUR);</pre>

### API usage (api_v1.py)
The API layer is built with Flask, see Flask's [Deployment Options](https://flask.palletsprojects.com/en/1.1.x/deploying/) to deploy the layer correctly. 
The Flask application object is inside `api_v1.py` script and it's the actual WSGI application.

**Note:** Neural Network prediction requires a `model.h5` file, it is mandatory to train a neural network before using it.

## API documentation (v1 2020-04-01)

### Current occupation
**Description**: Get the current occupation of parking `park_id`

**URL structure**: `/v1/parks/<int:park_id>/current_occupancy`

**Parameters**:
* `park_id`

**Method**: `GET`

**Example**: `/v1/parks/42/current_occupancy`

**Returns**: 

<pre>{"date": "2020-03-16T11:45:00Z", "occ": 0.833}</pre>

### Last 24h occupation
**Description**: Get the last 24 hours hourly occupancy of parking `park_id`

**URL structure**: `/v1/parks/<int:park_id>/last_24h_occupancy`

**Parameters**: 
* `park_id`

**Method**: `GET`

**Example**: `/v1/parks/42/hourly_occupancy`

**Returns**:

<pre>[{"date": "2020-03-15T11:00:00Z", "occ": 0.819}, {"date": "2020-03-15T12:00:00Z", "occ": 0.817}, {"date": "2020-03-15T13:00:00Z", "occ": 0.82}, {"date": "2020-03-15T14:00:00Z", "occ": 0.828}, {"date": "2020-03-15T15:00:00Z", "occ": 0.829}, {"date": "2020-03-15T16:00:00Z", "occ": 0.828}, {"date": "2020-03-15T17:00:00Z", "occ": 0.828}, {"date": "2020-03-15T18:00:00Z", "occ": 0.828}, {"date": "2020-03-15T19:00:00Z", "occ": 0.851}, {"date": "2020-03-15T20:00:00Z", "occ": 0.859}, {"date": "2020-03-15T21:00:00Z", "occ": 0.86}, {"date": "2020-03-15T22:00:00Z", "occ": 0.859}, {"date": "2020-03-15T23:00:00Z", "occ": 0.852}, {"date": "2020-03-16T00:00:00Z", "occ": 0.844}, {"date": "2020-03-16T01:00:00Z", "occ": 0.844}, {"date": "2020-03-16T02:00:00Z", "occ": 0.844}, {"date": "2020-03-16T03:00:00Z", "occ": 0.844}, {"date": "2020-03-16T04:00:00Z", "occ": 0.844}, {"date": "2020-03-16T05:00:00Z", "occ": 0.844}, {"date": "2020-03-16T06:00:00Z", "occ": 0.857}, {"date": "2020-03-16T07:00:00Z", "occ": 0.854}, {"date": "2020-03-16T08:00:00Z", "occ": 0.859}, {"date": "2020-03-16T09:00:00Z", "occ": 0.86}, {"date": "2020-03-16T10:00:00Z", "occ": 0.865}]</pre>

### Daily occupation
**Description**: Get the last day hourly occupancy of parking `park_id`

**URL structure**: `/v1/parks/<int:park_id>/daily_occupancy`

**Parameters**: 
* `park_id`

**Method**: `GET`

**Example**: `/v1/parks/42/daily_occupancy`

**Returns**:

<pre>[{"hour": 0, "occ": 0.875}, {"hour": 1, "occ": 0.875}, {"hour": 2, "occ": 0.875}, {"hour": 3, "occ": 0.875}, {"hour": 4, "occ": 0.875}, {"hour": 5, "occ": 0.882}, {"hour": 6, "occ": 0.863}, {"hour": 7, "occ": 0.836}, {"hour": 8, "occ": 0.851}, {"hour": 9, "occ": 0.896}, {"hour": 10, "occ": 0.877}, {"hour": 11, "occ": 0.899}, {"hour": 12, "occ": 0.889}, {"hour": 13, "occ": 0.868}, {"hour": 14, "occ": 0.845}, {"hour": 15, "occ": 0.833}, {"hour": 16, "occ": 0.874}, {"hour": 17, "occ": 0.863}, {"hour": 18, "occ": 0.88}, {"hour": 19, "occ": 0.886}, {"hour": 20, "occ": 0.865}, {"hour": 21, "occ": 0.879}, {"hour": 22, "occ": 0.88}, {"hour": 23, "occ": 0.875}]</pre>

### Weekly occupation
**Description**: Get the last week hourly occupancy of parking `park_id`

**URL structure**: `/v1/parks/<int:park_id>/weekly_occupancy`

**Parameters**: 
* `park_id`

**Method**: `GET`

**Example**: `/v1/parks/42/weekly_occupancy`

**Returns**:

<pre>[{"hour": 0, "occ": 0.864}, {"hour": 1, "occ": 0.865}, {"hour": 2, "occ": 0.862}, {"hour": 3, "occ": 0.862}, {"hour": 4, "occ": 0.862}, {"hour": 5, "occ": 0.87}, {"hour": 6, "occ": 0.864}, {"hour": 7, "occ": 0.865}, {"hour": 8, "occ": 0.865}, {"hour": 9, "occ": 0.881}, {"hour": 10, "occ": 0.883}, {"hour": 11, "occ": 0.879}, {"hour": 12, "occ": 0.87}, {"hour": 13, "occ": 0.868}, {"hour": 14, "occ": 0.857}, {"hour": 15, "occ": 0.86}, {"hour": 16, "occ": 0.862}, {"hour": 17, "occ": 0.867}, {"hour": 18, "occ": 0.876}, {"hour": 19, "occ": 0.872}, {"hour": 20, "occ": 0.873}, {"hour": 21, "occ": 0.874}, {"hour": 22, "occ": 0.868}, {"hour": 23, "occ": 0.864}]</pre>

### Monthly occupation
**Description**: Get the last month hourly occupancy of parking `park_id`

**URL structure**: `/v1/parks/<int:park_id>/monthly_occupancy`

**Parameters**: 
* `park_id`

**Method**: `GET`

**Example**: `/v1/parks/42/monthly_occupancy`

**Returns**:

<pre>[{"hour": 0, "occ": 0.866}, {"hour": 1, "occ": 0.866}, {"hour": 2, "occ": 0.866}, {"hour": 3, "occ": 0.867}, {"hour": 4, "occ": 0.867}, {"hour": 5, "occ": 0.87}, {"hour": 6, "occ": 0.866}, {"hour": 7, "occ": 0.867}, {"hour": 8, "occ": 0.868}, {"hour": 9, "occ": 0.875}, {"hour": 10, "occ": 0.878}, {"hour": 11, "occ": 0.878}, {"hour": 12, "occ": 0.872}, {"hour": 13, "occ": 0.861}, {"hour": 14, "occ": 0.86}, {"hour": 15, "occ": 0.867}, {"hour": 16, "occ": 0.867}, {"hour": 17, "occ": 0.873}, {"hour": 18, "occ": 0.882}, {"hour": 19, "occ": 0.878}, {"hour": 20, "occ": 0.878}, {"hour": 21, "occ": 0.878}, {"hour": 22, "occ": 0.871}, {"hour": 23, "occ": 0.867}]</pre>

### 8h prediction (Neural Network prediction)
**Description**: Get the 8 hours occupancy prediction of parking `park_id`

**URL structure**: `/v1/parks/<int:park_id>/8h_prediction` or `/v1/parks/<int:park_id>/nn_prediction`

**Parameters**: 
* `park_id`

**Method**: `GET`

**Example**: `/v1/parks/42/8h_prediction`

**Returns**: 

<pre>[{"date": "2020-03-16T16:00:00Z", "pred": {"min": 9, "max": 13}}, {"date": "2020-03-16T17:00:00Z", "pred": {"min": 12, "max": 16}}, {"date": "2020-03-16T18:00:00Z", "pred": {"min": 10, "max": 14}}, {"date": "2020-03-16T19:00:00Z", "pred": {"min": 10, "max": 14}}, {"date": "2020-03-16T20:00:00Z", "pred": {"min": 10, "max": 14}}, {"date": "2020-03-16T21:00:00Z", "pred": {"min": 9, "max": 13}}, {"date": "2020-03-16T22:00:00Z", "pred": {"min": 10, "max": 14}}, {"date": "2020-03-16T23:00:00Z", "pred": {"min": 11, "max": 15}}]</pre>

### Median prediction
**Description**: Get the median prediction of parking `park_id` in date `year`-`month`-`day` and time `hour`:`minute`

**URL structure**: `/v1/parks/<int:park_id>/median_prediction/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>`

**Parameters**: 
* `park_id`
* `year`
* `month`
* `hour`
* `minute`

**Method**: `GET`

**Example**: `/v1/parks/42/median_prediction/2020/5/3/11/55`

**Returns**: 

<pre>{"date": "2020-05-03T11:55:00Z", "pred": {"min": 5, "max": 11}}</pre>