# Original QuantConnect / library Python
# locale=en slug="货币动量因子策略-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
from AlgoLib import *

class CurrencyMomentumFactor(XXX):
'''该类实现了一种利用期货合约的货币动量因子策略。它根据货币的动量选择了一部分货币，该动量是在预定义的时期内计算的，并且每月将投资组合重新平衡到多头和空头头寸。'''

def Initialize(self):
    '''初始化算法设置，包括开始日期、初始资金、数据订阅、费率模型、杠杆和指标。它还设置了一个预热期，用于预加载历史数据进行动量计算。'''
    
    self.SetStartDate(2000, 1, 1)  # 设置回测的起始日期
    self.SetCash(100000)  # 设置初始资金

    self.data = {}  # 初始化一个字典来存储数据订阅
    self.period = 12 * 21  # 定义动量计算的回溯期
    self.SetWarmUp(self.period, Resolution.Daily)  # 设置预热期

    self.symbols = [
        "CME_AD1", "CME_BP1", "CME_CD1", "CME_EC1", 
        "CME_JY1", "CME_MP1", "CME_NE1", "CME_SF1"
    ]
    # 要交易的期货合约列表
    
    for symbol in self.symbols:
        data = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(5)
        self.data[symbol] = self.ROC(symbol, self.period, Resolution.Daily)
    
    self.recent_month = -1  # 用于跟踪每月重新平衡的当前月份的变量
    
def OnData(self, data):
    '''每当收到新数据时调用此方法。它检查是否是根据当前月份重新平衡投资组合的时间。如果是，它会根据变化率 (ROC) 指标计算每种货币的表现，对它们进行排名，并根据排名将投资组合重新平衡为多头和空头头寸。'''
    
    if self.IsWarmingUp:  # 如果正在预热数据，则跳过
        return

    if self.Time.month == self.recent_month:  # 检查是否需要每月重新平衡
        return
    self.recent_month = self.Time.month

    performance = {x[0]: x[1].Current.Value for x in self.data.items() if self.data[x[0]].IsReady and x[0] in data and data[x[0]]}
    # 计算表现并过滤已准备好的符号
    
    long_symbols = []
    short_symbols = []
    if len(performance) >= 6:  # 确保有足够的符号进行排名
        sorted_performance = sorted(performance.items(), key=lambda x: x[1], reverse=True)
        long_symbols = [x[0] for x in sorted_performance[:3]]  # 选择前3个用于多头头寸
        short_symbols = [x[0] for x in sorted_performance[-3:]]  # 选择最后3个用于空头头寸

    
    invested_symbols = [x.Key.Value for x in self.Portfolio if x.Value.Invested] # 执行交易
    for symbol in invested_symbols:
        if symbol not in long_symbols + short_symbols:
            self.Liquidate(symbol)  # 清算不在当前多头或空头列表中的头寸
            
    for symbol in long_symbols:
        self.SetHoldings(symbol, 1 / len(long_symbols))  # 设置多头头寸
    for symbol in short_symbols:
        self.SetHoldings(symbol, -1 / len(short_symbols))  # 设置空头头寸
