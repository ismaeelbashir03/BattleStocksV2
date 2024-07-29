from collections import deque
import string
from typing import List
from flask import Flask, request, jsonify
from flask_restx import fields, Resource, Api
import random
import threading
import time
import uuid


'''
APP INIT
'''
app = Flask(__name__)
api = Api(app)


'''
GLOBAL VARS
'''
exchanges = {}
trade_requests = {}
SECONDS_PER_TICK = 1
THREAD_TIMEOUT = 60
CODE_LENGTH = 6
NEWS_IMPACT_DURATION = 10
DIFFICULTY_MAP = {
    1: {
        'stock_std': 0.5,
        'headline_min_impact': 2,
        'headline_max_impact': 2
    },
    2: {
        'stock_std': 0.65,
        'headline_min_impact': 1.5,
        'headline_max_impact': 2,
    },
    3: {
        'stock_std': 0.8,
        'headline_min_impact': 1,
        'headline_max_impact': 2,
    },
    4: {
        'stock_std': 1,
        'headline_min_impact': 0.85,
        'headline_max_impact': 2,
    },
    5: {
        'stock_std': 2,
        'headline_min_impact': 0.8,
        'headline_max_impact': 2,
    }
}
STARTING_PRICE_RANGE = range(50, 150)
STARTING_CASH = 10000


'''
MODELS
'''
config_model = api.model('ConfigBody', {
    'stocks': fields.List(fields.String, required=True, description='List of stocks to include in the simulation.'),
    'difficulty': fields.Integer(required=True, description='Difficulty level of the simulation (1 to 5 inclusive).'),
})

news_model = api.model('NewsBody', {
    'stock': fields.String(required=True, description='Stock to affect.'),
    'impact': fields.String(required=True, description='Sentiment of the news headline (up or down).'),
})

order_model = api.model('Order', {
    'userId': fields.String,
    'stock': fields.String,
    'quantity': fields.Integer,
    'type': fields.String
    })

connect_model = api.model('ConnectBody', {
    'name': fields.String(required=True, description='Name of the user connecting to the exchange.'),
})

trade_request_model = api.model('TradeRequest', {
    'from_user': fields.String(required=True, description='User ID of the sender.'),
    'to_user': fields.String(required=True, description='User ID of the receiver.'),
    'stock': fields.String(required=True, description='Stock to be traded.'),
    'quantity': fields.Integer(required=True, description='Quantity of stock to be traded.'),
    'price': fields.Float(required=True, description='Proposed price per stock.'),
    'type': fields.String(required=True, description='Type of trade (buy or sell).')
})

trade_response_model = api.model('TradeResponse', {
    'request_id': fields.String(required=True, description='ID of the trade request.'),
    'response': fields.String(required=True, description='Response to the trade request (accept or decline).')
})

'''
HOST ENDPOINTS
'''
@api.route('/init-server', methods=['GET'])
@api.response(200, 'Success')
class Init(Resource):
    def get(self):
        global exchanges
        
        # get unique exchange id
        exchange_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(CODE_LENGTH))
        while exchange_id in exchanges:
            exchange_id = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(CODE_LENGTH))

        exchanges[exchange_id] = {
            'settings': {},
            'stocks': {},
            'news_headlines': deque(),
            'users': {},
            'tick_count': 0,
            'STARTED': False,
            'kill': False,
            'lock': threading.Lock()
        }

        response = jsonify({'exchange_id': exchange_id, 'message': f'Created Exchange {exchange_id}.'})
        response.status_code = 200
        return response

@api.route('/<string:exchange_id>/start-server', methods=['POST'])
@api.expect(config_model)
@api.response(200, 'Success')
class Start(Resource):
    def post(self, exchange_id):
        global exchanges
        
        config_data = request.json
        settings = DIFFICULTY_MAP[config_data['difficulty']]
        stocks = {stock: random.choice(STARTING_PRICE_RANGE) for stock in config_data['stocks']}
        
        with exchanges[exchange_id]['lock']:
            exchanges[exchange_id]['settings'].update(settings)
            exchanges[exchange_id]['stocks'].update(stocks)
            exchanges[exchange_id]['tick_count'] = 0
            exchanges[exchange_id]['STARTED'] = True
        
        start_simulation_thread(exchange_id, THREAD_TIMEOUT)

        response = jsonify({'exchange_id': exchange_id, 'message': f'Configuration updated and market simulation started for exchange {exchange_id}.'})
        response.status_code = 200
        return response

@api.route('/<string:exchange_id>/market-data', methods=['GET'])
@api.response(200, 'Success')
@api.response(400, 'Validation Error')
class MarketData(Resource):
    def get(self, exchange_id):
        global exchanges
        exchange_id = str(exchange_id)

        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response

        with exchanges[exchange_id]['lock']:
            if not exchanges[exchange_id]['STARTED']:
                response = jsonify({'message': 'Market simulation not started.'})
                response.status_code = 400
                return response
            
            account_details = {userId: details for userId, details in exchanges[exchange_id]['users'].items()}
            prices = exchanges[exchange_id]['stocks']

            response = jsonify({'details': account_details, 'prices': prices})
            response.status_code = 200
            return response

@api.route('/<string:exchange_id>/add-news', methods=['POST'])
@api.expect(news_model)
@api.response(200, 'Success')
@api.response(400, 'Validation Error')
class News(Resource):
    def post(self, exchange_id):
        global exchanges

        exchange_id = str(exchange_id)
        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response

        headline = {'stock': request.json['stock'], 'sentiment': request.json['impact']}

        with exchanges[exchange_id]['lock']:
            exchanges[exchange_id]['news_headlines'].append(headline)

        response = jsonify({'message': f'News headline published for exchange {exchange_id}. Market will be affected.'})
        response.status_code = 200
        return response

@api.route('/<string:exchange_id>/pause', methods=['GET'])
@api.response(200, 'Success')
@api.response(400, 'Validation Error')
class Pause(Resource):
    def get(self, exchange_id):
        global exchanges

        exchange_id = str(exchange_id)
        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response

        with exchanges[exchange_id]['lock']:
            exchanges[exchange_id]['STARTED'] = False

        response = jsonify({'message': f'Market simulation paused for exchange {exchange_id}.'})
        response.status_code = 200
        return response

@api.route('/<string:exchange_id>/resume', methods=['GET'])
@api.response(200, 'Success')
@api.response(400, 'Validation Error')
class Resume(Resource):
    def get(self, exchange_id):
        global exchanges

        exchange_id = str(exchange_id)
        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response

        with exchanges[exchange_id]['lock']:
            exchanges[exchange_id]['STARTED'] = True

        response = jsonify({'message': f'Market simulation resumed for exchange {exchange_id}.'})
        response.status_code = 200
        return response
    
@api.route('/<string:exchange_id>/stop', methods=['GET'])
@api.response(200, 'Success')
@api.response(400, 'Validation Error')
class Stop(Resource):
    def get(self, exchange_id):
        global exchanges

        exchange_id = str(exchange_id)
        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response

        with exchanges[exchange_id]['lock']:
            exchanges[exchange_id]['kill'] = True

        response = jsonify({'message': f'Market simulation stopped for exchange {exchange_id}.'})
        response.status_code = 200
        return response
    

'''
CLIENT ENDPOINTS
'''
@api.route('/<string:exchange_id>/connect', methods=['POST'])
@api.expect(connect_model)
@api.response(200, 'Success')
@api.response(400, 'Validation Error')
class Connect(Resource):
    def post(self, exchange_id):
        global exchanges

        userId = request.json['name']
        
        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response
        
        if userId in exchanges[exchange_id]['users']:
            response = jsonify({'message': 'Username taken.'})
            response.status_code = 400
            return response
        
        exchanges[exchange_id]['users'].update({userId: {'cash': STARTING_CASH, 'assets': {}, 'value': STARTING_CASH}})

        response = jsonify({'message': f"User {userId} connected to exchange {exchange_id}."})
        response.status_code = 200
        return response

@api.route('/<string:exchange_id>/order', methods=['POST'])
@api.expect(order_model)
@api.response(200, 'Success')
@api.response(400, 'Validation Error')
class Orders(Resource):
    def post(self, exchange_id):
        global exchanges

        exchange_id = str(exchange_id)
        order_data = request.json
        user_id = order_data['userId']

        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response

        with exchanges[exchange_id]['lock']:
            if not exchanges[exchange_id]['STARTED']:
                response = jsonify({'message': 'Market simulation not started.'})
                response.status_code = 400
                return response
            
            if user_id not in exchanges[exchange_id]['users']:
                response = jsonify({'message': 'User not found.'})
                response.status_code = 400
                return response
            
            user = exchanges[exchange_id]['users'][user_id]
            stock = order_data['stock']
            quantity = order_data['quantity']
            price = exchanges[exchange_id]['stocks'][stock]

            if order_data['type'] == 'buy' and user['cash'] >= quantity * price:
                user['cash'] -= quantity * price
                user['assets'][stock] = user['assets'].get(stock, 0) + quantity
            
            elif order_data['type'] == 'sell' and user['assets'].get(stock, 0) >= quantity:
                user['cash'] += quantity * price
                user['assets'][stock] -= quantity
            else:
                response = jsonify({'message': 'Order cannot be executed due to insufficient funds or stocks.'})
                response.status_code = 400
                return response
            
            exchanges[exchange_id]['users'][user_id] = user
        
        response = jsonify({'message': f'Order executed: {order_data["type"]} {quantity} {stock} for {price}.'})
        response.status_code = 200
        return response

@api.route('/<string:exchange_id>/trade-request', methods=['POST'])
@api.expect(trade_request_model)
@api.response(200, 'Success')
@api.response(400, 'Validation Error')
class TradeRequest(Resource):
    def post(self, exchange_id):
        global exchanges, trade_requests

        exchange_id = str(exchange_id)
        request_data = request.json

        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response

        from_user = request_data['from_user']
        to_user = request_data['to_user']
        if from_user not in exchanges[exchange_id]['users'] or to_user not in exchanges[exchange_id]['users']:
            response = jsonify({'message': 'User not found.'})
            response.status_code = 400
            return response

        request_id = str(uuid.uuid4())
        trade_requests[request_id] = {
            'exchange_id': exchange_id,
            'from_user': from_user,
            'to_user': to_user,
            'stock': request_data['stock'],
            'quantity': request_data['quantity'],
            'price': request_data['price'],
            'type': request_data['type'],
            'status': 'pending'
        }

        response = jsonify({'message': 'Trade request sent.', 'request_id': request_id})
        response.status_code = 200
        return response

@api.route('/<string:exchange_id>/inbox/<string:user_id>', methods=['GET'])
@api.response(200, 'Success')
@api.response(400, 'Validation Error')
class Inbox(Resource):
    def get(self, exchange_id, user_id):
        global trade_requests

        exchange_id = str(exchange_id)
        user_id = str(user_id)

        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response

        if user_id not in exchanges[exchange_id]['users']:
            response = jsonify({'message': 'User not found.'})
            response.status_code = 400
            return response

        user_inbox = {req_id: req for req_id, req in trade_requests.items() if req['to_user'] == user_id and req['exchange_id'] == exchange_id and req['status'] == 'pending'}

        response = jsonify({'inbox': user_inbox})
        response.status_code = 200
        return response
    
@api.route('/<string:exchange_id>/trade-response', methods=['POST'])
@api.expect(trade_response_model)
@api.response(200, 'Success')
@api.response(400, 'Validation Error')
class TradeResponse(Resource):
    def post(self, exchange_id):
        global exchanges, trade_requests

        exchange_id = str(exchange_id)
        response_data = request.json

        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response

        request_id = response_data['request_id']

        if request_id not in trade_requests:
            response = jsonify({'message': 'Trade request not found.'})
            response.status_code = 400
            return response

        trade_request = trade_requests[request_id]
        if trade_request['exchange_id'] != exchange_id:
            response = jsonify({'message': 'Trade request does not belong to this exchange.'})
            response.status_code = 400
            return response

        if response_data['response'] == 'accept':
            from_user = trade_request['from_user']
            to_user = trade_request['to_user']
            stock = trade_request['stock']
            quantity = trade_request['quantity']
            price = trade_request['price']
            type = trade_request['type']

            with exchanges[exchange_id]['lock']:
                if type == 'sell':
                    if exchanges[exchange_id]['users'][to_user]['cash'] >= quantity * price and exchanges[exchange_id]['users'][from_user]['assets'].get(stock, 0) >= quantity:
                        exchanges[exchange_id]['users'][to_user]['cash'] -= quantity * price
                        exchanges[exchange_id]['users'][to_user]['assets'][stock] = exchanges[exchange_id]['users'][to_user]['assets'].get(stock, 0) + quantity

                        exchanges[exchange_id]['users'][from_user]['cash'] += quantity * price
                        exchanges[exchange_id]['users'][from_user]['assets'][stock] -= quantity

                        trade_request['status'] = 'accepted'
                        response = jsonify({'message': 'Trade request accepted.'})
                        response.status_code = 200
                        return response
                    else:
                        response = jsonify({'message': 'Trade cannot be completed due to insufficient funds or stocks.'})
                        response.status_code = 400
                        return response
                else:
                    if exchanges[exchange_id]['users'][from_user]['cash'] >= quantity * price and exchanges[exchange_id]['users'][to_user]['assets'].get(stock, 0) >= quantity:
                        exchanges[exchange_id]['users'][from_user]['cash'] -= quantity * price
                        exchanges[exchange_id]['users'][from_user]['assets'][stock] = exchanges[exchange_id]['users'][from_user]['assets'].get(stock, 0) + quantity

                        exchanges[exchange_id]['users'][to_user]['cash'] += quantity * price
                        exchanges[exchange_id]['users'][to_user]['assets'][stock] -= quantity

                        trade_request['status'] = 'accepted'
                        response = jsonify({'message': 'Trade request accepted.'})
                        response.status_code = 200
                        return response
                    else:
                        response = jsonify({'message': 'Trade cannot be completed due to insufficient funds or stocks.'})
                        response.status_code = 400
                        return response

        trade_request['status'] = 'declined'
        response = jsonify({'message': 'Trade request declined.'})
        response.status_code = 200
        return response
    
@api.route('/<string:exchange_id>/get-users', methods=['GET'])
@api.response(200, 'Success')
@api.response(400, 'Validation Error')
class GetUsers(Resource):
    def get(self, exchange_id):
        global exchanges

        exchange_id = str(exchange_id)

        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response

        with exchanges[exchange_id]['lock']:
            
            users = {"users": [user for user in exchanges[exchange_id]['users']]}

            response = jsonify(users)
            response.status_code = 200
            return response

'''
ROUTES
'''
api.add_resource(Init, '/init-server')
api.add_resource(Pause, '/<string:exchange_id>/pause')
api.add_resource(Resume, '/<string:exchange_id>/resume')
api.add_resource(Stop, '/<string:exchange_id>/stop')
api.add_resource(Start, '/<string:exchange_id>/start-server')
api.add_resource(News, '/<string:exchange_id>/add-news')
api.add_resource(MarketData, '/<string:exchange_id>/market-data')
api.add_resource(Connect, '/<string:exchange_id>/connect')
api.add_resource(Orders, '/<string:exchange_id>/order')
api.add_resource(TradeRequest, '/<string:exchange_id>/trade-request')
api.add_resource(Inbox, '/<string:exchange_id>/inbox/<string:user_id>')
api.add_resource(TradeResponse, '/<string:exchange_id>/trade-response')


'''
SIMULATION
'''
class DecayEffect:
    """
    Class to represent a decay effect of a news headline on a stock.
    """
    def __init__(self, stock: str, total_impact: float, duration: int, sentiment: str):
        """
        :param stock: The stock symbol.
        :param total_impact: The total impact of the news headline.
        :param duration: The duration of the decay effect in ticks.
        :param sentiment: The sentiment of the news headline.
        """
        self.stock = stock
        self.total_impact = total_impact
        self.remaining_ticks = duration
        self.sentiment = sentiment

    def decay(self, stock_price: float) -> float:
        """
        Decay the impact of the news headline on the stock price.
        :param stock_price: The current stock price.
        :return: The new stock price after the decay effect.
        """

        per_tick_impact = (self.total_impact - 1) / self.remaining_ticks
        self.remaining_ticks -= 1

        if self.sentiment == 'up':
            return stock_price * (1 + per_tick_impact)
        else:
            return stock_price / (1 + per_tick_impact)

def simulate_market(exchange_id: str, timeout: int):
    """
    Simulate the stock market for a given exchange.
    :param exchange_id: The exchange ID.
    :param timeout: Timeout for the simulation in minutes.
    """
    global exchanges

    decay_effects: List[DecayEffect] = []

    while True:
        with exchanges[exchange_id]['lock']:
            if not exchanges[exchange_id]['STARTED']:
                time.sleep(SECONDS_PER_TICK)
                continue

            if SECONDS_PER_TICK * exchanges[exchange_id]['tick_count'] >= timeout * 60 or exchanges[exchange_id]['kill']:
                exchanges[exchange_id]['STARTED'] = False
                break

            config = exchanges[exchange_id]

            if len(decay_effects) == 0: # only update stock prices randomly if there are no decay effects
                for stock in config['stocks']:
                    config['stocks'][stock] += random.gauss(0, config['settings']['stock_std'])
            
            for effect in decay_effects[:]:
                config['stocks'][effect.stock] = effect.decay(config['stocks'][effect.stock])
                if effect.remaining_ticks <= 0:
                    decay_effects.remove(effect)

            if config['news_headlines']:
                headline = config['news_headlines'].popleft()
                stock = headline['stock']
                sentiment = headline['sentiment']
                impact = random.uniform(config['settings']['headline_min_impact'], config['settings']['headline_max_impact'])
                decay_effects.append(DecayEffect(stock, impact, NEWS_IMPACT_DURATION, sentiment))
            
            for user_id, user in config['users'].items():
                user['value'] = user['cash']
                for stock, quantity in user['assets'].items():
                    user['value'] += config['stocks'][stock] * quantity
                config['users'][user_id] = user
            
            exchanges[exchange_id]['tick_count'] += 1
            time.sleep(SECONDS_PER_TICK)
        
    # delete exchange if simulation is over
    del exchanges[exchange_id]

def start_simulation_thread(exchange_id: str, timeout: int) -> threading.Thread:
    """
    Start a thread to simulate the stock market for a given exchange.
    :param exchange_id: The exchange ID.
    :param timeout: Timeout for the simulation in minutes.
    :return: The thread object.
    """
    thread = threading.Thread(target=simulate_market, args=(exchange_id, timeout,))
    thread.start()
    return thread

if __name__ == '__main__':
    app.run(debug=True, threaded=True)