import os
import sys
import getopt
import shutil
from datetime import datetime
import pandas as pd

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # or any {‘0’, ‘1’, ‘2’}
pd.options.mode.chained_assignment = None

from analysis.plots import charts
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


# parser = argparse.ArgumentParser()
# parser.add_argument('--start_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
#                     default=datetime(2019, 12, 16, 0, 0, 0, 0))
# parser.add_argument('--end_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
#                     default=datetime(2020, 2, 26, 0, 0, 0, 0))
# parser.add_argument('--error', default=3)
# args = parser.parse_args()


def load_mantova_for_nn(start_date, end_date):
    df = pd.read_csv(
        '/mnt/c/Users/Luca/PycharmProjects/parking_lot_prediction/parking-lot-prediction/src/dataset/mantova.csv',
        parse_dates=['time'])
    df = df[(df['time'] >= start_date) & (df['time'] < end_date)][::12]
    df.drop(columns='park_id', inplace=True)
    return df


def load_mantova(start_date, end_date):
    df = pd.read_csv(
        '/mnt/c/Users/Luca/PycharmProjects/parking_lot_prediction/parking-lot-prediction/src/dataset/mantova.csv')

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
    df = pd.read_csv(
        '/mnt/c/Users/Luca/PycharmProjects/parking_lot_prediction/parking-lot-prediction/src/dataset/birmingham.csv')

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
    arg_parking = ""
    arg_help = "usage: {0} [-h] [--parking] [--chart_only] [--verbose] \n \
            options: \n \
            -h, --help  show this help message and exit \n \
            -p, --parking   if specified it will generate data just for the specified parking lot\n \
            -s, --statistical_data   if specified it will generate statistical data only\n \
            -n, --neural_network_data if specified it will generate neural_network data only\n \
            -v, --verbose   Wornings".format(argv[0])
    try:
        opts, args = getopt.getopt(argv[1:], "hp:snv",
                                   ["help", "parking=", "statistical_data", "neural_network_data", "verbose"])
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
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '0'
            pd.options.mode.chained_assignment = 'warn'

    if flag_parking:
        generate_data_for(arg_parking, flag_statistical, flag_neural_network)
    else:
        generate_all_parking_data()


def generate_all_parking_data():
    pass


def generate_data_for(parking_lot, flag_statistical, flag_neural_network):
    if parking_lot == 'mantova':
        df = load_mantova(datetime(2019, 12, 16, 0, 0, 0, 0), datetime(2020, 2, 26, 0, 0, 0, 0))[::12]
        start_fourier = datetime(2019, 12, 16)
        end_fourier = datetime(2020, 2, 24)
    elif parking_lot in birmingham_parks:
        df = load_birmingham(parking_lot)[::12]
        start_fourier = None  # TODO: fare file config con date migliori
        end_fourier = None
    else:
        print('ERROR: parking lot \'{}\' doesn\'t exists into the dataset'.format(parking_lot))
        sys.exit(2)

    if flag_statistical:
        path_plots = get_folder_path(parking_lot, 'plots')
        charts(df, path_plots)
        median.get_plot(df, path_plots, error=3)
        print('median accuracy (error={}) = {}'.format(3, median.get_accuracy(df, error=3)))
        print('median accuracy (error={}) = {}'.format(4, median.get_accuracy(df, error=4)))
        # calculating fourier passing 9 weeks, 8 for training 1 for validation 
        calculate_fourier(df, path_plots, start_fourier, end_fourier)

    if flag_neural_network:
        # Neural network #provare con datetime(2020, 2, 25, 0, 0, 0, 0)
        df = load_mantova_for_nn(datetime(2019, 12, 16), datetime(2020, 2, 26, 0, 0, 0, 0))
        train(df, get_folder_path("mantova", 'neural_network'), True)


if __name__ == '__main__':
    myfunc(sys.argv)
