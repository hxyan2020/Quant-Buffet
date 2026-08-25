# Original QuantConnect / library Python
# locale=zh slug="在中国对抗贝塔（beta）投资策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from scipy import stats
from AlgorithmImports import *
from typing import List, Dict
from pandas.core.frame import DataFrame
from pandas.core.series import Series
import data_tools
class BettingAgainstBetaInChina(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)
    
    self.leverage: float = 5
    self.period: int = 12 * 21 * 5 # 5 years of daily data
    self.traded_portion: float = 0.2
    self.data: Dict[Symbol, data_tools.SymbolData] = {}
    self.weight: Dict[Symbol, float] = {}

    symbol: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(symbol), self.TimeRules.AfterMarketOpen(symbol), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    
    if not self.selection_flag:
        return Universe.Unchanged
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.CompanyReference.BusinessCountryID == 'CHN'
    ]
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol in self.data:
            continue
        self.data[symbol] = data_tools.SymbolData(self.period)
        history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet")
            continue
        closes: Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].update(close)
    daily_returns: Dict[Symbol, np.ndarray] = {
        x.Symbol : self.data[x.Symbol].daily_returns() for x in selected if self.data[x.Symbol].is_ready()
    }
    
    if len(daily_returns) == 0:
        return Universe.Unchanged
        
    daily_returns_for_mean: np.ndarray = np.array([x[1] for x in daily_returns.items()])
    mean_daily_returns: List[float] = [np.mean(daily_returns_for_mean[:, i]) for i in range(len(daily_returns_for_mean[0]))]
    
    betas: Dict[Symbol, float] = {}
    for symbol, returns in daily_returns.items():
        regression_result = stats.linregress(mean_daily_returns, returns)
        betas[symbol] = regression_result[0]
        
    beta_median: float = np.median([x[1] for x in betas.items()])
    sorted_by_beta: List[Symbol] = [x[0] for x in sorted(betas.items(), key = lambda item: item[1], reverse = True)]
    
    # portfolios
    long: List[Symbol] = []
    short: List[Symbol] = []
    
    total_long_rank: float = 0.
    total_short_rank: float = 0.
    
    for symbol in sorted_by_beta:
        if betas[symbol]  beta_median:
            total_short_rank += betas[symbol]
            short.append(symbol)
    
    # Lowest beta has highest weight.
    # long and short lists are sorted ascending according to beta value.
    long_weights: List[float] = reversed([(betas[x] / total_long_rank) for x in long])
    short_weights: List[float] = reversed([(betas[x] / total_short_rank) for x in short])
    
    for i, portfolio_weights in enumerate([zip(long, long_weights), zip(short, short_weights)]):
        for symbol, weight in portfolio_weights:
            self.weight[symbol] = ((-1) ** i) * weight * self.traded_portion
    
    return long + short
    
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)  
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
class SymbolData():
def __init__(self, period: int) -> None:
    self.closes: RollingWindow = RollingWindow[float](period)
    
def update(self, close: float) -> None:
    self.closes.Add(close)
    
def is_ready(self) -> bool:
    return self.closes.IsReady
    
def daily_returns(self) -> np.ndarray:
    closes: np.ndarray = np.array([x for x in self.closes])
    returns: np.ndarray = (closes[:-1] - closes[1:]) / closes[1:]
    return returns
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
