import yaml

from utilities.init_data_path import get_data_path


def read_auth_info(suffix=''):
    auth_file = path.joinpath('auth{}.yaml'.format(suffix))
    with open(str(auth_file), 'r') as f:
        auth_data = yaml.load(f)
    return auth_data


path = get_data_path()
