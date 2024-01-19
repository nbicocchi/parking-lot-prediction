#!/usr/bin/python3
import argparse
from pathlib import Path
import paho.mqtt.client as mqtt
import ssl

from utilities.auth_info import read_auth_info
from utilities.init_data_path import get_data_path, get_log_path, get_log_filename
from utilities.init_logging import init_logging
from data_management.save_message import save_msg


def on_connect_callback(client, userdata, flags, rc):
    logger.info('MQTT client: Connected with result code {}'.format(rc))
    (result, mid) = client.subscribe(auth_info['mqtt_topic'])
    if result == mqtt.MQTT_ERR_SUCCESS:
        logger.info('MQTT client: Subscribed to {}'.format(auth_info['mqtt_topic']))
    else:
        logger.error('MQTT client: Can\'t subscribe to {}'.format(auth_info['mqtt_topic']))


def on_message_callback(client, userdata, msg):
    topic = str(msg.topic)
    payload = msg.payload.decode("utf-8")
    original = '{} | {}'.format(topic, payload)
    logger.info('original msg: {}'.format(original))
    with open(str(path.joinpath('data_original.jsonl')), 'a') as f:
        f.write(original + '\n')
    save_msg(topic, payload, args.park_id, args.save_to_file)


parser = argparse.ArgumentParser()
parser.add_argument('--park_id', type=str, default=0)
parser.add_argument('--log_to_sysout', action='store_true')
parser.add_argument('--save_to_file', action='store_true')
args = parser.parse_args()
path = get_data_path()
log_path = get_log_path()
log_filename = get_log_filename(Path(__file__).stem)
logger = init_logging(log_filename, args.log_to_sysout)
auth_info = read_auth_info()

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect_callback
mqtt_client.on_message = on_message_callback
mqtt_client.tls_set(keyfile=str(path.joinpath('keyfile.crt')), tls_version=ssl.PROTOCOL_TLSv1_2)
mqtt_client.username_pw_set(auth_info['mqtt_username'], password=auth_info['mqtt_password'])
mqtt_client.connect(auth_info['mqtt_host'], auth_info['mqtt_port'], 60)

mqtt_client.loop_forever()
