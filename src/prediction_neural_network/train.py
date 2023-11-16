import itertools
import os
import traceback
import random

random.seed(42)
import numpy as np

np.random.seed(42)
import tensorflow as tf

tf.random.set_seed(42)
from .build_fit_model import build_fit_model
from . import config
from .data_processing import process
from .plots import one_step_ahead_plot, multi_steps_ahead_plot
from .prediction import prediction


def tune_hyperparameters(X_train, X_test, y_train, y_test):
    model_list = list()
    print('n_timesteps_in={}, n_timesteps_out={}, n_features={}'.format(config.n_timesteps_in, config.n_timesteps_out,
                                                                        config.n_features))
    hyperparameters_combo = [dict(zip(config.hyperparameters_config.keys(), combo))
                             for combo in itertools.product(*config.hyperparameters_config.values())]
    for i, model_hyperparameters in enumerate(hyperparameters_combo):
        try:
            print(100 * '*')
            print('{}/{}'.format(i + 1, len(hyperparameters_combo)))
            model_metrics = build_fit_model(X_train, X_test, y_train, y_test, model_hyperparameters)
            model_list.append({'hyperparameters': model_hyperparameters, **model_metrics})
            model_list = sorted(model_list, key=lambda p: p['testing_metrics']['parking_accuracy'], reverse=True)[:5]
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


def train(df, path, plot=False):
    #dataset needs: ['time', 'percentage'] 
    data, timestamps = process(df, labels=True)
    print('Training set from {} to {}'.format(timestamps[0][0, 0], timestamps[0][-1, 0]))
    print('Testing set from {} to {}'.format(timestamps[1][0, 0], timestamps[1][-1, 0]))
    models = tune_hyperparameters(*data)
    print_results(models)
    best_model = save_best_model(models, path)
    if plot:
        test_data = (data[1], data[3])
        pred_data = prediction(best_model, *test_data, print_accuracy=True)
        one_step_ahead_plot(timestamps[3], pred_data, data[3], path, hours_to_plot=168) #168 = 24 dati all'ora * 7 giorni
        multi_steps_ahead_plot(timestamps[3], pred_data, data[3], path, hours_to_plot=168)
    return best_model
