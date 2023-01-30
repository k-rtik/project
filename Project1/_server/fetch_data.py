import os
from datetime import datetime
from time import sleep
import pandas as pd
import requests
from functools import partial


AV_URL = partial('https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY_EXTENDED&symbol={ticker}&interval={interval}min&slice={slice}&apikey={apikey}'.format, apikey=os.environ['AV_API_KEY'])
FINNHUB_URL = partial('https://finnhub.io/api/v1/quote?symbol={ticker}&token={apikey}'.format, apikey=os.environ['FH_API_KEY'])


def format_av(ticker, timeslice, interval=5):
    return AV_URL(ticker=ticker, slice=timeslice, interval=interval)


def save(df: pd.DataFrame, url='data.csv'):
    with open(url, 'w') as f:
        df.to_csv(f)


def get_initial_data(url: str, backoff=10):
    try:
        dataframe = pd.read_csv(url, index_col='time', parse_dates=True, keep_date_col=False)[['close']]
        dataframe.index.names = ['datetime']
        return dataframe.sort_index()
    # Handle rate limiter by "exponentially" backing off (20s, 20s, 40s, 60s)
    # Worst case scenario: sleep for a whole day if more than 500 requests
    except ValueError:
        sleep(backoff)
        return get_initial_data(url, max(backoff*2, 60))


def get_periodic_data(ticker_data, tickers):
    for ticker in tickers:
        # Get realtime quote for ticker
        data = requests.get(FINNHUB_URL(ticker=ticker)).json()

        # Get qoute time and close price
        # convert UTC to Eastern and drop timezone info to match other data
        time = pd.to_datetime(data['t'], unit='s', utc=True)\
            .tz_convert('US/Eastern')\
            .tz_localize(None)\
            .replace(second=0)
        close = data['c']

        # Add to existing dataframe for ticker
        ticker_data[ticker].loc[time] = {'close': close}
        ticker_data[ticker] = ticker_data[ticker]


def _fetch_slices(ticker, interval):
    slices = []
    timeslices = ['year{y}month{m}'.format(m=m, y=y) for y in range(1, 3) for m in range(1, 13)]

    for timeslice in timeslices:
        d = get_initial_data(format_av(ticker, timeslice, interval))
        slices.append(d)

    if len(slices) == 0:
        raise ValueError('Ticker not found')
    dataframe = pd.concat(slices).sort_index()
    if len(dataframe) == 0:
        raise ValueError('Ticker not found')

    return pd.concat(slices).sort_index()


def fetch(ticker, interval):
    return _fetch_slices(ticker, interval)


def fetch_all(tickers, interval):
    ticker_data = {}
    for ticker in tickers:
        try:
            ticker_data[ticker] = _fetch_slices(ticker, interval)
        except ValueError as e:
            print(e)
            print('Removing {ticker} from tickers list'.format(ticker=ticker))
            tickers.remove(ticker)

    return ticker_data
