import calendar
from collections import OrderedDict
import plotly.graph_objs as go
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from matplotlib import ticker
from pandas.plotting import register_matplotlib_converters

from legacy.load import load_devices

register_matplotlib_converters()


# plt.rcParams['figure.figsize'] = (20, 10)


def messages_frequency(df):
    # df = df[df.msg_type == 'update']
    print(df.groupby(df.index.dayofyear).size().mean())
    fr = df.groupby(df.index.hour).size()
    fr /= fr.sum()
    ax = fr.plot(kind='line', color='black')
    ax.set_xlabel('Time')
    ax.set_ylim(bottom=0, top=.1)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    plt.xticks(rotation=0)
    ax.grid(which='minor', color='#CCCCCC', linestyle='-')
    ax.grid(which='major', color='#CCCCCC', linestyle=':')
    # ax.set_title('Messages frequency')
    ax.set_ylabel('Frequency')
    plt.tight_layout()
    plt.show()


def occupancy_plot(df, days=None):
    if days and len(df) > 0:
        df = df[df.index >= df.index[-1] + timedelta(days=-days)]
    df = df.resample(rule='4H').mean()
    df.reset_index(inplace=True)
    df.drop(columns=['time'], inplace=True)
    ax = df.plot(color='black')
    ax.set_xticklabels(range(len(df) // 6), minor=False)
    ax.xaxis.set_major_locator(ticker.LinearLocator(len(df) // 6))
    ax.set_ylim(bottom=0, top=1)
    ax.set_ylabel('Occupancy')
    ax.set_xlabel('Days')
    ax.get_legend().remove()
    plt.xticks(size=9)
    ax.grid(which='minor', color='#CCCCCC', linestyle='-')
    ax.grid(which='major', color='#CCCCCC', linestyle=':')
    plt.tight_layout()
    plt.show()


def occupancy_heatmap(df, days=None):
    if days and len(df) > 0:
        df = df[df.index >= df.index[-1] + timedelta(days=-days)]
    pivot = pd.pivot_table(df, index=df.index.date, columns=df.index.hour, values='percentage')
    fig, ax = plt.subplots()
    ax.set_title('Percentage occupancy heatmap')
    ax.set_yticks(range(len(pivot.index)))
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_yticklabels([datetime.strftime(d, '%a %Y-%m-%d') for d in pivot.index])
    ax.set_xticklabels(pivot.columns)
    ax.set_xlabel('hour')
    plt.imshow(pivot, cmap='RdYlGn_r', vmin=df.quantile(q=0.02), vmax=df.quantile(q=0.98), aspect='auto')
    plt.colorbar()
    plt.tight_layout()
    plt.show()


def free_parking_hour_plot(df):
    pivot = pd.pivot_table(df, index=df.index.hour, columns=df.index.weekday, values='value')
    pivot.columns = calendar.day_name
    ax = pivot.plot()
    ax.set_xticks(range(len(pivot.index)))
    ax.set_xticklabels(pivot.index)
    # ax.set_title('Average free parking slot per hour')
    ax.set_xlabel('Hour')
    ax.set_ylabel('Free parking slot')
    ax.grid(which='major', color='#CCCCCC', linestyle='-')
    ax.legend()
    plt.tight_layout()
    plt.show()


def free_parking_week_boxplot(df, error=0):
    pivot = pd.pivot_table(df, index=[df.index.year, df.index.weekofyear], columns=[df.index.weekday, df.index.hour],
                           values='value')
    color = {'boxes': 'Black', 'whiskers': 'Black', 'medians': 'Green', 'caps': 'Black'}
    ax = pivot.plot(kind='box', color=color, positions=range(0, 24 * 7))
    # ax.set_title('Free parking slot per weekday and hour')
    ax.set(ylabel='Free parking slot', xlabel='Time')
    days = list(OrderedDict.fromkeys(map(lambda x: calendar.day_abbr[x[0]], pivot.columns)))
    hours = list(map(lambda x: '{:02d}'.format(x), 7 * list(range(0, 24, 6))))
    ax.set_xticks(range(0, 24 * 7, 24))
    ax.set_xticklabels(days)
    ax.xaxis.set_tick_params(which='major', pad=15, labelsize=8)
    ax.set_xticks(range(0, 24 * 7, 6), minor=True)
    ax.set_xticklabels(hours, minor=True)
    ax.xaxis.set_tick_params(which='minor', labelsize=8)
    # median = pivot.median(axis=0).astype('int32')
    # plt.fill_between(range(0, 24*7), median-error, median+error, alpha=0.3)
    ax.grid(which='major', color='#CCCCCC', linestyle='-')
    ax.grid(which='minor', color='#CCCCCC', linestyle='--')
    plt.tight_layout()
    plt.show()


def sensors_plot(df):
    fig, axs = plt.subplots(len(df.columns) // 3 + 1, 3, sharex='all')
    devices = load_devices()
    last_two_weeks = df.index >= datetime.now() + timedelta(days=-15)
    for i, sensor in enumerate(df):
        states = df[last_two_weeks][sensor]
        ax = axs[i // 3, i % 3]
        ax.plot(states, drawstyle='steps-post')
        ax.set_ylabel(devices[sensor]['label'], rotation='horizontal', ha='right')
        ax.set_yticklabels([])
        ax.set_yticks([0, 1])
        # ax.set_xticklabels([datetime.strftime(d, '%a %m-%d') for d in states.index])
        x_format = mdates.DateFormatter('%a %m-%d')
        ax.xaxis.set_major_formatter(x_format)
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 6)))
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
    plt.autoscale()
    plt.tight_layout()
    plt.show()


# def set_color(state):
#     if state == 0:
#         return 'green'
#     if state == 1:
#         return 'red'
#
#
# def sensors_map(df):
#     data = pd.DataFrame(df[:].iloc[-1])
#     data.columns = ['state']
#     data = data.join(pd.DataFrame(load_devices()).transpose())
#     data = pd.DataFrame(load_devices()).transpose()
#     data.dropna(subset=['lat', 'lon'], inplace=True)
#
#     fig = go.Figure(
#         go.Scattermapbox(
#             lat=data.lat,
#             lon=data.lon,
#             marker=dict(size=11, color='gray'), # list(map(set_color, data.state))),
#             text=['{} ({})'.format(label, dev_eui) for label, dev_eui in zip(data.label.values, data.index.values)]
#         ))
#     fig.update_layout(
#         mapbox_style="open-street-map",
#         autosize=True,
#         hovermode='closest',
#         mapbox=dict(center=dict(lat=data.lat.mean(), lon=data.lon.mean()), zoom=17)
#     )
#     fig.show()


def activity_plot(df):
    df = pd.pivot_table(df, index=df.index, columns=df.dev_eui, values='state')
    df.sort_index(axis=1, inplace=True)
    df = df.resample('24H').count()
    df.replace(0, np.nan, inplace=True)
    sensors = df.count(axis=1, numeric_only=True)
    msgs = df.sum(axis=1, numeric_only=True)
    out = pd.concat([sensors, msgs], axis=1)
    # remove days with incomplete data, just before/after missing data periods
    out.mask((out[0].shift(1) == 0) | (pd.isna(out[0].shift(-1))) | (out[0].shift(-1) == 0), other=np.nan, inplace=True)
    out.replace(0, np.nan, inplace=True)
    out.columns = ['sensors', 'messages']
    ax = out.plot(secondary_y=['messages'])
    ax.set_ylabel('Sensors')
    ax.right_ax.set_ylabel('Messages')
    ax.set_xlabel('Days')
    # ax.set_title('Activity')
    ax.grid(which='minor', color='#CCCCCC', linestyle='-')
    ax.grid(which='major', color='#CCCCCC', linestyle=':')
    plt.tight_layout()
    plt.show()
