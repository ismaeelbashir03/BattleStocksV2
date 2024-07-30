'''
GLOBAL VARS
'''
exchanges = {}
trade_requests = {}
SECONDS_PER_TICK = 1
THREAD_TIMEOUT = 60
CODE_LENGTH = 6
NEWS_IMPACT_DURATION = 10
DIFFICULTY_MAP = {
    1: {
        'stock_std': 0.5,
        'headline_min_impact': 2,
        'headline_max_impact': 2
    },
    2: {
        'stock_std': 0.65,
        'headline_min_impact': 1.5,
        'headline_max_impact': 2,
    },
    3: {
        'stock_std': 0.8,
        'headline_min_impact': 1,
        'headline_max_impact': 2,
    },
    4: {
        'stock_std': 1,
        'headline_min_impact': 0.85,
        'headline_max_impact': 2,
    },
    5: {
        'stock_std': 2,
        'headline_min_impact': 0.8,
        'headline_max_impact': 2,
    }
}
STARTING_PRICE_RANGE = range(50, 150)
STARTING_CASH = 10000
