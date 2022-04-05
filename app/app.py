import os

from flask import request, jsonify, make_response, Flask
# from __init__ import create_app
import pandas as pd
from flask_sqlalchemy import SQLAlchemy

# from app.models import BidAskModel

# app = create_app()
app = Flask(__name__)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)

TABLE_NAME = "bid_ask"

from sqlalchemy import Column, Float, Integer, String


# from app.app import TABLE_NAME, db


class BidAskModel(db.Model):
    """
    Defines the bid_ask model
    """
    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True, index=True)
    bid = Column(Float, nullable=True)
    ask = Column(Float, nullable=True)
    bid_size = Column(Float, nullable=True)
    ask_size = Column(Float, nullable=True)
    last = Column(Float, nullable=True)
    time = Column(Float, nullable=True)
    symbol = Column(String, nullable=True)
    datetime = Column(String, nullable=True)

    def __init__(self, bid, ask, bid_size, ask_size, last, time, symbol, datetime):
        # self.id = id TODO: Check if this auto increments for us
        self.bid = bid
        self.ask = ask
        self.bid_size = bid_size
        self.askSize = ask_size
        self.last = last
        self.time = time
        self.symbol = symbol
        self.datetime = datetime

    # TODO: Find out of this does anything?
    #     def create(self):
    #         db.session.add(self)
    #         db.session.commit()
    #         return self

    @property
    def serialize(self):
        """
        Return item in serializeable format
        """
        return {"id": self.id, "symbol": self.symbol, "bid": self.bid, "ask": self.ask,
                "time": self.time}


db.drop_all()
db.create_all()
db.session.commit()

add_data_manually = False
if add_data_manually:
    with open("bid_ask_data_interval_1_1648995959.7916217-1648995976.8139045.csv", 'r') as file:
        data_df = pd.read_csv(file)
    data_df.to_sql(TABLE_NAME, con=db.engine, index=False, index_label='id', if_exists='replace')

# @app.errorhandler(404)
# def showMessage(error=None):
#     message = {
#         'status': 404,
#         'message': 'Error: Record not found: ' + request.url,
#     }
#     response = jsonify(message)
#     response.status_code = 404
#     return response





@app.route('/')
def home():
    return make_response(jsonify({'message': 'Welcome to home page'}), 200)


# TODO:
"""
@app.route('/bid_ask/<ticker_name>/bid', methods=['GET'])
@app.route('/bid_ask/<ticker_name>/ask', methods=['GET'])
"""


@app.route('/bid_ask', methods=['GET'])
def get_items():
    try:
        if request.method == 'GET':
            bid_ask_model = BidAskModel.query.all()
            results = [bid_ask_entry.serialize()
                       for bid_ask_entry in bid_ask_model]

            return {"count": len(results), "bid_ask_entries": results}
    except Exception as e:
        print(e)
        return {"message": request}


@app.route('/bid_ask/<int:id>/', methods=['GET'])
def get_item_from_id(id):
    bid_ask_results = BidAskModel.query.get_or_404(id)
    result = {
        "id": bid_ask_results.id,
        "ask": bid_ask_results.ask,
        "bid": bid_ask_results.bid
    }
    return {"bid_ask_entries": result}


# Not working
@app.route('/bid_ask/<path:symbol>/', methods=['GET'])
def get_items_from_symbol(symbol):
    bid_ask_results = BidAskModel.query.filter_by(symbol=symbol)
    results = [{"symbol": bid_ask_result["symbol"], "id": bid_ask_result["id"]}
               for bid_ask_result in bid_ask_results]
    return {"bid_ask_entries": results}


@app.route('/bid_ask/<int:id>/', methods=['DELETE'])
def delete_item(id):
    db.session.query(BidAskModel).filter_by(id=id).delete()
    db.session.commit()
    return {"Success": f"Item {id} deleted"}


# TODO: Not working, might have to do with ID col?
@app.route('/bid_ask/', methods=['POST'])
def create_item():
    try:
        body = request.get_json()
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


# TODO: Try this post
# @app.route('/products', methods=['POST'])
# def create_product():
#     data = request.get_json()
#     product_schema = ProductSchema()
#     product = product_schema.load(data)
#     result = product_schema.dump(product.create())
#     return make_response(jsonify({"product": result}), 200)


# TODO: Not working - getting 405
@app.route('/bid_ask/<int:id>/', methods=['PUT'])
def update_item(id):
    body = request.get_json()
    db.session.query(BidAskModel).filter_by(id=id).update(
        dict(title=body['title'], content=body['content']))
    db.session.commit()

    return {"Success": f"Item Updated"}


# TODO: Try this return
#     return make_response(jsonify({"product": product}))


# TODO: Not working - getting 405
@app.route('/bid_ask2/<int:id>/', methods=['PUT'])
def update_item_ask(id):
    body = request.get_json()
    entry = BidAskModel.query.filter_by(id=id).first_or_404()
    entry.ask = body.get('ask', entry.ask)
    db.session.commit()

    return {"Success": f"Item updated: {entry.serialize()}"}
