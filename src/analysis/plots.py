import calendar
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
import matplotlib.dates as mdates
from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()


# plt.rcParams['figure.figsize'] = (20, 10)


def occupancy_plot(df):
    df = df.resample(rule='1H').mean()
    df.reset_index(inplace=True)
    df.drop(columns=['index'], inplace=True)
    ax = df.plot()
    ax.set_xticklabels(range(0, len(df) // 24, 4), minor=False)
    ax.xaxis.set_major_locator(ticker.LinearLocator(len(df) // 96))
    ax.set_title('Percentage occupancy')
    ax.set_ylabel('Occupancy')
    ax.set_xlabel('Days')
    ax.grid(which='minor', color='#CCCCCC', linestyle=':')
    ax.grid(which='major', color='#CCCCCC', linestyle=':')
    ax.set_ylim(bottom=0, top=1)
    ax.get_legend().remove()
    plt.tight_layout()
    plt.show()


def occupancy_heatmap(df):
    pivot = pd.pivot_table(df, index=df.index.date, columns=df.index.hour, values='occupancy')
    fig, ax = plt.subplots()
    ax.set_title('Percentage occupancy heatmap')
    ax.yaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    ax.set_yticklabels([datetime.strftime(d, '%a %Y-%m-%d') for d in pivot.index])
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_xlabel('hour')
    plt.imshow(pivot, cmap='RdYlGn_r', aspect='auto')
    plt.colorbar()
    plt.tight_layout()
    plt.show()


def free_parking_hour_plot(df):
    pivot = pd.pivot_table(df, index=df.index.hour, columns=df.index.weekday, values='occupancy')
    pivot.columns = calendar.day_name
    ax = pivot.plot()
    ax.set_xticks(range(24))
    ax.set_xticklabels(range(24))
    ax.set_title('Average free parking slot per hour')
    ax.set_xlabel('Hour')
    ax.set_ylabel('Free parking slot')
    ax.set_xlim(left=0, right=23)
    ax.grid(which='major', color='#CCCCCC', linestyle='-')
    ax.legend()
    #plt.tight_layout()
    plt.show()


def free_parking_week_boxplot(df, error=0):
    pivot = pd.pivot_table(df, index=[df.index.weekofyear], columns=[df.index.weekday, df.index.hour],
                           values='occupancy')

    hours_a_day=len(df.index.hour.unique())
    ax = pivot.plot(kind='box', positions=range(0, hours_a_day * 7), showfliers=False)
    ax.set(title='Free parking slot per weekday and hour',
        ylabel='Free parking slot',
        xlabel='Time')


    ax.set_xticks(range(0, 24 * 7, 24))
    ax.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    ax.xaxis.set_tick_params(which='major', pad=15, labelsize=8)

    ax.set_xticks(range(0, 24 * 7, 6), minor=True)
    ax.set_xticklabels(['{:02d}'.format(x) for x in [0, 6, 12, 18] * 7], minor=True)
    ax.xaxis.set_tick_params(which='minor', labelsize=8)

    #ax.set_ylim(bottom=0.5, top=1.0)

    ax.grid(which='major', color='#CCCCCC', linestyle='-')
    ax.grid(which='minor', color='#CCCCCC', linestyle='--')

    plt.tight_layout()
    plt.show()
