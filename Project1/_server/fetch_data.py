import os
from datetime import datetime
from io import StringIO
from time import sleep
import pandas as pd
import requests
from functools import partial


AV_URL = partial('https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval={interval}min&apikey={apikey}&datatype=csv'.format, apikey=os.environ['AV_API_KEY'])
FINNHUB_URL = partial('https://finnhub.io/api/v1/quote?symbol={ticker}&token={apikey}'.format, apikey=os.environ['FH_API_KEY'])


def format_av(ticker, interval=5):
    return AV_URL(ticker=ticker, interval=interval)


def save(df: pd.DataFrame, url='data.csv'):
    with open(url, 'w') as f:
        df.to_csv(f)


def get_initial_data(url: str, backoff=10):
    try:
        data = requests.get(url)
        with StringIO() as text:
            text.write(data.text)
            text.seek(0)

            dataframe = pd.read_csv(text, index_col='timestamp', parse_dates=True, keep_date_col=False)[['close']]
            dataframe.index.names = ['datetime']
            return dataframe.sort_index()
    # Handle rate limiter by "exponentially" backing off (20s, 20s, 40s, 60s)
    # Worst case scenario: sleep for a whole day if more than 500 requests
    except ValueError as e:
        # Check if rate limit exceeded (AV returns that in a Note, not Error Message)
        if 'Note' in data.json():
            sleep(backoff)
            return get_initial_data(url, max(backoff*2, 60))
        elif 'Error Message' in data.json():
            raise ValueError('Ticker not found')
        elif data.status_code != 200:
            raise RuntimeError('Data collection failed') from e


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
        ticker_data[ticker].sort_index(inplace=True)


def fetch(ticker, interval):
    dataframe = get_initial_data(format_av(ticker, interval))
    if len(dataframe) == 0:
        raise ValueError('Ticker has no data')

    return dataframe


def fetch_all(tickers, interval):
    ticker_data = {}
    for ticker in tickers:
        try:
            ticker_data[ticker] = fetch(ticker, interval)
        except (ValueError, RuntimeError) as e:
            print(e)
            print('Removing {ticker} from tickers list'.format(ticker=ticker))
            tickers.remove(ticker)

    return ticker_data
