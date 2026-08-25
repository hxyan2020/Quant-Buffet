# Original QuantConnect / library Python
# locale=zh slug="美国股票中的非对称特质性策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import statsmodels.api as sm
from AlgorithmImports import *
class IdiosyncraticAsymmetryInUSStocks(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}
    
    self.regression_period:int = 12 * 21 + 1    # need n daily prices
    self.selection_size:int = 10                # 10 = decile selection, 5 = quintile selection, ...
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # warm up SPY prices    
    self.PerformHistory(self.symbol)
    
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol, 0), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update daily closes
    for stock in fundamental:
        symbol = stock.Symbol
        
        if symbol in self.data:
            # update daily closes
            self.data[symbol].update_closes(stock.AdjustedPrice)
    
    # monthly rebalance
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price > self.min_share_price and \
        x.SecurityReference.ExchangeId in self.exchange_codes and x.MarketCap != 0 and x.Symbol != self.symbol and x.CompanyReference.BusinessCountryID == 'USA' and \
        not np.isnan(x.FinancialStatements.IncomeStatement.ResearchAndDevelopment.TwelveMonths) and x.FinancialStatements.IncomeStatement.ResearchAndDevelopment.TwelveMonths != 0
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # can't perform selection, when market closes aren't ready
    if not self.data[self.symbol].are_closes_ready():
        return Universe.Unchanged
        
    regression_x:List = [
        self.data[self.symbol].daily_returns(),
        self.data[self.symbol].daily_returns_squared()
    ]
    
    IE:Dict[Symbol, float] = {} # storing stocks IE values keyed by stocks symbols
    
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        # warm up stock prices
        if symbol not in self.data:
            self.PerformHistory(symbol)
        
        # check if closes data are ready
        if not self.data[symbol].are_closes_ready():
            continue
        
        # perform regression
        regression_y = self.data[symbol].daily_returns()
        
        regression_model = self.MultipleLinearRegression(regression_x, regression_y)
        
        # retrieve all residuals from regression
        daily_residuals = regression_model.resid
        
        # calcualte IE value from stock daily residuals
        IE_value:float = self.data[symbol].calculate_IE(daily_residuals)
        
        # store stock's IE value keyed by stock's symbol
        IE[stock] = IE_value
        
    # make sure, there are enough stocks for selection
    if len(IE)  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def PerformHistory(self, symbol):
    ''' warm up stock prices from History object based on symbol parameter '''
    
    self.data[symbol] = SymbolData(self.regression_period)
    history = self.History(symbol, self.regression_period, Resolution.Daily)
    
    # make sure history isn't empty
    if history.empty:
        return
    
    closes = history.loc[symbol].close
    for time, close in closes.items():
        self.data[symbol].update_closes(close)
        
def MultipleLinearRegression(self, x, y):
    ''' perform multiple regression and return regression model '''
    
    x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
    
def Selection(self) -> None:
    self.selection_flag = True
    
class SymbolData():
def __init__(self, regression_period: int):
    self._closes:RollingWindow = RollingWindow[float](regression_period)
    
def update_closes(self, close: float) -> None:
    self._closes.Add(close)
    
def are_closes_ready(self) -> bool:
    return self._closes.IsReady
    
def daily_returns(self) -> np.ndarray:
    # calculate daily returns for period t-6 to t-1 months
    closes:np.ndarray = np.array([x for x in self._closes])[21:]
    daily_returns:np.ndarray = (closes[:-1] - closes[1:]) / closes[1:]
    return daily_returns
    
def daily_returns_squared(self) -> List[float]:
    # calculate daily returns for period t-6 to t-1 months
    closes:np.ndarray = np.array([x for x in self._closes])[21:]
    daily_returns:np.ndarray = (closes[:-1] - closes[1:]) / closes[1:]
    daily_returns_squared:List[float] = [x*x for x in daily_returns]
    return daily_returns_squared
    
def calculate_IE(self, residuals) -> int:
    average_residuals:float = np.average(residuals)
    two_residuals_std:float = 2 * np.std(residuals)
    
    avg_plus_two_std:float = average_residuals + two_residuals_std
    avg_minus_two_std:float = average_residuals - two_residuals_std
    
    over_avg_plus_two_std:int = 0    # counting number of residuals, which were over avg_plus_two_std
    under_avg_minus_two_std:int = 0  # counting number of residuals, which were under avg_minus_two_std
    
    for residual in residuals:
        if residual > avg_plus_two_std:
            over_avg_plus_two_std += 1
        elif residual
