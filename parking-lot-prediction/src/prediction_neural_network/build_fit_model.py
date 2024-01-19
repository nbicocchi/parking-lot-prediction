from datetime import datetime

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, Dense, Dropout, Flatten, MaxPooling1D, LSTM
from tensorflow.keras.callbacks import EarlyStopping

from utilities.metrics import wrapper_accuracy_score


def build_model(model_hyperparameters, conf_nn, capacity, error):
    conv_layers = model_hyperparameters['conv_layers']
    lstm_layers = model_hyperparameters['lstm_layers']
    fc_layers = model_hyperparameters['fc_layers']
    dropout_rate = model_hyperparameters['dropout_rate']
    initializer = 'glorot_uniform'
    activation = 'tanh'

    model = Sequential()
    for i, (filters, kernel_size) in enumerate(conv_layers):
        if i == 0:
            model.add(Conv1D(filters, kernel_size, padding='same',
                             activation=activation, kernel_initializer=initializer,
                             input_shape=(conf_nn['n_timesteps_in'], conf_nn['n_features'])))
        else:
            model.add(Conv1D(filters, kernel_size, padding='same',
                             activation=activation, kernel_initializer=initializer))
    model.add(MaxPooling1D(pool_size=2))
    model.add(Dropout(dropout_rate))
    for i, units in enumerate(lstm_layers):
        if i < len(lstm_layers) - 1:
            model.add(LSTM(units, return_sequences=True, activation=activation, kernel_initializer=initializer))
        else:
            model.add(LSTM(units, activation=activation, kernel_initializer=initializer))
            model.add(Dropout(dropout_rate))
    model.add(Flatten()) #used to format LSTM output layer for compatiility to Dense layer
    for i, units in enumerate(fc_layers):
        if i < len(fc_layers) - 1:
            model.add(Dense(units, activation=activation, kernel_initializer=initializer))
        else:
            model.add(Dense(units, activation=activation, kernel_initializer=initializer))
            model.add(Dropout(dropout_rate))
    model.add(Dense(conf_nn['n_timesteps_out']))
    model.compile(loss='mse', optimizer='adam', metrics=[wrapper_accuracy_score(capacity, error)])
    return model


def build_fit_model(X_train, X_test, y_train, y_test, model_hyperparameters, conf_nn, capacity, error):
    early_stopping = EarlyStopping(monitor='parking_accuracy', mode='max',
                                   patience=10, restore_best_weights=True)
    print('{:%H:%M:%S}'.format(datetime.now()))
    print("hyperparameters: ",model_hyperparameters)
    model = build_model(model_hyperparameters, conf_nn, capacity, error)
    history = model.fit(X_train, y_train,
                        validation_split=conf_nn['validation_size'], 
                        epochs=conf_nn['max_epochs'],
                        shuffle=False, 
                        callbacks=[early_stopping], verbose=0)
    n_epochs = len(history.history['loss'])
    last_loss = history.history['loss'][-1]
    last_parking_accuracy = history.history['parking_accuracy'][-1]
    training_metrics = {'n_epochs': n_epochs,
                        'loss': last_loss,
                        'parking_accuracy': last_parking_accuracy,
                        'error': error}
    print('TRAINING epochs={n_epochs}, loss={loss:.5e}, parking_accuracy={parking_accuracy:.3f} (error=±{error})'.format(**training_metrics))
    testing_metrics = dict(zip(['loss', 'parking_accuracy'], model.evaluate(X_test, y_test, verbose=0)))
    testing_metrics['error'] = error
    print('TESTING loss={loss:.5e}, parking_accuracy={parking_accuracy:.3f} (error=±{error})'.format(**testing_metrics))
    return {'model': model, 'training_metrics': training_metrics, 'testing_metrics': testing_metrics}
