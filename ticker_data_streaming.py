import asyncio
import logging
import os
from datetime import datetime

import psycopg2
from dotenv import load_dotenv

from constants import TABLE_NAME, SYMBOL_SPREAD_TABLE_FIELDS
from websocket_ftx.client import FtxWebsocketClient

load_dotenv()

# Set up logger
main_logger = logging.getLogger("ticker-data-app")
main_logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
main_logger.addHandler(stream_handler)


def unix_timestamp_to_datetime(unix_timestamp):
    if unix_timestamp is None:
        return None
    date_time = datetime.utcfromtimestamp(unix_timestamp)
    date_time_str = date_time.strftime("%Y/%m/%d %H:%M:%S.%f")
    return date_time_str


def write_entry_data_to_db(db_connection, symbol, bid_ask_data):
    datetime_str = unix_timestamp_to_datetime(bid_ask_data.get("time"))

    values_str_list = ",".join([str(field) for field in bid_ask_data.values()])
    bid_ask_entry_values = f"{values_str_list},'{symbol}','{datetime_str}'"

    sql = f"INSERT INTO {TABLE_NAME} ({','.join(SYMBOL_SPREAD_TABLE_FIELDS)}) " \
          f"VALUES ({bid_ask_entry_values})"
    main_logger.info(f"Executing SQL: {sql}")
    print(f"Executing SQL: {sql}")
    db_connection.cursor.execute(sql)
    db_connection.connection.commit()


async def subscribe_to_symbol_ws_and_write_to_db(db_connection, websocket, symbol, symbol_id,
                                                 ticker_interval):
    while True:
        bid_ask_data = websocket.get_ticker(market=symbol)
        if len(bid_ask_data) > 0:
            # Write to DB
            write_entry_data_to_db(db_connection, symbol, bid_ask_data)
        else:
            main_logger.info(f"No data available for {symbol}")

        main_logger.info(f"{symbol} bid_ask_data: {bid_ask_data}")
        await asyncio.sleep(ticker_interval)


async def stream_and_write_data_to_db(db_connection, websocket, symbols, ticker_interval):
    async_symbol_streaming_coroutines = []
    for symbol_id, symbol in enumerate(symbols):
        streaming_coroutine = subscribe_to_symbol_ws_and_write_to_db(
            db_connection=db_connection, websocket=websocket, symbol=symbol,
            symbol_id=symbol_id, ticker_interval=ticker_interval
        )
        async_symbol_streaming_coroutines.append(streaming_coroutine)

    await asyncio.gather(
        *async_symbol_streaming_coroutines
    )


def init_ftx_websocket_client():
    """
    Make Websocket using api and secret key from the .env file

    :rtype: FtxWebsocketClient
    :return: The connected websocket
    """
    ws = FtxWebsocketClient(
        api_key=os.getenv("FTX_API_KEY"),
        api_secret=os.getenv("FTX_API_SECRET")
    )
    ws.connect()
    return ws


def write_symbol_data_to_postgres_db(db_connection, symbols):
    """
    Given a bunch of symbols - create websockets for each symbol and stream data into a database
    """

    ftx_websocket = init_ftx_websocket_client()

    # limit = 10
    ticker_interval = 1

    try:
        asyncio.run(stream_and_write_data_to_db(db_connection, ftx_websocket, symbols, ticker_interval))

    except KeyboardInterrupt:
        logging.info(f"Stopped - Keyboard interrupt")
        pass
    finally:
        logging.info('Closing Loop')


def get_all_table_data(cursor, table_name):
    """
    Executing an MYSQL function using the execute() method
    """
    sql = f"SELECT * from {table_name};"
    cursor.execute(sql)
    db_results = cursor.fetchall()
    return db_results


class DatabaseConnection:
    """
    Create the database connection to postgres db
    """

    def __init__(self, database="postgres", user='postgres', password='postgres', host="localhost",
                 port="5432", enable_autocommit=False):
        self.connection = psycopg2.connect(
            database=database, user=user, password=password, host=host, port=port
        )
        self.cursor = self.connection.cursor()

        if enable_autocommit:
            self.enable_autocommit()

    def enable_autocommit(self):
        self.connection.autocommit = True


if __name__ == "__main__":
    # TODO: Fetch symbols from a config file ?
    symbols_list = ["ETH/USD", "SOL/USD"]
    main_logger.info(f"Streaming data for : {symbols_list}")

    # postgres_conn, db_cursor = get_postgres_connection_and_cursor()

    db_connection = DatabaseConnection(enable_autocommit=False)

    get_postgres_current_data = True
    if get_postgres_current_data:
        results = get_all_table_data(db_connection.cursor, TABLE_NAME)
        for row in results:
            main_logger.info(f"{row}")

    write_symbol_data_to_postgres_db(db_connection, symbols_list)
