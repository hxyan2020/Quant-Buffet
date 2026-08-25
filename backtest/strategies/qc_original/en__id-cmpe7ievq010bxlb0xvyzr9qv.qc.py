# Original QuantConnect / library Python
# locale=en slug="因子策略-小市值因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List

class SmallCapPremiumStrategy(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)  # 算法的起始日期
    self.SetCash(100000)  # 算法的初始资金

    self.UniverseSettings.Leverage = 5  # 杠杆
    self.UniverseSettings.Resolution = Resolution.Daily  # 数据请求的分辨率
    self.AddUniverse(self.SelectStocks)  # 添加投资标的选择方法
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0  # 设置最低保证金
    
    self.long_list: List[Symbol] = []  # 多头股票列表
    self.short_list: List[Symbol] = []  # 空头股票列表

    self.market_ids: List[str] = ['NYSE', 'NASDAQ', 'AMEX']  # 目标交易所
    self.top_stocks_count: int = 3000  # 基于市值考虑的股票数量
    
    self.deciles: int = 10  # 分为十分位
    self.rebalance_period: int = 12  # 每月重新平衡
    self.should_rebalance: bool = True  # 重新平衡标志

    spy_symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthEnd(spy_symbol), 
                     self.TimeRules.AfterMarketOpen(spy_symbol), 
                     self.RebalancePortfolio)

def SelectStocks(self, fundamentals: List[Fundamental]) -> List[Symbol]:
    if not self.should_rebalance:
        return Universe.Unchanged

    filtered_stocks = [f for f in fundamentals if f.HasFundamentalData and f.SecurityReference.ExchangeId in self.market_ids]
    sorted_by_cap = sorted(filtered_stocks, key=lambda x: x.MarketCap)[:self.top_stocks_count]

    if len(sorted_by_cap) >= self.deciles:
        size = len(sorted_by_cap) // self.deciles
        self.long_list = [x.Symbol for x in sorted_by_cap[:size]]
        self.short_list = [x.Symbol for x in sorted_by_cap[-size:]]

    return self.long_list + self.short_list

def OnData(self, data: Slice):
    if not self.should_rebalance:
        return
    
    self.should_rebalance = False
    investments = [PortfolioTarget(symbol, 1 / len(self.long_list)) for symbol in self.long_list] + \
                  [PortfolioTarget(symbol, -1 / len(self.short_list)) for symbol in self.short_list]

    self.SetHoldings(investments)

    self.long_list.clear()
    self.short_list.clear()

def RebalancePortfolio(self):
    self.should_rebalance = True

def OnSecuritiesChanged(self, changes: SecurityChanges):
    for security in changes.AddedSecurities:
        security.SetFeeModel(SimpleFeeModel())

class SimpleFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
