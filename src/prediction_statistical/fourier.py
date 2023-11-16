import os
from datetime import datetime
import calendar
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy import fft
import sys
import tensorflow.keras.backend as k

sys.path.append("..")
from prediction_neural_network.utilities import parking_accuracy


def fourier_extrapolation(x, n_predict):
    n = x.size
    n_harm = 75  # number of harmonics in model
    t = np.arange(0, n)
    p = np.polyfit(t, x, 1)  # find linear trend in x
    x_notrend = x - p[0] * t  # detrended x
    x_freqdom = fft.fft(x_notrend)  # detrended x in frequency domain
    f = fft.fftfreq(n)  # frequencies
    indexes = list(range(n))
    # sort indexes by frequency, lower -> higher
    indexes.sort(key=lambda i: np.absolute(f[i]))

    t = np.arange(0, n + n_predict)
    restored_sig = np.zeros(t.size)
    for i in indexes[:1 + n_harm * 2]:
        ampli = np.absolute(x_freqdom[i]) / n  # amplitude
        phase = np.angle(x_freqdom[i])  # phase
        restored_sig += ampli * np.cos(2 * np.pi * f[i] * t + phase)
    return restored_sig + p[0] * t


def get_len_last_week(df):
    """ 
    :return: Index from the start of the last week
    """
    last_record_day = df.index[-1] - pd.Timedelta(days=7)
    return len(df[df.index >= datetime(last_record_day.year, last_record_day.month, last_record_day.day)])


def calculate_fourier(df, saving_path, start_date=None, end_date=None):
    """
    Given start_date and end_date fourier will be calculated on the given interval, otherwise on the entire dataset.
    A plot figure will be generated at the saving_path given.
    MSE and accuracy with +-3 and +-4% of error will be printed on terminal.
    """
    if(start_date is not None and end_date is not None):
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        split_idx = int(len(df) * (1 - 0.2))
        n_predict = len(df) - split_idx
    else:
        n_predict = get_len_last_week(df)
        split_idx = len(df) - n_predict
    
    n_sensors = 68
    df['extrapolation'] = fourier_extrapolation(df[:split_idx]['occupancy'].values, n_predict)
    train_df, test_df = df[:split_idx], df[split_idx:]

    start_week_day = df.index[-1] - pd.Timedelta(days=7)
    # make sure that the test set is exactly one week
    test = test_df[test_df.index >= datetime(start_week_day.year, start_week_day.month, start_week_day.day, 0, 0, 0)]
    test = test[test.index < datetime(end_date.year, end_date.month, end_date.day, 0, 0, 0)]

    print('Fourier MSE =', np.mean((test_df['occupancy'] - test_df['extrapolation']) ** 2))
    print('Fourier parking_accuracy +-3% =',
          k.get_value(parking_accuracy(test_df['occupancy'], test_df['extrapolation'], 3)))
    print('Fourier parking_accuracy +-4% =',
          k.get_value(parking_accuracy(test_df['occupancy'], test_df['extrapolation'], 4)))

    test_sensors = test_df.copy()
    test_sensors['occupancy'] = (n_sensors * (1 - test_sensors['occupancy'])).astype(int)
    test_sensors['extrapolation'] = (n_sensors * (1 - test_sensors['extrapolation'])).astype(int)
    fourier_plot(test_sensors, saving_path)


def fourier_plot(test_sensors, saving_path):
    days = calendar.day_abbr
    hours = list(map(lambda x: '{:02d}'.format(x), 7 * list(range(0, 24, 6))))
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(test_sensors['extrapolation'].values, 'tab:blue')
    ax.scatter(range(0, len(test_sensors['occupancy'].values)), test_sensors['occupancy'].values, s=10,
               color='darkgreen')
    ax.set_xticks(range(0, 24 * 7, 6), minor=True)
    ax.set_xticklabels(hours, minor=True)
    ax.xaxis.set_tick_params(which='minor', labelsize=8)
    ax.set_xticks(range(0, 24 * 7, 24))
    ax.set_xticklabels(days)
    ax.xaxis.set_tick_params(which='major', pad=15, labelsize=10)
    ax.grid(which='major')
    ax.set_xlim(left=-1, right=24 * 7)
    ax.set_ylim((0, 25))
    # ax.legend().remove()
    ax.fill_between(range(0, len(test_sensors['occupancy'].values)), test_sensors['extrapolation'] - 3,
                    test_sensors['extrapolation'] + 3,
                    color='tab:gray', alpha=0.25)
    ax.fill_between(range(0, len(test_sensors['occupancy'].values)), test_sensors['extrapolation'] - 4,
                    test_sensors['extrapolation'] + 4,
                    color='tab:gray', alpha=0.15)
    ax.set_ylabel('Free parking spot')
    ax.set_xlabel('Time')
    plt.tight_layout()
    plt.savefig(os.path.join(saving_path, "fourier_plot.png"))
