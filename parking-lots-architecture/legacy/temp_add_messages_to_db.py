import pandas as pd
from pathlib import Path

from data_management.database_utilities import get_last_n_records
from data_management.save_message import df_to_db

last_timestamp = get_last_n_records('messages', desc=True).index[0]
path = Path.home().joinpath(".bosch_pls")
csv_data = pd.read_csv(path.joinpath('data.csv'), parse_dates=['time'])
csv_data = csv_data[csv_data.time > last_timestamp]
csv_data['park_id'] = 0
df_to_db(csv_data)
