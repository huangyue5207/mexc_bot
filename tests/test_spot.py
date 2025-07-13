import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.spot import mexc_spot_v3

# symbols = mexc_spot_v3.mexc_trade().get_selfSymbols()
# print(symbols)

params = {
    'symbol': 'BTCUSDE',
    'side': 'BUY',
    'quoteOrderQty': 2,
    'type': 'MARKET',
}

response = mexc_spot_v3.mexc_trade().post_order(params)
print(response)
