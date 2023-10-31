import argparse
from pathlib import Path

from prediction import predict_last_data
from train import train

parser = argparse.ArgumentParser()
parser.add_argument('--path', type=Path, default=None)
parser.add_argument('--plot', type=bool, default=True)
args = parser.parse_args()

if __name__ == '__main__':
    model = train(args.path, args.plot)
    predict_last_data(model, args.path, args.plot)
