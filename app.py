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
    time = Column(Float, nullable=True)
    symbol = Column(String, nullable=True)
    datetime = Column(String, nullable=True)

    def __init__(self, bid, ask, bid_size, ask_size, last, time, symbol, datetime):
        """
        Init method for SymbolSpreadModel

        :param int bid: Best bid price
        :param float ask: Best ask price
        :param float bid_size: Bid Size
        :param float ask_size: Ask Size
        :param float last:
        :param float time: Unix timestamp
        :param str symbol: Symbol pairing between base and quote currency
        :param str datetime: Datetime string
        """
        self.bid = bid
        self.ask = ask
        self.bid_size = bid_size
        self.ask_size = ask_size
        self.last = last
        self.time = time
        self.symbol = symbol
        self.datetime = datetime

    def to_json(self):
        """
        Return item in json format

        :rtype: dict
        :return: json serialized SymbolSpreadModel object
        """
        return {"id": self.id, "symbol": self.symbol, "bid": self.bid, "ask": self.ask,
                "time": self.time}


# Create a fresh database
reset_database(db, populate_csv_initial_data=False)


def get_closest_timestamp_entry(query_timestamp, symbol=None):
    if symbol is None:
        results = SymbolSpreadModel.query.all()
    else:
        results = SymbolSpreadModel.query.filter_by(symbol=symbol)

    first_greater_timestamp = results.filter(
        query_timestamp <= SymbolSpreadModel.time
    ).order_by(SymbolSpreadModel.time.asc()).first()
    first_smaller_timestamp = results.filter(
        query_timestamp > SymbolSpreadModel.time
    ).order_by(SymbolSpreadModel.time.desc()).first()

    if not first_greater_timestamp and not first_smaller_timestamp:
        return {"message": f"Error - Unable to find any matching entries for timestamp: "
                           f"{query_timestamp}"}

    greater_timestamp_diff = first_greater_timestamp.time - query_timestamp \
        if first_greater_timestamp else np.inf

    smaller_timestamp_diff = query_timestamp - first_smaller_timestamp.time \
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
def get_items():
    if request.method == 'GET':
        try:
            symbol_spread_results = SymbolSpreadModel.query.all()
            results = [get_json_from_object(symbol_spread_entry, SYMBOL_SPREAD_TABLE_FIELDS)
                       for symbol_spread_entry in symbol_spread_results]

            return {"count": len(results), "symbol_spread_entries": results}
        except Exception as e:
            print(e)
            return {"message": "Failed in get_items()"}


# Example: 127.0.0.1/ETH/USD/bid?timestamp=1648995959
@app.route('/<path:symbol>/bid', methods=['GET'])
def get_items_with_query_timestamp_bid(symbol):
    try:
        if request.method == 'GET':
            if request.args:
                query_dict = request.args.to_dict()
                query_timestamp = float(query_dict.get("timestamp"))

                closest_entry = get_closest_timestamp_entry(
                    query_timestamp, symbol
                )
                if closest_entry is None:
                    return {"message": f"Error - Unable to find any matching entries for timestamp:"
                                       f"{query_timestamp}"}
                closest_entry_json = get_json_from_object(closest_entry,
                                                          ['bid', 'ask', 'time', 'symbol'])

                return {"message": f"Closest Bid price: {closest_entry_json['bid']} for entry:"
                                   f" {closest_entry_json}"}
            else:
                # Just get the latest bid
                latest_symbol_spread_entry = SymbolSpreadModel.query.all().\
                    order_by(SymbolSpreadModel.time.desc()).first()
                latest_result_json = get_json_from_object(latest_symbol_spread_entry,
                                                          SYMBOL_SPREAD_TABLE_FIELDS)
                latest_bid = latest_symbol_spread_entry.bid
                return {"message": f"Closest Bid price: {latest_bid} for"
                                   f" entry: {latest_result_json}"}

    except Exception as e:
        print(e)
        return {"message": "Failed in get_items_with_query_timestamp_bid()"}


# Example: 127.0.0.1/ETH/USD/ask?timestamp=1648995959
@app.route('/<path:symbol>/ask', methods=['GET'])
def get_items_with_query_timestamp_ask(symbol):
    try:
        if request.method == 'GET':
            if request.args:
                query_dict = request.args.to_dict()
                query_timestamp = float(query_dict.get("timestamp"))

                closest_entry = get_closest_timestamp_entry(
                    query_timestamp, symbol
                )
                if closest_entry is None:
                    return {"message": f"Error - Unable to find any matching entries for timestamp:"
                                       f"{query_timestamp}"}
                closest_entry_json = get_json_from_object(closest_entry,
                                                          ['bid', 'ask', 'time', 'symbol'])

                return {"message": f"Closest Ask price: {closest_entry_json['ask']} for entry:"
                                   f" {closest_entry_json}"}
            else:
                # Just get the latest ask
                latest_symbol_spread_entry = SymbolSpreadModel.query.all().\
                    order_by(SymbolSpreadModel.time.desc()).first()
                latest_result_json = get_json_from_object(latest_symbol_spread_entry,
                                                          SYMBOL_SPREAD_TABLE_FIELDS)
                latest_ask = latest_symbol_spread_entry.ask
                return {"message": f"Closest Ask price: {latest_ask} for "
                                   f"entry: {latest_result_json}"}

    except Exception as e:
        print(e)
        return {"message": "Failed in get_items_with_query_timestamp_ask() - with query str"}


# Example: http://127.0.0.1/symbol_spread/11/
@app.route('/symbol_spread/<int:id>/', methods=['GET'])
def get_item_from_id(id):
    if request.method == 'GET':
        try:
            symbol_spread_entry = SymbolSpreadModel.query.get_or_404(id)
            result = get_json_from_object(symbol_spread_entry, SYMBOL_SPREAD_TABLE_FIELDS)
            return {"symbol_spread_entries": result}
        except Exception as e:
            print(e)
            return {"message": "Failed in get_item_from_id()"}


# Example: http://127.0.0.1/symbol_spread/SOL/USD/
@app.route('/symbol_spread/<path:symbol>/', methods=['GET'])
def get_items_from_symbol(symbol):
    if request.method == 'GET':
        try:
            symbol_spread_results = SymbolSpreadModel.query.filter_by(symbol=symbol)
            results = [get_json_from_object(symbol_spread_entry, SYMBOL_SPREAD_TABLE_FIELDS)
                       for symbol_spread_entry in symbol_spread_results]
            return {"count": len(results), "symbol_spread_entries": results}

        except Exception as e:
            print(e)
            return {"message": "Failed in get_items_from_symbol()"}


# Example: http://127.0.0.1/symbol_spread/2 - with delete
@app.route('/symbol_spread/<int:id>/', methods=['DELETE'])
def delete_item(id):
    if request.method == 'DELETE':
        try:
            db.session.query(SymbolSpreadModel).filter_by(id=id).delete()
            db.session.commit()
            return {"Success": f"Item {id} deleted"}
        except Exception as e:
            print(e)
            return {"message": "Failed in delete_item()"}


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
#                 body.get('time'),
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
