import os
import sys
import time 
from DrissionPage import ChromiumPage, ChromiumOptions
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MexcWebAutomation:
    def __init__(self, headless=False):
        """
        初始化 MEXC 网页自动化测试程序
        
        参数:
        headless: 是否使用无头模式，默认为 False
        """
        # 配置浏览器选项
        options = ChromiumOptions()
        options.headless = headless
        
        # 可选：设置用户数据目录，保存登录状态
        options.set_user_data_path('./dp_data')
        
        # 初始化浏览器
        self.page = ChromiumPage(options)
        self.pair = "SOL_USDT"
        self.index_url = f"https://www.mexc.com/zh-MY/futures/{self.pair}?type=linear_swap"

        self.amount = 40
        self.leverage = 1

        self.login()
        
    def login(self):
        """
        登录 MEXC 交易所
        
        参数:
        username: 用户名/邮箱
        password: 密码
        
        返回:
        bool: 登录是否成功
        """
        try:
            # 访问登录页面
            self.page.get(self.index_url)
            # 等待手动登陆，登陆完成后按回车键继续
            input("按回车键继续...")
                
        except Exception as e:
            print(f"登录过程中出错: {e}")
            return False
            
    def long_entry(self) -> bool:
        """
        多头开仓
        """
        # 定位 class="InputNumberExtend_wrapper__qxkpD tebK37f6 extend-wrapper"的div下的input
        input_amount_element = self.page.ele('xpath://div[contains(@class, "InputNumberExtend_wrapper__qxkpD tebK37f6 extend-wrapper")]/input')
        if input_amount_element:
            input_amount_element.input(self.amount * self.leverage)
        else:
            logger.info("输入金额元素不存在")
            return False


        # 定位 data-testid="contract-trade-open-long-btn" 的button
        long_btn = self.page.ele('xpath://button[@data-testid="contract-trade-open-long-btn"]')
        if long_btn:
            long_btn.click()
            logger.info(f"多头开仓成功，开仓数量：{self.amount * self.leverage}")
            return True
        else:
            logger.info("多头开仓按钮不存在")
            return False

    def short_entry(self) -> bool:
        """
        空头开仓
        """
        # 定位 class="InputNumberExtend_wrapper__qxkpD tebK37f6 extend-wrapper"的div下的input
        input_amount_element = self.page.ele('xpath://div[contains(@class, "InputNumberExtend_wrapper__qxkpD tebK37f6 extend-wrapper")]/input')
        if input_amount_element:
            input_amount_element.input(self.amount * self.leverage)
        else:
            logger.info("输入金额元素不存在")
            return False

        # 定位 data-testid="contract-trade-open-short-btn" 的button
        short_btn = self.page.ele('xpath://button[@data-testid="contract-trade-open-short-btn"]')
        if short_btn:
            short_btn.click()
            logger.info(f"空头开仓成功，开仓数量：{self.amount * self.leverage}")
        else:
            logger.info("空头开仓按钮不存在")
            return False
        return True
    
    def cancel_stop(self) -> bool:
        """
        取消止损
        """
        # 定位 class="InputNumberExtend_wrapper__qxkpD tebK37f6 extend-wrapper"的div下的input
        current_entrust_tab = self.page.ele('@id=rc-tabs-0-tab-4')
        if current_entrust_tab:
            current_entrust_tab.click()
        else:
            logger.info("当前委托标签不存在")
            return False

        # 定位 class="InputNumberExtend_wrapper__qxkpD tebK37f6 extend-wrapper"的div下的input
        # stop_loss_tab = self.page.ele('@id=rc-tabs-4-tab-4')
        # stop_loss_tab.click()

        # 定位 class="InputNumberExtend_wrapper__qxkpD tebK37f6 extend-wrapper"的div下的input
        cancel_btn = self.page.ele('xpath://*[@id="mexc-web-inspection-futures-exchange-current-entrust"]/section/div[1]/div/div/div/div/div/table/tbody/tr[2]/td[8]/div/button')
        if cancel_btn:
            cancel_btn.click()
            logger.info(f"取消止损成功")
            return True
        else:
            logger.info("取消止损按钮不存在")
            return False
    
    def set_stop(self, price: float) -> bool:
        """
        设置止损
        """
        i = 0
        
        while i < 3:
            if i == 0:
                current_position_tab = self.page.ele('@id=rc-tabs-0-tab-1')
                if current_position_tab:
                    current_position_tab.click()
                else:
                    logger.info("当前持仓标签不存在")
                    return False

                set_stop_btn = self.page.ele('xpath://*[@id="mexc-web-inspection-futures-exchange-current-position"]/div[1]/div/div/div/div/div/table/tbody/tr[2]/td[12]/div/div/span')
                if set_stop_btn:
                    set_stop_btn.click()
                else:
                    logger.info("设置止损按钮不存在")
                    return False
                
                # 等待弹框出现
                self.page.wait.ele_displayed('css:.ant-modal-content', timeout=5)
                
                # 使用更可靠的选择器定位输入价格的元素
                input_price_elements = self.page.eles('css:.ant-modal-content input[placeholder*="价格"]')
                
                if input_price_elements:
                    input_price_elements[-1].input(price)
                else:
                    logger.error("无法找到价格输入框")
                    return False
                
                # 使用更可靠的选择器定位反向开仓复选框
                reverse_check_boxes = self.page.eles('css:.ant-modal-content .ant-checkbox-input')
                if reverse_check_boxes:
                    reverse_check_boxes[-1].click()
                else:
                    logger.warning("无法找到反向开仓复选框")
            
            # 使用更可靠的选择器定位确认按钮
            confirm_btn = self.page.ele('css:.ant-modal-content .ant-btn-primary')
            if confirm_btn:
                confirm_btn.click()
                logger.info(f"设置止损成功，止损价格：{price}")
            else:
                logger.error("无法找到确认按钮")
                i += 1
                continue
            
            # if self.page.wait.ele_displayed('@text()=多仓止损价需小于当前最新价', timeout=1) \
            #     or self.page.wait.ele_displayed('@text()=空仓止损价需大于当前最新价', timeout=1) \
            #     or self.page.wait.ele_displayed('@text()=止损价设置有误', timeout=1):
            #     logger.error("设置止损失败")
            #     i += 1
            #     self.page.wait(1)
            #     continue

            if self.page.wait.ele_displayed('xpath:/html/body/div[13]/div/div[2]/div', timeout=5):
                risk_confirm_btn = self.page.ele('xpath:/html/body/div[13]/div/div[2]/div/div[2]/div[3]/div/button[2]')
                if risk_confirm_btn:
                    risk_confirm_btn.click()
                    logger.info(f"确认风险")
                else:
                    logger.error("无法找到确认风险按钮")
                    i += 1
                    continue
            
            return True
        
        cancel_btn = self.page.ele('css:.ant-modal-content .ant-btn-default')
        if cancel_btn:
            cancel_btn.click()
            logger.info(f"取消设置止损")
        return False

    def close_position(self) -> bool:
        """
        平仓(都是闪电平仓，共用函数)
        """
        current_position_tab = self.page.ele('@id=rc-tabs-0-tab-1')
        if current_position_tab:
            current_position_tab.click()
        else:
            logger.info("当前持仓标签不存在")
            return False

        # 先判断闪电平仓的按钮是否存在
        flash_close_btn = self.page.ele('@text()=闪电平仓')
        if flash_close_btn:
            flash_close_btn.click()
            logger.info(f"闪电平仓成功")
        else:
            logger.info("闪电平仓按钮不存在")
            return False
        return True
            
        
    def close(self):
        """关闭浏览器"""
        self.page.quit()

# 使用示例
if __name__ == "__main__":
    # 创建自动化实例
    mexc = MexcWebAutomation(headless=False)
    
    mexc.long_entry()
    time.sleep(3)
    # mexc.short_entry()
   
    mexc.set_stop(146.1)
    time.sleep(10)
    mexc.cancel_stop()
    # time.sleep(10)
    # mexc.set_stop(100)
    # time.sleep(10)
    # mexc.cancel_stop()
    mexc.close_position()