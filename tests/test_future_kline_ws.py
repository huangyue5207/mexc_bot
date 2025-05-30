import os
import sys
import time
import datetime
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.future import mexc_future

mexc_future = mexc_future.mexc_market()

params = {
    "method":"sub.kline",
    "param":{
        "symbol":"BTC_USDT",
        "interval":"Min1"
    }
}

mexc_future.get_kline_ws(params)