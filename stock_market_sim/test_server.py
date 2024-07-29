import pytest
import json
import time
from server import app

@pytest.fixture
def client():
    return app.test_client()

def test_init_server(client):
    response = client.get('/init-server')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert 'exchange_id' in data

def test_start_server(client):
    response = client.get('/init-server')
    exchange_id = json.loads(response.data)['exchange_id']

    response = client.post(f'/{exchange_id}/start-server', json={
        'stocks': ['AAPL', 'GOOG'],
        'difficulty': 3
    })
    assert response.status_code == 200

def test_market_data(client):
    response = client.get('/init-server')
    exchange_id = json.loads(response.data)['exchange_id']
    
    response = client.post(f'/{exchange_id}/start-server', json={
        'stocks': ['AAPL', 'GOOG'],
        'difficulty': 3
    })

    response = client.get(f'/{exchange_id}/market-data')
    assert response.status_code == 200

def test_add_news(client):
    response = client.get('/init-server')
    exchange_id = json.loads(response.data)['exchange_id']

    response = client.post(f'/{exchange_id}/start-server', json={
        'stocks': ['AAPL', 'GOOG'],
        'difficulty': 3
    })

    response = client.post(f'/{exchange_id}/add-news', json={
        'stock': 'AAPL',
        'impact': 'up'
    })
    assert response.status_code == 200

def test_pause_resume_stop(client):
    response = client.get('/init-server')
    exchange_id = json.loads(response.data)['exchange_id']

    response = client.post(f'/{exchange_id}/start-server', json={
        'stocks': ['AAPL', 'GOOG'],
        'difficulty': 3
    })

    initial_prices = client.get(f'/{exchange_id}/market-data').json['prices']

    response = client.get(f'/{exchange_id}/pause')
    assert response.status_code == 200

    time.sleep(2)

    paused_response = client.get(f'/{exchange_id}/market-data')
    assert paused_response.status_code == 400
    assert paused_response.json['message'] == 'Market simulation not started.'

    response = client.get(f'/{exchange_id}/resume')
    assert response.status_code == 200

    time.sleep(2)

    resumed_prices = client.get(f'/{exchange_id}/market-data').json['prices']
    assert resumed_prices != initial_prices

    response = client.get(f'/{exchange_id}/stop')
    assert response.status_code == 200

    time.sleep(2)

    response = client.get(f'/{exchange_id}/market-data')
    assert response.status_code == 400
    assert json.loads(response.data)['message'] == 'Exchange not found.'

def test_connect(client):
    response = client.get('/init-server')
    exchange_id = json.loads(response.data)['exchange_id']

    response = client.post(f'/{exchange_id}/connect', json={'name': 'user1'})
    assert response.status_code == 200

    response = client.post(f'/{exchange_id}/connect', json={'name': 'user1'})
    assert response.status_code == 400
    assert json.loads(response.data)['message'] == 'Username taken.'

def test_order(client):
    response = client.get('/init-server')
    exchange_id = json.loads(response.data)['exchange_id']

    client.post(f'/{exchange_id}/start-server', json={
        'stocks': ['AAPL', 'GOOG'],
        'difficulty': 3
    })

    client.post(f'/{exchange_id}/connect', json={'name': 'user1'})

    response = client.post(f'/{exchange_id}/order', json={
        'userId': 'user1',
        'stock': 'AAPL',
        'quantity': 5,
        'type': 'buy'
    })
    assert response.status_code == 200

    user_data = client.get(f'/{exchange_id}/market-data').json['details']['user1']
    assert user_data['cash'] < 10000
    assert 'AAPL' in user_data['assets'] and user_data['assets']['AAPL'] == 5

def test_trade_request(client):
    response = client.get('/init-server')
    exchange_id = json.loads(response.data)['exchange_id']

    client.post(f'/{exchange_id}/start-server', json={
        'stocks': ['AAPL', 'GOOG'],
        'difficulty': 3
    })

    client.post(f'/{exchange_id}/connect', json={'name': 'user1'})
    client.post(f'/{exchange_id}/connect', json={'name': 'user2'})

    client.post(f'/{exchange_id}/order', json={
        'userId': 'user1',
        'stock': 'AAPL',
        'quantity': 5,
        'type': 'buy'
    })

    response = client.post(f'/{exchange_id}/trade-request', json={
        'from_user': 'user1',
        'to_user': 'user2',
        'stock': 'AAPL',
        'quantity': 5,
        'price': 100,
        'type': 'sell'
    })
    assert response.status_code == 200

def test_inbox(client):
    response = client.get('/init-server')
    exchange_id = json.loads(response.data)['exchange_id']

    client.post(f'/{exchange_id}/start-server', json={
        'stocks': ['AAPL', 'GOOG'],
        'difficulty': 3
    })

    client.post(f'/{exchange_id}/connect', json={'name': 'user1'})
    client.post(f'/{exchange_id}/connect', json={'name': 'user2'})

    client.post(f'/{exchange_id}/order', json={
        'userId': 'user1',
        'stock': 'AAPL',
        'quantity': 5,
        'type': 'buy'
    })

    client.post(f'/{exchange_id}/trade-request', json={
        'from_user': 'user1',
        'to_user': 'user2',
        'stock': 'AAPL',
        'quantity': 5,
        'price': 100,
        'type': 'sell'
    })

    response = client.get(f'/{exchange_id}/inbox/user2')
    assert response.status_code == 200
    inbox = json.loads(response.data)['inbox']
    assert len(inbox) > 0

def test_trade_response(client):
    response = client.get('/init-server')
    exchange_id = json.loads(response.data)['exchange_id']

    client.post(f'/{exchange_id}/start-server', json={
        'stocks': ['AAPL', 'GOOG'],
        'difficulty': 3
    })

    client.post(f'/{exchange_id}/connect', json={'name': 'user1'})
    client.post(f'/{exchange_id}/connect', json={'name': 'user2'})

    client.post(f'/{exchange_id}/order', json={
        'userId': 'user1',
        'stock': 'AAPL',
        'quantity': 5,
        'type': 'buy'
    })

    trade_request_response = client.post(f'/{exchange_id}/trade-request', json={
        'from_user': 'user1',
        'to_user': 'user2',
        'stock': 'AAPL',
        'quantity': 5,
        'price': 150,
        'type': 'sell'
    })

    request_id = json.loads(trade_request_response.data)['request_id']

    response = client.post(f'/{exchange_id}/trade-response', json={
        'request_id': request_id,
        'response': 'accept'
    })
    assert response.status_code == 200

    user_data = client.get(f'/{exchange_id}/market-data').json['details']

    user1_data = next(details for user, details in user_data.items() if user == 'user1')
    user2_data = next(details for user, details in user_data.items() if user == 'user2')

    assert user1_data['cash'] >= 10000
    assert 'AAPL' not in user1_data['assets'] or user1_data['assets']['AAPL'] == 0 

    assert user2_data['cash'] < 10000 
    assert 'AAPL' in user2_data['assets'] and user2_data['assets']['AAPL'] == 5 

def test_get_users(client):
    response = client.get('/init-server')
    exchange_id = json.loads(response.data)['exchange_id']

    client.post(f'/{exchange_id}/start-server', json={
        'stocks': ['AAPL', 'GOOG'],
        'difficulty': 3
    })

    client.post(f'/{exchange_id}/connect',json={'name': 'user1'})
    client.post(f'/{exchange_id}/connect', json={'name': 'user2'})
    response = client.get(f'/{exchange_id}/get-users')
    assert response.status_code == 200

    users = json.loads(response.data)['users']
    assert 'user1' in users
    assert 'user2' in users

if __name__ == "__main__":
    pytest.main()