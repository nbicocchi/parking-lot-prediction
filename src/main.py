import json
import os
import sys
import getopt
import shutil
from datetime import datetime
import pandas as pd

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' #info, messages and error are't printed
pd.options.mode.chained_assignment = None

from plots.data_plots import charts
from prediction_statistical.fourier import calculate_fourier
import prediction_statistical.median as median
from prediction_neural_network.train import train

birmingham_parks = ['BHMBCCMKT01', 'BHMBCCPST01', 'BHMBCCSNH01', 'BHMBCCTHL01', 'BHMBRCBRG01', 'BHMBRCBRG02',
                    'BHMBRCBRG03', 'BHMEURBRD01', 'BHMEURBRD02', 'BHMMBMMBX01', 'BHMNCPHST01', 'BHMNCPLDH01',
                    'BHMNCPNHS01',
                    'BHMNCPNST01', 'BHMNCPPLS01', 'BHMNCPRAN01', 'Broad Street', 'Bull Ring', 'NIA Car Parks',
                    'NIA North',
                    'NIA South', 'Others-CCCPS105a', 'Others-CCCPS119a', 'Others-CCCPS133', 'Others-CCCPS135a',
                    'Others-CCCPS202',
                    'Others-CCCPS8', 'Others-CCCPS98', 'Shopping']

#configuration for neural network - if weekday_hour = True than n_features = 3, otherwise n_features = 1
general_config_nn = {'n_timesteps_in': 24,'n_timesteps_out': 8, 'weekday_hour': True,'n_features': 3, 'test_size': 0.2, 'validation_size': 0.2, 'max_epochs': 1000, 'percentual_error': 3 }


def load_mantova_for_nn(start_date, end_date):
    df = pd.read_csv(os.path.join(os.getcwd(), 'src', 'dataset', 'mantova.csv'),parse_dates=['time'])
    df = df[(df['time'] >= start_date) & (df['time'] < end_date)]
    df.drop(columns='park_id', inplace=True)
    return df


def load_mantova(start_date, end_date):
    df = pd.read_csv(os.path.join(os.getcwd(), 'src', 'dataset', 'mantova.csv'))
    df.index = pd.to_datetime(df.time)
    df = df[(df.index >= start_date) & (df.index <= end_date)]
    df.index.name = None

    df['occupancy'] = df['percentage']
    df['free_slots'] = 68 - df['occupancy'] * 68

    df.drop(columns='percentage', inplace=True)
    df.drop(columns='time', inplace=True)
    df.drop(columns='park_id', inplace=True)
    return df


def load_birmingham(park):
    df = pd.read_csv(os.path.join(os.getcwd(), 'src', 'dataset', 'birmingham.csv'))

    df = df[df['SystemCodeNumber'].str.contains(park)]

    df = df.drop_duplicates(subset='LastUpdated', keep='first')
    df.index = pd.to_datetime(df.LastUpdated)
    df.index.name = None
    df = df.asfreq(freq='1H', method='bfill')

    df['occupancy'] = df['Occupancy'] / df['Capacity']
    df['free_slots'] = df['Capacity'] - df['Occupancy']

    df.drop(columns='Capacity', inplace=True)
    df.drop(columns='Occupancy', inplace=True)
    df.drop(columns='LastUpdated', inplace=True)
    df.drop(columns='SystemCodeNumber', inplace=True)
    return df


def get_folder_path(parking, folder):
    """
    if the path doesn't exist this function will create it
    :param parking: parking lot used
    :param folder: folder where to store relative files
    :return: path to the folder
    """
    path = os.getcwd()
    if parking == 'mantova':
        path_parking = os.path.join(path, 'data_analysis_mantova', folder)
    else:
        path_parking = os.path.join(path, 'data_analysis_birmingham', parking, folder)
    if os.path.exists(path_parking):
        shutil.rmtree(path_parking)
    os.makedirs(os.path.join(path, path_parking))
    return path_parking


def myfunc(argv):
    flag_parking = False
    flag_statistical = True
    flag_neural_network = True
    flag_create_config_file = False
    arg_parking = ""
    arg_help = "usage: {0} [-h] [--parking=] [--chart_only] [--wornings] \n \
            options: \n \
            -h, --help  show this help message and exit \n \
            -p, --parking   if specified it will generate data just for the specified parking lot\n \
            -s, --statistical_data   if specified it will generate statistical data only\n \
            -n, --neural_network_data if specified it will generate neural_network data only\n \
            -w, --wornings   Wornings \
            --create_config_file    will generate the configuration file for mantova and birmingham automatically".format(argv[0])
    try:
        opts, args = getopt.getopt(argv[1:], "hp:snw",
                                   ["help", "parking=", "statistical_data", "neural_network_data", "wornings", "create_config_file"])
    except:
        print(arg_help)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(arg_help)  # print the help message
            sys.exit(2)
        elif opt in ("-p", "--parking"):
            arg_parking = arg
            flag_parking = True
        elif opt in ("-s", "--statistical_data"):
            flag_neural_network = False
        elif opt in ("-n", "--neural_network_data"):
            flag_statistical = False
        elif opt in ("-v", "--verbose"):
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '0' #restore info and messages
            pd.options.mode.chained_assignment = 'warn'
        elif opt in ("--create_config_file"):
            flag_create_config_file = True

    config_dict = read_config_file(flag_create_config_file)
    if arg_parking not in config_dict.keys():
        print('ERROR: missing configuration for parking lot \'{}\' in config.json'.format(arg_parking))
        sys.exit(2)

    if flag_parking:
        generate_data_for(arg_parking, config_dict.get(arg_parking),flag_statistical, flag_neural_network)
    else:
        generate_data_for_every_parking_lot(config_dict, flag_statistical, flag_neural_network)
    print('*' * 100)


def generate_data_for_every_parking_lot(config_dict: dict,flag_statistical: bool, flag_neural_network: bool):
    birmingham_parks.insert(0,'mantova')
    for parking in birmingham_parks:
        generate_data_for(parking, config_dict.get(parking),flag_statistical, flag_neural_network)


def generate_data_for(parking_lot: str, parking_config: dict,flag_statistical: bool, flag_neural_network: bool):
    print()
    if parking_lot == 'mantova':
        df = load_mantova(parking_config['start_date'], parking_config['end_date'])
        start_fourier = None  # TODO: fare file config con date migliori
        end_fourier = None
    elif parking_lot in birmingham_parks:
        df = load_birmingham(parking_lot)
        start_fourier = None  # TODO: fare file config con date migliori
        end_fourier = None
    else:
        print('ERROR: parking lot \'{}\' doesn\'t exists into the dataset'.format(parking_lot))
        sys.exit(2)

    print('*' * 100)
    print('parking lot: ', parking_lot)
    path_plots = get_folder_path(parking_lot, 'plots')
    

    capacity_parking_lot = 68
    hyperparameters_config = 34

    charts(df, path_plots)
    if flag_statistical:
        median.get_plot_and_print_accuracy(df,path_plots,parking_config['capacity'],[3,4])
        if parking_lot == 'mantova':
            df = df[::12]
        calculate_fourier(df, path_plots, parking_config['capacity'],[3,4],start_fourier, end_fourier)

    if flag_neural_network:
        df = load_mantova_for_nn(datetime(2019, 12, 16,0,0,0), datetime(2020, 2, 26, 0, 0, 0, 0))#provare con datetime(2020, 2, 25, 0, 0, 0, 0)
        train(df, path_plots, get_folder_path(parking_lot, 'neural_network_build'), parking_config['capacity'], parking_config['hyperparameters_config'], general_config_nn, True)


def read_config_file(create_file = False):
    """
    if the file exists this function will return a dictionary containing all parking lots configurations, 
    otherwise it will create it if: create = True
    """
    json_config = {}
    path = os.path.join('src','config.json')
    if os.path.exists(path):
        with open(path, 'r') as openfile:
            json_config = json.load(openfile)
    else:
        if create_file:
            json_config = create_config_file()

    # casting string to datetime
    for parking in json_config:
        start_date = json_config.get(parking)['start_date']
        if start_date is not None:
            json_config.get(parking)['start_date'] =  datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        end_date = json_config.get(parking)['end_date']
        if start_date is not None:
            json_config.get(parking)['end_date'] =  datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
        #data = json_config.get(key)
        #data['start_date'] = datetime.strptime(data['start_date'], '%y-%m-%d %H:%M:%S')
    return json_config


def create_config_file():
    """
    Crearion of the config JSON, inserting mantova and birmingham info
    this file is needed to let the statistical and neural network working.
    """
    config_file = {}
    config_file['mantova'] = { 
            "capacity": 68,
            'start_date' : '2019-12-16 0:0:0',
            'end_date' : '2020-2-25 0:0:0',
            "hyperparameters_config": {'conv_layers': [[(60, 12)]],
                                        'fc_layers': [[400, 400, 400]],
                                        'dropout_rate': [0.04],
                                        'lstm_layers': [[], [1000]]}
            }
    df = pd.read_csv(os.path.join(os.getcwd(), 'src', 'dataset', 'birmingham.csv'))    
    for parking in birmingham_parks:
        capacity =  int(df[df['SystemCodeNumber'].str.contains(parking)]['Capacity'].values[0])
        config_file[parking]= { 
            'capacity': capacity,
            'start_date' : None,
            'end_date' : None,
            "hyperparameters_config": {}
            }

    with open(os.path.join('src','config.json'), "w") as outfile:
        outfile.write(json.dumps(config_file, indent=4))
    return config_file


if __name__ == '__main__':
    myfunc(sys.argv)

