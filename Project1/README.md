# README

## Environment Setup
`!important`
Minimum Python version required: 3.8

`!important`
Minimum pip version: 19.3

Install required packages (`pandas`, `numpy`, `apscheduler`, `requests`) by running
```commandline
pip install -r requirements.txt
```

Before starting the server, please set the following environment variables:

`AV_API_KEY`: AlphaVantage API key

`FH_API_KEY`: FinnHub API key

# Update
Initially, I was using the [Intraday (Extended History)](https://www.alphavantage.co/documentation/#intraday-extended)
API that splits 2 year historical data into 24 slices, with each slice requiring its own API call.

I replaced that with the [1-2 month historical rates](https://www.alphavantage.co/documentation/#intraday)
API instead.

# Outdated
## Server start time
The server application first performs a blocking historical data collection of
initial list of tickers before starting the TCP server.

When using a free AlphaVantage API key, this can take 5 minutes per ticker.
This is because the external historical data API is queried,
which splits the 2 year historical data into 24 slices.
(24 slices / 5 slices / min = ~5 mins)

## Server add time
Similarly, adding a new ticker to the server will also take ~5 mins if a free
AV API key is provided.