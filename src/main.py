import json
import os
import sys
import getopt
from datetime import datetime
from matplotlib import pyplot as plt
import pandas as pd
from multiprocessing import Process, Queue
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' #info and general messages aren't printed
pd.options.mode.chained_assignment = None

from plots.data_plots import charts
from prediction_statistical.fourier import calculate_fourier
import prediction_statistical.median as median
from prediction_neural_network.train import train_get_data

#configuration for neural network - if weekday_hour = True than n_features = 3, otherwise n_features = 1
general_config_nn = {'n_timesteps_in': 24,'n_timesteps_out': 8, 'weekday_hour': True,'n_features': 3, 'test_size': 0.2, 'validation_size': 0.2, 'max_epochs': 1000, 'percentual_error': [3,4]}


base_hyperparameters_config = {'conv_layers': [[(60, 3)], [(60, 6)], [(60, 12)], [(120, 6)], [(120, 12)]],
                          'fc_layers': [[400, 200], [400, 300], [400, 400],
                                        [100, 100, 100], [200, 200, 200], [300, 300, 300], [400, 400, 400],
                                        [400, 300, 200], [300, 200, 100]],
                          'dropout_rate': [0.04, 0.08],
                          'lstm_layers': [[1000]]}


def load_mantova(start_date, end_date):
    df = pd.read_csv(os.path.join(os.getcwd(), 'src', 'dataset', 'mantova.csv'),parse_dates=['time'])
    df = df[(df['time'] >= start_date) & (df['time'] < end_date)]
    #renaming to have same column name as birmingham
    
    df.index = df.time
    df.index.name = None
    
    df['occupancy'] = df['percentage']
    df['free_slots'] = 68 - df['occupancy'] * 68 #number of sensors in the parking lot
    
    #df = df.resample(rule='1H').mean()
    
    df.drop(columns='time', inplace=True)
    df.drop(columns='percentage', inplace=True)
    df.drop(columns='park_id', inplace=True)
    return df[::12]


def load_birmingham(park):
    #pd.set_option('display.max_rows', None)
    df = pd.read_csv(os.path.join(os.getcwd(), 'src', 'dataset', 'birmingham.csv'), parse_dates=['LastUpdated'])
    df = df[df['SystemCodeNumber'].str.contains(park)]
    df = df.drop_duplicates(subset='LastUpdated', keep='first')

    df.index = df.LastUpdated
    df.index.name = None
  
    df = df.asfreq(freq='1H', method='bfill')
    df['free_slots'] = df['Capacity'] - df['Occupancy']
    df['occupancy'] = df['Occupancy'] / df['Capacity']
    df['var'] = df.groupby(by=df.index.date)['occupancy'].transform('var')
    
    df = df[df['var'] != 0]

    df.drop(columns='LastUpdated', inplace=True)
    df.drop(columns='Capacity', inplace=True)
    df.drop(columns='Occupancy', inplace=True)
    df.drop(columns='SystemCodeNumber', inplace=True)
    df.drop(columns='var', inplace=True)
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


def check_data(df):
    #df = df[::12]
    #df = df[df.index > datetime(2016,12,12)]
    df = df[df.index > datetime(2020,2,17)]
    df.plot(y='occupancy', kind='line')	
    plt.savefig('analysis.png')


def get_parking_where_config_hyperparameter_is_null(config_dict, parking_lots):
    """
    return a list with only parking lots that needs hyperparameter tuning.
    """
    new_list= []
    for parking in parking_lots:
        if config_dict.get(parking)['hyperparameters_config'] is None:
            new_list.append(parking)
    return new_list


def get_config(parking_lots):
    """
    return a dictionary from config.json file, needed to process data.
    Called Sys.exit() if a parking lot hasn't it's own configuration.
    """
    config_dict = read_config_file(parking_lots)
    for parking in parking_lots:
        if parking not in config_dict.keys():
            print('ERROR: parking lot \'{}\' isn\'t in config.json'.format(parking))
            sys.exit(2)
    return config_dict


def mymain(argv, parking_lots):
    flag_args = {'statistics' : False, 'neural_network' : False, 'create_chart' : False, 'update_hyperparameters' : False}
    arg_parking = None
    config_dict = get_config(parking_lots)
    
    arg_help = "usage: {0} [-csnwp 'parking_lot_name'] or [-u] [--help] [--parking=] [--chart_only] [--statistical_data] [--neural_network_data] [--wornings] [--update_hyper]\n \
            options: \n \
            -h, --help  show this help message and exit \n \
            -p, --parking   if specified it will generate data just for the specified parking lot\n \
            -c, --chart_only    if specified it will generate data chart\n \
            -s, --statistical_data   if specified it will generate statistical data\n \
            -n, --neural_network_data if specified it will generate neural_network data\n \
            -w, --wornings   Wornings\n\
            -u  --update_hyper\n if specified it will update hyperparameters of parking lots where hyperparameters_config is null\
            if -csn are not specified then everything will be generated automatically".format(argv[0])
    try:
        opts, args = getopt.getopt(argv[1:], "hp:csnwu",
                                   ["help", "parking=", "chart_only", "statistical_data", "neural_network_data", "wornings", 'update_hyper'])
    except:
        print(arg_help)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(arg_help)  # print the help message
            sys.exit(2)
        elif opt in ("-p", "--parking"):
            arg_parking = arg
        elif opt in ("-s", "--statistical_data"):
            flag_args['statistics'] = True
        elif opt in ("-c", "--chart_only"):
            flag_args['create_chart'] = True
        elif opt in ("-n", "--neural_network_data"):
            flag_args['neural_network'] = True
        elif opt in ("-u", "--update_hyper"):
            flag_args['update_hyperparameters'] = True
        elif opt in ("-w", "--wornings"):
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '0' #restore info and messages
            pd.options.mode.chained_assignment = 'warn'

    if arg_parking != None:
        if arg_parking not in parking_lots:
            print('ERROR: parking lot \'{}\' doesn\'t exists into the dataset'.format(arg_parking))
            sys.exit(2)
        parking_lots = [arg_parking]
    
    if flag_args.get('update_hyperparameters'):
        parking_lots = get_parking_where_config_hyperparameter_is_null(config_dict, parking_lots)
        flag_args['neural_network'] = True
        print("parking lots to update: ",parking_lots)

    if not flag_args.get('statistics') and not flag_args.get('create_chart') and not flag_args.get('neural_network'):
        flag_args['create_chart'] = True
        flag_args['statistics'] = True
        flag_args['neural_network'] = True
        
    generate_data_for_every_parking_lot(parking_lots, config_dict, flag_args)
    

def generate_data_for_every_parking_lot(parking_lots: list, config_dict: dict, flag_args: dict):
    counter :int = 1
    for parking in parking_lots:
        print(f"\n{'=' * 40} {counter}/{len(parking_lots)} parking lot: {parking} {'=' * 40}\n")
        generate_data_for(parking, config_dict.get(parking), flag_args)
        counter+=1


def get_df(parking_id: str, parking_config: dict):
    """Return a dataframe from a given parking_id."""
    df = pd.DataFrame
    if parking_id == 'mantova':
        df = load_mantova(parking_config['start_date'], parking_config['end_date'])
    else:
        df = load_birmingham(parking_id)
    return df


def generate_data_for(parking_id: str, parking_config: dict, flag_args: dict):
    """
    given a parking lots and it's configurations this function will generate data where value in flag_args = True.
    """
    df = get_df(parking_id, parking_config)
    path_plots = get_folder_path(parking_id, '')
    check_data(df) 
    #sys.exit(0)
    if flag_args.get('create_chart'):
        charts(df, path_plots)
        print(f'charts generated at path: {path_plots}\n')

    if flag_args.get('statistics'):
        median.get_plot_and_print_accuracy(df,path_plots,parking_config['capacity'],[3,4])
        calculate_fourier(df, path_plots, parking_config['capacity'],[3,4])
        print()

    if flag_args.get('neural_network'):
        print("Getting neural network data with lstm")
        path = get_folder_path(parking_id, 'neural_network_WITH_lstm_build')
        if parking_config['hyperparameters_config'] is None: #then find the best parameters and save them
            #creating new process every parcking lot due to memory leak of tensorflow with CPU or GPU
            queue = Queue()
            p1 = Process(target=train_get_data, args=(df, path, get_folder_path(parking_id, 'neural_network_build'), parking_config['capacity'], base_hyperparameters_config, general_config_nn, queue, True))
            p1.start()
            p1.join()
            best_hp = queue.get()
            update_config_file(parking_id, best_hp)
        else:   
            train_get_data(df, path, path, parking_config['capacity'], parking_config['hyperparameters_config'], general_config_nn, plot=True)
            parking_config['hyperparameters_config']['lstm_layers'] = [[]]
            print("\nGetting neural network data without lstm")
            path = get_folder_path(parking_id, 'neural_network_NO_lstm_build')
            train_get_data(df, path, path, parking_config['capacity'], parking_config['hyperparameters_config'], general_config_nn, plot=True)


def update_config_file(parking_id: str, bast_hyperparameters: dict):
    print("Updating config file")
    path = os.path.join('src','config.json')
    with open(path, 'r') as file:
            json_config = json.load(file)
    #transform string to dict
    hyperparameters = {} 
    for key, item in bast_hyperparameters.items():
        hyperparameters[key] = [item]
    json_config[parking_id]['hyperparameters_config'] = hyperparameters

    with open(path, 'w') as file:
        file.write(json.dumps(json_config, indent=4))


def read_config_file(parking_lots):
    """
    if the file exists this function will return a dictionary containing all parking lots configurations, 
    in case the file doesn't exists it's going to be generated
    """
    json_config = {}
    path = os.path.join('src','config.json')
    if os.path.exists(path):
        with open(path, 'r') as file:
            json_config = json.load(file)
    else:
        json_config = create_config_file(parking_lots)
    # casting string from json file to datetime
    for parking in json_config:
        start_date = json_config.get(parking)['start_date']
        if start_date is not None:
            json_config.get(parking)['start_date'] =  datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        end_date = json_config.get(parking)['end_date']
        if start_date is not None:
            json_config.get(parking)['end_date'] =  datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
    return json_config


def create_config_file(parking_lots):
    """
    Crearion of the config JSON file, inserting mantova and birmingham info.
    This file is NEEDED to let statistical and neural network working.
    """
    config_file = {}
    for parking in parking_lots:
        if parking == 'mantova':
            config_file['mantova'] = { 
                    "capacity": 68,
                    'start_date' : '2019-12-16 0:0:0',
                    'end_date' : '2020-2-25 0:0:0',
                    "hyperparameters_config": {'conv_layers': [[(60, 12)]],
                                                'fc_layers': [[400, 400, 400]],
                                                'dropout_rate': [0.04],
                                                'lstm_layers': [[1000]]}
                    }
        else:
            df = pd.read_csv(os.path.join(os.getcwd(), 'src', 'dataset', 'birmingham.csv'))
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
    #NIA North gives error with charts
    parking_lots = ['mantova','BHMBCCMKT01', 'BHMBCCPST01', 'BHMBCCSNH01', 'BHMBCCTHL01', 'BHMBRCBRG01', 'BHMBRCBRG02',
                    'BHMBRCBRG03', 'BHMEURBRD01', 'BHMEURBRD02', 'BHMMBMMBX01', 'BHMNCPHST01', 'BHMNCPLDH01',
                    'BHMNCPNHS01',
                    'BHMNCPNST01', 'BHMNCPPLS01', 'BHMNCPRAN01', 'Broad Street', 'Bull Ring', 'NIA Car Parks',
                    'NIA South', 'Others-CCCPS105a', 'Others-CCCPS119a', 'Others-CCCPS133', 'Others-CCCPS135a',
                    'Others-CCCPS202',
                    'Others-CCCPS8', 'Others-CCCPS98', 'Shopping']
    mymain(sys.argv,parking_lots)