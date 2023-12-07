import itertools
import os
import sys
import traceback
import random
import numpy as np
import tensorflow as tf

random.seed(42)
np.random.seed(42)
tf.random.set_seed(42)

sys.path.append("..")
from .build_fit_model import build_fit_model
from .data_processing import process_data
from plots.neural_network_plots import one_step_ahead_plot, multi_steps_ahead_plot
from .utilities import parking_accuracy


def prediction(model, X, capacity, error, percentual_error, y=None, print_accuracy=True):
    y_pred = model.predict(X).squeeze()
    if y is not None and print_accuracy:
        print('Network parking accuracy [error=±{}(±{}%)] = {}'.format(error, percentual_error, parking_accuracy(y, y_pred,  capacity, error)))
    return y_pred


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
            model_list = sorted(model_list, key=lambda p: p['testing_metrics']['parking_accuracy'], reverse=True)[:1]
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


def train_get_data(df, path_plot: str, path_model: str, capacity_parking_lot: int,  hyperparameters_config: dict, config_nn: dict, plot=False):
    """
    This function will return the best model after tuning with the best hyperparameter passed.
    The result of every model is printed to the terminal, if plot = true plots will be generated at the given path.
    """
    #dataframe columns: ['time', 'percentage'] 
    data, timestamps = process_data(df, config_nn, labels=True)
    print('Training set from {} to {}'.format(timestamps[0][0, 0], timestamps[0][-1, 0]))
    print('Testing set from {} to {}'.format(timestamps[1][0, 0], timestamps[1][-1, 0]))
    
    #tuning with minor error
    error = round(capacity_parking_lot * (config_nn['percentual_error'][0]/100))
    models = tune_hyperparameters(*data, config_nn, hyperparameters_config, capacity_parking_lot, error)
    if len(models) != 1: #tune_hyperparameters will print the same if len = 1
        print_results(models)
    best_model = save_best_model(models, path_model)
    best_hyperparameter = models[0]['hyperparameters']
    for percentual_error in config_nn['percentual_error']:
        error = round(capacity_parking_lot * (percentual_error/100))  
        if plot:
            pred_data = prediction(best_model, data[1], capacity_parking_lot, error, percentual_error, y=data[3], print_accuracy=True)
            one_step_ahead_plot(timestamps[3], pred_data, data[3], path_plot, capacity_parking_lot, error, percentual_error,hours_to_plot=168) #168 = 24 data * 7 days
            multi_steps_ahead_plot(timestamps[3], pred_data, data[3], path_plot, config_nn['n_timesteps_out'], capacity_parking_lot, error, percentual_error,hours_to_plot=168)
    return best_hyperparameter
