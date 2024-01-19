import json
from collections import OrderedDict

from utilities.init_data_path import get_data_path


def load_devices():
    devices = dict()
    with open(str(path.joinpath('devices.jsonl')), mode='r') as f:
        for line in f.readlines():
            device = json.loads(line)
            lat, lon = device['gps'].split(',')
            if lat != '0' and lon != '0':
                lat = float(lat)
                lon = float(lon)
            else:
                lat = None
                lon = None
            devices[device['dev_eui']] = {'lat': lat, 'lon': lon, 'label': device['label']}
    return devices


def jsonl_to_csv():
    data = list()
    with open(str(path.joinpath('data.jsonl')), mode='r') as f:
        for line in f.readlines():
            x = json.loads(line, object_pairs_hook=OrderedDict)
            if x and x not in data:
                data.append(x)
    import pandas as pd
    df = pd.DataFrame(data)
    df.to_csv(path.joinpath('data.csv'), index=None)


path = get_data_path()
