import pandas as pd
import sys

sys.path.append("..")
from plots.statistical_plots import median_plot

def get_accuracy(df, error):
    split_idx = int(len(df) * 0.8)
    train_df, test_df = df[:split_idx], df[split_idx:]

    pivot_train = pd.pivot_table(train_df, columns=[train_df.index.dayofweek, train_df.index.hour],
                                 values='free_slots',
                                 aggfunc='median').transpose()

    test_df = test_df.resample(rule='1H').mean()
    test_df['lower_bound'] = test_df['free_slots'] - error
    test_df['upper_bound'] = test_df['free_slots'] + error
    test_df['prediction'] = [pivot_train.loc[(x.dayofweek, x.hour)].values[0] for x in test_df.index]

    return len(test_df[(test_df['prediction'] < test_df['upper_bound']) &
                       (test_df['prediction'] > test_df['lower_bound'])]) / len(test_df)


def get_plot_and_print_accuracy(df: pd.DataFrame, path_plot: str, capacity: int, percentual_error: list):
    #percentual_error can be max of 2 values
    for per_error in percentual_error:
        error = round(capacity * (per_error/100))
        print('median accuracy [error=±{}(±{}%)] = {:.4f}'.format(error, per_error, get_accuracy(df, error)))
    median_plot(df, path_plot, capacity, percentual_error)

