# -*- coding: utf-8 -*-
# @Author: zz
# @Date:   2018-06-24 18:15:55
# @Last Modified by:   zhiz
# @Last Modified time: 2018-06-25 17:34:04


# 交易类型
symbols = ['btc', 'usdt']
# 数量
amount = 0.002
# 深度图买一卖一差值
price_difference = 0.000004
# 当前直接购买 （万二的差价，1直接下单）
is_direct_buy = 1
# 查询余额类型
symbol_type = ['usdt', 'fj', 'btc']
# 买卖间隔时间
second = 0.5
# 下单价格间隔，避免重复下单
price_range = 0.0003
#买卖差价
price_diff = 0.00005
#交易价格区间
trade_range = 50
#订单数量区间
order_count_diff = 15


# 需要计算手续费的开始时间
fees_start_time = {
	'year': 2018,
	'month': 11,
	'day': 15,
	'hour': 23,
	'minute': 0,
	'second': 0
}

