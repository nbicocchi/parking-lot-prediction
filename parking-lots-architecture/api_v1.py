from collections import OrderedDict
import json
from flask import Flask
from datetime import datetime

from data_management.database_utilities import get_last_n_records, get_data
from api.prediction_median import compute_median, predict
from neural_network.prediction import predict_last_data
from neural_network.utilities import parking_accuracy
from utilities.init_data_path import get_data_path
from tensorflow.keras.models import load_model

model = load_model(get_data_path().joinpath('model.h5'), custom_objects={'parking_accuracy': parking_accuracy})
app = Flask(__name__)


@app.route("/v1/parks/<int:park_id>/current_occupancy")
def get_real_time_occupancy(park_id):
    occupancy = get_last_n_records('occupancy', park_id=park_id)
    if occupancy.empty:
        return json.dumps({})
    data = eval(occupancy['percentage'].to_json(date_format='iso', date_unit='s', double_precision=3))
    out = [OrderedDict([('date', k), ('occ', v)]) for (k, v) in data.items()][0]
    return json.dumps(out)


@app.route("/v1/parks/<int:park_id>/last_24h_occupancy")
def get_last_24h_occupancy(park_id):
    data_frequency = 60 // 5
    occupancy = get_last_n_records('occupancy', park_id=park_id, n=24 * data_frequency)
    if occupancy.empty:
        return json.dumps([])
    occupancy = occupancy[::-1].resample(rule='60T').mean()[:24]
    data = eval(occupancy['percentage'].to_json(date_format='iso', date_unit='s', double_precision=3))
    out = [OrderedDict([('hour', k), ('occ', v)]) for (k, v) in sorted(data.items(), key=lambda x: x[0])]
    return json.dumps(out)


def get_hourly_occupancy(park_id, hours):
    data_frequency = 60 // 5
    occupancy = get_last_n_records('occupancy', park_id=park_id, n=hours * data_frequency)
    if occupancy.empty:
        return json.dumps([])
    occupancy = occupancy[::-1].resample(rule='60T').mean()
    occupancy = occupancy.pivot_table(index=occupancy.index.hour)
    data = eval(occupancy['percentage'].to_json(date_format='iso', date_unit='s', double_precision=3))
    out = [OrderedDict([('hour', int(k)), ('occ', v)]) for (k, v) in sorted(data.items(), key=lambda x: x[0])]
    out.sort(key=lambda x: x['hour'])
    return json.dumps(out)


@app.route("/v1/parks/<int:park_id>/daily_occupancy")
def get_daily_occupancy(park_id):
    return get_hourly_occupancy(park_id, hours=24)


@app.route("/v1/parks/<int:park_id>/weekly_occupancy")
def get_weekly_occupancy(park_id):
    return get_hourly_occupancy(park_id, hours=24 * 7)


@app.route("/v1/parks/<int:park_id>/monthly_occupancy")
def get_monthly_occupancy(park_id):
    return get_hourly_occupancy(park_id, hours=24 * 30)


@app.route("/v1/parks/<int:park_id>/nn_prediction")
@app.route("/v1/parks/<int:park_id>/8h_prediction")
def get_nn_prediction(park_id):
    predictions = predict_last_data(model, park_id=park_id, path=None, plot=False, verbose=False)
    if predictions.empty:
        return json.dumps([])
    predictions_json = predictions.T.to_json(date_format='iso', date_unit='s', double_precision=3)
    predictions_dict = eval(predictions_json)
    sorted_predictions = sorted(predictions_dict.items(), key=lambda x: x[0])
    out = [OrderedDict([('date', k), ('pred', v)]) for (k, v) in sorted_predictions]
    return json.dumps(out)


@app.route('/v1/parks/<int:park_id>/median_prediction/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>')
def get_median_prediction(park_id, year, month, day, hour, minute):
    date_string = '{}-{}-{} {}:{}'.format(year, month, day, hour, '00')
    date = datetime.strptime(date_string, '%Y-%m-%d %H:%M')
    occupancy = get_data(tables_names=['occupancy'], park_id=park_id)[0]
    occupancy.drop(columns='park_id', inplace=True)
    if occupancy.empty:
        return json.dumps([])
    median = compute_median(occupancy)
    prediction = predict(median, date)
    prediction = eval(prediction.T.to_json(date_format='iso', date_unit='s', double_precision=3))
    out = [OrderedDict([('date', k), ('pred', v)]) for (k, v) in prediction.items()]
    out.sort(key=lambda x: x['date'])
    if len(out) == 1:
        out = out[0]
    return json.dumps(out)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
