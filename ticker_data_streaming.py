import asyncio
import json
import logging
import os
from datetime import datetime

import psycopg2
from dotenv import load_dotenv

from constants import SYMBOL_SPREAD_TABLE_NAME, SYMBOL_SPREAD_TABLE_FIELDS
from websocket_ftx.client import FtxWebsocketClient

# Load in the .env file with FTX credentials
load_dotenv()

# Set up logger
main_logger = logging.getLogger("ticker-data-app")
main_logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
main_logger.addHandler(stream_handler)


def unix_timestamp_to_datetime(unix_timestamp):
    """
    Given a unix timestamp, convert it into the datetime equivalent

    :param float unix_timestamp: The unix timestamp to convert
    :rtype: str
    :return: A datatome string which is more human-understandable
    """
    if unix_timestamp is None:
        return None
    date_time = datetime.utcfromtimestamp(unix_timestamp)
    date_time_str = date_time.strftime("%Y/%m/%d %H:%M:%S.%f")
    return date_time_str


def write_entry_data_to_db(db_connection, symbol, bid_ask_data):
    """
    Given a single data point from the websocket, write this to the postgres db
    
    :param DatabaseConnection db_connection: A connection to a database
    :param symbol: The symbol which data was collected for
    :param dict bid_ask_data: The latest ticker information on the symbol
    """
    datetime_str = unix_timestamp_to_datetime(bid_ask_data.get("time"))

    values_str_list = ",".join([str(field) for field in bid_ask_data.values()])
    bid_ask_entry_values = f"{values_str_list},'{symbol}','{datetime_str}'"

    sql = f"INSERT INTO {SYMBOL_SPREAD_TABLE_NAME} ({','.join(SYMBOL_SPREAD_TABLE_FIELDS)}) " \
          f"VALUES ({bid_ask_entry_values})"
    main_logger.info(f"Executing SQL: {sql}")
    print(f"Executing SQL: {sql}")
    db_connection.cursor.execute(sql)
    db_connection.connection.commit()


async def subscribe_to_symbol_ws_and_write_to_db(db_connection, websocket, symbol, symbol_id,
                                                 ticker_interval):
    """
    Fetch ticker data and write to the database

    :param DatabaseConnection db_connection: A connection to a database
    :param FtxWebsocketClient websocket:  The connected websocket
    :param symbol: The symbol to stream data for
    :param symbol_id: The symbol unique ID
    :param float ticker_interval: The interval between consecutive calls to for a symbol to the
        websocket
    :return:
    """
    while True:
        bid_ask_data = websocket.get_ticker(market=symbol)
        if len(bid_ask_data) > 0:
            # Write to DB
            write_entry_data_to_db(db_connection=db_connection, symbol=symbol,
                                   bid_ask_data=bid_ask_data)
        else:
            main_logger.info(f"No data available for {symbol}")

        main_logger.info(f"{symbol} bid_ask_data: {bid_ask_data}")
        await asyncio.sleep(ticker_interval)


async def stream_and_write_data_to_db(db_connection, websocket, ticker_symbols):
    """
    Using asynchronous processors - create a subroutine to stream data and write to a database for
    every symbol

    :param DatabaseConnection db_connection: A connection to a database
    :param FtxWebsocketClient websocket:  The connected websocket
    :param list[TickerSymbol] ticker_symbols: List of symbols to stream data for
    """
    async_symbol_streaming_coroutines = []
    for symbol_id, ticker_symbol_obj in enumerate(ticker_symbols):
        ticker_symbol = ticker_symbol_obj.get_symbol_name()
        streaming_coroutine = subscribe_to_symbol_ws_and_write_to_db(
            db_connection=db_connection, websocket=websocket, symbol=ticker_symbol,
            symbol_id=symbol_id, ticker_interval=ticker_symbol_obj.get_symbol_ticker_interval()
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


def write_symbol_data_to_postgres_db(db_connection, ticker_symbols):
    """
    Given a list of symbols - create websockets for each symbol and stream data into a database

    :param DatabaseConnection db_connection: A connection to a database
    :param list[TickerSymbol] ticker_symbols: List of symbols to stream data for
    :return:
    """
    ftx_websocket = init_ftx_websocket_client()

    try:
        asyncio.run(stream_and_write_data_to_db(
            db_connection, ftx_websocket, ticker_symbols
        ))

    except KeyboardInterrupt:
        logging.info(f"Stopped - Keyboard interrupt")
        pass
    finally:
        logging.info('Closing Loop')


def get_all_table_data(cursor, table_name):
    """
    Extract data from a table using the given curssor

    :param psycopg2._psycopg.connection.connection cursor: Database cursor
    :param str table_name: Table name to extract data from
    :return: Table entries
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


class TickerSymbol:
    def __init__(self, symbol_name, symbol_info):
        """
        :param str symbol_name: Symbol Name
        :param dict symbol_info: Additional websocket streaming information
        """
        self.symbol_name = symbol_name
        self.ticker_interval = symbol_info.get("ticker_interval")

    def get_symbol_name(self):
        return self.symbol_name

    def get_symbol_ticker_interval(self):
        return self.ticker_interval


def get_symbol_objects_from_config(file_name="ticker_config.json"):
    """
    Using the given config file name, extract the symbols and associated meta-data for streaming
    :param str file_name: config file name
    :rtype: list[TickerSymbol]
    :return: List of symbol objects stream data for
    """
    try:
        config_file = open(file_name, "r")
        symbols_json_config = json.loads(config_file.read())

        ticker_symbols_list = []
        for symbol_name, symbol_info in symbols_json_config["Symbols"].itmes():
            main_logger.info(f"symbol_name: {symbol_name}")
            ticker_symbol = TickerSymbol(symbol_name, symbol_info)
            ticker_symbols.append(ticker_symbol)

        return ticker_symbols_list
    except FileNotFoundError:
        main_logger.error(f"No config file found at {config_file_name}")
        return []


if __name__ == "__main__":

    config_file_name = "ticker_config.json"
    ticker_symbols = get_symbol_objects_from_config(config_file_name)

    main_logger.info(f"Streaming data for : {[ts.get_symbol_name() for ts in ticker_symbols]}")

    # postgres_conn, db_cursor = get_postgres_connection_and_cursor()

    db_connection = DatabaseConnection(enable_autocommit=False)

    get_postgres_current_data = True
    if get_postgres_current_data:
        results = get_all_table_data(cursor=db_connection.cursor,
                                     table_name=SYMBOL_SPREAD_TABLE_NAME)
        for row in results:
            main_logger.info(f"{row}")

    if len(ticker_symbols) > 0:
        write_symbol_data_to_postgres_db(db_connection=db_connection, ticker_symbols=ticker_symbols)

    print("DOOOOOOOOOOOOOOOOOOONE")
