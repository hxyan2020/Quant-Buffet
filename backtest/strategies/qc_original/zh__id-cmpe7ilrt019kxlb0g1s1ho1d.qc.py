# Original QuantConnect / library Python
# locale=zh slug="股票中的广义风险调整动量策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from collections import deque
from AlgorithmImports import *
from math import sqrt
import operator
import numpy as np
from pandas.core.frame import DataFrame
class GeneralisedRiskAdjustedMomentuminStocks(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    # Daily price data.
    self.data:Dict[Symbol, SymbolData] = {}
    # Volatility factor.
    self.volatility_factor_symbols:List[Symbol] = []                  # Symbols
    self.volatility_factor_vector:deque = deque(maxlen = 6)    # Monthly volatility.
    
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.data[self.market] = SymbolData(21) # One month RollingWindow
    
    # Minimal data count needed for optimalization.
    self.period:int = 12 * 21
    
    self.leverage_cap:int = 3
    self.leverage:int = 5
    self.quantile:int = 4
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    self.fundamental_count:int = 200
    self.fundamental_sorting_key = lambda x: x.DollarVolume
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
        
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and  x.MarketCap != 0]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        
    # Sharpe ratio indexed by n.
    sharpe_ratio_data:Dict = {}
    n = 0
    while n = self.quantile:
            sorted_by_momentum:List[Symbol] = sorted(generalized_momentum, key = generalized_momentum.get, reverse = True)
            quantile:int = int(len(sorted_by_momentum) / self.quantile)
            long:List[Symbol] = sorted_by_momentum[:quantile]
            short:List[Symbol] = sorted_by_momentum[-quantile:]
            
            # Sharpe ratio calc.
            symbol_count:int = len(long + short)
            total_performance:float = sum([performance_volatility[x][0] / symbol_count for x in long])
            total_performance += sum([((-1) * performance_volatility[x][0]) / symbol_count for x in short])
            
            total_volatility:float = sum([performance_volatility[x][1] / symbol_count for x in long + short])
            portfolio_sharpe_ratio:float = total_performance / total_volatility
            
            portfolio_symbols:List[List[Symbol]] = [long, short]
            sharpe_ratio_data[str(n)] = (portfolio_sharpe_ratio, portfolio_symbols)
            
        n += 0.1
    
    if len(sharpe_ratio_data) != 0:
        max_by_sharpe_ratio = max(sharpe_ratio_data.items(), key = operator.itemgetter(1))
        self.long = max_by_sharpe_ratio[1][1][0]
        self.short = max_by_sharpe_ratio[1][1][1]        
    
    return self.long + self.short
                    
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Calculate last month's volatility.
    if len(self.volatility_factor_symbols) != 0:
        monthly_volatility:float = self.CalculateFactorVolatility(self.data, self.volatility_factor_symbols)
        if monthly_volatility != 0:
            self.volatility_factor_vector.append(monthly_volatility)
    # Store new factor symbols.
    self.volatility_factor_symbols = self.long + self.short
    # Volatility factor is ready.
    if len(self.volatility_factor_vector) == self.volatility_factor_vector.maxlen:
        # Volatility targetting.
        if self.data[self.market].is_ready():
            annual_index_volatility:float = self.data[self.market].volatility() * sqrt(12*21)
            realized_strategy_volatility:float = sum(self.volatility_factor_vector) / len(self.volatility_factor_vector)
            
            # Cap leverage if needed.
            target_leverage:float = min(self.leverage_cap, (annual_index_volatility / realized_strategy_volatility))
                    
            # Trade execution.
            targets:List[PortfolioTarget] = []
            for i, portfolio in enumerate([self.long, self.short]):
                for symbol in portfolio:
                    if symbol in data and data[symbol]:
                        targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
            self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
def CalculateFactorVolatility(self, data, factor_symbols) -> float:
    monthly_volatility:float = 0
    if len(factor_symbols) != 0:
        for symbol in factor_symbols:
            if symbol in data and data[symbol].length() >= 21:
                monthly_volatility += (data[symbol].last_month_volatility() / len(factor_symbols))
    return monthly_volatility
    
class SymbolData():
def __init__(self, period: int):
    self.twelve_months_data:RollingWindow = RollingWindow[float](period)
    
def update(self, close: float) -> None:
    self.twelve_months_data.Add(close)
    
def is_ready(self) -> bool:
    return self.twelve_months_data.IsReady
    
def length(self) -> int:
    return self.twelve_months_data.Count
    
def performance(self) -> float:
    return self.twelve_months_data[0] / self.twelve_months_data[self.twelve_months_data.Count - 1] - 1
    
def volatility(self) -> float:
    closes:np.ndarray = np.array(list(self.twelve_months_data))
    returns:np.ndarray = (closes[:-1] - closes[1:]) / closes[1:]
    return np.std(returns) 
    
def last_month_volatility(self) -> float:
    closes:np.ndarray = np.array(list(self.twelve_months_data)[:21])
    returns:np.ndarray = (closes[:-1] - closes[1:]) / closes[1:]
    return np.std(returns) 
    
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
