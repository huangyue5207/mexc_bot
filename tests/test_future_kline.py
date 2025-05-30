import os
import sys
import time
import datetime
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.future import mexc_future

def get_future_kline() -> list:
    ret = []
    params = {
        "symbol": "SOL_USDT",
        "interval": "Min1",
        "start": int((datetime.datetime.now() - datetime.timedelta(minutes=15)).timestamp()),
        "end": int(datetime.datetime.now().timestamp()),
    }
    future = mexc_future.mexc_market()
    i = 0
    while i < 3:
        try:
            logger.info(f"获取期货K线数据: {params}")
            kline = future.get_kline(params)
            for i, ts in enumerate(kline.get('data', {}).get('time', [])):
                ret.append([
                    ts,
                    kline.get('data', {}).get('realOpen', [])[i],
                    kline.get('data', {}).get('realHigh', [])[i],
                    kline.get('data', {}).get('realLow', [])[i],
                    kline.get('data', {}).get('realClose', [])[i],
                    kline.get('data', {}).get('vol', [])[i],
                ])
            break
        except Exception as e:
            logger.error(f"获取期货K线数据失败: {e}")
            i += 1
            time.sleep(1)
    return ret

if __name__ == "__main__":
    kline = get_future_kline()
    logger.info(kline)
