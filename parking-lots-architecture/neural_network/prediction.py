import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model

import neural_network.config as config
from neural_network.data_processing import process
from neural_network.plots import unseen_data_plot
from neural_network.utilities import parking_accuracy, get_occupancy, occupancy_to_free_parking


def prediction(model, X, y=None, print_accuracy=True):
    y_pred = model.predict(X).squeeze()
    if y is not None and print_accuracy:
        print('Network parking accuracy=', parking_accuracy(y, y_pred))
    return y_pred


def api_prediction():
    from utilities.init_data_path import get_data_path
    model = load_model(get_data_path().joinpath('model.h5'), custom_objects={'parking_accuracy': parking_accuracy})
    return predict_last_data(model, path=None, plot=False, verbose=False)


def build_output_df(y_pred, pred_timestamps):
    y_pred = occupancy_to_free_parking(y_pred)
    prediction_with_error = np.tile(y_pred, (2, 1)).T + [-config.error, +config.error]
    output_df = pd.DataFrame(columns=['min', 'max'], index=pred_timestamps, data=prediction_with_error)
    return output_df


def predict_last_data(model, park_id=None, path=None, plot=False, verbose=True):
    unseen_df = get_occupancy(path, park_id, config.end_date, None)[::12][-24:]
    if 'park_id' in unseen_df.columns:
        unseen_df.drop(columns='park_id', inplace=True)
    unseen_pred, pred_timestamps = prediction_on_unseen_data_from_df(model, unseen_df)
    output_df = build_output_df(unseen_pred, pred_timestamps)
    if plot:
        unseen_data_plot(unseen_df, unseen_pred, pred_timestamps)
    if verbose:
        print(100 * '*')
        print('Unseen data:')
        print(unseen_df)
        print('Prediction:')
        print(output_df)
    return output_df


def prediction_on_unseen_data_from_df(model, df):
    data, timestamps = process(df, labels=False)
    y_pred = prediction(model, data)
    pred_timestamps = pd.date_range(start=timestamps.iloc[-1], periods=config.n_timesteps_out + 1, freq='H')[1:]
    return y_pred, pred_timestamps
