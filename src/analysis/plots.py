import calendar
import os
from datetime import timedelta
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
from pandas.plotting import register_matplotlib_converters
import warnings


warnings.filterwarnings('ignore', category=UserWarning)
register_matplotlib_converters()


# plt.rcParams['figure.figsize'] = (20, 10)

def occupancy_plot(df, path_saving_chart):
    """
    occupancy plot over a month from the start
    """
    days = 30
    df = df[(df.index <= (df.index[0] + timedelta(days=days)))]
    df = df.resample(rule='1H').mean()
    df.reset_index(inplace=True)
    df.drop(columns=['index'], inplace=True)
    
    ax = df.plot(y='occupancy', use_index=True)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(24))
    ax.set_xticklabels(range(-1,days+1))
    ax.set_title('Percentage occupancy')
    ax.set_ylabel('Occupancy')
    ax.set_xlabel('Days')
    ax.grid(which='minor', color='#CCCCCC', linestyle=':')
    ax.grid(which='major', color='#CCCCCC', linestyle=':')
    ax.set_ylim(bottom=0, top=1)
    ax.set_xlim(left=0, right=days*24)
    ax.get_legend().remove()
    plt.tight_layout()
    plt.savefig(os.path.join(path_saving_chart, 'occupancy_plot.png'))


def free_parking_hour_plot(df, path_saving_chart):
    pivot = pd.pivot_table(df, index=df.index.hour, columns=df.index.weekday, values='free_slots')
    pivot.columns = list(calendar.day_name)
    ax = pivot.plot()
    ax.set_xticks(range(24))
    ax.set_xticklabels(range(24))
    ax.set_title('Average free parking slot per hour')
    ax.set_xlabel('Hour')
    ax.set_ylabel('Free parking slot')
    ax.set_xlim(left=0, right=23)
    ax.grid(which='major', color='#CCCCCC', linestyle='-')
    ax.legend(loc='upper right')
    plt.savefig(os.path.join(path_saving_chart, 'free_parking_hour_plot.png'))


def free_parking_week_boxplot(df, path_saving_chart, error=0):
    pivot = pd.pivot_table(df, index=[df.index.isocalendar().week],
                           columns=[df.index.weekday, df.index.hour],
                           values='free_slots')

    hours_a_day = len(df.index.hour.unique())
    ax = pivot.plot(kind='box', positions=range(0, hours_a_day * 7),patch_artist=True) #boxprops=dict(facecolor='black')
    ax.set(title='Free parking slot per weekday and hour',
           ylabel='Free parking slot',
           xlabel='Time')

    ax.set_xticks(range(0, 24 * 7, 24))
    ax.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    ax.xaxis.set_tick_params(which='major', pad=15, labelsize=8)

    ax.set_xticks(range(0, 24 * 7, 6), minor=True)
    ax.set_xticklabels(['{:02d}'.format(x) for x in [0, 6, 12, 18] * 7], minor=True)
    ax.xaxis.set_tick_params(which='minor', labelsize=8)

    # ax.set_ylim(bottom=0.5, top=1.0)
    
    ax.grid(which='major', color='#CCCCCC', linestyle='-')
    ax.grid(which='minor', color='#CCCCCC', linestyle='--')

    plt.tight_layout()
    plt.savefig(os.path.join(path_saving_chart, 'free_parking_week_boxplot.png'))


def charts(df, path_saving_chart):
    occupancy_plot(df, path_saving_chart)
    free_parking_hour_plot(df, path_saving_chart)
    free_parking_week_boxplot(df, path_saving_chart)