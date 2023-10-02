import sys
import argparse
from datetime import datetime

import pandas as pd

import prediction_statistical.median as median

parser = argparse.ArgumentParser()
parser.add_argument('--start_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
                    default=datetime(2019, 11, 15, 0, 0, 0, 0))
parser.add_argument('--end_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
                    default=datetime(2020, 2, 26, 0, 0, 0, 0))
parser.add_argument('--error', default=3)
args = parser.parse_args()

if __name__ == '__main__':
    df = load_birminghan()
    sys.exit()

    median.get_plot(df, error=args.error)
    accuracy = median.get_accuracy(df, error=args.error)
    print('accuracy (error={}) = {}'.format(args.error, accuracy))



