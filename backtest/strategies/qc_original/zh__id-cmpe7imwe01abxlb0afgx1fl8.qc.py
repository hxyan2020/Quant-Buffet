# Original QuantConnect / library Python
# locale=zh slug="彩票型股票与过去表现"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from pandas.core.frame import DataFrame
class LotteryStocksandPastPerformance(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)  
    self.SetCash(100000) 
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.period:int = 3 * 21
    self.performance_quantile:int = 3
    self.lottery_quantile:int = 10
    self.leverage:int = 5
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.weight:Dict[Symbol, float] = {}
    
    # Daily price data.
    self.data:Dict[Symbol, RollingWindow] = {}
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)
            
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    performance:Dict[Fundamental, float] = {}
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = RollingWindow[float](self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].Add(close)
        
        if self.data[symbol].IsReady:
            performance[stock] = self.data[symbol][0] / self.data[symbol][self.period-1] - 1
    if len(performance) >= self.performance_quantile * self.lottery_quantile:
        # Performance sorting.
        sorted_by_performance:List[Fundamental] = sorted(performance, key = performance.get, reverse = True)
        quantile:int = int(len(sorted_by_performance) / self.performance_quantile)
        losers:List[Fundamental] = sorted_by_performance[-quantile:]
        
        # MAX calc.
        lottery:Dict[Fundamental, float] = {}
        for stock in losers:
            daily_closes:np.ndarray = np.array([x for x in self.data[stock.Symbol]][:21])
            daily_returns:np.ndarray = (daily_closes[:-1] - daily_closes[1:]) / daily_closes[1:]
            lottery[stock] = max(daily_returns)
        
        # Lottery sorting.
        sorted_by_lottery = sorted(lottery, key = lottery.get, reverse = True)
        quantile:int = int(len(lottery) / self.lottery_quantile)
        long:List[Fundamental] = sorted_by_lottery[-quantile:]
        short:List[Fundamental] = sorted_by_lottery[:quantile]
    
        # Market cap weighting.
        for i, portfolio in enumerate([long, short]):
            mc_sum:float = sum(map(lambda x: x.MarketCap, portfolio))
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum

    return list(self.weight.keys())

def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
                    
def Selection(self) -> None:
    self.selection_flag = True
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
