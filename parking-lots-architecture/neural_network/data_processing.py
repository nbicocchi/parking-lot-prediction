import numpy as np
import tensorflow as tf

import neural_network.config as config


# split a univariate sequence into samples
def split_sequence(sequence):
    X, y = list(), list()
    for i in range(len(sequence)):
        # find the end of this pattern
        end_ix = i + config.n_timesteps_in
        out_end_ix = end_ix + config.n_timesteps_out
        # check if we are beyond the sequence
        if out_end_ix > len(sequence):
            break
        # gather input and output parts of the pattern
        seq_x, seq_y = sequence[i:end_ix], sequence[end_ix:out_end_ix]
        X.append(seq_x)
        y.append(seq_y)
    return np.asarray(X), np.asarray(y)


def split_data(df):
    split_idx = int(len(df) * (1 - config.test_size))
    train_df, test_df = df[:split_idx], df[split_idx:]
    train, test = train_df.values, test_df.values
    X_train, y_train = split_sequence(train)
    X_test, y_test = split_sequence(test)

    return X_train, X_test, y_train, y_test


def add_weekday_hour(data):
    # DO NOT CHANGE with a def
    vfunc = lambda x: np.apply_along_axis(lambda l: list(map(lambda t: (t.dayofweek, t.hour), l)), axis=1, arr=x)
    return np.dstack((vfunc(data[:, :, 0]), np.expand_dims(data[:, :, 1], axis=2)))


def get_data(X_train, y_train, X_test, y_test):
    # train and test dimensions: [n_chunks, n_timesteps_in, 1+n_features]
    if config.weekday_hour:
        # n_features=3 (weekday-hour-percentage)
        X_train_data = add_weekday_hour(X_train)
        X_test_data = add_weekday_hour(X_test)
    else:
        # n_features=1 (percentage)
        X_train_data, X_test_data = X_train[:, :, 1], X_test[:, :, 1]
        # # train and test dimensions: [n_chunks, n_timesteps_in, n_features]
        X_train_data = X_train_data.reshape((X_train_data.shape[0], X_train_data.shape[1], config.n_features))
        X_test_data = X_test_data.reshape((X_test_data.shape[0], X_test_data.shape[1], config.n_features))
    y_train_data, y_test_data = y_train[:, :, 1], y_test[:, :, 1]
    # converting to tensor
    X_train_data = tf.convert_to_tensor(X_train_data, dtype=tf.float32)
    X_test_data = tf.convert_to_tensor(X_test_data, dtype=tf.float32)
    y_train_data = tf.convert_to_tensor(y_train_data, dtype=tf.float32)
    y_test_data = tf.convert_to_tensor(y_test_data, dtype=tf.float32)
    return X_train_data, X_test_data, y_train_data, y_test_data


def get_timestamps(X_train, y_train, X_test, y_test):
    # train and test dimensions: [n_chunks, n_timesteps_in, n_features+1]
    # actually n_features=1 (percentage)
    X_train_timestamps, X_test_timestamps = X_train[:, :, 0], X_test[:, :, 0]
    y_train_timestamps, y_test_timestamps = y_train[:, :, 0], y_test[:, :, 0]
    return X_train_timestamps, X_test_timestamps, y_train_timestamps, y_test_timestamps


def process(df, labels=False):
    if labels:
        return process_data_with_labels(df)
    return process_data_without_labels(df)


def process_data_with_labels(df):
    X_train, X_test, y_train, y_test = split_data(df)
    X_train_data, X_test_data, y_train_data, y_test_data = get_data(X_train, y_train, X_test, y_test)
    X_train_timestamps, X_test_timestamps, y_train_timestamps, y_test_timestamps = get_timestamps(X_train, y_train,
                                                                                                  X_test, y_test)
    return (X_train_data, X_test_data, y_train_data, y_test_data), \
           (X_train_timestamps, X_test_timestamps, y_train_timestamps, y_test_timestamps)


def process_data_without_labels(df):
    timestamps = df['time'][-config.n_timesteps_in:]
    if config.weekday_hour:
        data = np.expand_dims(df.values[-config.n_timesteps_in:], axis=2)
        data = data.reshape((config.n_timesteps_in, -1, 2))
        data = add_weekday_hour(data)
    else:
        data = df.drop(columns=['time']).values[-config.n_timesteps_in:]
    data = data.reshape((1, config.n_timesteps_in, config.n_features)).astype(float)
    return data, timestamps
