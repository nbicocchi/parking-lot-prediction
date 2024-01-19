import calendar
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.offsetbox import AnchoredText

import neural_network.config as config
from data_management.database_utilities import get_data
from utilities.init_data_path import get_data_path

# plt.rcParams["figure.figsize"] = (20, 10)
plt.rcParams['figure.figsize'] = (7, 5)


def compute_median(df):
    free_parking = pd.DataFrame(df, copy=True)
    if 'park_id' in free_parking.columns:
        free_parking.drop(columns=['park_id'], inplace=True)
    free_parking.columns = ['value']
    free_parking.value = ((1 - free_parking.value) * 68).astype('int32')
    pivot = pd.pivot_table(free_parking, index=[free_parking.index.year, free_parking.index.weekofyear],
                           columns=[free_parking.index.weekday, free_parking.index.hour], values='value')
    return pivot


def get_accuracy(train, test, error=3):
    predictions = train.median(axis=0).astype('int32')
    weekly_accuracy = (abs(test - predictions) <= error).mask(test.isnull(), np.nan).mean().unstack()
    daily_accuracy = weekly_accuracy.mean(axis=1)
    return daily_accuracy.mean()


def predict(df, date, hours=None, error=3):
    median = df[date.weekday()].median(axis=0).astype('int32')
    if hours:
        pred_timestamps = pd.date_range(start=date.isoformat(), periods=8, freq='H')
        median = median[pred_timestamps.hour]
        prediction_with_error = np.tile(median, (2, 1)).T + [-error, +error]
        return pd.DataFrame(data=prediction_with_error, index=pred_timestamps, columns=['min', 'max'])
    median = median[date.hour]
    prediction = (median - error, median + error)
    return pd.DataFrame(index=[date], columns=['min', 'max'], data=[prediction])


def median_predictions_weekday_plot(df, error=3):
    # first week of year workaround
    # TODO create a year independent fix
    # df.loc[2020].loc[1] = df.loc[2019].loc[1].fillna(0) + df.loc[2020].loc[1].fillna(0)
    df.dropna(inplace=True)
    split_idx = int(len(df) * (1 - 0.2))
    train_df, test_df = df[:split_idx], df[split_idx:]
    days = calendar.day_abbr
    hours = list(map(lambda x: '{:02d}'.format(x), 7 * list(range(0, 24, 6))))
    predictions = train_df.median(axis=0).astype('int32').values
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(predictions, label='median')
    colors = ['green', 'orangered']
    for i, (year, week) in enumerate(test_df.index):
        ax.scatter(range(0, 24 * 7), test_df.loc[year].loc[week].astype(int), s=10, label='{}-{}'.format(week, year),
                   color=colors[i])
    ax.set_xticks(range(0, 24 * 7, 24))
    ax.set_xticklabels(days)
    ax.xaxis.set_tick_params(which='major', pad=15, labelsize=10)
    ax.set_xticks(range(0, 24 * 7, 6), minor=True)
    ax.set_xticklabels(hours, minor=True)
    ax.xaxis.set_tick_params(which='minor', labelsize=8)
    ax.grid(which='major')
    ax.set_xlim(left=-1, right=24 * 7)
    ax.legend().remove()
    ax.set_ylim((0, 25))
    # error_3 = np.floor(0.03 * config.n_sensors)
    # error_4 = np.ceil(0.04 * config.n_sensors)
    # print('accuracy2:', get_accuracy(train_df, test_df, error_3))
    # print('accuracy3:', get_accuracy(train_df, test_df, error_4))
    accuracy_text = 'Parking accuracy={:.2f} (with error=±{})'.format(get_accuracy(train_df, test_df, error + 1),
                                                                      error + 1)
    accuracy_box = AnchoredText(accuracy_text, loc='lower left')
    ax.add_artist(accuracy_box)
    ax.set_title('Median predictions by weekday')
    ax.set_ylabel('Free parking spot')
    ax.set_xlabel('Time')
    plt.fill_between(range(0, 24 * 7), predictions - error, predictions + error, alpha=0.25, color='grey')
    # plt.fill_between(range(0, 24*7), predictions-error_3, predictions+error_3, alpha=0.25, color='grey')
    # plt.fill_between(range(0, 24*7), predictions-error_4, predictions+error_4, alpha=0.15, color='grey')
    plt.tight_layout()
    plt.show()
    plt.savefig(str(path.joinpath('median_predictions.png')))


def user_input_prediction():
    occupancy = get_data(tables_names=['occupancy'])[0]
    median = compute_median(occupancy)

    try:
        str_date = input('Date (YYYY-mm-dd): ')
        str_time = input('Time (HH:MM): ')
        input_date = datetime.strptime(str_date + ' ' + str_time, '%Y-%m-%d %H:%M')
        print(predict(median, input_date))
    except ValueError:
        print('Wrong datetime format!')
    except KeyboardInterrupt:
        pass


path = get_data_path()
if __name__ == '__main__':
    occupancy_df = get_data(tables_names=['occupancy'])[0]
    median_df = compute_median(occupancy_df)
    median_predictions_weekday_plot(median_df, error=2)
    user_input_prediction()
