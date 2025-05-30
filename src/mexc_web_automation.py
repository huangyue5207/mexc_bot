import os
import sys
import time
from playwright.sync_api import sync_playwright, Page
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MexcWebAutomation:
    def __init__(self, headless=False):
        """
        初始化 MEXC 网页自动化测试程序
        
        参数:
        headless: 是否使用无头模式，默认为 False
        """

        self.retry_times = 3

        # 初始化 Playwright
        self.playwright = sync_playwright().start()
        
        # 配置浏览器选项 - 增强真实浏览器特征
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-web-security',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--window-size=1920,1080',
            '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # 启动浏览器
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=browser_args
        )
        
        # 创建上下文，可以保存登录状态并设置更多真实浏览器特征
        self.context = self.browser.new_context(
            storage_state="./playwright_data/state.json" if os.path.exists("./playwright_data/state.json") else None,
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            geolocation={'latitude': 39.9042, 'longitude': 116.4074},
            permissions=['geolocation'],
            color_scheme='no-preference',
            device_scale_factor=1.0,
            is_mobile=False,
            has_touch=False,
            ignore_https_errors=True
        )
        
        # 创建新页面
        self.page = self.context.new_page()
        
        # 注入脚本以绕过自动化检测
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            
            // 覆盖 Permissions API
            if (window.Notification) {
                window.Notification.permission = 'granted';
            }
            
            // 修改 navigator 属性
            const newProto = navigator.__proto__;
            delete newProto.webdriver;
            navigator.__proto__ = newProto;
            
            // 添加插件数量
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [1, 2, 3, 4, 5];
                }
            });
            
            // 修改 Chrome 对象
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
        """)

        # 启用请求拦截
        self.page.route("**/*.js", self.handle_route)

        self.pair = "SOL_USDT"
        self.index_url = f"https://www.mexc.co/futures/{self.pair}?type=linear_swap"

        self.amount = 50
        self.leverage = 50

        self.login()

    # 设置请求拦截
    def handle_route(self, route, request):
        url = request.url
        if "https://static.mocortech.com/futures-v3/_next/static/chunks/8267" in url:
            logger.info(f"拦截到请求: {url}")
            # 读取本地修改过的 JS 文件
            with open("/Users/huangyue/Workspace/mexc_bot/js/static.mocortech.com/futures-v3/_next/static/chunks/8544.js", 
                        "r", encoding="utf-8") as f:
                modified_js = f.read()
            
            # 返回修改后的内容
            route.fulfill(
                status=200,
                content_type="application/javascript",
                body=modified_js
            )
        else:
            # 其他请求正常处理
            route.continue_() 
        
    def login(self):
        """
        登录 MEXC 交易所
        
        返回:
        bool: 登录是否成功
        """
        try:
            # 访问登录页面
            self.page.goto(self.index_url, timeout=120000)
            # 等待手动登陆，登陆完成后按回车键继续
            input("按回车键继续...")
            
            # 保存登录状态
            os.makedirs("./playwright_data", exist_ok=True)
            self.context.storage_state(path="./playwright_data/state.json")
            
            return True
        except Exception as e:
            logger.error(f"登录过程中出错: {e}")
            return False
        
    def get_open_position(self) -> dict:
        """
        获取持仓
        """
        js_code = """() => {
            if (window.mexcAPI && window.mexcAPI.getUserPositions) {
                return window.mexcAPI.getUserPositions();
            } else {
                return {"error": "getUserPositions function not available"};
            }
        }"""
        
        i = 0
        while i < self.retry_times:
            # 传递参数给JavaScript函数
            result = self.page.evaluate(
                js_code,
            )
            if result and result.get("success"):
                logger.info(f"获取持仓结果: {result}")
                return result
            i += 1
        logger.error(f"获取持仓结果失败")
        return None
    
    def get_open_stop_orders(self) -> dict:
        """
        获取止损订单
        """
        js_code = """() => {
            if (window.mexcAPI && window.mexcAPI.getOpenStopOrderList) {
                return window.mexcAPI.getOpenStopOrderList();
            } else {
                return {"error": "getOpenStopOrderList function not available"};
            }
        }"""

        result = self.page.evaluate(js_code)
        logger.info(f"获取止损订单结果: {result}")
        return result

    def long_entry(self) -> bool:
        """
        多头开仓
        """
        i = 0
        while i < self.retry_times:
            ret = self.open_position(self.pair, 1, 1, 5, self.amount, self.leverage)
            if ret and ret.get("success"):
                logger.info(f"多头开仓成功")
                return True
            i += 1
        logger.error(f"多头开仓失败")
        return False

    def short_entry(self) -> bool:
        """
        空头开仓
        """
        i = 0
        while i < self.retry_times:
            ret = self.open_position(self.pair, 3, 1, 5, self.amount, self.leverage)
            if ret and ret.get("success"):
                logger.info(f"空头开仓成功")
                return True
            i += 1
        logger.error(f"空头开仓失败")
        return False

    def close_open_position(self) -> bool:
        """
        平仓
        """
        i = 0
        while i < self.retry_times:
            ret = self.get_open_position()
            if ret and ret.get("data"):
                for position in ret["data"]:
                    position_type = 4 if position["positionType"] == 1 else 2
                    close_result = self.close_position(self.pair, position_type, 1, 5, position["positionId"], self.amount, self.leverage)
                    if not close_result or not close_result.get("success"):
                        logger.info(f"平仓失败，重试")
                        break 
                return True 
            i += 1
        logger.error(f"平仓失败")
        return False
    
    def set_open_stop_loss(self, price: float) -> bool:
        """
        设置止损
        """
        i = 0
        while i < self.retry_times:
            logger.info(f"设置止损，price: {price}")
            ret = self.get_open_position()
            if ret and ret.get("data"):
                position_id = ret["data"][0]["positionId"]
                set_stop_loss_result = self.set_stop_loss(price, 1, position_id, "SAME", 2, 2)
                if set_stop_loss_result and set_stop_loss_result.get("success"):
                    logger.info(f"设置止损成功")
                    return True
                elif set_stop_loss_result and set_stop_loss_result.get("success") == False:
                    logger.info(f"设置止损失败")
                    if set_stop_loss_result.get("code") == 5003:
                        return False
            i += 1
        logger.error(f"设置止损失败")
        return False

    def cancel_stop_loss(self) -> dict:
        """
        取消止损
        """
        js_code = """() => {
            if (window.mexcAPI && window.mexcAPI.cancelStopOrderAll) {
                return window.mexcAPI.cancelStopOrderAll({});
            } else {
                return {"error": "cancelStopOrderAll function not available"};
            }
        }"""

        result = self.page.evaluate(js_code)
        logger.info(f"取消止损结果: {result}")
        return result
    
    def set_stop_loss(self, price: float, loss_trend: int, position_id: int, profit_loss_vol_type: int, vol_type: int, take_profit_reverse: int) -> dict:
        """
        设置止损
        """
        js_code = """([price, loss_trend, position_id, profit_loss_vol_type, vol_type, take_profit_reverse]) => {
            if (window.mexcAPI && window.mexcAPI.addStopOrderByPosition) {
                return window.mexcAPI.addStopOrderByPosition({
                    stopLossPrice: price,
                    lossTrend: loss_trend,
                    positionId: position_id,
                    profitLossVolType: profit_loss_vol_type,
                    volType: vol_type,
                    takeProfitReverse: take_profit_reverse,
                    stopLossReverse: 1
                });
            } else {
                return {"error": "addStopOrderByPosition function not available"};
            }
        }"""
        
        # 传递参数给JavaScript函数
        result = self.page.evaluate(
            js_code, 
            [price, loss_trend, position_id, profit_loss_vol_type, vol_type, take_profit_reverse]
        )
        
        logger.info(f"设置空头止损结果: {result}")
        return result

    def close_position(self, symbol: str, side: int, open_type: int, order_type: int, position_id: int, 
                       vol: float, leverage: int) -> dict:
        """
        通过注入的JavaScript函数提交订单
        
        参数:
        symbol: 交易对，如 "BTC_USDT"
        side: 4为平多仓，3为平空仓
        open_type: 1为平仓
        order_type: 5为市价单
        position_id: 持仓ID
        vol: 数量
        leverage: 杠杆

        返回:
        dict: 订单结果
        """

        js_code = """([symbol, side, openType, orderType, positionId, vol, leverage]) => {
            if (window.mexcAPI && window.mexcAPI.submitOrder) {
                return window.mexcAPI.submitOrder({
                    symbol: symbol,
                    side: side,
                    openType: openType,
                    type: orderType,
                    positionId: positionId,
                    vol: vol,
                    leverage: leverage,
                    flashClose: true
                });
            } else {
                return {"error": "submitOrder function not available"};
            }
        }"""
        
        # 传递参数给JavaScript函数
        result = self.page.evaluate(
            js_code, 
            [symbol, side, open_type, order_type, position_id, vol, leverage]
        )
        
        logger.info(f"提交订单结果: {result}")
        return result

    def open_position(self, symbol: str, side: int, open_type: int, order_type: int, 
                      vol: float, leverage: int) -> dict:
        """
        通过注入的JavaScript函数提交订单
        
        参数:
        symbol: 交易对，如 "BTC_USDT"
        side: 方向，1为买入，3为卖出
        open_type: 开仓类型
        order_type: 订单类型，1为限价单, 5为市价单
        vol: 数量
        leverage: 杠杆
        
        返回:
        dict: 订单结果
        """
        # 使用函数形式而不是直接的代码块
        js_code = """([symbol, side, openType, orderType, vol, leverage]) => {
            if (window.mexcAPI && window.mexcAPI.submitOrder) {
                return window.mexcAPI.submitOrder({
                    symbol: symbol,
                    side: side,
                    openType: openType,
                    type: orderType,
                    vol: vol,
                    leverage: leverage,
                    marketCeiling: false
                });
            } else {
                return {"error": "submitOrder function not available"};
            }
        }"""
        
        # 传递参数给JavaScript函数
        result = self.page.evaluate(
            js_code, 
            [symbol, side, open_type, order_type, vol, leverage]
        )
        
        logger.info(f"提交订单结果: {result}")
        return result
    
    def close(self):
        """关闭浏览器"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

# 使用示例
if __name__ == "__main__":
    # 创建自动化实例
    mexc = MexcWebAutomation(headless=False)
    try:
        mexc.long_entry()
        time.sleep(10)
        mexc.set_open_stop_loss(2530)
        time.sleep(10)
        mexc.cancel_stop_loss()
        time.sleep(10)
        mexc.close_open_position()
        time.sleep(10)
    finally:
        # 确保浏览器正常关闭
        mexc.close()