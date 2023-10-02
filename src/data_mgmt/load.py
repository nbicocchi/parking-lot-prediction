import pandas as pd
import numpy as np

def load_mantova(start_date, end_date):
    df = pd.read_csv('dataset/mantova.csv')

    df.index = pd.to_datetime(df.time)
    df = df[(df.index >= start_date) & (df.index <= end_date)]
    df.index.name = None

    df['occupancy'] = df['percentage']
    df['free_slots'] = 68 - df['occupancy'] * 68

    df.drop(columns='percentage', inplace=True)
    df.drop(columns='time', inplace=True)
    df.drop(columns='park_id', inplace=True)
    return df


def load_birminghan(park):
    print(park)
    df = pd.read_csv('dataset/birmingham.csv')

    #summary = pd.pivot_table(df, index=['SystemCodeNumber'], values='Capacity')

    df = df[df['SystemCodeNumber'].str.contains(park)]

    df = df.drop_duplicates(subset='LastUpdated', keep='first')
    df.index = pd.to_datetime(df.LastUpdated)
    df.index.name = None
    df = df.asfreq(freq='1H', method='bfill')

    df['occupancy'] = df['Occupancy'] / df['Capacity']
    df['free_slots'] = df['Capacity'] - df['Occupancy']

    df.drop(columns='Capacity', inplace=True)
    df.drop(columns='Occupancy', inplace=True)
    df.drop(columns='LastUpdated', inplace=True)
    df.drop(columns='SystemCodeNumber', inplace=True)

    return df
