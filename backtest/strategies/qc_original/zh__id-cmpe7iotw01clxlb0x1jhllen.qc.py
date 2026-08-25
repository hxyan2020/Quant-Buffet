# Original QuantConnect / library Python
# locale=zh slug="中国市场的季节性差异"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List, Dict
from pandas.core.frame import DataFrame
from pandas.core.series import Series
#endregion
class SeasonalDifferenceInChina(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)
    
    self.period: int = 5 * 21 # storing n months of daily prices for each month
    self.quantile: int = 10
    self.leverage: int = 10
    self.min_share_price: float = 1.
    self.market_cap_quantile: int = 3
    self.traded_percentage: float = .1
    self.data: Dict[Symbol, SymbolData] = {}
    self.weight: Dict[Symbol, float] = {}
    
    market: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.selection_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    current_month: int = self.Time.month
    # update the rolling window every day
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].update(current_month, stock.AdjustedPrice)
    
    # rebalace monthly
    if not self.selection_flag:
        return Universe.Unchanged
    selected: List[Fundamental] = [
        f for f in fundamental if f.HasFundamentalData 
        and f.MarketCap != 0 
        and f.Market == 'usa' 
        and f.CompanyReference.BusinessCountryID == 'CHN' 
        and f.Price >= self.min_share_price
    ]
    # exclude 30% of lowest stocks by MarketCap
    sorted_by_market_cap: List[Fundamental] = sorted(selected, key = lambda x: x.MarketCap)
    selected = sorted_by_market_cap[int(len(sorted_by_market_cap) / self.market_cap_quantile):]
    seasonal_difference: Dict[Fundamental, float] = {}
    
    # calculate seasonal return for this month 
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        # Get stock's closes
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            # five years of daily prices
            history: DataFrame = self.History(symbol, self.period * 12, Resolution.Daily)
            
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            
            closes: Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(time.month, close)
        
        if self.data[symbol].is_ready():
            # calculate average return for each month separately
            months_averages: Dict[int, float] = self.data[symbol].months_averages()
            
            # get seasonal momentum of the month
            same_month_avg_return: Dict[int, float] = months_averages[current_month]
            
            # sum averages of all other seasonal returns
            other_months_avg_return: float = sum([avg_return for month_num, avg_return in months_averages.items() if month_num != current_month])
            
            # calculate seasonal diffrence for current stock
            seasonal_difference[stock] = same_month_avg_return - other_months_avg_return
    
    if len(seasonal_difference)  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if slice.contains_key(symbol) and slice[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
class SymbolData():
def __init__(self, period: int) -> None:
    self.daily_prices: Dict[int, RollingWindow] = {}
    
    for i in range(1, 13):
        # Storing daily prices under month number
        self.daily_prices[i] = RollingWindow[float](period)
    
def update(self, month: int , close: float) -> None:
    self.daily_prices[month].Add(close)
    
def is_ready(self) -> bool:
    for _, rolling_window in self.daily_prices.items():
        # Return False if atleast one rolling window in dictionary isn't ready
        if not rolling_window.IsReady:
            return False
    
    # If all rolling windows are ready return True
    return True
    
def months_averages(self) -> Dict[int, float]:
    averages: Dict[int, float] = {}
    
    for month_num, rolling_window in self.daily_prices.items():
        month_performances: List[float] = []
        closes: List[float] = list(rolling_window)
        
        # calculate month performacnes
        for i in range(0, len(closes), 21):
            month_closes: List[float] = closes[i:i+21]
            performance: float = (month_closes[0] - month_closes[-1]) / month_closes[-1]
            month_performances.append(performance)
            
        averages[month_num] = np.mean(month_performances)
        
    return averages
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
