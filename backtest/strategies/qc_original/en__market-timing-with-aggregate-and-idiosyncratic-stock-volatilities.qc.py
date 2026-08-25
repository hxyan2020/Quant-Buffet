# Original QuantConnect / library Python
# locale=en slug="market-timing-with-aggregate-and-idiosyncratic-stock-volatilities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
import statsmodels.api as sm
import numpy as np
from typing import Dict, List, Tuple
from pandas.core.frame import DataFrame
from pandas.core.series import Series
class MarketTimingwithAggregateandIdiosyncraticStockVolatilities(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}
    
    self.period:int = 3*21
    self.fundamental_count:int = 500
    self.leverage:int = 5
    self.quantile:int = 10
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    
    self.last_size_long:List[Symbol] = []
    self.last_size_short:List[Symbol] = []
    self.last_book_long:List[Symbol] = []
    self.last_book_short:List[Symbol] = []
    
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.data[self.market] = SymbolData(self.period)
    
    self.bonds:Symbol = self.AddEquity('SHY', Resolution.Daily).Symbol
    
    self.regression_data:List[Tuple[float, float, float]] = []
    self.regression_data_min_period:int = 12
    
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    
    self.Schedule.On(self.DateRules.MonthEnd(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)

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
            self.data[symbol].update(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected: List[Fundamental] = sorted([x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0 \
                        and not np.isnan(x.ValuationRatios.PBRatio) and x.ValuationRatios.PBRatio != 0
                        and x.SecurityReference.ExchangeId in self.exchange_codes],
                        key=lambda x: x.DollarVolume, reverse=True)[:self.fundamental_count]
        
    selected_dict: Dict[Symbol, Fundamental] = {x.Symbol : x for x in selected}
    market_cap:Dict[Symbol, float] = {}
    book_to_market:Dict[Symbol, float] = {}
    # Warmup price rolling windows.
    for symbol in list(selected_dict.keys()) + [self.market]:
        if symbol in self.data:
            continue
        
        self.data[symbol] = SymbolData(self.period)
        history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet")
            continue
        closes:Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].update(close)
        if self.data[symbol].is_ready():
            market_cap[symbol] = selected_dict[symbol].MarketCap
            book_to_market[symbol] = 1 / selected_dict[symbol].ValuationRatios.PBRatio # book-to-market
            
    # Return, if after fundamental filtration we don't have enough stocks to sort them into deciles.
    # In next month we will use size and book factors from t-3 month, where t is current month.
    if len(market_cap)  0 and len(self.last_size_short) > 0 and
        len(self.last_book_long) > 0 and len(self.last_book_short) > 0):
        # Check if market prices are ready
        if self.data[self.market].is_ready(): 
            # Calculate factors daily returns
            book_factor_daily_returns:List[float] = self.CalculateFactorDailyReturns(self.last_book_long, self.last_book_short)
            size_factor_daily_returns:List[float] = self.CalculateFactorDailyReturns(self.last_size_long, self.last_size_short)
            
            market_returns:np.ndarray = self.data[self.market].daily_performances()
            market_variance:np.ndarray = (np.std(market_returns) * np.sqrt(252)) ** 2
            market_return:float = self.data[self.market].performance()
            
            # stock residuals
            idiosyncratic_variance:List[Tuple[float, float]] = []
            for stock in selected:
                symbol: Symbol = stock.Symbol
                if symbol not in self.data:
                    continue
                
                if not self.data[symbol].is_ready():
                    continue
                Y:np.ndarray = self.data[symbol].daily_performances()
                X:np.ndarray = [
                    market_returns,
                    size_factor_daily_returns,
                    book_factor_daily_returns
                ]
                    
                regression_model = self.MultipleLinearRegression(X, Y)
                
                idiosyncratic_variance.append((regression_model.resid[-1], selected_dict[symbol].MarketCap))
            
            # summary idiosyncratic variance calculation
            summary_market_cap:float = sum([x[1] for x in idiosyncratic_variance])
            summary_idiosyncratic_variance:float = sum([x[0] * (x[1] / summary_market_cap) for x in idiosyncratic_variance])
            
            self.regression_data.append((market_return, market_variance, summary_idiosyncratic_variance))
            
    self.last_size_long = current_size_long
    self.last_size_short = current_size_short
    self.last_book_long = current_book_long
    self.last_book_short = current_book_short
                
    return Universe.Unchanged
def OnData(self, data:Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    if self.bonds not in data or not data[self.bonds]:
        return
    # regression data is ready
    if len(self.regression_data) >= self.regression_data_min_period:
        Y = [x[0] for x in self.regression_data][:-1]
        X = [
            [x[1] for x in self.regression_data][1:],
            [x[2] for x in self.regression_data][1:]
        ]
        
        # expected market return calculation
        regression_model = self.MultipleLinearRegression(X, Y)
        alpha:float = regression_model.params[0]
        beta1:float = regression_model.params[1]
        beta2:float = regression_model.params[2]
        
        expected_market_return:float = alpha + self.regression_data[0][1]*beta1 + self.regression_data[0][2]*beta2
        expected_market_variance:float = np.mean([x[1] for x in self.regression_data])
        risk_aversion:int = 5
        
        # equity and tbill weight
        equity_weight:float = expected_market_return / (risk_aversion * expected_market_variance)
        tbill_weight:float = 1 - equity_weight
        
        # trade execution
        if self.market in data and data[self.market] and self.bonds in data and data[self.bonds]:
            self.SetHoldings(self.market, equity_weight)
            self.SetHoldings(self.bonds, tbill_weight)
        
def CalculateFactorDailyReturns(self, factor_long:List[Symbol], factor_short:List[Symbol]) -> List[float]:
    long_daily_returns:List[Symbol] = self.ListOfDailyReturns(factor_long, True)
    short_daily_returns:List[Symbol] = self.ListOfDailyReturns(factor_short, False)
    
    stocks_daily_returns:np.ndarray = np.array(long_daily_returns + short_daily_returns)
    
    factor_daily_returns:List[float] = []
    
    for i in range(len(stocks_daily_returns[0])):
        factor_daily_returns.append(np.mean(stocks_daily_returns[:, i])) # Takes column of 2d array
        
    return factor_daily_returns
    
def ListOfDailyReturns(self, symbols:List[Symbol], long_flag:bool) -> List[Symbol]:
    symbol_list = []
    
    for symbol in symbols:
        # Those aren't symbols which were return from coarse
        if symbol in self.data:
            if self.data[symbol].is_ready():
                if long_flag:
                    symbol_list.append(self.data[symbol].daily_performances())
                else:
                    symbol_list.append(self.data[symbol].short_daily_performances())
    return symbol_list
 
def MultipleLinearRegression(self, x, y):
    x:np.ndarray = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result     

def Selection(self):
    if self.Time.month % 3 == 0:
        self.selection_flag = True
class SymbolData():
def __init__(self, period:int) -> None:
    self.closes:RollingWindow[float] = RollingWindow[float](period)
    self.period:int = period
    
def update(self, close:float) -> None:
    self.closes.Add(close)
    
def is_ready(self) -> bool:
    return self.closes.IsReady

def performance(self) -> float:
    return self.closes[0] / self.closes[self.period - 1] - 1

def daily_performances(self) -> np.ndarray:
    closes = np.array([x for x in self.closes])
    return (closes[:-1] - closes[1:]) / closes[1:]
    
def short_daily_performances(self) -> np.ndarray:
    closes = np.array([x for x in self.closes])
    return ( -(closes[:-1] - closes[1:]) ) / closes[1:] # We change mark of daily performance for short stocks.
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
