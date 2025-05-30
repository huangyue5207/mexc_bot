import datetime
import os
import sys
import time
import websocket
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

class mexc_market(object):
    def __init__(self):
        self.hosts = [
            'https://contract.mexc.kr/',
            'https://contract.mexc.co/',
        ]
        self.index = 0

    def public_request(self, method, url, params=None, proxies=None):
        try:
            url = '{}{}'.format(self.hosts[self.index], url)
            print(f"kline url: {url}")
            return requests.request(method, url, params=params, proxies=proxies)
        except Exception as e:
            self.index = (self.index + 1) % len(self.hosts)
            raise e
    
    def get_kline(self, params):
        url = f'api/v1/contract/kline/{params["symbol"]}'
        response = self.public_request('GET', url, params)
        return response.json()
    
    def get_kline_ws(self, params):
        def on_message(ws, message):
            print(message)

        def on_error(ws, error):
            print(error)

        def on_close(ws):
            print("### closed ###")

        url = f'wss://contract.mexc.com/ws'
        # 使用websocket订阅
        ws = websocket.WebSocketApp(url, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.send(json.dumps(params))
        ws.run_forever()

if __name__ == '__main__':
    mexc_market = mexc_market()
    params = {
        "symbol": "BTC_USDT",
        "interval": "Min1",
        "start": int((datetime.datetime.now() - datetime.timedelta(minutes=15)).timestamp()),
        "end": int(datetime.datetime.now().timestamp()),
    }
    print(mexc_market.get_kline(params))
    