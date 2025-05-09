import datetime
import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

class mexc_market(object):

    def __init__(self):
        self.hosts = 'https://contract.mexc.com/'

    def public_request(self, method, url, params=None):
        url = '{}{}'.format(self.hosts, url)
        return requests.request(method, url, params=params)
    
    def get_kline(self, params):
        url = f'api/v1/contract/kline/{params["symbol"]}'
        response = self.public_request('GET', url, params)
        return response.json()
    

if __name__ == '__main__':
    mexc_market = mexc_market()
    params = {
        "symbol": "BTC_USDT",
        "interval": "Min1",
        "start": int((datetime.datetime.now() - datetime.timedelta(minutes=15)).timestamp()),
        "end": int(datetime.datetime.now().timestamp()),
    }
    print(mexc_market.get_kline(params))
    