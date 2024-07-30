from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
import random
import string
from collections import deque
import threading
from config import exchanges, CODE_LENGTH, DIFFICULTY_MAP, STARTING_PRICE_RANGE
from simulation import start_simulation_thread

api = Namespace('host', description='Host related operations')

@api.route('/init-server')
class Init(Resource):
    def get(self):
        global exchanges
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

@api.route('/<string:exchange_id>/start-server')
@api.expect(api.model('StartBody', {
    'stocks': fields.List(fields.String, required=True, description='List of stocks to include in the simulation.'),
    'difficulty': fields.Integer(required=True, description='Difficulty level of the simulation (1 to 5 inclusive).'),
}))
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
        start_simulation_thread(exchange_id, 60)
        response = jsonify({'exchange_id': exchange_id, 'message': f'Configuration updated and market simulation started for exchange {exchange_id}.'})
        response.status_code = 200
        return response

@api.route('/<string:exchange_id>/market-data')
class MarketData(Resource):
    def get(self, exchange_id):
        global exchanges
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

@api.route('/<string:exchange_id>/add-news')
@api.expect(api.model('NewsBody', {
    'stock': fields.String(required=True, description='Stock to affect.'),
    'impact': fields.String(required=True, description='Sentiment of the news headline (up or down).'),
}))
class News(Resource):
    def post(self, exchange_id):
        global exchanges
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

@api.route('/<string:exchange_id>/pause')
class Pause(Resource):
    def get(self, exchange_id):
        global exchanges
        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response
        with exchanges[exchange_id]['lock']:
            exchanges[exchange_id]['STARTED'] = False
        response = jsonify({'message': f'Market simulation paused for exchange {exchange_id}.'})
        response.status_code = 200
        return response

@api.route('/<string:exchange_id>/resume')
class Resume(Resource):
    def get(self, exchange_id):
        global exchanges
        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response
        with exchanges[exchange_id]['lock']:
            exchanges[exchange_id]['STARTED'] = True
        response = jsonify({'message': f'Market simulation resumed for exchange {exchange_id}.'})
        response.status_code = 200
        return response

@api.route('/<string:exchange_id>/stop')
class Stop(Resource):
    def get(self, exchange_id):
        global exchanges
        if exchange_id not in exchanges:
            response = jsonify({'message': 'Exchange not found.'})
            response.status_code = 400
            return response
        with exchanges[exchange_id]['lock']:
            exchanges[exchange_id]['kill'] = True
        response = jsonify({'message': f'Market simulation stopped for exchange {exchange_id}.'})
        response.status_code = 200
        return response