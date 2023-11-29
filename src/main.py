import json
import os
import sys
import getopt
import shutil
from datetime import datetime
import numpy as np
import pandas as pd

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' #info, messages aren't printed
pd.options.mode.chained_assignment = None

from plots.data_plots import charts
from prediction_statistical.fourier import calculate_fourier
import prediction_statistical.median as median
from prediction_neural_network.train import train_get_data

birmingham_parks = ['BHMBCCMKT01', 'BHMBCCPST01', 'BHMBCCSNH01', 'BHMBCCTHL01', 'BHMBRCBRG01', 'BHMBRCBRG02',
                    'BHMBRCBRG03', 'BHMEURBRD01', 'BHMEURBRD02', 'BHMMBMMBX01', 'BHMNCPHST01', 'BHMNCPLDH01',
                    'BHMNCPNHS01',
                    'BHMNCPNST01', 'BHMNCPPLS01', 'BHMNCPRAN01', 'Broad Street', 'Bull Ring', 'NIA Car Parks',
                    'NIA North',
                    'NIA South', 'Others-CCCPS105a', 'Others-CCCPS119a', 'Others-CCCPS133', 'Others-CCCPS135a',
                    'Others-CCCPS202',
                    'Others-CCCPS8', 'Others-CCCPS98', 'Shopping']
#configuration for neural network - if weekday_hour = True than n_features = 3, otherwise n_features = 1
general_config_nn = {'n_timesteps_in': 24,'n_timesteps_out': 8, 'weekday_hour': True,'n_features': 3, 'test_size': 0.2, 'validation_size': 0.2, 'max_epochs': 1000, 'percentual_error': 3}

base_hyperparameters_config = {'conv_layers': [[(60, 6)], [(60, 12)], [(120, 6)], [(120, 12)],
                                          [(60, 3), (120, 6)], [(60, 6), (120, 6)]],
                          'fc_layers': [[400, 400], [200, 200, 200], [300, 300, 300], [400, 400, 400],[400, 300, 200], [300, 200, 100]],
                          'dropout_rate': [0.04],
                          'lstm_layers': [[], [1000]]}


def load_mantova(start_date, end_date, for_neural_network =False):
    """
    Neural network needs only time and occupancy/percentage data with frequancy of one hour, without indexing.
    """
    df = pd.read_csv(os.path.join(os.getcwd(), 'src', 'dataset', 'mantova.csv'),parse_dates=['time'])
    df = df[(df['time'] >= start_date) & (df['time'] < end_date)]
    #renaming to have same column name as birmingham
    df['occupancy'] = df['percentage']

    df.drop(columns='percentage', inplace=True)
    df.drop(columns='park_id', inplace=True)
    if not for_neural_network:
        df.index = df.time
        df.index.name = None
        df.drop(columns='time', inplace=True)
        df['free_slots'] = 68 - df['occupancy'] * 68 #number of sensors in the parking lot
    else:
        df = df[::12]
    return df


def load_birmingham(park, for_neural_network = False):
    pd.set_option('display.max_rows', None)
    df = pd.read_csv(os.path.join(os.getcwd(), 'src', 'dataset', 'birmingham.csv'), parse_dates=['LastUpdated'])
    df = df[df['SystemCodeNumber'].str.contains(park)]
    df = df.drop_duplicates(subset='LastUpdated', keep='first')
    df.index = df.LastUpdated
    df.index.name = None
    df = df.asfreq(freq='1H', method='bfill')
    
    
    if not for_neural_network:
        df['free_slots'] = df['Capacity'] - df['Occupancy']
    else:
        df['time'] = df.index
        df = df.reset_index(drop=True)
    df['occupancy'] = df['Occupancy'] / df['Capacity']
    print(df.groupby(by=df.index.dt.date)['occupancy'].transform('var'))
    df['var'] = df.groupby(by=df.index.dt.date)['occupancy'].transform('var')
    #print(df)

    df.drop(columns='LastUpdated', inplace=True)
    df.drop(columns='Capacity', inplace=True)
    df.drop(columns='Occupancy', inplace=True)
    df.drop(columns='SystemCodeNumber', inplace=True)
    #print(df)
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
    if not os.path.exists(path_parking):
        os.makedirs(os.path.join(path, path_parking))
    return path_parking


def myfunc(argv):
    flag_parking = False
    flag_statistical = False
    flag_neural_network = False
    flag_create_chart = False
    arg_parking = ""
    arg_help = "usage: {0} [-csnwp 'parking_lot_name'] [--help] [--parking=] [--chart_only] [--statistical_data] [--neural_network_data] [--wornings] \n \
            options: \n \
            -h, --help  show this help message and exit \n \
            -p, --parking   if specified it will generate data just for the specified parking lot\n \
            -c, --chart_only    if specified it will generate data chart\n \
            -s, --statistical_data   if specified it will generate statistical data\n \
            -n, --neural_network_data if specified it will generate neural_network data\n \
            -w, --wornings   Wornings\n\
            if -csn are not specified then everything will be generated automatically".format(argv[0])
    try:
        opts, args = getopt.getopt(argv[1:], "hp:csnw",
                                   ["help", "parking=", "chart_only", "statistical_data", "neural_network_data", "wornings"])
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
            flag_statistical = True
        elif opt in ("-c", "--chart_only"):
            flag_create_chart = True
        elif opt in ("-n", "--neural_network_data"):
            flag_neural_network = True
        elif opt in ("-v", "--verbose"):
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '0' #restore info and messages
            pd.options.mode.chained_assignment = 'warn'

    if not flag_statistical and not flag_create_chart and not flag_neural_network:
        flag_statistical = flag_create_chart = flag_neural_network = True
    config_dict = read_config_file()
    if arg_parking not in config_dict.keys():
        print('ERROR: parking lot \'{}\' isn\'t in config.json'.format(arg_parking))
        sys.exit(2)
    if flag_parking:
        generate_data_for(arg_parking, config_dict.get(arg_parking), flag_create_chart, flag_statistical, flag_neural_network)
    else:
        generate_data_for_every_parking_lot(config_dict,flag_create_chart, flag_statistical, flag_neural_network)
    print('*' * 100)


def generate_data_for_every_parking_lot(config_dict: dict,flag_create_chart: bool, flag_statistical: bool, flag_neural_network: bool):
    birmingham_parks.insert(0,'mantova')
    for parking in birmingham_parks:
        generate_data_for(parking, config_dict.get(parking), flag_create_chart, flag_statistical, flag_neural_network)


def get_df(parking_id: str, parking_config: dict, for_neural_network: bool):
    df = pd.DataFrame
    if parking_id == 'mantova':
        df = load_mantova(parking_config['start_date'], parking_config['end_date'], for_neural_network)
    elif parking_id in birmingham_parks:
        df = load_birmingham(parking_id, for_neural_network)
    else:
        print('ERROR: parking lot \'{}\' doesn\'t exists into the dataset'.format(parking_id))
        sys.exit(2)
    return df


def generate_data_for(parking_id: str, parking_config: dict, flag_create_chart: bool, flag_statistical: bool, flag_neural_network: bool):
    df = get_df(parking_id, parking_config, False)
    path_plots = get_folder_path(parking_id, 'plots')
    print('*' * 100,'\nparking lot: ', parking_id )

    if flag_create_chart:
        charts(df, path_plots)
        print('charts generated at path: {}'.format(path_plots))

    if flag_statistical:
        median.get_plot_and_print_accuracy(df,path_plots,parking_config['capacity'],[3,4])
        #for better resoult in fourier analysis mantova needs data frequency of one hour 
        if parking_id == 'mantova':
            df = df[::12]
        calculate_fourier(df, path_plots, parking_config['capacity'],[3,4])

    if flag_neural_network:
        df = get_df(parking_id, parking_config, True)
        if parking_config['hyperparameters_config'] is None:
                parking_config['hyperparameters_config'] = base_hyperparameters_config
        model = train_get_data(df, path_plots, get_folder_path(parking_id, 'neural_network_build'), parking_config['capacity'], parking_config['hyperparameters_config'], general_config_nn, plot=True)
        print(model)

def read_config_file():
    """
    if the file exists this function will return a dictionary containing all parking lots configurations, 
    in case the file doesn't exists it's going to be created
    """
    json_config = {}
    path = os.path.join('src','config.json')
    if os.path.exists(path):
        with open(path, 'r') as openfile:
            json_config = json.load(openfile)
    else:
        json_config = create_config_file()

    # casting string from json file to datetime
    for parking in json_config:
        start_date = json_config.get(parking)['start_date']
        if start_date is not None:
            json_config.get(parking)['start_date'] =  datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        end_date = json_config.get(parking)['end_date']
        if start_date is not None:
            json_config.get(parking)['end_date'] =  datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
    return json_config


def create_config_file():
    """
    Crearion of the config JSON file, inserting mantova and birmingham info.
    This file is NEEDED to let statistical and neural network working.
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
            "hyperparameters_config": None
        }
    print("creation of config.json file")
    with open(os.path.join('src','config.json'), "w") as outfile:
        outfile.write(json.dumps(config_file, indent=4))
    return config_file


if __name__ == '__main__':
    myfunc(sys.argv)

