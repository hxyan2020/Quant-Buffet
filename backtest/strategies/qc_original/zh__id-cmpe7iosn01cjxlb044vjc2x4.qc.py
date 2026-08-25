# Original QuantConnect / library Python
# locale=zh slug="中国市场中的特质波动率"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import statsmodels.api as sm
#endregion
class IdiosyncraticVolatilityInChina(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)
    
    self.period: int = 251 # Regression needs n-1 daily returns
    
    self.data: Dict[Symbol, SymbolData] = {}
    self.long: List[Symbol] = []
    self.short: List[Symbol] = []
    self.quantile: int = 5
    self.leverage: int = 10
    self.min_share_price: float = 3.
    self.market_cap_quantile: int = 3
    self.traded_percentage: float = .2
    market: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    # factors
    self.last_market_factor: Tuple[List[Symbol], List[Symbol]] = None  # long only dict
    self.last_size_factor: Tuple[List[Symbol], List[Symbol]] = None    # long/short lists
    self.last_value_factor: Tuple[List[Symbol], List[Symbol]] = None   # long/short lists
    
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
    # update the rolling window every day
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    
    # rebalace monthly
    if not self.selection_flag:
        return Universe.Unchanged
    selected: List[Fundamental] = [
        f for f in fundamental if f.HasFundamentalData 
        and f.MarketCap != 0 
        and not np.isnan(f.ValuationRatios.PBRatio) and f.ValuationRatios.PBRatio != 0 
        and f.Market == 'usa' 
        and f.CompanyReference.BusinessCountryID == 'CHN' 
        and f.Price >= self.min_share_price
    ]
        
    # exclude 30% of lowest stocks by MarketCap
    sorted_by_market_cap: List[Fundamental] = sorted(selected, key = lambda x: x.MarketCap)
    selected = sorted_by_market_cap[int(len(sorted_by_market_cap) / self.market_cap_quantile):]
    
    market_cap: Dict[Symbol, float] = {}
    value_factor: Dict[Symbol, float] = {}
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
        
        # Get stock's volumes
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            
            history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
            
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            
            closes: Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        
        if self.data[symbol].is_ready():
            market_cap[symbol] = stock.MarketCap
            value_factor[symbol] = stock.ValuationRatios.PBRatio
    
    if len(market_cap)  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in slice and slice[symbol]:
                targets.append(PortfolioTarget(symbol, (((-1) ** i) / len(portfolio)) * self.traded_percentage))
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
def DailyPerformanceValueWeight(self, market_cap: Dict[Symbol, float]) -> np.ndarray:
    # Create numpy array with zeros
    total_daily_returns: np.ndarray = np.zeros(self.period - 1)
    
    total_cap: float = sum([x[1] for x in market_cap.items()])
    for symbol, cap in market_cap.items():
        # calculate weight for current stock
        weight: float = cap / total_cap
        # get daily returns of current stock
        daily_returns: np.ndarray = self.data[symbol].daily_returns()
        # multiply each daily return by weight
        daily_returns: np.ndarray = daily_returns * weight
        # add daily returns of current stock to total_daily_returns of portfolio
        total_daily_returns += daily_returns
    
    return total_daily_returns
    
def FactorDailyPerformance(self, long: List[Symbol], short: List[Symbol]) -> np.ndarray:
    # create numpy array with zeros
    total_daily_returns: np.ndarray = np.zeros(self.period - 1)
    
    # go through each long and short stock
    # Add daily returns of long stocks and sub daily returns of short stocks.
    for long_sym, short_sym in zip(long, short):
        total_daily_returns += self.data[long_sym].daily_returns()
        total_daily_returns -= self.data[short_sym].daily_returns()
        
    return total_daily_returns
    
def MultipleLinearRegression(self, x, y):
    x: np.ndarray = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
class SymbolData():
def __init__(self, period: int) -> None:
    self.daily_prices: RollingWindow = RollingWindow[float](period)
    
def update(self, close: float) -> None:
    self.daily_prices.Add(close)
    
def is_ready(self) -> bool:
    return self.daily_prices.IsReady
    
def daily_returns(self) -> np.ndarray:
    daily_prices: np.ndarray = np.array([x for x in self.daily_prices])
    return (daily_prices[:-1] - daily_prices[1:]) / daily_prices[1:]
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
