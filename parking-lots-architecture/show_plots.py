import argparse

from analysis.plots import *
from data_management.database_utilities import get_data

parser = argparse.ArgumentParser()
parser.add_argument('--park_id', type=str, default=0)
parser.add_argument('--days', type=int, default=None)
parser.add_argument('--start_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'), default=None)
parser.add_argument('--end_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'), default=None)
args = parser.parse_args()

if __name__ == '__main__':
    tables = ['messages', 'occupancy']
    messages_df, occupancy_df = get_data(tables, park_id=args.park_id,
                                         start_date=args.start_date, end_date=args.end_date)
    free_parking_df = pd.DataFrame(occupancy_df, copy=True)
    free_parking_df.drop(columns='park_id', inplace=True)
    free_parking_df.columns = ['value']
    free_parking_df.value = ((1 - free_parking_df.value) * 68).astype('int32')

    activity_plot(messages_df)
    occupancy_plot(occupancy_df, args.days)
    occupancy_heatmap(occupancy_df, args.days)
    free_parking_week_boxplot(free_parking_df, error=2)
    free_parking_hour_plot(free_parking_df)
