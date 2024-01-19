import os
import pandas as pd

def load_mantova(start_date, end_date):
    pd.set_option('display.max_rows', None)
    df = pd.read_csv(os.path.join(os.getcwd(), 'dataset', 'mantova.csv'),parse_dates=['time'])
    df = df[(df['time'] >= start_date) & (df['time'] < end_date)]
    #renaming to have same column name as birmingham
    
    df.index = df.time
    df.index.name = None
    
    df = df.asfreq(freq='1H')
    df['occupancy'] = df['percentage']
    df['free_slots'] = 68 - df['occupancy'] * 68 #number of sensors in the parking lot
    
    df.drop(columns='time', inplace=True)
    df.drop(columns='percentage', inplace=True)
    df.drop(columns='park_id', inplace=True)
    return df


def load_birmingham(park):
    df = pd.read_csv(os.path.join(os.getcwd(), 'dataset', 'birmingham.csv'), parse_dates=['LastUpdated'])
    df = df[df['SystemCodeNumber'].str.contains(park)]
    df = df.drop_duplicates(subset='LastUpdated', keep='first')

    df.index = df.LastUpdated
    df.index.name = None
  
    df = df.asfreq(freq='1H', method='bfill')
    df['free_slots'] = df['Capacity'] - df['Occupancy']
    df['occupancy'] = df['Occupancy'] / df['Capacity']
    df['var'] = df.groupby(by=df.index.date)['occupancy'].transform('var')
    
    df = df[df['var'] != 0]

    df.drop(columns='LastUpdated', inplace=True)
    df.drop(columns='Capacity', inplace=True)
    df.drop(columns='Occupancy', inplace=True)
    df.drop(columns='SystemCodeNumber', inplace=True)
    df.drop(columns='var', inplace=True)
    return df