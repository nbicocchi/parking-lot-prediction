from tensorflow.keras.models import load_model

from .utilities import parking_accuracy


def prediction(model, X, y=None, print_accuracy=True):
    y_pred = model.predict(X).squeeze()
    if y is not None and print_accuracy:
        print('Network parking accuracy=', parking_accuracy(y, y_pred))
    return y_pred