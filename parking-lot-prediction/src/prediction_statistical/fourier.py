from cgi import test
from datetime import datetime
import numpy as np
import pandas as pd
from numpy import fft
from keras import backend as k


from utilities.metrics import parking_accuracy
from plots.statistical_plots import fourier_plot

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


def calculate_fourier(df: pd.DataFrame, saving_path: str, capacity: int, percentual_error: list, start_date=None, end_date=None):
    """
    Given start_date and end_date fourier will be calculated on the given interval, otherwise on the entire dataset.
    A plot figure will be generated at the saving_path given.
    MSE and accuracy will be printed according to the percentual errors given.
    Return parking accuracy values
    """
    if(start_date is not None and end_date is not None):
        df = df[(df.index >= start_date) & (df.index <= end_date)]
    split_idx = int(len(df) * (1 - 0.2))
    n_predict = len(df) - split_idx

    df['extrapolation'] = fourier_extrapolation(df[:split_idx]['occupancy'].values, n_predict)
    train_df, test_df = df[:split_idx], df[split_idx:]
    # make sure that the test set is exactly a week
    start_week_day = df.index[-1] - pd.Timedelta(days=7)
    #test = test_df[test_df.index >= datetime(start_week_day.year, start_week_day.month, start_week_day.day, 0, 0, 0)]
    #test = test[test.index < datetime(df.index[-1].year, df.index[-1].month, df.index[-1].day, 0, 0, 0)]
    test = test_df
    print('Fourier MSE = {:.4f}'.format(np.mean((test['occupancy'] - test['extrapolation']) ** 2)))
    #error is the number of parking_lot more or less right
    error_list=[]
    accuracy_valeus = []
    
    for per_error in percentual_error:
        error = round(capacity * (per_error/100))
        error_list.append(error)
        accuracy_valeus.append((f"FOURIER (±{per_error}%)",k.get_value(parking_accuracy(test['occupancy'], test['extrapolation'], capacity, error))))
        print('Fourier parking_accuracy [error=±{}(±{}%)] = {:.4f}'.format(error, per_error, accuracy_valeus[-1][1]))

    test_sensors = test.copy()
    test_sensors['occupancy'] = (capacity * (1 - test_sensors['occupancy'])).astype(int)
    test_sensors['extrapolation'] = (capacity * (1 - test_sensors['extrapolation'])).astype(int)
    fourier_plot(test_sensors, saving_path, error_list)
    return accuracy_valeus
