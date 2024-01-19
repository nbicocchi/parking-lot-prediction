import csv
import json

from utilities.init_data_path import get_data_path


def load_info():
    devices = dict()
    with open(str(path.joinpath('application_devices.csv')), mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            original_dict = dict(row)
            dev_eui = original_dict['deveui']
            devices[dev_eui] = {'dev_eui': dev_eui, 'label': original_dict['label']}
    with open(str(path.joinpath('posizioni.csv')), mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
        for row in csv_reader:
            original_dict = dict(row)
            dev_eui = original_dict['dev_eui']
            devices[dev_eui] = {'dev_eui': dev_eui, 'label': original_dict['label'],
                                'gps': original_dict[list(original_dict.keys())[0]]}

    with open(str(path.joinpath('devices.jsonl')), mode='w') as jsonl_file:
        for device in list(devices.values()):
            json_data = json.dumps(device)
            jsonl_file.write(json_data + '\n')


path = get_data_path()
load_info()
