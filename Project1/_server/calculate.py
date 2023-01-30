import pandas as pd
import numpy as np


def analyse_ticker_data(data):
    # get close quotes
    close = (data.iloc[::-1]['close']).rename('price')

    # calculate indicators
    sampled_24h_window = close.rolling('24H')
    average = sampled_24h_window.mean()
    sigma = sampled_24h_window.std().fillna(0)

    # create data dataframe to get signal
    data = pd.concat([close, average, sigma], axis=1)

    # get signal (shifted from P(t+1) to P(t)) and shifted position (P(t-1) for pnl calculation)
    signal = data\
        .apply(get_signal, axis=1)\
        .shift(1)\
        .interpolate(method='pad', limit_direction='forward')\
        .fillna(0)\
        .astype('int32')\
        .rename('signal')
    pos = signal.shift(1).fillna(0).astype('int32')

    # get profit and loss
    diff = close.diff().fillna(0)
    pnl = (pos * diff).round(2).rename('pnl')

    # return only required columns
    return pd.concat([close, signal, pnl], axis=1)


def get_signal(data):
    close, daily, signal = data
    if close > (daily + signal):
        return 1
    elif close < (daily - signal):
        return -1
    # will be back-filled after mapping this function on dataframe
    return np.NaN


def create_initial_dataframe(ticker_data):
    analyzed_data = {}
    for key, value in ticker_data.items():
        analyzed_data[key] = analyse_ticker_data(value)
    try:
        return pd.concat(analyzed_data, names=['ticker', 'datetime'])\
            .swaplevel()\
            .sort_index(level=0)
    except ValueError:
        return None
