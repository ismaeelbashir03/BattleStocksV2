from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import random
import threading
import time
import uuid

"""
APP INIT
"""
app = Flask(__name__)
api = Api(app)

"""
GLOBAL VARS
"""
exchanges = {}
TICKS_PER_SECOND = 1

"""
ENDPOINTS
"""
class Config(Resource):
    def post(self, exchange_id):
        """
        POST request to set the configuration and start the market simulation for a specific exchange.

        Query parameters:
            - exchange_id: str

        Request body:
            - stocks: dict content: {'stock_name': {'price': float}}
            - users: dict content: ('user_id': {'assets': {'stock_name': int}, 'money': float})
            - ticks_per_news: int
            - stock_std: float
            - headline_min_impact: float
            - headline_max_impact: float
        """
        global exchanges
        
        config_data = request.json
        exchange_id = str(exchange_id)

        if exchange_id not in exchanges:
            exchanges[exchange_id] = {
                'config': {},
                'tick_count': 0,
                'STARTED': False,
                'lock': threading.Lock()
            }
        
        with exchanges[exchange_id]['lock']:
            exchanges[exchange_id]['config'].update(config_data)
            exchanges[exchange_id]['tick_count'] = 0
            exchanges[exchange_id]['STARTED'] = True
        
        start_simulation_thread(exchange_id)

        return jsonify({"message": f"Configuration updated and market simulation started for exchange {exchange_id}."})

class MarketData(Resource):
    def get(self, exchange_id):
        """
        GET request to get the current market data for a specific exchange.

        Query parameters:
            - exchange_id: str

        Response:
            - stocks: dict
        """
        global exchanges
        exchange_id = str(exchange_id)

        if exchange_id not in exchanges:
            return jsonify({"message": "Exchange not found."})

        with exchanges[exchange_id]['lock']:
            if not exchanges[exchange_id]['STARTED']:
                return jsonify({"message": "Market simulation not started."})
            return jsonify(exchanges[exchange_id]['config']['stocks'])

class Orders(Resource):
    def post(self, exchange_id, user_id):
        """
        POST request to place an order for a specific exchange.

        Query parameters:
            - exchange_id: str
            - user_id: str

        Request body:
            - stock: str
            - quantity: int
            - type: str (buy/sell)
        """
        global exchanges
        exchange_id = str(exchange_id)
        
        order_data = request.json

        if exchange_id not in exchanges:
            return jsonify({"message": "Exchange not found."})

        with exchanges[exchange_id]['lock']:
            if not exchanges[exchange_id]['STARTED']:
                return jsonify({"message": "Market simulation not started."})

            config = exchanges[exchange_id]['config']
            
            if user_id not in config['users']:
                return jsonify({"message": "User not found."})
            
            user = config['users'][user_id]
            stock = order_data['stock']
            quantity = order_data['quantity']
            price = config['stocks'][stock]['price']

            if order_data['type'] == 'buy' and user['money'] >= quantity * price:
                user['money'] -= quantity * price
                user['assets'][stock] = user['assets'].get(stock, 0) + quantity
            
            elif order_data['type'] == 'sell' and user['assets'].get(stock, 0) >= quantity:
                user['money'] += quantity * price
                user['assets'][stock] -= quantity
            
            config['users'][user_id] = user

        return jsonify(user)

class News(Resource):
    def post(self, exchange_id):
        """
        POST request to set the news headlines for a specific exchange.

        Query parameters:
            - exchange_id: str

        Request body:
            - headline: dict
        """
        global exchanges
        exchange_id = str(exchange_id)

        if exchange_id not in exchanges:
            return jsonify({"message": "Exchange not found."})

        headline = request.json["headline"]

        with exchanges[exchange_id]['lock']:
            exchanges[exchange_id]['config']['news_headlines'].append(headline)

        return jsonify({"message": f"News headline published for exchange {exchange_id}. Market will be affected."})

api.add_resource(News, '/<string:exchange_id>/add-news')
api.add_resource(Config, '/<string:exchange_id>/start-server')
api.add_resource(MarketData, '/<string:exchange_id>/market-data')
api.add_resource(Orders, '/<string:exchange_id>/order/<string:user_id>')

"""
SIMULATION
"""
def simulate_market(exchange_id):
    global exchanges
    
    while True:
        time.sleep(TICKS_PER_SECOND)

        with exchanges[exchange_id]['lock']:
            if not exchanges[exchange_id]['STARTED']:
                continue

            exchanges[exchange_id]['tick_count'] += 1
            config = exchanges[exchange_id]['config']

            for stock in config['stocks']:
                config['stocks'][stock]['price'] += random.gauss(0, config['stock_std'])
            
            if config['news_headlines']:
                headline = config['news_headlines'].pop(0)
                stock = headline['stock']
                sentiment = headline['sentiment']
                impact = random.uniform(config['headline_min_impact'], config['headline_max_impact'])
                config['stocks'][stock]['price'] *= impact if sentiment == 'up' else 1/impact

def start_simulation_thread(exchange_id):
    thread = threading.Thread(target=simulate_market, args=(exchange_id,))
    thread.start()
    return thread

if __name__ == '__main__':
    app.run(debug=True, threaded=True)