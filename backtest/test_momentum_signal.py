import os
import sys
import time
import datetime
import schedule
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.spot import mexc_spot_v3
from mexc_web_automation import MexcWebAutomation

def get_kline(self) -> list:
    params = {
        "symbol": "SOLUSDT",
        "interval": "1m",
        "limit": "15",
        "startTime": int((datetime.datetime.now() - datetime.timedelta(minutes=15)).timestamp() * 1000),
        "endTime": int(datetime.datetime.now().timestamp() * 1000),
    }
    i = 0
    while i < self.request_retries:
        try:
            return self.market.get_kline(params)
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            i += 1
            time.sleep(1)
    return []

def calculate_momentum_signal(self, close_prices: list) -> int:
    """
    计算最后一个K线的动量信号
    
    参数:
    close_prices: 收盘价列表，最新的价格在最后
    length: 动量计算周期，默认为12
    
    返回:
    signal: 1(多头), -1(空头), 0(无信号)
    """
    if len(close_prices) < self.length + 1:
        return 0
    
    # 计算动量
    mom0 = close_prices[-1] - close_prices[-self.length-1]
    mom1 = mom0 - (close_prices[-2] - close_prices[-self.length-2])
    
    # 计算信号
    if mom0 > 0 and mom1 > 0:
        return 1  # 多头信号
    elif mom0 < 0 and mom1 < 0:
        return -1  # 空头信号
    else:
        return 0  # 无信号