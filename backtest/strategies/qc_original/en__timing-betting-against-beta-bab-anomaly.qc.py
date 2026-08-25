# Original QuantConnect / library Python
# locale=en slug="timing-betting-against-beta-bab-anomaly"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from math import sqrt
import pandas as pd
from scipy import stats
from typing import Dict, List

class TimingBettingAgainstBetaAnomaly(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.exchange_codes:List[str] = ['NYS']	

    # Daily price data.
    self.data:Dict[Symbol, RollingWindow] = {}
    self.period:int = 21

    self.leverage:int = 10
    self.min_share_price:int = 5

    # Warmup market daily data.
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.data[self.symbol] = RollingWindow[float](self.period)
    history:DataFrame = self.History(self.symbol, self.period, Resolution.Daily)
    if history.empty:
        self.Log(f"Not enough data for {self.symbol} yet")
    else:
        closes:Series = history.loc[self.symbol].close
        for time, close in closes.items():
            self.data[self.symbol].Add(close)
    
    self.target_volatility:float = 0.12
    
    self.weight:Dict[Symbol, float] = {}
    
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 250
    
    self.selection_flag = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)

    self.settings.daily_precise_end_time = False

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        if symbol in self.data:
            # Store daily price.
            self.data[symbol].Add(stock.AdjustedPrice)
    
    # Selection once a month.
    if not self.selection_flag:
        return Universe.Unchanged
    
    # selected = [x.Symbol for x in fundamental if x.HasFundamentalData and x.Market == 'usa']
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.Market == 'usa' \
        and x.MarketCap != 0 and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
        
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        if symbol not in self.data:
            self.data[symbol] = RollingWindow[float](self.period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].Add(close)

    if not self.data[self.symbol].IsReady:
        return Universe.Unchanged
    
    market_returns:List[float] = []
    market_closes:np.ndarray = np.array([x for x in self.data[self.symbol]])
    market_returns = (market_closes[:-1] - market_closes[1:]) / market_closes[1:]
    
    beta:Dict[Symbol, float] = {}
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        # Data is ready.
        if self.data[symbol].IsReady and len(market_returns) != 0:
            stock_closes:np.ndarray = np.array([x for x in self.data[symbol]])
            stock_returns:np.ndarray = (stock_closes[:-1] - stock_closes[1:]) / stock_closes[1:]
            
            # cov = np.cov(market_returns, stock_returns)[0][1]
            # market_variance = np.std(market_returns) ** 2
            # beta[symbol] = cov / market_variance
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(market_returns, stock_returns)
            beta[symbol] = slope

    # Beta diff calc.
    beta_median:float = np.median([x[1] for x in beta.items()])
    long_diff:List[Tuple[Symbol, float]] = [(x[0], x[1] - beta_median) for x in beta.items() if x[1] >= beta_median]
    short_diff:List[Tuple[Symbol, float]] = [(x[0], beta_median - x[1]) for x in beta.items() if x[1]  None:
    # Market daily data is stored in fundamental.
    if not self.selection_flag:
        return
    self.selection_flag = False

    # Portfolio volatility calc.
    df:DataFrame = pd.DataFrame()
    weights:List[float] = []
    for symbol, w in self.weight.items():
        df[str(symbol)] = [x for x in self.data[symbol]]
        weights.append(w)
    
    weights = np.array(weights)
    
    daily_returns:DataFrame = df.pct_change()
    portfolio_vol:flaot = np.sqrt(np.dot(weights.T, np.dot(daily_returns.cov() * 21, weights.T)))
    
    leverage:float = self.target_volatility / portfolio_vol
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w * leverage) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
