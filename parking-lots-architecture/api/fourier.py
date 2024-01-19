from datetime import datetime
import calendar

import matplotlib.pyplot as plt
import numpy as np
from numpy import fft

from data_management.database_utilities import get_data
from neural_network.utilities import parking_accuracy
from utilities.init_data_path import get_data_path


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


path = get_data_path()
df = get_data(tables_names=['occupancy'], start_date=datetime(2019, 12, 16), end_date=datetime(2020, 2, 24))[0][::12]
test_size = 0.2
df.drop(columns=['park_id'], inplace=True)

# import pandas as pd
# df = pd.read_csv('dataset.csv', parse_dates=['LastUpdated'])
# df.columns = ['park_id', 'capacity', 'occupancy', 'time']
# df.set_index('time', inplace=True)
# df['percentage'] = df['occupancy'] / df['capacity']
# df = df[df['park_id'] == 'Others-CCCPS202'].resample('1H').mean()
# # df.fillna(inplace=True, method='ffill')
# df.interpolate(method='linear', inplace=True)
#
# plt.rcParams['figure.figsize'] = (7, 5)
fourier_df = df
split_idx = int(len(fourier_df) * (1 - 0.2))
n_predict = len(fourier_df) - split_idx
n_sensors = 68
extrapolation = fourier_extrapolation(fourier_df[:split_idx]['percentage'].values, n_predict)
fourier_df['extrapolation'] = extrapolation
train_df, test_df = fourier_df[:split_idx], fourier_df[split_idx:]

test = test_df[test_df.index >= datetime(2020, 2, 17, 0, 0, 0)]
test = test[test.index < datetime(2020, 2, 24, 0, 0, 0)]

print('MSE =', np.mean((test['percentage'] - test['extrapolation']) ** 2))
print('parking_accuracy +-2 =', parking_accuracy(test['percentage'], test['extrapolation'], 2))
print('parking_accuracy +-3 =', parking_accuracy(test['percentage'], test['extrapolation'], 3))

test_sensors = test.copy()
test_sensors['percentage'] = (n_sensors * (1 - test_sensors['percentage'])).astype(int)
test_sensors['extrapolation'] = (n_sensors * (1 - test_sensors['extrapolation'])).astype(int)

days = calendar.day_abbr
hours = list(map(lambda x: '{:02d}'.format(x), 7 * list(range(0, 24, 6))))
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
ax.plot(test_sensors['extrapolation'].values, 'tab:blue')
ax.scatter(range(0, 24 * 7), test_sensors['percentage'].values, s=10, color='darkgreen')
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
ax.fill_between(range(0, 24 * 7), test_sensors['extrapolation'] - 2, test_sensors['extrapolation'] + 2,
                color='tab:gray', alpha=0.25)
ax.fill_between(range(0, 24 * 7), test_sensors['extrapolation'] - 3, test_sensors['extrapolation'] + 3,
                color='tab:gray', alpha=0.15)
ax.set_ylabel('Free parking spot')
ax.set_xlabel('Time')
plt.tight_layout()
plt.savefig('fourier.svg', bbox_inches='tight', format='svg')
plt.show()
