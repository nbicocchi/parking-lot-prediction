from datetime import datetime

n_timesteps_in = 24
n_timesteps_out = 8
n_features = 1
weekday_hour = True
if weekday_hour:
    n_features += 2
test_size = 0.2
validation_size = 0.2
max_epochs = 1000
n_sensors = 68
error = 2
start_date = datetime(2019, 12, 16, 0, 0, 0)
end_date = datetime(2020, 2, 25, 0, 0, 0)
hyperparameters_config = {'conv_layers': [[(60, 12)]],
                          'fc_layers': [[400, 400, 400]],
                          'dropout_rate': [0.04],
                          'lstm_layers': [[], [1000]]}
# hyperparameters_config = {'conv_layers': [[(60, 3)], [(60, 6)], [(60, 12)], [(120, 6)], [(120, 12)],
#                                           [(60, 3), (120, 6)], [(60, 6), (120, 6)]],
#                           'fc_layers': [[400, 200], [400, 300], [400, 400],
#                                         [100, 100, 100], [200, 200, 200], [300, 300, 300], [400, 400, 400],
#                                         [400, 300, 200], [300, 200, 100], [400, 300, 200, 100]],
#                           'dropout_rate': np.arange(0.04, .12, .04),
#                           'lstm_layers': [[], [1000]]}
# hyperparameters_config = {'conv_layers': [[(60, 3)], [(60, 6)], [(120, 6)],
#                                           [(60, 3), (120, 6)], [(60, 6), (120, 6)]],
#                           'fc_layers': [[400, 200], [400, 300], [400, 400],
#                                         [100, 100, 100], [400, 400, 400],
#                                         [400, 300, 200], [300, 200, 100], [400, 300, 200, 100]],
#                           'dropout_rate': np.arange(0.04, .12, .04),
#                           'lstm_layers': [[], [1000]]}
# hyperparameters_config = {'conv_layers': [[(60, 12)]],
#                           'fc_layers': [[]],
#                           'dropout_rate': [0.04],
#                           'lstm_layers': [[400, 400, 400], [n_timesteps_in * 10, n_timesteps_out * 10], [1500, 1500]]}
