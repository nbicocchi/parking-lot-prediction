import argparse
from pathlib import Path

from neural_network.prediction import predict_last_data
from neural_network.train import train

parser = argparse.ArgumentParser()
parser.add_argument('--path', type=Path, default=None)
parser.add_argument('--plot', type=bool, default=True)
args = parser.parse_args()

if __name__ == '__main__':
    model = train(args.path, args.plot)
    predict_last_data(model, args.path, args.plot)
