from tensorflow import cast, int32
import tensorflow.keras.backend as k
import pandas as pd

from data_management.database_utilities import get_data
import neural_network.config as config


def occupancy_to_free_parking(occ):
    return cast((1 - occ) * config.n_sensors, int32).numpy().squeeze()


def parking_accuracy(true, pred, error=config.error):
    true_occupation = cast(config.n_sensors * true, int32)
    pred_occupation = cast(config.n_sensors * pred, int32)
    return k.mean(k.abs(true_occupation - pred_occupation) <= error)


def true_pred_occ_to_free_parking(true, pred, accuracy=False):
    free_parking_true = occupancy_to_free_parking(true)
    free_parking_pred = occupancy_to_free_parking(pred)
    if accuracy:
        acc = parking_accuracy(true, pred)
        return free_parking_true, free_parking_pred, acc
    return free_parking_true, free_parking_pred


def get_occupancy(path=None, park_id=None, start=None, end=None):
    if path:
        return pd.read_csv(path.joinpath('occupancy.csv'), parse_dates=['time'])
    return get_data(tables_names=['occupancy'], park_id=park_id, start_date=start, end_date=end)[0].reset_index()
