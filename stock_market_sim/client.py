import random
import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"

USER_ID = "user1"

config_data = {
    'stocks': {"stock1": {"price": 100}},
    'users': {USER_ID: {'assets': {}, 'money': 10000}},
    'news_headlines': [{"stock": "stock1", "sentiment": "up"}],
    'ticks_per_news': 10,
    "stock_std": 0.5,
    "headline_min_impact": 1.1,
    "headline_max_impact": 5
}

def configure_market():
    response = requests.post(f"{BASE_URL}/config", json=config_data)
    print(response.json())

def get_market_data():
    response = requests.get(f"{BASE_URL}/market-data")
    return response.json()

def make_order(stock, quantity, order_type):
    order_data = {
        "stock": stock,
        "quantity": quantity,
        "type": order_type
    }
    response = requests.post(f"{BASE_URL}/order/{USER_ID}", json=order_data)
    return response.json()

def main():
    configure_market()
    last_headline_tick = 0

    while True:
        market_data = get_market_data()
        print("Market Data:", market_data)

        tick_count = int(time.time())  
        if (tick_count - last_headline_tick) >= config_data['ticks_per_news']:
            print("Headline Announcement!")
            for headline in config_data['news_headlines']:
                print(f"Stock: {headline['stock']}, Sentiment: {headline['sentiment']}")
            last_headline_tick = tick_count

        if tick_count % 15 == 0:
            stock_to_trade = random.choice(list(market_data.keys()))
            order_type = random.choice(["buy", "sell"])
            quantity = random.randint(1, 10)
            user_data = make_order(stock_to_trade, quantity, order_type)
            print(f"Order: {order_type} {quantity} of {stock_to_trade}")
            print("User Data:", user_data)

        time.sleep(1) 

if __name__ == "__main__":
    main()