import itertools
import os
import traceback
import random
import numpy as np
import tensorflow as tf
from keras import backend as k
from multiprocessing import Queue
from tensorflow.keras.models import load_model
random.seed(42)
np.random.seed(42)
tf.random.set_seed(42)

from .build_fit_model import build_fit_model
from .data_processing import process_data
from plots.neural_network_plots import one_step_ahead_plot, multi_steps_ahead_plot
from utilities.metrics import parking_accuracy


def prediction(model, X, capacity, error, percentual_error, y=None, print_accuracy=True):
    """
    return the prediction of the model with accuracy of one and eight hours ahead 
    """
    y_pred = model.predict(X).squeeze()
    accuracy_one_hour = parking_accuracy(y[:, 0], y_pred[:, 0],  capacity, error)
    accuracy_eight_hour = parking_accuracy(y[:, 7], y_pred[:, 7],  capacity, error)
    if y is not None and print_accuracy:
        print(f"error: ±{error} parking lots (±{percentual_error}%)")
        print(f'Median network parking accuracy = {parking_accuracy(y, y_pred,  capacity, error)}')
        print(f'Network parking accuracy 1-Hour ahead  = {accuracy_one_hour}')
        print(f'Network parking accuracy 8-hour ahead  = {accuracy_eight_hour}')
    return y_pred, accuracy_one_hour, accuracy_eight_hour


def clear_session(model_list, n):
    """ 
    prevent memory growht and set model_list size to n
    """
    if len(model_list)> n:
        model_list[-1].clear()
        del model_list[-1]
        k.clear_session()

def tune_hyperparameters(X_train, X_test, y_train, y_test, conf_nn, hyperparameters_config, capacity, error):
    model_list = list()
    print('n_timesteps_in={}, n_timesteps_out={}, n_features={}'.format(conf_nn['n_timesteps_in'], conf_nn['n_timesteps_out'],
                                                                        conf_nn['n_features']))
    hyperparameters_combo = [dict(zip(hyperparameters_config.keys(), combo))
                             for combo in itertools.product(*hyperparameters_config.values())]
    for i, model_hyperparameters in enumerate(hyperparameters_combo):
        try:
            print(100 * '*')
            if len(hyperparameters_combo) != 1:
                print('{}/{}'.format(i + 1, len(hyperparameters_combo)))
            model_metrics = build_fit_model(X_train, X_test, y_train, y_test, model_hyperparameters, conf_nn, capacity, error)
            model_list.append({'hyperparameters': model_hyperparameters, **model_metrics})
            model_list = sorted(model_list, key=lambda p: p['testing_metrics']['parking_accuracy'], reverse=True)
            clear_session(model_list, 3)
        except (KeyboardInterrupt, Exception):
            print()
            traceback.print_exc(limit=1)
            break
    return model_list


def print_results(model_list):
    print(100 * '*')
    print('Best {} models'.format(len(model_list)))
    for i, model_config in enumerate(model_list):
        print('{}/{}'.format(i + 1, len(model_list)))
        print('Hyperparameters: {}'.format(model_config['hyperparameters']))
        print(
            'Training metrics: epochs={n_epochs}, loss={loss:.5e}, parking_accuracy={parking_accuracy:.3f} (error=±{'
            'error})'.format(**model_config['training_metrics']))
        print('Testing metrics: loss={loss:.5e}, parking_accuracy={parking_accuracy:.3f} (error=±{error})'.format(
            **model_config['testing_metrics']))


def save_best_model(model_list, path, print_summary=True):
    model = model_list[0]['model']
    if print_summary:
        model.summary()
    model.save(os.path.join(path, 'model.h5'))
    with open(os.path.join(path, 'model_architecture.json'), 'w') as json_file:
        json_file.write(model.to_json())
    return model


def train_get_data(df, path_plot: str, path_model: str, capacity_parking_lot: int,  hyperparameters_config: dict, config_nn: dict, queue: Queue = None, plot=False):
    """
    This function will tuning the network with the best hyperparameter passed if the model doesn't exists.
    The result of every model is printed to the terminal, if plot = true plots will be generated at the given path.
    Returns the best hyperparameter if hyperparameter tuning is done.
    Otherwise returns a list containing accuracy of one and eight hours for every percentual error given. 
    """
    #dataframe columns: ['time', 'percentage'] 
    data, timestamps = process_data(df, config_nn, labels=True)
    print('Training set from {} to {}'.format(timestamps[0][0, 0], timestamps[0][-1, 0]))
    print('Testing set from {} to {}'.format(timestamps[1][0, 0], timestamps[1][-1, 0]))
    #tuning with minor error
    error = round(capacity_parking_lot * (config_nn['percentual_error'][0]/100))
    #load model if the tuning of the hyperparameters was already done
    if os.path.exists(os.path.join(path_model,'model.h5')) and queue is None:
        print("Loading model...")
        best_model = load_model(os.path.join(path_model,'model.h5'), custom_objects={'parking_accuracy': parking_accuracy})
    else: 
        models = tune_hyperparameters(*data, config_nn, hyperparameters_config, capacity_parking_lot, error)
        print_results(models)
        best_model = save_best_model(models, path_model)
    accuracy_list = []
    for percentual_error in config_nn['percentual_error']:
        error = round(capacity_parking_lot * (percentual_error/100))
        pred_data, accuracy_one_hour, accuracy_eight_hour = prediction(best_model, data[1], capacity_parking_lot, error, percentual_error, y=data[3], print_accuracy=True)
        #getting data to return
        lstm = ''
        if len(hyperparameters_config.get('lstm_layers')[0]) > 0:
            lstm = '+LSTM'
        accuracy_list.append((f"CNN{lstm}+FC (±{percentual_error}%) (1-hour)",k.get_value(accuracy_one_hour)))
        accuracy_list.append((f"CNN{lstm}+FC (±{percentual_error}%) (8-hours)",k.get_value(accuracy_eight_hour)))
        if plot:
            one_step_ahead_plot(timestamps[3], pred_data, data[3], path_plot, capacity_parking_lot, error, percentual_error) #168 = 24 data * 7 days
            multi_steps_ahead_plot(timestamps[3], pred_data, data[3], path_plot, config_nn['n_timesteps_out'], capacity_parking_lot, error, percentual_error8)
    if queue is not None:#set hyperparameter to retrive from the main
        queue.put(models[0]['hyperparameters'])
        return 1
    return accuracy_list