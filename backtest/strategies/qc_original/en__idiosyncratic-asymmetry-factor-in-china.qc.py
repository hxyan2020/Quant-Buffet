# Original QuantConnect / library Python
# locale=en slug="idiosyncratic-asymmetry-factor-in-china"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import statsmodels.api as sm
from typing import List, Dict
#endregion
class IdiosyncraticAsymmetryFactorInChina(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    
    self.leverage: int = 10
    self.market_cap_quantile: int = 3
    self.quantile: int = 5 # 10 = decile selection, 5 = quintile selection, ...
    self.regression_period: int = 6 * 21 + 1 # need n daily prices
    self.data: Dict[Symbol, SymbolData] = {}
    self.weights: Dict[Symbol, float] = {}
    
    self.market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # warm up SPY prices    
    self.PerformHistory(self.market)
    
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.BeforeMarketClose(self.market, 0), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update daily closes
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        if symbol in self.data:
            # update daily closes
            self.data[symbol].update_closes(stock.AdjustedPrice)
    
    # monthly rebalance
    if not self.selection_flag:
        return Universe.Unchanged
    
    # filter stocks, which symbols isn't SPY equity symbol and has fundamental data
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.MarketCap != 0 
        and x.CompanyReference.BusinessCountryID == 'CHN'
    ]
    
    if not self.data[self.market].are_closes_ready():
        return Universe.Unchanged
        
    regression_x: List[np.ndarray] = [
        self.data[self.market].daily_returns(),
        self.data[self.market].daily_returns_squared()
    ]
    
    # Exclude 30% of lowest stocks by MarketCap
    sorted_by_market_cap: List[Fundamental] = sorted(selected, key = lambda x: x.MarketCap)
    selected = sorted_by_market_cap[int(len(sorted_by_market_cap) / self.market_cap_quantile):]
    
    IE: Dict[Symbol, float] = {} # storing stocks IE values keyed by stocks symbols
    market_cap: Dict[Symbol, float] = {} # storing stocks market capitalization keyed by stocks symbols
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
        
        # warm up stock prices
        if symbol not in self.data:
            self.PerformHistory(symbol)
        
        # check if closes data are ready
        if not self.data[symbol].are_closes_ready():
            continue
        
        # perform regression
        regression_y: np.ndarray = self.data[symbol].daily_returns()
        
        regression_model = self.MultipleLinearRegression(regression_x, regression_y)
        
        # retrieve all residuals from regression
        daily_residuals: np.ndarray = regression_model.resid
        
        # calcualte IE value from stock daily residuals
        IE_value: float = self.data[symbol].calculate_IE(daily_residuals)
        
        # store stock's IE value keyed by stock's symbol
        IE[symbol] = IE_value
        
        # store stock's market capitalization for value weighting
        market_cap[symbol] = stock.MarketCap
        
    # make sure, there are enough stocks for selection
    if len(IE)  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weights.items() if slice.contains_key(symbol) and slice[symbol]]
    self.SetHoldings(portfolio, True)
    self.weights.clear()
    
def PerformHistory(self, symbol: Symbol) -> None:
    ''' warm up stock prices from History object based on symbol parameter '''
    
    self.data[symbol] = SymbolData(self.regression_period)
    history: DataFrame = self.History(symbol, self.regression_period, Resolution.Daily)
    
    # make sure history isn't empty
    if history.empty:
        return
    
    closes: Series = history.loc[symbol].close
    for time, close in closes.items():
        self.data[symbol].update_closes(close)
        
def MultipleLinearRegression(self, x: np.ndarray, y: np.ndarray):
    ''' perform multiple regression and return regression model '''
    
    x: np.ndarray = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
    
def Selection(self) -> None:
    self.selection_flag = True
    
class SymbolData():
def __init__(self, regression_period: int) -> None:
    self.closes: RollingWindow = RollingWindow[float](regression_period)
    
def update_closes(self, close: float) -> None:
    self.closes.Add(close)
    
def are_closes_ready(self) -> bool:
    return self.closes.IsReady
    
def daily_returns(self) -> np.ndarray:
    # calculate daily returns for period t-6 to t-1 months
    closes = np.array([x for x in self.closes])[21:]
    daily_returns = (closes[:-1] - closes[1:]) / closes[1:]
    return daily_returns
    
def daily_returns_squared(self) -> np.ndarray:
    # calculate daily returns for period t-6 to t-1 months
    closes = np.array([x for x in self.closes])[21:]
    daily_returns = (closes[:-1] - closes[1:]) / closes[1:]
    daily_returns_squared = daily_returns**2
    return daily_returns_squared
    
def calculate_IE(self, residuals: np.ndarray) -> int:
    average_residuals: float = np.average(residuals)
    two_residuals_std: float = 2 * np.std(residuals)
    
    avg_plus_two_std: float = average_residuals + two_residuals_std
    avg_minus_two_std: float = average_residuals - two_residuals_std
    
    over_avg_plus_two_std: int = 0 # counting number of residuals, which were over avg_plus_two_std
    under_avg_minus_two_std: int = 0 # counting number of residuals, which were under avg_minus_two_std
    
    for residual in residuals:
        if residual > avg_plus_two_std:
            over_avg_plus_two_std += 1
        elif residual  OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
