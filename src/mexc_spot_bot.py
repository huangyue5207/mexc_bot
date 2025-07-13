import os
import sys
import time
import datetime
from loguru import logger
import schedule
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.spot import mexc_spot_v3



class MexcSpotBot:
    def __init__(self):
        self.symbol = 'BTCUSDC'
        self.buy_asset = 'USDC'
        self.sell_asset = 'BTC'
        self.request_retries = 3
        self.order_id = None
        self.length = 8
        self.mintick = 0.01
        self.mexc_spot_v3 = mexc_spot_v3

    def get_spot_kline(self) -> list:
        params = {
            "symbol": self.symbol,
            "interval": "1m",
            "limit": "15",
        }
        i = 0
        while i < self.request_retries:
            try:
                return self.mexc_spot_v3.mexc_market().get_kline(params)
            except Exception as e:
                logger.error(f"获取现货K线数据失败: {e}")
                i += 1
                time.sleep(1)
        return []

    def get_btcusde_spot_kline(self) -> list:
        """
        temperate
        """
        params = {
            "symbol": "BTCUSDE",
            "interval": "1m",
            "limit": "15",
        }
        i = 0
        while i < self.request_retries:
            try:
                return self.mexc_spot_v3.mexc_market().get_kline(params)
            except Exception as e:
                logger.error(f"获取现货K线数据失败: {e}")
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
        logger.info(f"{close_prices[-1]}, {close_prices[-self.length-1]}, {close_prices[-2]}, {close_prices[-self.length-2]}")
        logger.info(f"动量0: {mom0}, 动量1: {mom1}")
        # 计算信号
        if mom0 > 0 and mom1 > 0:
            return 1  # 多头信号
        elif mom0 < 0 and mom1 < 0:
            return -1  # 空头信号
        else:
            return 0  # 无信号

    def get_selfSymbols(self):
        return self.mexc_spot_v3.mexc_trade().get_selfSymbols()

    def buy(self, quantity: float, price: float) -> dict:
        params = {
            'symbol': self.symbol,
            'side': 'BUY',
            'quantity': quantity,
            'price': price,
            'type': 'LIMIT',
        }
        response = self.mexc_spot_v3.mexc_trade().post_order(params)
        self.order_id = response.get("orderId")
        return response
    
    def sell(self, quantity: float) -> dict:
        params = {
            'symbol': self.symbol,
            'side': 'SELL',
            'quantity': quantity,
            'type': 'MARKET',
        }
        return self.mexc_spot_v3.mexc_trade().post_order(params)
    
    def cancel_order(self, order_id: str) -> None:
        params = {
            'symbol': self.symbol,
            'orderId': order_id,
        }
        self.mexc_spot_v3.mexc_trade().delete_order(params)
        self.order_id = None
        return
    
    def get_asset_balance(self, asset: str) -> float:
        account_info = self.mexc_spot_v3.mexc_trade().get_account_info()
        for item in account_info.get("balances", []):
            if item.get("asset") == asset:
                return float(item.get("free", 0))
        return 0
    
    def job(self):
        """每分钟执行一次的任务"""
        kline = self.get_spot_kline()
        btcusde_kline = self.get_btcusde_spot_kline()

        if not kline or not btcusde_kline:
            logger.error("获取K线数据失败")
            asset_balance = self.get_asset_balance(self.sell_asset)
            if asset_balance > 0:
                self.sell(asset_balance)
            return
            
        logger.info(f"当前分钟的时间戳: {int(datetime.datetime.now().timestamp()) - int(datetime.datetime.now().timestamp()) % 60}")
        if kline[-1][0] > int(datetime.datetime.now().timestamp()) - 60:
            kline = kline[:-1]
        logger.info(f"获取K线数据: {kline}")

        if btcusde_kline[-1][0] > int(datetime.datetime.now().timestamp()) - 60:
            btcusde_kline = btcusde_kline[:-1]
        logger.info(f"获取BTCUSDE K线数据: {btcusde_kline}")
        
        # 提取出close_prices
        close_prices = [float(item[4]) for item in kline]

        btcusde_close_prices = [float(item[4]) for item in btcusde_kline]

        # 计算动量信号
        signal = self.calculate_momentum_signal(btcusde_close_prices) # 使用BTCUSDE的价格来计算动量信号

        logger.info(f"最新动量信号: {'long entry' if signal == 1 else 'short entry' if signal == -1 else 'no signal'}")
        if signal == 1:
            asset_balance = self.get_asset_balance(self.buy_asset)
            logger.info(f"USDE余额: {asset_balance}")
            if asset_balance > 1:
                response = self.buy(asset_balance / close_prices[-1], close_prices[-1])
                logger.info(f"买入成功: {response}")
        elif signal == -1:
            logger.info(f"order_id: {self.order_id}")
            if self.order_id:
                response = self.cancel_order(self.order_id)
                logger.info(f"取消订单成功: {response}")
            asset_balance = self.get_asset_balance(self.sell_asset)
            logger.info(f"BTC余额: {asset_balance}")
            if asset_balance > 0:
                response = self.sell(asset_balance)
                logger.info(f"卖出成功: {response}")
        else:
            logger.info(f"order_id: {self.order_id}")
            if self.order_id:
                response = self.cancel_order(self.order_id)
                logger.info(f"取消订单成功: {response}")

    def run(self):
        """准时在每分钟的0秒启动任务"""
        logger.info(f"机器人启动...")
        
        # 设置每分钟执行一次
        schedule.every().minute.at(":00").do(self.job)
        
        while True:
            schedule.run_pending()
            time.sleep(0.5)  # 小的睡眠时间，减少CPU使用
    
if __name__ == '__main__':
    bot = MexcSpotBot()
    bot.run()
    # asset_balance = bot.get_asset_balance('USDE')
    # print(asset_balance)
    # buy_response = bot.buy(asset_balance / 100000, 100000)
    # print(buy_response)
    # print(bot.get_asset_balance('BTC'))

    # bot.cancel_order('C02__559720481322852352099')

    # asset_balance = bot.get_asset_balance('BTC')
    # print(asset_balance)
    # sell_response = bot.sell(asset_balance)
    # print(sell_response)
    # print(bot.get_asset_balance('USDE'))
