import os
import sys
import time
import datetime
import schedule
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.spot import mexc_spot_v3
from utils.future import mexc_future
from mexc_web_automation import MexcWebAutomation

class MexcBot:
    def __init__(self):
        self.spot_market = mexc_spot_v3.mexc_market()
        self.future_market = mexc_future.mexc_market()
        self.signal = 0
        self.mexc_web_automation = MexcWebAutomation()

        self.length = 10
        self.request_retries = 3

        self.mintick = 0.01


    def get_spot_kline(self) -> list:
        params = {
            "symbol": "SOLUSDT",
            "interval": "1m",
            "limit": "15",
            # "startTime": int((datetime.datetime.now() - datetime.timedelta(minutes=15)).timestamp() * 1000),
            # "endTime": int(datetime.datetime.now().timestamp() * 1000),
        }
        i = 0
        while i < self.request_retries:
            try:
                return self.spot_market.get_kline(params)
            except Exception as e:
                logger.error(f"获取现货K线数据失败: {e}")
                i += 1
                time.sleep(1)
        return []
    
    def get_future_kline(self) -> list:
        ret = []
        params = {
            "symbol": "SOL_USDT",
            "interval": "Min1",
            "start": int((datetime.datetime.now() - datetime.timedelta(minutes=15)).timestamp()),
            "end": int(datetime.datetime.now().timestamp()),
        }
        i = 0
        while i < self.request_retries:
            try:
                kline = self.future_market.get_kline(params)
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
        logger.info(f"{close_prices[-1]}, {close_prices[-self.length-1]}, {close_prices[-2]}, {close_prices[-self.length-2]}")
        logger.info(f"动量0: {mom0}, 动量1: {mom1}")
        # 计算信号
        if mom0 > 0 and mom1 > 0:
            return 1  # 多头信号
        elif mom0 < 0 and mom1 < 0:
            return -1  # 空头信号
        else:
            return 0  # 无信号
    
    def job(self):
        """每分钟执行一次的任务"""
        kline = self.get_future_kline()
        if not kline:
            logger.error("获取K线数据失败")
            return
        logger.info(f"当前分钟的时间戳: {int(datetime.datetime.now().timestamp()) - int(datetime.datetime.now().timestamp()) % 60}")
        if kline[-1][0] > int(datetime.datetime.now().timestamp()) - 60:
            kline = kline[:-1]
        logger.info(f"获取K线数据: {kline}")
        # 提取出close_prices
        close_prices = [float(item[4]) for item in kline]
        high_prices = [float(item[2]) for item in kline]
        low_prices = [float(item[3]) for item in kline]
        # 计算动量信号
        signal = self.calculate_momentum_signal(close_prices)
        logger.info(f"动量信号: {'long entry' if signal == 1 else 'short entry' if signal == -1 else 'no signal'}")
        if self.signal == 0:
            if signal == 1:
                self.mexc_web_automation.long_entry()
                self.signal = signal
            elif signal == -1:
                self.mexc_web_automation.short_entry()
                self.signal = signal
        else:
            if signal == 0:
                is_successed = self.mexc_web_automation.cancel_stop()
                if not is_successed:
                    return
                if self.signal == 1:
                    self.signal = -1
                elif self.signal == -1:
                    self.signal = 1
            if signal == 1:
                if self.signal == 1:
                    return
                if self.signal == -1:
                    is_successed = self.mexc_web_automation.set_stop(high_prices[-1] + self.mintick)
                    if not is_successed:
                        self.mexc_web_automation.close_position()
                        self.signal = 0
                        return
                self.signal = signal
            elif signal == -1:
                if self.signal == -1:
                    return
                if self.signal == 1:
                    is_successed = self.mexc_web_automation.set_stop(low_prices[-1] - self.mintick)
                    if not is_successed:
                        self.mexc_web_automation.close_position()
                        self.signal = 0
                        return
                self.signal = signal

    def run(self):
        """准时在每分钟的0秒启动任务"""
        logger.info(f"机器人启动...")
        
        # 设置每分钟执行一次
        schedule.every().minute.at(":00").do(self.job)
        
        while True:
            schedule.run_pending()
            time.sleep(0.5)  # 小的睡眠时间，减少CPU使用

# 使用示例
if __name__ == "__main__":
    bot = MexcBot()
    bot.run()
