import calendar

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def get_accuracy(df, error=2):
    split_idx = int(len(df) * 0.8)
    train_df, test_df = df[:split_idx], df[split_idx:]

    pivot_train = pd.pivot_table(train_df, columns=[train_df.index.dayofweek, train_df.index.hour],
                                 values='free_slots',
                                 aggfunc=np.median).transpose()

    test_df = test_df.resample(rule='1H').mean()
    test_df['lower_bound'] = test_df['free_slots'] - error
    test_df['upper_bound'] = test_df['free_slots'] + error
    test_df['prediction'] = [pivot_train.loc[(x.dayofweek, x.hour)].values[0] for x in test_df.index]

    return len(test_df[(test_df['prediction'] < test_df['upper_bound']) &
                       (test_df['prediction'] > test_df['lower_bound'])]) / len(test_df)


def get_plot(df, error=2):
    split_idx = int(len(df) * 0.8)
    train_df, test_df = df[:split_idx], df[split_idx:]

    # median
    pivot_train = pd.pivot_table(train_df, columns=[train_df.index.weekday, train_df.index.hour], values='free_slots',
                                 aggfunc=np.median).transpose()
    ax = pivot_train.plot()

    # bands
    ax.fill_between(range(0, 24 * 7),
                    pivot_train['free_slots'] + error,
                    pivot_train['free_slots'] - error,
                    color='blue', alpha=0.1)
    ax.fill_between(range(0, 24 * 7),
                    pivot_train['free_slots'] + error * 0.66,
                    pivot_train['free_slots'] - error * 0.66,
                    color='blue', alpha=0.15)

    # scatter
    pivot_test = pd.pivot_table(test_df, index=[test_df.index.weekofyear],
                                columns=[test_df.index.weekday, test_df.index.hour],
                                values='free_slots')

    ax.scatter(range(len(pivot_test.loc[7])), pivot_test.loc[7], s=10)
    ax.scatter(range(len(pivot_test.loc[8])), pivot_test.loc[8], s=10)

    ax.set_title('Predictive model (median) results')
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Free parking slots')

    days = calendar.day_abbr
    hours = list(map(lambda x: '{:02d}'.format(x), 7 * list(range(0, 24, 6))))
    ax.set_xticks(range(0, 24 * 7, 24))
    ax.set_xticks(range(0, 24 * 7, 6), minor=True)
    ax.set_xticklabels(days)
    ax.set_xticklabels(hours, minor=True)
    ax.xaxis.set_tick_params(which='major', pad=15, labelsize=10)
    ax.xaxis.set_tick_params(which='minor', labelsize=8)
    ax.grid(which='major')
    ax.set_xlim(left=-1, right=24 * 7)
    ax.set_yticks(range(0, 22, 2))
    ax.set_ylim(bottom=0, top=20)
    ax.legend().remove()

    plt.tight_layout()
    plt.show()
