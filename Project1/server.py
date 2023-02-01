# Check for required API keys
import os
from time import sleep

if 'AV_API_KEY' not in os.environ:
    print('Missing AlphaVantage API key (AV_API_KEY)')
    exit(1)
if 'FH_API_KEY' not in os.environ:
    print('Missing FinnHub API key (FH_API_KEY)')
    exit(1)

import argparse
import asyncio
import threading
import socketserver

import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from _server.calculate import create_initial_dataframe
from _server.data import get_data
from _server.fetch_data import fetch_all, fetch, get_periodic_data
from _server.report import get_report


def handle_delete(data):
    if len(data) != 2 or data[1] not in tickers:
        return b'2'

    try:
        tickers.remove(data[1])
        global ticker_dataframe
        ticker_indices = ticker_dataframe.groupby(by='ticker').get_group(data[1]).index
        ticker_dataframe = ticker_dataframe.drop(ticker_indices)
        return b'0'
    # ticker not tracked
    except ValueError:
        return b'2'
    # error dropping dataframe
    except Exception:
        return b'1'


def handle_data(data):
    if len(data) > 2:
        return b'Invalid date arguments'

    date = None
    if len(data) == 2:
        try:
            # Convert date from UTC to EST and drop timezone info
            date = pd\
                .to_datetime(data[1], format='%Y-%m-%d-%H:%M', utc=True)\
                .tz_convert('US/Eastern')\
                .tz_localize(None)
        except Exception:
            return b'1'

    latest_data = get_data(ticker_dataframe, date)
    response = latest_data.encode('utf-8')

    return response


def handle_add(data):
    if len(data) != 2 or data[1] in tickers:
        return b'2'
    try:
        ticker = data[1]
        ticker_data[ticker] = fetch(ticker, sampling)

        global ticker_dataframe
        ticker_dataframe = create_initial_dataframe(ticker_data)

        tickers.append(ticker)
    except ValueError:
        return b'2'
    except Exception:
        return b'1'
    return b'0'


def handle_report(data):
    if len(data) != 1:
        return b'2'
    try:
        get_report(ticker_dataframe)
        return b'0'
    except Exception:
        return b'1'


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = str(self.request.recv(1024), 'ascii').split(' ')

        if data[0] == 'report':
            response = handle_report(data)
        elif data[0] == 'add':
            response = handle_add(data)
        elif data[0] == 'delete':
            response = handle_delete(data)
        elif data[0] == 'data':
            response = handle_data(data)
        else:
            response = b'1'

        self.request.sendall(response)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def run_periodic_collection():
    try:
        global ticker_data, tickers, ticker_dataframe
        get_periodic_data(ticker_data, tickers)
        ticker_dataframe = create_initial_dataframe(ticker_data)
    except (KeyboardInterrupt, SystemExit):
        exit(0)


def schedule_periodic_task():
    asyncio.set_event_loop(asyncio.new_event_loop())

    scheduler = AsyncIOScheduler(timezone="US/Eastern")
    scheduler.add_job(run_periodic_collection, "cron", second="*/{sampling}".format(sampling=sampling))
    scheduler.start()

    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    try:
        # Define arguments (server)
        parser = argparse.ArgumentParser(
            prog='Project 1 Server',
            description='Server that collects data, makes reports and serves Project 1 Clients that are running on the same network'
        )
        parser.add_argument('--port', default='8000')
        parser.add_argument('--tickers', default="AAPL,MSFT,TOST")
        parser.add_argument('--sampling', choices=[5, 15, 30, 60], default=5)

        args = parser.parse_args()
        port = args.port
        try:
            port = int(port)
        except ValueError as e:
            raise ValueError('Invalid port: not a number') from e
        if not (1 <= int(port) <= 65535):
            raise ValueError('Invalid port number: not in valid port range')

        global tickers, ticker_data, ticker_dataframe, sampling
        tickers = args.tickers.split(',')
        sampling = args.sampling

        server = ThreadedTCPServer(("", port), ThreadedTCPRequestHandler)
        server.allow_reuse_address = True

        # Generate first report before serving
        print('Starting initial data collection. Server will not be ready until this is done.')
        ticker_data = fetch_all(tickers, sampling)
        ticker_dataframe = create_initial_dataframe(ticker_data)
        get_report(ticker_dataframe)
        print('Initial data collection complete')

        with server:
            ip, port = server.server_address

            # Start a thread with the server -- that thread will then start one
            # more thread for each request
            server_thread = threading.Thread(target=server.serve_forever)
            # Exit the server thread when the main thread terminates
            server_thread.daemon = True
            server_thread.start()

            # Start a thread with the periodic data grabber
            periodic_thread = threading.Thread(target=schedule_periodic_task)
            # Exit the periodic data grabber when the main thread terminates
            periodic_thread.daemon = True
            periodic_thread.start()

            print("Server loop running in thread:", server_thread.name)
            print(f'IP: {ip} PORT: {port}')

            while True:
                sleep(5)
    except (KeyboardInterrupt, SystemExit):
        exit(0)
