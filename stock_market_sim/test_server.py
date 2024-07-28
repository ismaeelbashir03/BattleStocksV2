import pytest
from time import sleep

from server import app, exchanges, TICKS_PER_SECOND

@pytest.fixture
def client():
    return app.test_client()

@pytest.fixture(scope="session", autouse=True)
def start_simulations():
    exchange_ids = []
    yield exchange_ids

def test_start_server(client, start_simulations):
    response = client.post('/start-server', json={
        'stocks': ['AAPL', 'GOOG'],
        'duration': 1,
        'difficulty': 1
    })

    assert response.status_code == 200
    exchange_id = response.json['exchange_id']
    start_simulations.append(exchange_id)
    assert response.json['message'].startswith("Configuration updated and market simulation started for exchange")

    response = client.post('/start-server', json={
        'stocks': ['AAPL', 'GOOG'],
        'duration': 1,
        'difficulty': 1
    })

    assert response.status_code == 200
    exchange_id = response.json['exchange_id']
    start_simulations.append(exchange_id)
    assert response.json['message'].startswith("Configuration updated and market simulation started for exchange")

def test_get_market_data(client, start_simulations):
    for exchange_id in start_simulations:
        response = client.get(f'/{exchange_id}/market-data')

        assert response.status_code == 200
        assert 'prices' in response.json
        assert 'details' in response.json

def test_place_order_buy(client, start_simulations):
    for exchange_id in start_simulations:
        connect_response = client.post(f'/{exchange_id}/connect', json={'name': 'user1'})
        user_id = connect_response.json['userId']

        response = client.post(f'/{exchange_id}/order', json={
            'userId': user_id,
            'stock': 'AAPL',
            'quantity': 5,
            'type': 'buy'
        })

        assert response.status_code == 200
        assert response.json['message'].startswith("Order executed")

def test_place_order_sell(client, start_simulations):
    for exchange_id in start_simulations:
        connect_response = client.post(f'/{exchange_id}/connect', json={'name': 'user1'})
        user_id = connect_response.json['userId']

        response = client.post(f'/{exchange_id}/order', json={
            'userId': user_id,
            'stock': 'AAPL',
            'quantity': 5,
            'type': 'sell'
        })

        assert response.status_code == 200
        assert response.json['message'].startswith("Order executed")

def test_add_news(client, start_simulations):
    for exchange_id in start_simulations:
        response = client.post(f'/{exchange_id}/add-news', json={
            'stock': 'AAPL',
            'impact': 'up'
        })

        assert response.status_code == 200
        assert response.json['message'].startswith("News headline published for exchange")

def test_market_simulation(client, start_simulations):
    for exchange_id in start_simulations:
        initial_prices = client.get(f'/{exchange_id}/market-data').json['prices']
        
        sleep(10)
        
        current_prices = client.get(f'/{exchange_id}/market-data').json['prices']
        for stock in initial_prices:
            assert initial_prices[stock] != current_prices[stock]

def test_isolation_between_exchanges(client, start_simulations):

    exchange_id_1, exchange_id_2 = start_simulations[:2]

    connect_response_1 = client.post(f'/{exchange_id_1}/connect', json={'name': 'user1'})
    assert connect_response_1.status_code == 200
    user_id_1 = connect_response_1.json['userId']
    connect_response_2 = client.post(f'/{exchange_id_2}/connect', json={'name': 'user2'})
    assert connect_response_2.status_code == 200
    user_id_2 = connect_response_2.json['userId']

    client.post(f'/{exchange_id_1}/order', json={
        'userId': user_id_1,
        'stock': 'AAPL',
        'quantity': 5,
        'type': 'buy'
    })

    client.post(f'/{exchange_id_2}/order', json={
        'userId': user_id_2,
        'stock': 'AAPL',
        'quantity': 5,
        'type': 'sell'
    })

    sleep(10)

    response_1 = client.get(f'/{exchange_id_1}/market-data')
    response_2 = client.get(f'/{exchange_id_2}/market-data')

    assert response_1.status_code == 200
    assert response_2.status_code == 200

    prices_1 = response_1.json['prices']
    prices_2 = response_2.json['prices']

    assert prices_1['AAPL'] != prices_2['AAPL']

def test_exchange_stops_after_duration(client, start_simulations):
    response = client.post('/start-server', json={
        'stocks': ['AAPL', 'GOOG'],
        'duration': 0.25, # 15 seconds
        'difficulty': 1
    })
    assert response.status_code == 200
    exchange_id = response.json['exchange_id']
    
    sleep(16)  
    
    assert exchange_id not in exchanges

if __name__ == "__main__":
    pytest.main()