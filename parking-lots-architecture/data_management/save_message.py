import csv
import logging
from collections import OrderedDict
from datetime import datetime
import json
import pandas as pd

from data_management.database_utilities import get_db_connection
from utilities.init_data_path import get_data_path

msg_type_map = {'/uplink/3': 'startup',
                '/uplink/2': 'heartbeat',
                '/uplink/1': 'update'}
logger = logging.getLogger(__name__)


def optimize(topic: str, msg: str, park_id: str = 0):
    data = None
    msg_dict = json.loads(msg)
    topic = topic.replace('/sub/v1/users/unimore/apps/1/devices/', '')
    msg_type = topic[16:]
    if 'statistics' in msg_dict.keys() and msg_type in msg_type_map.keys():
        data = OrderedDict()
        data['time'] = datetime.fromtimestamp(round(msg_dict['statistics']['time'] / 1000)).isoformat()
        data['park_id'] = park_id
        data['dev_eui'] = topic[0:16]
        data['seqno'] = msg_dict['seqno']
        data['msg_type'] = msg_type_map[msg_type]
        payload = msg_dict['payload']
        data['state'] = int(payload[-2:])
        if len(payload) != 2:
            data['payload'] = payload
        logger.info('optimize msg: {}'.format(data))
    return data


def df_to_db(df):
    df['time'] = pd.to_datetime(df['time'])
    df = df.reindex(columns=['time', 'dev_eui', 'seqno', 'msg_type', 'state', 'payload'])
    with get_db_connection().begin() as connection:
        df.to_sql(con=connection, name='messages', if_exists='append', index=False)
        logger.info('saved in database')


def msg_to_db(data: dict):
    df_to_db(pd.DataFrame([data]))


def msg_to_jsonl(data: dict):
    json_data = json.dumps(data)
    with open(str(path.joinpath('data.jsonl')), 'a') as f:
        f.write(json_data + '\n')
    logger.info('saved in data.jsonl')


def msg_to_csv(data: dict):
    with open(str(path.joinpath('data.csv')), 'a') as f:
        w = csv.DictWriter(f, fieldnames=data.keys())
        if f.tell() == 0:
            w.writeheader()
            w.writerow(data)
        else:
            w.writerow(data)
    logger.info('saved in data.csv')


def save_msg(topic: str, payload: str, park_id: str, to_file):
    data = optimize(topic, payload, park_id)
    if data:
        if to_file:
            msg_to_csv(data)
            # msg_to_jsonl(data)
        else:
            msg_to_db(data)


path = get_data_path()
