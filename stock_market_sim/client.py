import threading
import time
import requests
import tkinter as tk
from tkinter import simpledialog, messagebox

BASE_URL = 'http://127.0.0.1:5000'

def start_server():
    response = requests.post(f'{BASE_URL}/start-server', json={
        'stocks': ['AAPL', 'GOOG'],
        'duration': 10,
        'difficulty': 1
    })
    data = response.json()
    exchange_id = data['exchange_id']
    print(f'Started exchange {exchange_id}')
    return exchange_id

def get_market_data(exchange_id):
    response = requests.get(f'{BASE_URL}/{exchange_id}/market-data')
    return response.json()

def place_order(exchange_id, user_id, stock, quantity, order_type):
    response = requests.post(f'{BASE_URL}/{exchange_id}/order', json={
        'userId': user_id,
        'stock': stock,
        'quantity': quantity,
        'type': order_type
    })
    return response.json()

def add_news(exchange_id, stock, impact):
    response = requests.post(f'{BASE_URL}/{exchange_id}/add-news', json={
        'stock': stock,
        'impact': impact
    })
    return response.json()

def connect_user(exchange_id, name):
    response = requests.post(f'{BASE_URL}/{exchange_id}/connect', json={'name': name})
    return response.json()['userId']

class TradingApp(tk.Tk):
    def __init__(self, exchange_id, user_id):
        super().__init__()
        self.exchange_id = exchange_id
        self.user_id = user_id
        self.title("Trading Simulator")
        self.geometry("400x400")

        self.market_data_label = tk.Label(self, text="Market Prices")
        self.market_data_label.pack()

        self.price_text = tk.Text(self, height=10, width=50)
        self.price_text.pack()

        self.assets_label = tk.Label(self, text="Your Assets")
        self.assets_label.pack()

        self.assets_text = tk.Text(self, height=10, width=50)
        self.assets_text.pack()

        self.trade_button = tk.Button(self, text="Trade", command=self.trade)
        self.trade_button.pack()

        self.news_button = tk.Button(self, text="Add News", command=self.add_news)
        self.news_button.pack()

        self.tick = 0

        self.previous_prices = {}
        self.update_prices()

    def update_prices(self):
        data = get_market_data(self.exchange_id)
        prices = data['prices']
        self.price_text.delete(1.0, tk.END)
        for stock, price in prices.items():
            color = "white"
            if stock in self.previous_prices:
                if price > self.previous_prices[stock]:
                    color = "green"
                elif price < self.previous_prices[stock]:
                    color = "red"
            self.price_text.insert(tk.END, f"{stock}: {price:.2f}\n", stock)
            self.price_text.tag_config(stock, foreground=color)
            self.previous_prices[stock] = price

        user_data = next((user for user in data['details'] if user['name'] == "trader"), None)
        self.assets_text.delete(1.0, tk.END)
        if user_data:
            self.assets_text.insert(tk.END, f"Cash: {user_data['cash']:.2f}\n")
            for asset, quantity in user_data['assets'].items():
                self.assets_text.insert(tk.END, f"{asset}: {quantity}\n")
            self.assets_text.insert(tk.END, f"Total value: {user_data['value']:.2f}\n")
            self.assets_text.insert(tk.END, f"Tick: {self.tick}\n")

        self.tick += 1
        self.after(1000, self.update_prices)

    def trade(self):
        stock = simpledialog.askstring("Input", "Enter stock:")
        quantity = simpledialog.askinteger("Input", "Enter quantity:")
        order_type = simpledialog.askstring("Input", "Enter type (buy/sell):")
        if stock and quantity and order_type:
            response = place_order(self.exchange_id, self.user_id, stock.upper(), quantity, order_type.lower())
            messagebox.showinfo("Trade", response['message'])

    def add_news(self):
        stock = simpledialog.askstring("Input", "Enter stock:")
        impact = simpledialog.askstring("Input", "Enter impact (up/down):")
        if stock and impact:
            response = add_news(self.exchange_id, stock.upper(), impact.lower())
            messagebox.showinfo("News", response['message'])

def main():
    exchange_id = start_server()
    user_id = connect_user(exchange_id, "trader")

    app = TradingApp(exchange_id, user_id)
    app.mainloop()

if __name__ == "__main__":
    main()