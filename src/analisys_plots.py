import argparse
from datetime import datetime

import pandas as pd

import data_mgmt.load as load
import analysis.plots as plots

parser = argparse.ArgumentParser()
parser.add_argument('--start_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'), default=datetime(2019, 11, 15, 0, 0, 0, 0))
parser.add_argument('--end_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'), default=datetime(2020, 2, 26, 0, 0, 0, 0))
args = parser.parse_args()


def charts(df):
    # plots.plt.style.use('fivethirtyeight')
    plots.occupancy_plot(df)
    plots.occupancy_heatmap(df)
    plots.free_parking_hour_plot(df)
    plots.free_parking_week_boxplot(df)


if __name__ == '__main__':
    birminghan_parks = ['BHMBCCMKT01', 'BHMBCCPST01', 'BHMBCCSNH01', 'BHMBCCTHL01', 'BHMBRCBRG01', 'BHMBRCBRG02', 'BHMBRCBRG03',
     'BHMEURBRD01', 'BHMEURBRD02', 'BHMMBMMBX01', 'BHMNCPHST01', 'BHMNCPLDH01', 'BHMNCPNHS01',
     'BHMNCPNST01', 'BHMNCPPLS01', 'BHMNCPRAN01', 'Broad Street', 'Bull Ring', 'NIA Car Parks', 'NIA North',
     'NIA South', 'Others-CCCPS105a', 'Others-CCCPS119a', 'Others-CCCPS133', 'Others-CCCPS135a', 'Others-CCCPS202',
     'Others-CCCPS8', 'Others-CCCPS98', 'Shopping']

    df = load.load_mantova(args.start_date, args.end_date)
    charts(df)

    #for park in birminghan_parks:
    #    df = load.load_birminghan(park)
    #    charts(df)


