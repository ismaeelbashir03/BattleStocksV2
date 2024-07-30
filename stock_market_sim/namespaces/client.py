from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
import uuid
from config import exchanges, trade_requests, STARTING_CASH

api = Namespace('client', description='Client related operations')

@api.route('/<string:exchange_id>/connect', methods=['POST'])
@api.expect(api.model('ConnectBody', {
    'name': fields.String(required=True, description='Name of the user connecting to the exchange.'),
}))
@api.response(200, 'Success', model=api.model('ConnectResponse', {
    'message': fields.String(description='Description of the action taken.')
}))
@api.response(400, 'Validation Error', model=api.model('ErrorResponse', {
    'message': fields.String(description='Error message.')
}))
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
@api.expect(api.model('Order', {
    'userId': fields.String,
    'stock': fields.String,
    'quantity': fields.Integer,
    'type': fields.String
}))
@api.response(200, 'Success', model=api.model('OrderResponse', {
    'message': fields.String(description='Description of the action taken.')
}))
@api.response(400, 'Validation Error', model=api.model('ErrorResponse', {
    'message': fields.String(description='Error message.')
}))
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
@api.expect(api.model('TradeRequest', {
    'from_user': fields.String(required=True, description='User ID of the sender.'),
    'to_user': fields.String(required=True, description='User ID of the receiver.'),
    'stock': fields.String(required=True, description='Stock to be traded.'),
    'quantity': fields.Integer(required=True, description='Quantity of stock to be traded.'),
    'price': fields.Float(required=True, description='Proposed price per stock.'),
    'type': fields.String(required=True, description='Type of trade (buy or sell).')
}))
@api.response(200, 'Success', model=api.model('TradeRequestResponse', {
    'message': fields.String(description='Description of the action taken.'),
    'request_id': fields.String(description='Unique identifier for the trade request.')
}))
@api.response(400, 'Validation Error', model=api.model('ErrorResponse', {
    'message': fields.String(description='Error message.')
}))
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
@api.response(200, 'Success', model=api.model('InboxResponse', {
    'inbox': fields.Raw(description='List of pending trade requests for the user.')
}))
@api.response(400, 'Validation Error', model=api.model('ErrorResponse', {
    'message': fields.String(description='Error message.')
}))
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
@api.expect(api.model('TradeResponse', {
    'request_id': fields.String(required=True, description='ID of the trade request.'),
    'response': fields.String(required=True, description='Response to the trade request (accept or decline).')
}))
@api.response(200, 'Success', model=api.model('TradeResponseResponse', {
    'message': fields.String(description='Description of the action taken.')
}))
@api.response(400, 'Validation Error', model=api.model('ErrorResponse', {
    'message': fields.String(description='Error message.')
}))
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
@api.response(200, 'Success', model=api.model('GetUsersResponse', {
    'users': fields.List(fields.String, description='List of connected users.')
}))
@api.response(400, 'Validation Error', model=api.model('ErrorResponse', {
    'message': fields.String(description='Error message.')
}))
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