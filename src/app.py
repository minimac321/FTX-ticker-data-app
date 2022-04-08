import os

import numpy as np
from flask import request, Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Float, Integer, String

from constants import SYMBOL_SPREAD_TABLE_FIELDS, SYMBOL_SPREAD_TABLE_NAME
from db_utils import reset_database

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)

# Create a fresh database
reset_database(db, populate_csv_initial_data=True)


class SymbolSpreadModel(db.Model):
    """
    Defines the symbol_spread model
    """
    __tablename__ = SYMBOL_SPREAD_TABLE_NAME

    id = Column(Integer, primary_key=True, autoincrement=True)
    bid = Column(Float, nullable=True)
    ask = Column(Float, nullable=True)
    bid_size = Column(Float, nullable=True)
    ask_size = Column(Float, nullable=True)
    last = Column(Float, nullable=True)
    unix_timestamp = Column(Float, nullable=True)
    symbol = Column(String, nullable=True)
    datetime = Column(String, nullable=True)

    def __init__(self, bid, ask, bid_size, ask_size, last, unix_timestamp, symbol, datetime):
        """
        Init method for SymbolSpreadModel

        :param int bid: Best bid price
        :param float ask: Best ask price
        :param float bid_size: Bid Size
        :param float ask_size: Ask Size
        :param float last:
        :param float unix_timestamp: Unix timestamp
        :param str symbol: Symbol pairing between base and quote currency
        :param str datetime: Datetime string
        """
        self.bid = bid
        self.ask = ask
        self.bid_size = bid_size
        self.ask_size = ask_size
        self.last = last
        self.unix_timestamp = unix_timestamp
        self.symbol = symbol
        self.datetime = datetime

    def to_json(self):
        """
        Return item in json format

        :rtype: dict
        :return: json serialized SymbolSpreadModel object
        """
        return {"id": self.id, "symbol": self.symbol, "bid": self.bid, "ask": self.ask,
                "unix_timestamp": self.unix_timestamp}


def get_closest_timestamp_entry(query_timestamp, symbol=None):
    if symbol is None:
        results = SymbolSpreadModel.query.all()
    else:
        results = SymbolSpreadModel.query.filter_by(symbol=symbol)

    first_greater_timestamp = results.filter(
        query_timestamp <= SymbolSpreadModel.unix_timestamp
    ).order_by(SymbolSpreadModel.unix_timestamp.asc()).first()
    first_smaller_timestamp = results.filter(
        query_timestamp > SymbolSpreadModel.unix_timestamp
    ).order_by(SymbolSpreadModel.unix_timestamp.desc()).first()

    if not first_greater_timestamp and not first_smaller_timestamp:
        return {"message": f"Error - Unable to find any matching entries for timestamp: "
                           f"{query_timestamp}"}

    greater_timestamp_diff = first_greater_timestamp.unix_timestamp - query_timestamp \
        if first_greater_timestamp else np.inf

    smaller_timestamp_diff = query_timestamp - first_smaller_timestamp.unix_timestamp \
        if first_smaller_timestamp else np.inf

    if greater_timestamp_diff < smaller_timestamp_diff:
        return first_greater_timestamp
    else:
        return first_smaller_timestamp


def get_json_from_object(symbol_spread_entry, list_of_columns):
    """
    Return a json format of the given entry

    :param symbol_spread_entry:
    :param list_of_columns:
    :return:
    """
    symbol_spread_entry_dict = symbol_spread_entry.__dict__
    object_dict = {}
    for col in list_of_columns:
        object_dict.update({col: symbol_spread_entry_dict.get(col)})
    return object_dict


# Example: 127.0.0.1/symbol_spread
@app.route('/symbol_spread', methods=['GET'])
def get_all_items():
    try:
        symbol_spread_results = SymbolSpreadModel.query.all()
        results = [get_json_from_object(symbol_spread_entry, SYMBOL_SPREAD_TABLE_FIELDS)
                   for symbol_spread_entry in symbol_spread_results]

        return {"count": len(results), "symbol_spread_entries": results}
    except Exception as e:
        print(e)
        return {"message": "Failed to fetch all items"}, 404


# Example: http://127.0.0.1/symbol_spread/SOL/USD/
@app.route('/symbol_spread/<path:symbol>/', methods=['GET'])
def get_items_from_symbol(symbol):
    try:
        symbol_spread_results = SymbolSpreadModel.query.filter_by(symbol=symbol)
        results = [get_json_from_object(symbol_spread_entry, SYMBOL_SPREAD_TABLE_FIELDS)
                   for symbol_spread_entry in symbol_spread_results]
        return {"count": len(results), "symbol_spread_entries": results}

    except Exception as e:
        print(e)
        return {"message": "Failed to get items from symbol"}, 404


# Example: 127.0.0.1/symbol_spread/ETH/USD/bid
# Example: 127.0.0.1/symbol_spread/ETH/USD/bid?timestamp=1648995959
@app.route('/symbol_spread/<path:symbol>/bid', methods=['GET'])
def get_items_with_query_timestamp_bid(symbol):
    try:
        if request.args:
            query_dict = request.args.to_dict()
            query_timestamp = float(query_dict.get("timestamp"))

            closest_entry = get_closest_timestamp_entry(
                query_timestamp, symbol
            )
            if closest_entry is None:
                return {"message": f"Error - Unable to find any matching entries for timestamp:"
                                   f"{query_timestamp}"}
            closest_entry_json = get_json_from_object(
                closest_entry, ['bid', 'ask', 'unix_timestamp', 'symbol']
            )

            return {"message": f"Closest Bid price: {closest_entry_json['bid']} for entry:"
                               f" {closest_entry_json}"}
        else:
            # Just get the latest bid
            latest_symbol_spread_entry = SymbolSpreadModel.query.filter_by(symbol=symbol).\
                order_by(SymbolSpreadModel.unix_timestamp.desc()).first()

            latest_bid = latest_symbol_spread_entry.bid
            return {"message": f"Latest {symbol} Bid price: {latest_bid}"}

    except Exception as e:
        print(e)
        return {"message": "Failed to get ticker info for a symbol"}, 404


# Example: 127.0.0.1/symbol_spread/ETH/USD/ask
# Example: 127.0.0.1/symbol_spread/ETH/USD/ask?timestamp=1648995959
@app.route('/symbol_spread/<path:symbol>/ask', methods=['GET'])
def get_items_with_query_timestamp_ask(symbol):
    try:
        if request.args:
            query_dict = request.args.to_dict()
            query_timestamp = float(query_dict.get("timestamp"))

            closest_entry = get_closest_timestamp_entry(
                query_timestamp, symbol
            )
            if closest_entry is None:
                return {"message": f"Error - Unable to find any matching entries for timestamp:"
                                   f"{query_timestamp}"}
            closest_entry_json = get_json_from_object(
                closest_entry, ['bid', 'ask', 'unix_timestamp', 'symbol']
            )

            return {"message": f"Closest Ask price: {closest_entry_json['ask']} for entry:"
                               f" {closest_entry_json}"}
        else:
            # Just get the latest bid
            latest_symbol_spread_entry = SymbolSpreadModel.query.filter_by(symbol=symbol).\
                order_by(SymbolSpreadModel.unix_timestamp.desc()).first()

            latest_ask = latest_symbol_spread_entry.ask
            return {"message": f"Latest {symbol} Ask price: {latest_ask}"}

    except Exception as e:
        print(e)
        return {"message": "Failed to get ticker info for a symbol"}, 404


# Example: http://127.0.0.1/symbol_spread/1
@app.route('/symbol_spread/<int:id>/', methods=['GET'])
def get_item_from_id(id):
    try:
        symbol_spread_entry = SymbolSpreadModel.query.get_or_404(id)
        result = get_json_from_object(symbol_spread_entry, SYMBOL_SPREAD_TABLE_FIELDS)
        return {"symbol_spread_entries": result}
    except Exception as e:
        print(e)
        return {"message": "Failed to get entry from id"}, 404


# Example: http://127.0.0.1/symbol_spread/2 - with delete
@app.route('/symbol_spread/<int:id>/', methods=['DELETE'])
def delete_item(id):
    try:
        db.session.query(SymbolSpreadModel).filter_by(id=id).delete()
        db.session.commit()
        return {"Success": f"Item {id} deleted"}
    except Exception as e:
        print(e)
        return {"message": "Failed to delete item"}, 404


# Not working
# @app.route('/symbol_spread', methods=['POST'])
# def create_item():
#     if request.method == 'POST':
#         try:
#             body = request.get_json(force=True)
#             body = dict(body)
#
#             model_entry = SymbolSpreadModel(
#                 body.get('bid'),
#                 body.get('ask'),
#                 body.get('bid_size'),
#                 body.get('ask_size'),
#                 body.get('last'),
#                 body.get('unix_timestamp'),
#                 body.get('symbol'),
#                 body.get('datetime'),
#             )
#             db.session.add(model_entry)
#             db.session.commit()
#             return {"Success": f"Item created: {body}"}
#         except Exception as e:
#             print(e)
#             return {"message": "Failed in create_item()"}
#
#
# @app.route('/symbol_spread/<int:id>/', methods=['PUT'])
# def update_item(id):
#     try:
#         body = request.get_json()
#         db.session.query(SymbolSpreadModel).filter_by(id=id).update(
#             dict(bid=body['bid'], ask=body['ask'])
#         )
#         db.session.commit()
#         return {"Success": f"Item Updated"}
#     except Exception as e:
#         print(e)
#         return {"message": "Failed in update_item()"}

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=80)
