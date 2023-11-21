from tensorflow import cast, int32
import tensorflow.keras.backend as k
import pandas as pd
import sys


def occupancy_to_free_parking(occ, capacity):
    return cast((1 - occ) * capacity, int32).numpy().squeeze()


def wrapper_accuracy_score(capacity, error):
    def parking_accuracy(true, pred):
            true_occupation = cast(capacity * true, int32)
            pred_occupation = cast(capacity * pred, int32)
            return k.mean(k.abs(true_occupation - pred_occupation) <= error)
    return parking_accuracy


def parking_accuracy(true, pred, capacity, error):
    #error = number of parching lot more or less aviable
    true_occupation = cast(capacity * true, int32)
    pred_occupation = cast(capacity * pred, int32)
    return k.mean(k.abs(true_occupation - pred_occupation) <= error)


def true_pred_occ_to_free_parking(true, pred, capacity, error, accuracy=False):
    free_parking_true = occupancy_to_free_parking(true, capacity)
    free_parking_pred = occupancy_to_free_parking(pred, capacity)
    if accuracy:
        acc = parking_accuracy(true, pred, capacity, error)
        return free_parking_true, free_parking_pred, acc
    return free_parking_true, free_parking_pred