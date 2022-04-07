import os

from flask import request, jsonify, make_response, Flask
import pandas as pd
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)
# TODO find out how to spawn a table and use the .add() functionality
# db_session = sessionmaker(engine) - ?
# db_session = db.session           - ?

TABLE_NAME = "bid_ask"

from sqlalchemy import Column, Float, Integer, String

BID_ASK_FIELDS = ['bid', 'ask', 'bid_size', 'ask_size', 'last', 'time', 'symbol', 'datetime']


class BidAskModel(db.Model):
    """
    Defines the bid_ask model
    """
    __tablename__ = TABLE_NAME

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
        self.bid = bid
        self.ask = ask
        self.bid_size = bid_size
        self.askSize = ask_size
        self.last = last
        self.time = time
        self.symbol = symbol
        self.datetime = datetime

    def to_json(self):
        """
        Return item in serializeable format
        """
        return {"id": self.id, "symbol": self.symbol, "bid": self.bid, "ask": self.ask,
                "time": self.time}


db.drop_all()
db.create_all()
db.session.commit()


def add_and_commit_new_entry(db, entry):
    new_entry = BidAskModel(**entry)
    db.session.add(new_entry)
    db.commit()


add_csv_data = False
if add_csv_data:
    with open("bid_ask_initial_data.csv", 'r') as file:
        data_df = pd.read_csv(file)
        for i, row in data_df.iterrows():
            del row["id"]
            print("row", row)
            add_and_commit_new_entry(db, row)

    data_df.to_sql(TABLE_NAME, con=db.engine, index=False, index_label='id', if_exists='replace')

# TODO:
"""
@app.route('/bid_ask/<ticker_name>/bid', methods=['GET'])
@app.route('/bid_ask/<ticker_name>/ask', methods=['GET'])

Use make_response through out

Add doc strings
"""

@app.route('/')
def home():
    return make_response(jsonify({'message': 'Welcome to home page'}), 200)


def get_json_from_object(bid_ask_entry, list_of_columns):
    bid_ask_entry_dict = bid_ask_entry.__dict__
    object_dict = {}
    for col in list_of_columns:
        object_dict.update({col: bid_ask_entry_dict.get(col)})
    return object_dict


@app.route('/bid_ask', methods=['GET'])
def get_items():
    if request.method == 'GET':
        try:
            bid_ask_results = BidAskModel.query.all()
            results = [get_json_from_object(bid_ask_entry, BID_ASK_FIELDS)
                       for bid_ask_entry in bid_ask_results]

            return {"count": len(results), "bid_ask_entries": results}
        except Exception as e:
            print(e)
            return {"message": "Failed in get_items()"}


@app.route('/bid_ask/<int:id>/', methods=['GET'])
def get_item_from_id(id):
    if request.method == 'GET':
        try:
            bid_ask_entry = BidAskModel.query.get_or_404(id)
            result = get_json_from_object(bid_ask_entry, BID_ASK_FIELDS)
            return {"bid_ask_entries": result}
        except Exception as e:
            print(e)
            return {"message": "Failed in get_item_from_id()"}


@app.route('/bid_ask_symbol/<path:symbol>/', methods=['GET'])
def get_items_from_symbol(symbol):
    if request.method == 'GET':
        try:
            bid_ask_results = BidAskModel.query.filter_by(symbol=symbol)
            results = [get_json_from_object(bid_ask_entry, BID_ASK_FIELDS)
                       for bid_ask_entry in bid_ask_results]
            return {"bid_ask_entries": results}

        except Exception as e:
            print(e)
            return {"message": "Failed in get_items_from_symbol()"}


@app.route('/bid_ask/<int:id>/', methods=['DELETE'])
def delete_item(id):
    if request.method == 'DELETE':
        try:
            db.session.query(BidAskModel).filter_by(id=id).delete()
            db.session.commit()
            return {"Success": f"Item {id} deleted"}
        except Exception as e:
            print(e)
            return {"message": "Failed in delete_item()"}


# Not working
@app.route('/bid_ask', methods=['POST'])
def create_item():
    if request.method == 'POST':
        try:
            body = request.get_json(force=True)
            body = dict(body)
            # TODO: Add some assertion testing here on the actual data input
            model_entry = BidAskModel(
                body.get('bid'),
                body.get('ask'),
                body.get('bid_size'),
                body.get('ask_size'),
                body.get('last'),
                body.get('time'),
                body.get('symbol'),
                body.get('datetime'),
            )
            db.session.add(model_entry)
            db.session.commit()
            return {"Success": f"Item created: {body}"}
        except Exception as e:
            print(e)
            return {"message": "Failed in create_item()"}


@app.route('/bid_ask/<int:id>/', methods=['PUT'])
def update_item(id):
    try:
        body = request.get_json()
        db.session.query(BidAskModel).filter_by(id=id).update(
            dict(bid=body['bid'], ask=body['ask'])
        )
        db.session.commit()
        return {"Success": f"Item Updated"}
    except Exception as e:
        print(e)
        return {"message": "Failed in update_item()"}


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
