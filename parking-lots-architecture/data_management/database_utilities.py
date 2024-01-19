import logging
import pandas as pd
import sqlalchemy as db

from utilities.auth_info import read_auth_info

logger = logging.getLogger(__name__)


def get_db_connection():
    auth_info = read_auth_info()
    db_connection_str = 'mysql+mysqlconnector://{}:{}@{}/{}'.format(auth_info['db_username'],
                                                                    auth_info['db_password'],
                                                                    auth_info['db_host'],
                                                                    auth_info['db_name'])
    return db.create_engine(db_connection_str)


def get_last_n_records(table, park_id=None, n=1, desc=False):
    where_string = build_where_string(park_id=park_id)
    query = 'SELECT * FROM {} {} ORDER BY time DESC LIMIT {}'.format(table, where_string, n)
    df = pd.read_sql_query(query, get_db_connection(), index_col='time', parse_dates=True)
    if desc:
        return df[::-1]
    return df


def build_where_string_equal(params: dict):
    param_list = ['{} = \'{}\''.format(k, v) for k, v in params.items()]
    where = 'WHERE '
    where += 'AND '.join(param_list)
    return where


def build_where_string(park_id=None, start_date=None, end_date=None):
    where = ''
    lst = list()
    if park_id:
        lst.append('park_id = \'{}\' '.format(park_id))
    if start_date:
        lst.append('time >= \'{}\' '.format(start_date.isoformat()))
    if end_date:
        lst.append('time < \'{}\' '.format(end_date.isoformat()))
    if lst:
        where = 'WHERE '
        where += 'AND '.join(lst)
    return where


def get_data(tables_names, park_id=None, start_date=None, end_date=None):
    df_list = list()
    where_string = build_where_string(park_id, start_date, end_date)
    with get_db_connection().begin() as connection:
        for table in tables_names:
            df_list.append(pd.read_sql_query('SELECT * FROM {} {}'.format(table, where_string),
                                             connection, index_col='time', parse_dates=True))
    return df_list
