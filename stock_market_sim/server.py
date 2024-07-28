import string
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
TICKS_PER_SECOND = 1
CODE_LENGTH = 6
DIFFICULTY_MAP = {
    1: {
        'stock_std': 0.5,
        'headline_min_impact': 3,
        'headline_max_impact': 3
    },
    2: {
        'stock_std': 0.65,
        'headline_min_impact': 2,
        'headline_max_impact': 3,
    },
    3: {
        'stock_std': 0.8,
        'headline_min_impact': 1,
        'headline_max_impact': 3,
    },
    4: {
        'stock_std': 1,
        'headline_min_impact': 0.95,
        'headline_max_impact': 2,
    },
    5: {
        'stock_std': 2,
        'headline_min_impact': 0.9,
        'headline_max_impact': 1.5,
    }
}
STARTING_PRICE_RANGE = range(50, 150)
STARTING_CASH = 1000


'''
MODELS
'''
config_model = api.model('ConfigBody', {
    'stocks': fields.List(fields.String, required=True, description='List of stocks to include in the simulation.'),
    'duration': fields.Integer(required=True, description='Duration of the simulation in minutes.'),
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


'''
HOST ENDPOINTS
'''
@api.route('/start-server', methods=['POST'])
@api.expect(config_model)
@api.response(200, 'Success')
class Config(Resource):
    def post(self):
        global exchanges
        
        config_data = request.json
        duration = config_data['duration']
        settings = DIFFICULTY_MAP[config_data['difficulty']]
        stocks = {stock: random.choice(STARTING_PRICE_RANGE) for stock in config_data['stocks']}
        
        exchange_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(CODE_LENGTH))

        while exchange_id in exchanges:
            exchange_id = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(CODE_LENGTH))

        if exchange_id not in exchanges:
            exchanges[exchange_id] = {
                'settings': {},
                'stocks': {},
                'news_headlines': [],
                'users': {},
                'tick_count': 0,
                'STARTED': False,
                'lock': threading.Lock()
            }
        
        with exchanges[exchange_id]['lock']:
            exchanges[exchange_id]['settings'].update(settings)
            exchanges[exchange_id]['stocks'].update(stocks)
            exchanges[exchange_id]['tick_count'] = 0
            exchanges[exchange_id]['STARTED'] = True
        
        start_simulation_thread(exchange_id, duration)

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
            
            account_details = [details for details in exchanges[exchange_id]['users'].values()]
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

        name = request.json['name']
        userId = str(uuid.uuid4())
        exchanges[exchange_id]['users'].update({userId: {'name': name, 'cash': STARTING_CASH, 'assets': {}, 'value': STARTING_CASH}})

        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response

        response = jsonify({'userId': userId})
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
            
            exchanges[exchange_id]['users'][user_id] = user

        response = jsonify({'message': f'Order executed: {order_data["type"]} {quantity} {stock} for {price}.'})
        response.status_code = 200
        return response


'''
ROUTES
'''
api.add_resource(News, '/<string:exchange_id>/add-news')
api.add_resource(Config, '/start-server')
api.add_resource(MarketData, '/<string:exchange_id>/market-data')
api.add_resource(Connect, '/<string:exchange_id>/connect')
api.add_resource(Orders, '/<string:exchange_id>/order')


'''
SIMULATION
'''
def simulate_market(exchange_id, timeout):
    global exchanges

    start = time.time()
    while True:
        if time.time() - start > timeout * 60:
            with exchanges[exchange_id]['lock']:
                exchanges[exchange_id]['STARTED'] = False
            break

        time.sleep(TICKS_PER_SECOND)

        with exchanges[exchange_id]['lock']:
            if not exchanges[exchange_id]['STARTED']:
                continue

            exchanges[exchange_id]['tick_count'] += 1
            config = exchanges[exchange_id]

            for stock in config['stocks']:
                config['stocks'][stock] += random.gauss(0, config['settings']['stock_std'])
            
            if config['news_headlines']:
                headline = config['news_headlines'].pop(0)
                stock = headline['stock']
                sentiment = headline['sentiment']
                impact = random.uniform(config['settings']['headline_min_impact'], config['settings']['headline_max_impact'])
                config['stocks'][stock] *= impact if sentiment == 'up' else 1/impact
        
    # delete exchange if simulation is over
    del exchanges[exchange_id]

def start_simulation_thread(exchange_id, timeout):
    thread = threading.Thread(target=simulate_market, args=(exchange_id, timeout,))
    thread.start()
    return thread

if __name__ == '__main__':
    app.run(debug=True, threaded=True)