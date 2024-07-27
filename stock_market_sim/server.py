from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import random
import threading
import time


"""
APP INIT
"""
app = Flask(__name__)
api = Api(app)


"""
GLOBAL VARS
"""
config = {
    'stocks': {},
    'users': {},
    "stock_std": 0.5,
    "headline_min_impact": 1.1,
    "headline_max_impact": 5,
    'news_headlines': []
}
STARTED = False
TICKS_PER_SECOND = 1
tick_count = 0
lock = threading.Lock()


"""
ENDPOINTS
"""
class Config(Resource):
    def post(self):
        """
        POST request to set the configuration and start the market simulation.

        Request body:
            - stocks: dict content: {'stock_name': {'price': float}}
            - users: dict content: ('user_id': {'assets': {'stock_name': int}, 'money': float})
            - ticks_per_news: int
            - stock_std: float
            - headline_min_impact: float
            - headline_max_impact: float
        """
        global config, tick_count, STARTED
        
        config_data = request.json

        # set news_headlines if not present
        if "news_headlines" not in config_data:
            config_data['news_headlines'] = []
        
        with lock:
            config.update(config_data)
            tick_count = 0
            STARTED = True

        return jsonify({"message": "Configuration updated and market simulation started."})

class MarketData(Resource):
    def get(self):
        """
        GET request to get the current market data.

        Response:
            - stocks: dict
        """
        global STARTED

        with lock:
            if not STARTED:
                return jsonify({"message": "Market simulation not started."})
            return jsonify(config['stocks'])

class Orders(Resource):
    def post(self, user_id):
        """
        POST request to place an order.

        Request body:
            - stock: str
            - quantity: int
            - type: str (buy/sell)
        """
        global STARTED
        
        order_data = request.json

        with lock:
            if not STARTED:
                return jsonify({"message": "Market simulation not started."})

            user = config['users'].get(user_id, {'assets': {}, 'money': 10000})
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
    def post(self):
        """
        POST request to set the news headlines.

        Request body:
            - headline: dict
        """
        global config

        headline = request.json["headline"]

        with lock:
            config['news_headlines'].append(headline)

        return jsonify({"message": "News headline published. Market will be affected."})

api.add_resource(News, '/add-news')
api.add_resource(Config, '/start-server')
api.add_resource(MarketData, '/market-data')
api.add_resource(Orders, '/order/<string:user_id>')


"""
SIMULATION
"""
def simulate_market():
    global tick_count, STARTED
    
    # game loop
    while True:

        time.sleep(TICKS_PER_SECOND)

        with lock:
            
            # config not set yet
            if not STARTED:
                continue
            
            tick_count += 1

            # TODO: add cooler market simulation (maybe use trade bot agents??)
            for stock in config['stocks']:
                config['stocks'][stock]['price'] += random.uniform(-config['stock_std'], config['stock_std'])
            
            # affect market with news
            if config['news_headlines']:
                headline = config['news_headlines'].pop(0)
                stock = headline['stock']
                sentiment = headline['sentiment']
                impact = random.uniform(config['headline_min_impact'], config['headline_max_impact'])
                config['stocks'][stock]['price'] *= impact if sentiment == 'up' else 1/impact
                

if __name__ == '__main__':
    market_thread = threading.Thread(target=simulate_market)
    market_thread.start()
    app.run(debug=True)