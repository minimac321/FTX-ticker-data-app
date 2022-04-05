import concurrent.futures
import logging
import os
import time

import pandas as pd
import numpy as np
from dotenv import load_dotenv

from websocket_ftx.client import FtxWebsocketClient

load_dotenv()

# Set up logger
main_logger = logging.getLogger("tree-group-app")
main_logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
main_logger.addHandler(stream_handler)


DRT_RUN = False
BID_ASK_DATAFRAME_COLUMNS = ['bid', 'ask', 'bidSize', 'askSize', 'last', 'time']


# TODO: Implement this in the endpoint call
def find_closest_timestamp(data=None, approx_search_timestamp=1):
    if data is None:
        data = [
            [1427837961000.0, 243.586],
            [1427962162000.0, 245.674],
            [1428072262000.0, 254.372],
            [1428181762000.0, 253.366]
        ]

    data.sort(key=lambda l: l[0])  # Sort by timestamp
    timestamps = [l[0] for l in data]  # Extract timestamps

    import bisect

    idx = bisect.bisect_left(timestamps, approx_search_timestamp)  # Find insertion point

    # Check which timestamp with idx or idx - 1 is closer
    if idx > 0 and \
            abs(timestamps[idx] - approx_search_timestamp) > abs(timestamps[idx - 1] - approx_search_timestamp):
        idx -= 1
    return data[idx][1]  # Return price


def create_websocket(ws, symbol, total_duration, ticker_interval, thread_id):
    main_logger.info(f"Thread {thread_id} started to fetch stream data for {symbol} for a duration of {total_duration}")
    bid_ask_data_list = []

    for i_seconds in range(1, total_duration):
        bid_ask_data = ws.get_ticker(market=symbol)
        print(f"Thread {thread_id}: {symbol}: {bid_ask_data.get('bid')} {bid_ask_data.get('ask')}")
        if len(bid_ask_data) != 0:
            bid_ask_data_list.append(list(bid_ask_data.values()))
            print("list(bid_ask_data.values())", list(bid_ask_data.values()))
        # Sleep
        time.sleep(ticker_interval)

    main_logger.info(f"Thread {thread_id}. Successful websocket connection for {symbol}")

    symbol_bid_ask_df = pd.DataFrame(columns=[BID_ASK_DATAFRAME_COLUMNS], data=bid_ask_data_list)
    symbol_bid_ask_df["symbol"] = symbol

    return symbol_bid_ask_df, thread_id


def fetch_symbol_ticker_data(working_dir, symbols, save_locally=True):
    """
    Given a bunch of symbols - create websockets for each symbol
    """
    # Make Websocket
    ws = FtxWebsocketClient(
        api_key=os.getenv("FTX_API_KEY"),
        api_secret=os.getenv("FTX_API_SECRET")
    )
    ws.connect()

    # Create threads
    executor = concurrent.futures.ThreadPoolExecutor()

    total_duration = 20  # in seconds
    ticker_interval = 1  # in seconds
    websocket_threads = []
    for thread_id, symbol in enumerate(symbols):
        future = executor.submit(create_websocket,
                                 ws, symbol, total_duration, ticker_interval, thread_id)
        main_logger.info(f"Created thread {thread_id} for {symbol}")

        websocket_threads.append(future)
    main_logger.info("Done submitting all symbol ticker data collection jobs.")

    all_symbol_dfs = []
    for symbol, websocket_thread in zip(symbols, websocket_threads):
        symbol_df, returned_thread_id = websocket_thread.result()
        all_symbol_dfs.append(symbol_df)
        main_logger.info(f"Finished thread {returned_thread_id} for {symbol}")

    bid_ask_data_df = pd.concat(all_symbol_dfs)
    bid_ask_data_df.reset_index(inplace=True, drop=True)
    
    time_values = np.array(bid_ask_data_df['time']).flatten()
    bid_ask_data_df["datetime"] = pd.to_datetime(time_values, utc=False, unit='s')

    start_date = bid_ask_data_df["time"].min()[0]
    end_date = bid_ask_data_df["time"].max()[0]

    if save_locally:
        bid_ask_data_fname = os.path.join(working_dir, f"bid_ask_data_interval_{ticker_interval}_{start_date}-{end_date}.csv")
        bid_ask_data_df.to_csv(bid_ask_data_fname, index=False)

    return bid_ask_data_df


if __name__ == "__main__":
    working_dir = "working_dir"
    symbol_data = ["ETH/USD", "SOL/USD", "BTC/USD"]

    fname = "working_dir/bid_ask_data_interval_1_1648994810.377584-1648994827.4729884.csv"
    if not os.path.exists(fname):
        bid_ask_data_df = fetch_symbol_ticker_data(working_dir, symbol_data)
    else:
        bid_ask_data_df = pd.read_csv(fname, index_col=False)

    print(bid_ask_data_df.shape)
    print(list(bid_ask_data_df.columns))
