# Original QuantConnect / library Python
# locale=zh slug="股票中的最低特质收益"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import statsmodels.api as sm
import numpy as np
from typing import List, Dict, Tuple
from numpy import isnan
from pandas.core.frame import DataFrame
from pandas.core.series import Series
#endregion
class MinimumIdiosyncraticReturnsinStocks(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']
    # Daily price data.
    self.period: int = 21
    self.quantile: int = 5
    self.leverage: int = 10
    self.min_share_price: int = 5
    self.momentum_period: int = 12
    
    self.fundamental_count: int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.long: List[Symbol] = []
    self.short: List[Symbol] = []
    self.data: Dict[Symbol, RollingWindow] = {}
    self.market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.data[self.market] = RollingWindow[float](self.period)
    
    # Factors.
    self.size_factor_symbols: List[Tuple[Symbol, bool]] = []   # Symbol,long flag tuple.
    self.value_factor_symbols: List[Tuple[Symbol, bool]] = []
    self.momentum_factor_symbols: List[Tuple[Symbol, bool]] = []
    
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetLeverage(self.leverage)
        security.SetFeeModel(CustomFeeModel())
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData and 
        x.Market == 'usa' 
        and x.MarketCap != 0 
        and x.Price > self.min_share_price
        and x.SecurityReference.ExchangeId in self.exchange_codes 
        and not isnan(x.ValuationRatios.PBRatio) and x.ValuationRatios.PBRatio != 0 
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # Warmup price rolling windows.
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol in self.data:
            continue
        
        self.data[symbol] = RollingWindow[float](self.momentum_period*self.period)
        history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes: Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].Add(close)
    
    selected = [x for x in selected if self.data[x.Symbol].IsReady]
    if len(selected) = self.momentum_period * self.period], 
                        key = lambda x: self.Return([x for x in self.data[x.Symbol]][:self.momentum_period * self.period][self.period:]), reverse = True)
    quantile: int = int(len(sorted_by_momentum) / self.quantile)
    momentum_factor_long: List[Symbol] = [(i.Symbol, True) for i in sorted_by_momentum[:quantile]]
    momentum_factor_short: List[Symbol] = [(i.Symbol, False) for i in sorted_by_momentum[-quantile:]]
    # Calculate last month's performance.
    if len(self.momentum_factor_symbols) != 0:
        momentum_factor_vector = self.factor_daily_returns(self.data, self.momentum_factor_symbols)
    # Store new factor symbols.
    self.momentum_factor_symbols = momentum_factor_long + momentum_factor_short
    
    IMIN: Dict[Symbol, float] = {}
    long: List[Symbol] = []
    short: List[Symbol] = []
    
    # Every factor vector is ready.
    if len(market_factor_vector) == self.period - 1 and \
        len(size_factor_vector) == self.period - 1 and  \
        len(value_factor_vector) == self.period - 1 and \
        len(momentum_factor_vector) == self.period - 1:
        
        # Residual return calc.
        x: List[List[float]] = [[x for x in market_factor_vector][::-1],
             [x for x in size_factor_vector][::-1],
             [x for x in value_factor_vector][::-1],
             [x for x in momentum_factor_vector][::-1]]
        
        for stock in selected:
            symbol: Symbol = stock.Symbol
            
            # 12 months of stock history is ready.
            daily_prices: np.ndarray = np.array([x for x in self.data[symbol]][:self.period])
            daily_returns: np.ndarray = daily_prices[:-1] / daily_prices[1:] - 1
        
            regression_model: RegressionResultWrapper = MultipleLinearRegression(x, daily_returns[::-1])
            IMIN[symbol] = min(regression_model.resid)
                
    sorted_by_IMIN: List[Tuple[Symbol, float]] = sorted(IMIN.items(), key = lambda x: x[1], reverse = True)
    quantile: int = int(len(sorted_by_IMIN) / self.quantile)
    self.long: List[Symbol] = [x[0] for x in sorted_by_IMIN[:quantile]]
    self.short: List[Symbol] = [x[0] for x in sorted_by_IMIN[-quantile:]]
    return self.long + self.short
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)        
    self.long.clear()
    self.short.clear()

def Selection(self) -> None:
    self.selection_flag = True
def factor_daily_returns(self, data: Dict[Symbol, RollingWindow], factor_symbols: List[Tuple[Symbol, bool]]) -> np.ndarray:
    daily_returns: np.ndarray = np.array([float(0) for x in range(self.period - 1)])
    
    if len(factor_symbols) != 0:
        for symbol, long_flag in factor_symbols:
            if symbol in data and data[symbol].Count >= self.period:
                daily_closes = np.array([x for x in self.data[symbol]][:self.period])
                if long_flag:
                    daily_returns += (daily_closes[:-1] / daily_closes[1:] - 1)
                else:
                    daily_returns -= (daily_closes[:-1] / daily_closes[1:] - 1)
    
        daily_returns /= len(factor_symbols)
    
    return daily_returns

def Return(self, values: List[float]) -> float:
    return (values[0] / values[-1]) - 1
def MultipleLinearRegression(x: np.ndarray, y: np.ndarray):
x = np.array(x).T
x = sm.add_constant(x)
result: RegressionResultWrapper = sm.OLS(endog=y, exog=x).fit()
return result

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
