import logging
from pathlib import Path
import pandas as pd
import sqlalchemy as db
from sshtunnel import SSHTunnelForwarder

from utilities.auth_info import read_auth_info

logger = logging.getLogger(__name__)
auth_info = read_auth_info('_remote')
tunnel = SSHTunnelForwarder((auth_info['ssh_host'], auth_info['ssh_port']),
                            ssh_username=auth_info['ssh_user'],
                            ssh_password=auth_info['ssh_passwd'],
                            remote_bind_address=(auth_info['db_host'], auth_info['db_port']))


def get_db_connection(port=3306, auth=auth_info):
    db_connection_str = 'mysql+mysqlconnector://{}:{}@{}:{}/{}'.format(auth['db_username'],
                                                                       auth['db_password'],
                                                                       auth['db_host'],
                                                                       port,
                                                                       auth['db_name'])
    return db.create_engine(db_connection_str)


def create_messages_table(connection=None, drop_if_exists=False):
    if not connection:
        raise Exception('Connection is None')
    if drop_if_exists:
        raw = get_db_connection(3306, read_auth_info()).raw_connection()
        cursor = raw.cursor()
        command = "DROP TABLE IF EXISTS messages;"
        cursor.execute(command)
        raw.commit()
        cursor.close()
    if not connection.engine.dialect.has_table(connection.engine, 'messages'):
        path = Path.home().joinpath(".bosch_pls")
        with open(str(path.joinpath('messages.sql'))) as table:
            connection.execute(table.read())
        logger.info('created table "messages"')


def get_last_n_records(table, n):
    with tunnel:
        query = 'SELECT * FROM {} ORDER BY time DESC LIMIT {}'.format(table, n)
        with get_db_connection(tunnel.local_bind_port).begin() as connection:
            df = pd.read_sql_query(query, connection, index_col='time', parse_dates=True)[::-1]
    return df


def get_data_from_server(tables_names, start_date=None):
    df_list = list()
    with tunnel:
        for table in tables_names:
            if start_date:
                df_list.append(
                    pd.read_sql_query('SELECT * FROM {} WHERE time >= \'{}\''.format(table, start_date.isoformat()),
                                      get_db_connection(tunnel.local_bind_port), index_col='time'))
            else:
                df_list.append(pd.read_sql_table(table, get_db_connection(tunnel.local_bind_port), index_col='time'))
    return df_list


def save_data_to_server(df, table_name, if_exists):
    with tunnel:
        df.to_sql(con=get_db_connection(tunnel.local_bind_port), name=table_name, if_exists=if_exists)


def remote_to_local(tables_names):
    tables_data = get_data_from_server(tables_names)
    with get_db_connection(3306, read_auth_info()).begin() as connection:
        create_messages_table(connection, drop_if_exists=True)
        for (name, data) in zip(tables_names, tables_data):
            data.to_sql(con=connection, name=name, if_exists='replace', chunksize=5000)
