# Original QuantConnect / library Python
# locale=en slug="low-volatility-factor-effect-in-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
import numpy as np
from typing import List, Dict

class LowVolatilityFactorEffectStocks(XXX):
"""
A class designed to implement a low volatility factor effect trading strategy.
It selects stocks based on their volatility and constructs a portfolio that is rebalanced monthly.
"""

def Initialize(self) -> None:
    """
    Initializes the strategy by setting starting cash, adding the target equity (SPY),
    setting parameters for the strategy, and scheduling function calls.
    """
    self.SetStartDate(2000, 1, 1)  # Set the start date for the backtest
    self.SetCash(100000)  # Set the initial cash for the backtest
    self.symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol  # Add SPY as the equity to trade
    self.period: int = 12 * 21  # Define the period for rolling window calculations
    self.fundamental_count: int = 3000  # Number of fundamental data points to consider
    self.quantile: int = 4  # Division of data into quantiles
    self.leverage: int = 10  # Set the leverage for the strategy
    self.data: Dict[Symbol, SymbolData] = {}  # Initialize a dictionary to store symbol data
    self.long: List[Symbol] = []  # List to keep track of symbols to go long on
    self.selection_flag: bool = True  # Flag to control the selection process
    self.UniverseSettings.Resolution = Resolution.Daily  # Set universe resolution to daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.  # Set minimum margin percentage
    self.AddUniverse(self.FundamentalSelectionFunction)  # Define the universe based on a custom selection function
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)  # Schedule the selection function

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    """
    Updates securities settings on changes in the investment universe, like setting a custom fee model and leverage.
    """
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())  # Set a custom fee model for added securities
        security.SetLeverage(self.leverage)  # Set the leverage for the securities
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    """
    Selects symbols based on fundamental data, targeting low volatility stocks within the top market capitalization.
    """
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    fundamental: List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0]
    if len(fundamental) > self.fundamental_count:
        fundamental = sorted(fundamental, key=lambda x: x.MarketCap, reverse=True)[:self.fundamental_count]
    weekly_vol: Dict[Symbol, float] = {}
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes: pd.Series = history.loc[symbol].close
            for time, close in closes.iteritems():
                self.data[symbol].update(close)         
        if self.data[symbol].is_ready():
            weekly_vol[symbol] = self.data[symbol].volatility()
    if len(weekly_vol) >= self.quantile:
        sorted_by_vol: List[Tuple] = sorted(weekly_vol.items(), key = lambda x: x[1], reverse = True)
        quantile: int = int(len(sorted_by_vol) / self.quantile)
        self.long = [x[0] for x in sorted_by_vol[-quantile:]]
    return self.long
    
def OnData(self, data: Slice) -> None:
    """
    Executes the trading logic at each data point, adjusting the portfolio based on the selection of low volatility stocks.
    """
    if not self.selection_flag:
        return
    self.selection_flag = False
    invested: List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.long:
            self.Liquidate(symbol)
    for symbol in self.long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, 1. / len(self.long))
    self.long.clear()
    
def Selection(self) -> None:
    """
    Sets a flag to true to trigger the selection process at the next opportunity.
    """
    self.selection_flag = True

class SymbolData():
"""
A helper class for storing and updating price data for symbols, and calculating their volatility.
"""
def __init__(self, period: int) -> None:
    self.price: RollingWindow = RollingWindow[float](period)  # Initialize a rolling window for prices

def update(self, value: float) -> None:
    """
    Updates the rolling window with the latest price.
    """
    self.price.Add(value)

def is_ready(self) -> bool:
    """
    Checks if the rolling window has enough data.
    """
    return self.price.IsReady
    
def volatility(self) -> float:
    """
    Calculates the volatility of the symbol based on price data in the rolling window.
    """
    closes: List[float] = [x for x in self.price]
    separate_weeks: List[float] = [closes[x:x+5] for x in range(0, len(closes), 5)]
    weekly_returns: List[float] = [(x[0] - x[-1]) / x[-1] for x in separate_weeks]
    return np.std(weekly_returns)   

class CustomFeeModel(FeeModel):
"""
A custom fee model that calculates trading fees based on the transaction volume.
"""
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
