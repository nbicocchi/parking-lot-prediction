from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()

path = Path.home().joinpath(".bosch_pls")
# sensors_data, percentage_occupancy = resample(to_file=False, start_date=datetime(2019, 11, 16, 0, 0))
percentage_occupancy = pd.read_csv(path.joinpath('percentage.csv'), index_col='time', parse_dates=True)
percentage_occupancy = percentage_occupancy[percentage_occupancy.index >= datetime(2019, 12, 16, 0, 0, 0)]
df = pd.read_csv(path.joinpath('rain.csv'),
                 names=['sensor', 'time', 'rain'],
                 skiprows=1,
                 usecols=[1, 2], index_col=[0], na_values=[-999])
df.index = pd.to_datetime(df.index)
df.plot()
plt.show()
date_mask = (df.index >= percentage_occupancy.index[0]) & (df.index < percentage_occupancy.index[-1])
df = df[date_mask]
threshold = 0.1
df[df.rain >= threshold] = 1
df[df.rain < threshold] = 0
merged = df.merge(percentage_occupancy, left_index=True, right_index=True)
fig, ax = plt.subplots()
ax.plot(percentage_occupancy)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %m-%d'))
ax.xaxis.set_major_locator(mdates.DayLocator())
ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 6)))
ax.grid(which='minor', color='#CCCCCC', linestyle=':')
ax.grid(which='major', color='#CCCCCC', linestyle='-')
for x in df[df.rain == 1].index:
    ax.axvspan(x, x + timedelta(hours=1), facecolor='g', alpha=0.5)
plt.xticks(rotation=90, fontsize=8)
plt.show()
print(merged.corr())
