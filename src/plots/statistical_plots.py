import os
import matplotlib.pyplot as plt
import calendar
import pandas as pd

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


def median_plot(df, saving_path, error=2):
    split_idx = int(len(df) * 0.8)
    train_df, test_df = df[:split_idx], df[split_idx:]

    # median
    pivot_train = pd.pivot_table(train_df, columns=[train_df.index.weekday, train_df.index.hour], values='free_slots',
                                 aggfunc='median').transpose()
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
    pivot_test = pd.pivot_table(test_df, index=[test_df.index.isocalendar().week],
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
    plt.savefig(os.path.join(saving_path, "median_plot.png"))
    # plt.show()