import argparse
from datetime import datetime
from pathlib import Path
import sqlalchemy.exc
import pandas as pd

from data_management.database_utilities import get_db_connection, get_data, get_last_n_records
from utilities.init_data_path import get_data_path, get_log_path, get_log_filename
from utilities.init_logging import init_logging


def resample(data, start_date=None, park_id=None, rule=1):
    if start_date is not None:
        data = data[data.index > start_date]
    if park_id is not None:
        data = data[data.park_id == park_id]
    sensors_data = pd.pivot_table(data, index=data.index, columns=data.dev_eui, values='state').resample('1Min').mean()
    sensors_data.fillna(method='ffill', inplace=True)
    sensors_data.sort_index(axis=1, inplace=True)
    sensors_data = sensors_data.resample('{}Min'.format(rule)).mean()
    sensors_data.fillna(method='ffill', inplace=True)
    occupancy_data = pd.DataFrame(sensors_data.mean(axis=1), columns=['percentage'])
    if park_id is None:
        occupancy_data['park_id'] = 0
    else:
        occupancy_data['park_id'] = park_id
    return sensors_data, occupancy_data


def resample_active_sensors(data, start_date=None, park_id=None, rule=1):
    if start_date is not None:
        data = data[data.index > start_date]
    if park_id is not None:
        data = data[data.park_id == park_id]
    sensors_data = pd.pivot_table(data, index=data.index, columns=data.dev_eui,
                                  values='state').resample('{}min'.format(rule)).mean()
    sensors_data.sort_index(axis=1, inplace=True)
    sensors_data.fillna(method='ffill', inplace=True, limit=60 // rule * 24)
    sensors_data = sensors_data.round(0)
    occupancy_data = pd.DataFrame(sensors_data.mean(axis=1), columns=['percentage'])
    occupancy_data.replace({0: None, 1: None}, inplace=True)
    occupancy_data.drop(occupancy_data[occupancy_data.isnull().any(axis=1)].index, inplace=True)
    return sensors_data, occupancy_data


def get_last_timestamp():
    try:
        timestamp = get_last_n_records('occupancy')
    except sqlalchemy.exc.SQLAlchemyError:
        timestamp = pd.DataFrame()
    if timestamp.empty:
        timestamp = pd.read_sql_query('SELECT * FROM messages LIMIT 1;',
                                      connection, index_col='time', parse_dates=True)
    return timestamp.index[0]


parser = argparse.ArgumentParser()
parser.add_argument('--park_id', type=str, default=0)
parser.add_argument('--start_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'), default=None)
parser.add_argument('--rule', type=int, default=5)
parser.add_argument('--log_to_sysout', action='store_true')
parser.add_argument('--occupancy_to_file', action='store_true')
args = parser.parse_args()
path = get_data_path()
log_path = get_log_path()
log_filename = get_log_filename(Path(__file__).stem)

if __name__ == "__main__":
    logger = init_logging(log_filename, args.log_to_sysout)
    start = datetime.now()
    df = get_data(tables_names=['messages'], park_id=args.park_id, start_date=args.start_date)[0]
    sensors_df, occupancy_df = resample(df, rule=args.rule)
    with get_db_connection().begin() as connection:
        last_timestamp = get_last_timestamp()
        last_sensors_df = sensors_df.drop(sensors_df[sensors_df.index <= last_timestamp].index)
        last_occupancy_df = occupancy_df.drop(occupancy_df[occupancy_df.index <= last_timestamp].index)
        # last_sensors_df.to_sql(con=connection, name='sensors_data', if_exists='append', chunksize=5000)
        last_occupancy_df.to_sql(con=connection, name='occupancy', if_exists='append', chunksize=5000)
    end = datetime.now()
    elapsed = (end - start).seconds
    logger.info('Saved in occupancy table (rule={}) in {} seconds'.format(args.rule, elapsed))
    if args.occupancy_to_file:
        occupancy_df.to_csv(path.joinpath('occupancy.csv'))
        logger.info('Saved in occupancy.csv')
