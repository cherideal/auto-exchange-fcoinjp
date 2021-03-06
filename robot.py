# -*- coding: utf-8 -*-
# @Author: zz
# @Date:   2018-06-24 18:15:55
# @Last Modified by:   zhiz
# @Last Modified time: 2018-06-25 17:23:56
import logging
from fcoin import Fcoin
from fcoin_websocket.fcoin_client import fcoin_client
from auth import api_key, api_secret
from config import symbols, second, amount, price_difference, is_direct_buy, fees_start_time, price_range, trade_range, price_diff, order_count_diff
import os, time, base64
from datetime import datetime
import time

symbol = symbols[0] + symbols[1]


class Robot(object):
    logging.basicConfig(filename='logger.log', level=logging.WARN)
    
    """docstring for Robot"""
    def __init__(self):
        self.fcoin = Fcoin(api_key, api_secret)

    # 截取指定小数位数
    def trunc(self, f, n):
        return round(f, n)

    def ticker_handler(self, message):
        if 'ticker' in message:
            self.ticker = message['ticker']
        # print('ticker', self.ticker)

    def symbols_action(self):
        all_symbols = self.fcoin.get_symbols()
        for info in all_symbols:
            if symbol == info['name']:
                self.price_decimal = int(info['price_decimal'])
                self.amount_decimal = int(info['amount_decimal'])
                print('price_decimal:', self.price_decimal, 'amount_decimal:', self.amount_decimal)
                return

    # 查询账户余额
    def get_balance_action(self, symbols, specfic_symbol = None):
        balance_info = self.fcoin.get_balance()
        specfic_balance = 0
        for info in balance_info['data']:
            for symbol in symbols:
                if info['currency'] == symbol:
                    balance = info
                    print(balance['currency'], '账户余额', balance['balance'], '可用', balance['available'], '冻结', balance['frozen'])
                    if info['currency'] == specfic_symbol:
                        specfic_balance = float(info['available'])
        return specfic_balance

    # 买操作
    def buy_action(self, this_symbol, this_price, this_amount, diff, should_repeat = 0):
        ticker = self.ticker
        cur_price = str(self.trunc(this_price - diff, self.price_decimal))
        print('准备买入', this_price, ticker)
        buy_result = self.fcoin.buy(this_symbol, cur_price, str(this_amount))
        print('buy_result is', buy_result)
        buy_order_id = buy_result['data']
        if buy_order_id:
            print('++++++++++++++++++++++++++++买单: ' + cur_price + '价格成功委托, 订单ID: ' + buy_order_id)
            logging.warning('买单: ' + cur_price + '价格成功委托, 订单ID: ' + buy_order_id)
        return buy_order_id

    # 卖操作
    def sell_action(self, this_symbol, this_price, this_amount, diff):
        ticker = self.ticker
        cur_price = str(self.trunc(this_price + diff, self.price_decimal))
        print('准备卖出', cur_price, ticker)
        sell_result = self.fcoin.sell(this_symbol, cur_price, str(this_amount))
        print('sell_result is: ', sell_result)
        sell_order_id = sell_result['data']
        if sell_order_id:
            print('----------------------------卖单: ' + cur_price + '价格成功委托, 订单ID: ' + sell_order_id)
            logging.warning('卖单: ' + cur_price + '价格成功委托, 订单ID: ' + sell_order_id)
        return sell_order_id

    def list_active_orders(self, this_symbol, state = 'submitted'):
        dt = datetime(fees_start_time['year'], fees_start_time['month'], fees_start_time['day'], fees_start_time['hour'], fees_start_time['minute'], fees_start_time['second'])
        timestamp = int(dt.timestamp() * 1000)
        return self.fcoin.list_orders(symbol = this_symbol, states = state, after = timestamp)

    def get_order_count(self, this_symbol):
        order_list = self.list_active_orders(this_symbol)
        order_buy = 0
        order_sell = 0
        price_buy_max = 0
        price_buy_min = 655350
        id_buy_min = ""
        price_sell_min = 655350
        price_sell_max = 0
        id_sell_max  = ""
        for i in range(len(order_list['data'])):
            price_cur = float(order_list['data'][i]['price'])
            if order_list['data'][i]['side'] == 'buy':
                order_buy = order_buy + 1
                if price_cur > price_buy_max:
                    price_buy_max = price_cur
                if price_cur < price_buy_min:
                    price_buy_min = price_cur
                    id_buy_min = order_list['data'][i]['id']
            else:
                order_sell = order_sell + 1
                if price_cur < price_sell_min:
                    price_sell_min = price_cur
                if price_cur > price_sell_max:
                    price_sell_max = price_cur
                    id_sell_max = order_list['data'][i]['id']
        order_price_range = abs(price_sell_max - price_buy_min)
        print("buy_count:", order_buy, "buy_min:", price_buy_min, "buy_max:", price_buy_max, "sell_count:", order_sell, "sell_min", price_sell_min, "sell_max", price_sell_max, "order_price_range", order_price_range)
        return (order_buy, price_buy_max, id_buy_min, order_sell, price_sell_min, id_sell_max, order_price_range)

    def adjust(self, real_diff, order_price):
        diff = order_price * price_diff
        if (diff < real_diff):
            diff = real_diff
        buy_diff = diff
        sell_diff = diff
        return (buy_diff, sell_diff)

    def strategy(self, symbol, order_price, amount, real_diff):
        order_buy, price_buy_max, id_buy_min, order_sell, price_sell_min, id_sell_max, order_price_range = self.get_order_count(symbol)
        if (order_price_range > trade_range):
            if (order_buy > order_sell + order_count_diff):
                if "" != id_buy_min:
                    print("order_price_range:", order_price_range, "buy_order_cancel:", id_buy_min)
                    self.fcoin.cancel_order(id_buy_min)
            if (order_sell > order_buy + order_count_diff):
                if "" != id_sell_max:
                    print("order_price_range", order_price_range, "sell_order_cancel:", id_sell_max)
                    self.fcoin.cancel_order(id_sell_max)

        buy_diff, sell_diff = self.adjust(real_diff, order_price)
        cur_price_range = price_range * order_price
        if ((price_buy_max + cur_price_range) < order_price):
            try:
                buy_id = self.buy_action(symbol, order_price, amount, buy_diff)
            except Exception as err:
                print("failed to buy", err)
        if ((price_sell_min - cur_price_range) > order_price):
            try:
                sell_id = self.sell_action(symbol, order_price, amount, sell_diff)
            except Exception as err:
                print("failed to sell", err)

    def trade(self):
        time.sleep(second)
        ticker = self.ticker
        newest_price = ticker[0]
        high_bids = ticker[2]
        high_bids_amount = ticker[3]
        low_ask = ticker[4]
        low_ask_amount = ticker[5]
        order_price = self.trunc((low_ask + high_bids) / 2, self.price_decimal)
        real_price_difference = float(low_ask - high_bids)
        print('最低卖价:', low_ask, '最高买价', high_bids, '欲下订单价: ', order_price, 
                '当前差价:', '{:.9f}'.format(real_price_difference), '设定差价:', '{:.9f}'.format(price_difference))
        if real_price_difference > price_difference:
            print('现在价格:', newest_price, '挂单价格', order_price)
            self.strategy(symbol, order_price, amount, real_price_difference / 2)
        else:
            print('差价太小，放弃本次成交')

    def run(self):
        self.client = fcoin_client()
        self.client.start()
        self.client.subscribe_ticker(symbol, self.ticker_handler)
        self.symbols_action()
        self.get_balance_action(symbols)
        
        time = 0
        while True:
            self.trade()
            time = time + 1
            if (time > 100):
                break

if __name__ == '__main__':
    try:
        while (True):
            robot = Robot()
            robot.run()
    except KeyboardInterrupt:
        os._exit(1)




