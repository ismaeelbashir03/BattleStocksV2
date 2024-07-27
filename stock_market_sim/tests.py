import pytest
from threading import Thread
from time import sleep

from server import app, simulate_market, config

@pytest.fixture
def client():
    return app.test_client()

# start the sim before running tests
@pytest.fixture(scope="session", autouse=True)
def start_simulation():
    sim_thread = Thread(target=simulate_market)
    sim_thread.daemon = True
    sim_thread.start()
    yield
    sim_thread.join(0)

def test_start_server(client):
    response = client.post('/start-server', json={
        'stocks': {'AAPL': {'price': 150}, 'GOOG': {'price': 2800}},
        'users': {'user1': {'assets': {'AAPL': 10}, 'money': 10000}},
        'stock_std': 1.0,
        'headline_min_impact': 1.1,
        'headline_max_impact': 2.0,
        'news_headlines': []
    })

    assert response.status_code == 200
    assert response.json['message'] == "Configuration updated and market simulation started."

def test_get_market_data(client):
    response = client.get('/market-data')

    assert response.status_code == 200
    assert 'AAPL' in response.json
    assert 'GOOG' in response.json

def test_place_order_buy(client):
    response = client.post('/order/user1', json={
        'stock': 'AAPL',
        'quantity': 5,
        'type': 'buy'
    })

    assert response.status_code == 200
    
    user_data = response.json
    
    assert user_data['assets']['AAPL'] == 15
    assert user_data['money'] < 10000

def test_place_order_sell(client):
    response = client.post('/order/user1', json={
        'stock': 'AAPL',
        'quantity': 5,
        'type': 'sell'
    })

    assert response.status_code == 200
    
    user_data = response.json
    
    assert user_data['assets']['AAPL'] == 10
    assert user_data['money'] > 10000

def test_add_news(client):
    response = client.post('/add-news', json={
        'headline': {
            'stock': 'AAPL',
            'sentiment': 'up'
        }
    })

    assert response.status_code == 200
    assert response.json['message'] == "News headline published. Market will be affected."

def test_market_simulation(client):
    initial_prices = {stock: data['price'] for stock, data in config['stocks'].items()}
    
    sleep(5)
    
    response = client.get('/market-data')
    assert response.status_code == 200
    
    current_prices = response.json
    for stock in initial_prices:
        assert initial_prices[stock] != current_prices[stock]['price']

if __name__ == "__main__":
    pytest.main()