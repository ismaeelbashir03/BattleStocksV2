import threading
import time
import random
from typing import List
from config import exchanges, SECONDS_PER_TICK, NEWS_IMPACT_DURATION

class DecayEffect:
    def __init__(self, stock: str, total_impact: float, duration: int, sentiment: str):
        self.stock = stock
        self.total_impact = total_impact
        self.remaining_ticks = duration
        self.sentiment = sentiment

    def decay(self, stock_price: float) -> float:
        per_tick_impact = (self.total_impact - 1) / self.remaining_ticks
        self.remaining_ticks -= 1
        if self.sentiment == 'up':
            return stock_price * (1 + per_tick_impact)
        else:
            return stock_price / (1 + per_tick_impact)

def simulate_market(exchange_id: str, timeout: int):
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

            if len(decay_effects) == 0:
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
        
    del exchanges[exchange_id]

def start_simulation_thread(exchange_id: str, timeout: int) -> threading.Thread:
    thread = threading.Thread(target=simulate_market, args=(exchange_id, timeout,))
    thread.start()
    return thread