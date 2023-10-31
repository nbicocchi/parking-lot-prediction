import os
from datetime import datetime
import calendar
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy import fft
import sys

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
    :return: test set
    """
    last_record_day = df.index[-1] - pd.Timedelta(days=7)
    return len(df[df.index >= datetime(last_record_day.year, last_record_day.month, last_record_day.day)])


def calculate_fourier(df, saving_path):
    test_len = get_len_last_week(df)
    split_idx = len(df) - test_len
    n_predict = test_len
    n_sensors = 68
    df['extrapolation'] = fourier_extrapolation(df[:split_idx]['occupancy'].values, n_predict)
    train_df, test_df = df[:split_idx], df[split_idx:]

    # make sure that the test set is after the sensors has trained
    # test = test_df[test_df.index >= datetime(2020, 2, 17, 0, 0, 0)]
    # test = test[test.index < datetime(2020, 2, 24, 0, 0, 0)]
    # print(df)
    print('Fourier MSE =', np.mean((test_df['occupancy'] - test_df['extrapolation']) ** 2))
    print('Fourier parking_accuracy +-2 =', parking_accuracy(test_df['occupancy'], test_df['extrapolation'], 2))
    print('Fourier parking_accuracy +-3 =', parking_accuracy(test_df['occupancy'], test_df['extrapolation'], 3))

    test_sensors = test_df.copy()
    test_sensors['occupancy'] = (n_sensors * (1 - test_sensors['occupancy'])).astype(int)
    test_sensors['extrapolation'] = (n_sensors * (1 - test_sensors['extrapolation'])).astype(int)
    show_plot(test_sensors, saving_path)


def show_plot(test_sensors, saving_path):
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
    ax.fill_between(range(0, len(test_sensors['occupancy'].values)), test_sensors['extrapolation'] - 2,
                    test_sensors['extrapolation'] + 2,
                    color='tab:gray', alpha=0.25)
    ax.fill_between(range(0, len(test_sensors['occupancy'].values)), test_sensors['extrapolation'] - 3,
                    test_sensors['extrapolation'] + 3,
                    color='tab:gray', alpha=0.15)
    ax.set_ylabel('Free parking spot')
    ax.set_xlabel('Time')
    plt.tight_layout()
    plt.savefig(os.path.join(saving_path, "fourier_plot.png"))
    #plt.show()
