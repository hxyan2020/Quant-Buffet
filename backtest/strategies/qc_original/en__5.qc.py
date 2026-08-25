# Original QuantConnect / library Python
# locale=en slug="美国股市未来5个月回报预测策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
# endregion
class ANewPredictabilityPatternInTheUSStockMarketReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    # NOTE be cautions about combination of signal months, lag and holding period while setting up the algorithm
    self.required_months:list[int] = [12, 1]    # NOTE these should be following months
    self.lag:int = 5
    self.holding_period:int = 2
    self.trade_month:int = (datetime(2000, self.required_months[1], 1) + relativedelta(months=self.lag-1)).date().month
    self.prices:dict[list[float]] = { month: [] for month in self.required_months }
    self.dow_jones:Symbol = self.AddEquity('DIA', Resolution.Daily).Symbol
    self.recent_month:int = -1
def OnData(self, data: Slice):
    curr_date:datetime.date = self.Time
    curr_month:int = curr_date.month
    # store required daily prices
    if curr_month in self.required_months:
        if self.dow_jones in data and data[self.dow_jones]:
            price:float = data[self.dow_jones].Price
            self.prices[curr_month].append(price)
    if curr_month == self.recent_month:
        return
    self.recent_month = curr_month
    # open position
    if curr_month == self.trade_month:
        if all(lookup_month in self.prices and len(self.prices[lookup_month]) > 0 for lookup_month in self.required_months):
            perf:float = (self.prices[self.required_months[1]][-1] / self.prices[self.required_months[0]][0]) - 1
            # trade execution
            if perf > 0:
                self.SetHoldings(self.dow_jones, 1)
            else:
                self.SetHoldings(self.dow_jones, -1)
            
            self.prices[self.required_months[0]].clear()
            self.prices[self.required_months[1]].clear()
        else:
            self.Liquidate(self.dow_jones)
            return
    
    # close position
    if curr_month == self.trade_month + self.holding_period and self.Portfolio[self.dow_jones].Invested:
        self.Liquidate(self.dow_jones)
