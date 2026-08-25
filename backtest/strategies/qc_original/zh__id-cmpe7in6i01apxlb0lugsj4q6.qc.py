# Original QuantConnect / library Python
# locale=zh slug="低风险异象指数"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import statsmodels.api as sm
class LowRiskAnomalyIndex(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}
    self.period:int = 21
    self.quantile:int = 10
    self.leverage:int = 5
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.last_size_long:List[Symbol] = []
    self.last_size_short:List[Symbol] = []
    self.last_book_long:List[Symbol] = []
    self.last_book_short:List[Symbol] = []
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.data[self.market] = SymbolData(self.period)
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
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
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes and \
        not np.isnan(x.ValuationRatios.PBRatio) and x.ValuationRatios.PBRatio != 0]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    book_to_market:Dict[Fundamental, float] = {}
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        
        if self.data[symbol].is_ready():
            book_to_market[stock] = 1 / stock.ValuationRatios.PBRatio # book-to-market
    if len(book_to_market) >= self.quantile**2:
        quantile:int = int(len(book_to_market) / self.quantile)
        sorted_by_market_cap:List[Fundamental] = [x[0] for x in sorted(book_to_market.items(), key=lambda item: item[0].MarketCap)]
        sorted_book_to_market:List[Fundamental] = [x[0] for x in sorted(book_to_market.items(), key=lambda item: item[1])]
    
        # Size Factor
        current_size_long:List[Symbol] = list(map(lambda x: x.Symbol, sorted_by_market_cap[:quantile]))
        current_size_short:List[Symbol] = list(map(lambda x: x.Symbol, sorted_by_market_cap[-quantile:]))
        
        # Book to market Factor
        current_book_long:List[Symbol] = list(map(lambda x: x.Symbol, sorted_book_to_market[:quantile]))
        current_book_short:List[Symbol] = list(map(lambda x: x.Symbol, sorted_book_to_market[-quantile:]))
    
        # Check if factors are ready
        if (len(self.last_size_long) > 0 and len(self.last_size_short) > 0 and
            len(self.last_book_long) > 0 and len(self.last_book_short) > 0):
            # Check if market prices are ready
            if self.data[self.market].is_ready(): 
                # Calculate factors daily returns
                book_factor_daily_returns = self.CalculateFactorDailyReturns(self.last_book_long, self.last_book_short)
                size_factor_daily_returns = self.CalculateFactorDailyReturns(self.last_size_long, self.last_size_short)
                
                # Calculate daily returns of market
                first_regression_X = self.data[self.market].daily_performances()
    
                LRA:Dict[Fundamental, float] = {}
                MAX:Dict[Fundamental, float] = {}
                BETA:Dict[Fundamental, float] = {}
                IVOL:Dict[Fundamental, float] = {}
                
                for stock in selected:
                    symbol:Symbol = stock.Symbol
                    
                    Y = self.data[symbol].daily_performances()
                    if first_regression_X.shape == Y.shape:
                        regression_model = self.MultipleLinearRegression(first_regression_X, Y)
                        BETA[stock] = regression_model.params[1] # First parameter is alpha and second is beta.
                        sorted_daily_returns = sorted(Y, reverse=True)
                        MAX[stock] = np.mean(sorted_daily_returns[:5]) # MAX is average of five highest daily returns
                            
                        X = [
                            first_regression_X,
                            size_factor_daily_returns,
                            book_factor_daily_returns
                        ]
                            
                        regression_model = self.MultipleLinearRegression(X, Y)
                        IVOL[stock] = np.std(regression_model.resid) 
                        
                # Sort MAX, BETA and IVOL
                sorted_by_MAX = [x[0] for x in sorted(MAX.items(), key=lambda item: item[1], reverse=True)]
                sorted_by_BETA = [x[0] for x in sorted(BETA.items(), key=lambda item: item[1], reverse=True)]
                sorted_by_IVOL = [x[0] for x in sorted(IVOL.items(), key=lambda item: item[1], reverse=True)]
                
                quantile:int = int(len(sorted_by_MAX) / self.quantile)
                
                # For each stock calculate it's LRA
                for stock in sorted_by_MAX:
                    symbol:Symbol = stock.Symbol
                    
                    # Note: We need to add 1 to each index, because lists starts from 0.
                    MAX_index:int = sorted_by_MAX.index(stock) + 1
                    BETA_index:int = sorted_by_BETA.index(stock) + 1
                    IVOL_index:int = sorted_by_IVOL.index(stock) + 1
                    
                    # Need to round up, because stock belongs to that decile
                    LRA[stock] = math.ceil(MAX_index / quantile) + math.ceil(BETA_index / quantile) + math.ceil(IVOL_index / quantile)
                
                # Sort stocks by LRA
                sorted_by_LRA = [x[0] for x in sorted(LRA.items(), key=lambda item: item[1], reverse=True)]
                
                long:List[Fundamental] = sorted_by_LRA[:quantile] # Highest goes long
                short:List[Fundamental] = sorted_by_LRA[-quantile:] # Lowest goes short
                
                # Market cap weighting.
                for i, portfolio in enumerate([long, short]):
                    mc_sum:float = sum(map(lambda x: x.MarketCap, portfolio))
                    for stock in portfolio:
                        self.weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum
                
    self.last_size_long = current_size_long
    self.last_size_short = current_size_short
    self.last_book_long = current_book_long
    self.last_book_short = current_book_short
                
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

def CalculateFactorDailyReturns(self, factor_long, factor_short):
    long_daily_returns = self.ListOfDailyReturns(factor_long, True)
    short_daily_returns = self.ListOfDailyReturns(factor_short, False)
    
    stocks_daily_returns = np.array(long_daily_returns + short_daily_returns)
    
    factor_daily_returns = []
    
    for i in range(len(stocks_daily_returns[0])):
        factor_daily_returns.append(np.mean(stocks_daily_returns[:, i])) # Takes column of 2d array
        
    return factor_daily_returns
    
def ListOfDailyReturns(self, symbols, long_flag):
    list = []
    
    for symbol in symbols:
        # Those aren't symbols which were return from coarse
        if symbol in self.data:
            if self.data[symbol].is_ready():
                if long_flag:
                    list.append(self.data[symbol].daily_performances())
                else:
                    list.append(self.data[symbol].short_daily_performances())
                
    return list
 
def MultipleLinearRegression(self, x, y):
    x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result     

class SymbolData():
def __init__(self, period):
    self._closes:RollingWindow = RollingWindow[float](period)
    
def update(self, close: float) -> None:
    self._closes.Add(close)
    
def is_ready(self) -> bool:
    return self._closes.IsReady
    
def daily_performances(self) -> float:
    closes:np.ndarray = np.array(list(self._closes))
    return (closes[:-1] - closes[1:]) / closes[1:]
    
def short_daily_performances(self) -> float:
    closes:np.ndarray = np.array(list(self._closes))
    return ( -(closes[:-1] - closes[1:]) ) / closes[1:] # We change mark of daily performance for short stocks.
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
