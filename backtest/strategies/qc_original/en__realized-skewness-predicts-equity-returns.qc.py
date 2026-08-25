# Original QuantConnect / library Python
# locale=en slug="realized-skewness-predicts-equity-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from collections import deque
from scipy.stats import skew
import numpy as np
from pandas.core.frame import DataFrame
#endregion
class RealizedSkewnessPredictsEquityReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Minute).Symbol
    # 5-minute price data.
    self.data:Dict[Symbol, deque] = {}
    self.period:int = 5 * 78
    self.rebalance_month:int = 12
    self.leverage:int = 5
    self.quantile:int = 10
    self.min_share_price:float = 5.
    
    self.fundamental_count:int = 100
    self.fundamental_sorting_key = lambda x: x.MarketCap
    # Yearly selected universe with symbol and market cap data.
    self.selected_universe:List[Fundamental] = []
    
    self.month:int = 12
    self.days:int = 5
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        symbol = security.Symbol
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
        if symbol not in self.data:
            history:DataFrame = self.History(symbol, self.period * 5, Resolution.Minute)
            if len(history) == self.period and 'close' in history:
                closes_1M:List[float] = list(history['close'])
                closes_5M:List[float] = closes_1M[::5]
                self.data[symbol] = deque(closes_5M, maxlen = self.period)
    
    # Remove old stocks from selected universe data.
    for security in changes.RemovedSecurities:
        if security.Symbol in self.data:
            del self.data[security.Symbol]
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag: 
        return Universe.Unchanged
    self.selection_flag = False
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price >= self.min_share_price
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    self.selected_universe = selected
    
    return list(map(lambda x: x.Symbol, selected))
    
def OnData(self, data: Slice) -> None:
    if self.Time.minute % 5 == 0:
        # Store 5 minute data.
        for symbol in self.data:
            if symbol in data and data[symbol]:
                price = data[symbol].Value
                self.data[symbol].append(price)
    if not (self.Time.hour == 16 and self.Time.minute == 0):
        return
    if self.days == 5:
        aggregate_skewness:Dict[Symbol, float] = {}
        for stock in self.selected_universe:
            symbol:Symbol = stock.Symbol
            # 5 Minute data is ready.
            if symbol in self.data and len(self.data[symbol]) == self.data[symbol].maxlen:
                closes_5M:np.ndarray = np.array(self.data[symbol])
                returns_5M:np.ndarray = (closes_5M[1:] - closes_5M[:-1]) / closes_5M[:-1]
                skewness:float = skew(returns_5M)
                aggregate_skewness[stock] = skewness
                        
        if len(aggregate_skewness) != 0:
            # Aggregate skewness sorting.
            sorted_by_aggregate_skewness:List = sorted(aggregate_skewness.items(), key = lambda x: x[1], reverse = True)
            quantile:int = int(len(sorted_by_aggregate_skewness) / self.quantile)
            long:List[Fundamental] = [x[0] for x in sorted_by_aggregate_skewness[-quantile:]]
            short:List[Fundamental] = [x[0] for x in sorted_by_aggregate_skewness[:quantile]]
        
            weight:Dict[Symbol, float] = {}
            # Market cap weighting.
            for i, portfolio in enumerate([long, short]):
                mc_sum:float = sum(map(lambda x: x.MarketCap, portfolio))
                for stock in portfolio:
                    weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum
                    
            # Trade execution.
            portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in weight.items() if symbol in data and data[symbol]]
            self.SetHoldings(portfolio, True)
    
    self.days += 1
    if self.days > 5:
        self.days = 1      

def Selection(self) -> None:
    if self.month == self.rebalance_month:
        self.selection_flag = True
    
    self.month += 1
    if self.month > 12:
        self.month = 1
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
