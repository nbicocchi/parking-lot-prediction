import argparse
import os
import shutil
from datetime import datetime
from analysis.plots import charts
import data_mgmt.load as load
from prediction_statistical.fourier import calculate_fourier
import prediction_statistical.median as median
from prediction_neural_network.train import train
from prediction_neural_network.prediction import prediction

path = os.getcwd()

parser = argparse.ArgumentParser()
parser.add_argument('--start_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
                    default=datetime(2019, 11, 15, 0, 0, 0, 0))
parser.add_argument('--end_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
                    default=datetime(2020, 2, 26, 0, 0, 0, 0))
parser.add_argument('--error', default=3)
args = parser.parse_args()


def get_path_folder_for(parking, folder):
    """
    if the path doesn't exist this function will create the path
    :param parking: parking lot used
    :param folder: folder to get everything organized
    :return: the path to the folder
    """
    if parking == 'mantova':
        path_parking = os.path.join(path, 'data_analysis_mantova', folder)
    else:
        path_parking = os.path.join(path, 'data_analysis_birmingham', parking, folder)
    if os.path.exists(path_parking):
        shutil.rmtree(path_parking)
    os.makedirs(os.path.join(path, path_parking))
    return path_parking


if __name__ == '__main__':
    birmingham_parks = ['BHMBCCMKT01', 'BHMBCCPST01', 'BHMBCCSNH01', 'BHMBCCTHL01', 'BHMBRCBRG01', 'BHMBRCBRG02',
                        'BHMBRCBRG03', 'BHMEURBRD01', 'BHMEURBRD02', 'BHMMBMMBX01', 'BHMNCPHST01', 'BHMNCPLDH01',
                        'BHMNCPNHS01',
                        'BHMNCPNST01', 'BHMNCPPLS01', 'BHMNCPRAN01', 'Broad Street', 'Bull Ring', 'NIA Car Parks',
                        'NIA North',
                        'NIA South', 'Others-CCCPS105a', 'Others-CCCPS119a', 'Others-CCCPS133', 'Others-CCCPS135a',
                        'Others-CCCPS202',
                        'Others-CCCPS8', 'Others-CCCPS98', 'Shopping']

    path_plots_mantova = get_path_folder_for("mantova", 'plots')
    df = load.load_mantova(args.start_date, args.end_date)[::12]
    charts(df, path_plots_mantova)

    # Prediction Statistical
    # median.get_plot(df, path_plots_mantova, error=args.error)
    # print('median accuracy (error={}) = {}'.format(args.error, median.get_accuracy(df, error=args.error)))
    # calculate_fourier(df, path_plots_mantova)

    # Neural network
    model = train(df, get_path_folder_for("mantova", 'neural_network'))

    # for park in birmingham_parks:
    #     path_parking_lot = get_path_folder_for(park)
    #     df = load.load_birmingham(park)
    #     #charts(df,path_parking_lot)
    #     calculate_fourier(df)
