import pytest
from threading import Thread
from time import sleep
import uuid

from server import app, start_simulation_thread, exchanges

@pytest.fixture
def client():
    return app.test_client()

@pytest.fixture(scope="session", autouse=True)
def start_simulations():
    exchange_ids = [str(uuid.uuid4()) for _ in range(2)]
    threads = [start_simulation_thread(exchange_id) for exchange_id in exchange_ids]
    sleep(1)  # Give the threads some time to start
    yield exchange_ids
    for thread in threads:
        thread.join(0)

def test_start_server(client, start_simulations):
    for exchange_id in start_simulations:
        response = client.post(f'/{exchange_id}/start-server', json={
            'stocks': {'AAPL': {'price': 150}, 'GOOG': {'price': 2800}},
            'users': {'user1': {'assets': {'AAPL': 10}, 'money': 10000}},
            'stock_std': 1.0,
            'headline_min_impact': 1.1,
            'headline_max_impact': 2.0,
            'news_headlines': []
        })

        assert response.status_code == 200
        assert response.json['message'] == f"Configuration updated and market simulation started for exchange {exchange_id}."

def test_get_market_data(client, start_simulations):
    for exchange_id in start_simulations:
        response = client.get(f'/{exchange_id}/market-data')

        assert response.status_code == 200
        assert 'AAPL' in response.json
        assert 'GOOG' in response.json

def test_place_order_buy(client, start_simulations):
    for exchange_id in start_simulations:
        # reset the user's assets and money
        client.post(f'/{exchange_id}/start-server', json={
            'stocks': {'AAPL': {'price': 150}, 'GOOG': {'price': 2800}},
            'users': {'user1': {'assets': {'AAPL': 10}, 'money': 10000}},
            'stock_std': 1.0,
            'headline_min_impact': 1.1,
            'headline_max_impact': 2.0,
            'news_headlines': []
        })

        response = client.post(f'/{exchange_id}/order/user1', json={
            'stock': 'AAPL',
            'quantity': 5,
            'type': 'buy'
        })

        assert response.status_code == 200
        
        user_data = response.json
        
        assert user_data['assets']['AAPL'] == 15
        assert user_data['money'] < 10000

def test_place_order_sell(client, start_simulations):
    for exchange_id in start_simulations:
        # reset the user's assets and money
        client.post(f'/{exchange_id}/start-server', json={
            'stocks': {'AAPL': {'price': 150}, 'GOOG': {'price': 2800}},
            'users': {'user1': {'assets': {'AAPL': 10}, 'money': 10000}},
            'stock_std': 1.0,
            'headline_min_impact': 1.1,
            'headline_max_impact': 2.0,
            'news_headlines': []
        })

        client.get(f'/{exchange_id}/market-data')
        response = client.post(f'/{exchange_id}/order/user1', json={
            'stock': 'AAPL',
            'quantity': 5,
            'type': 'sell'
        })

        assert response.status_code == 200
        
        user_data = response.json
        
        assert user_data['assets']['AAPL'] == 5
        assert user_data['money'] > 10000

def test_add_news(client, start_simulations):
    for exchange_id in start_simulations:
        response = client.post(f'/{exchange_id}/add-news', json={
            'headline': {
                'stock': 'AAPL',
                'sentiment': 'up'
            }
        })

        assert response.status_code == 200
        assert response.json['message'] == f"News headline published for exchange {exchange_id}. Market will be affected."

def test_market_simulation(client, start_simulations):
    for exchange_id in start_simulations:
        initial_prices = {stock: data['price'] for stock, data in exchanges[exchange_id]['config']['stocks'].items()}
        
        sleep(5)
        
        response = client.get(f'/{exchange_id}/market-data')
        assert response.status_code == 200
        
        current_prices = response.json
        for stock in initial_prices:
            assert initial_prices[stock] != current_prices[stock]['price']

def test_isolation_between_exchanges(client, start_simulations):
    exchange_id_1, exchange_id_2 = start_simulations

    # buy order exchange 1
    client.post(f'/{exchange_id_1}/start-server', json={
        'stocks': {'AAPL': {'price': 150}, 'GOOG': {'price': 2800}},
        'users': {'user1': {'assets': {'AAPL': 10}, 'money': 10000}},
        'stock_std': 1.0,
        'headline_min_impact': 1.1,
        'headline_max_impact': 2.0,
        'news_headlines': []
    })
    client_1 = client.post(f'/{exchange_id_1}/order/user1', json={
        'stock': 'AAPL',
        'quantity': 5,
        'type': 'buy'
    }).json

    # sell order exchange 2
    client.post(f'/{exchange_id_2}/start-server', json={
        'stocks': {'AAPL': {'price': 150}, 'GOOG': {'price': 2800}},
        'users': {'user2': {'assets': {'AAPL': 10}, 'money': 10000}},
        'stock_std': 1.0,
        'headline_min_impact': 1.1,
        'headline_max_impact': 2.0,
        'news_headlines': []
    })
    client_2 = client.post(f'/{exchange_id_2}/order/user2', json={
        'stock': 'AAPL',
        'quantity': 5,
        'type': 'sell'
    }).json

    sleep(15)
    response_1 = client.get(f'/{exchange_id_1}/market-data')
    response_2 = client.get(f'/{exchange_id_2}/market-data')
    
    assert response_1.status_code == 200
    assert response_2.status_code == 200

    prices_1 = response_1.json
    prices_2 = response_2.json

    assert client_1['assets']['AAPL'] == 15
    assert client_2['assets']['AAPL'] == 5
    assert prices_1['AAPL']['price'] != prices_2['AAPL']['price']

if __name__ == "__main__":
    pytest.main()