# Original QuantConnect / library Python
# locale=en slug="momentum-and-reversal-combined-with-volatility-effect-in-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgoLib import *

class MomentumReversalCombinedWithVolatilityEffectinStocks(XXX):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)

    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # EW Tranching.
    self.holding_period:int = 6
    self.managed_queue:List[RebalanceQueueItem] = []

    # Daily price data.
    self.data:Dict[Symbol, SymbolData] = {}
    self.period:int = 6 * 21
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.quantile:int = 5
    
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume

    self.selection_flag = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> None:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol = stock.Symbol

        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)

    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.AdjustedPrice > self.min_share_price and \
        x.SecurityReference.ExchangeId in self.exchange_codes and x.MarketCap != 0]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    sorted_by_market_cap:List[Fundamental] = sorted(selected, key = lambda x: x.MarketCap, reverse=True)
    half:int = int(len(sorted_by_market_cap) / 2)
    top_by_market_cap:List[Symbol] = [x.Symbol for x in sorted_by_market_cap][:half]

    perf_volatility:Dict[Symbol, Tuple[float, float]] = {}

    # Warmup price rolling windows.
    for stock in selected:
        symbol = stock.Symbol
        
        if symbol not in self.data:
            self.data[symbol] = SymbolData(symbol, self.period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        
        # Performance and volatility tuple.
        if self.data[symbol].is_ready():
            performance = self.data[symbol].performance()
            annualized_volatility = self.data[symbol].volatility()
            perf_volatility[symbol] = (performance, annualized_volatility)                
    
    long:List[Symbol] = []
    short:List[Symbol] = []
    if len(perf_volatility) >= self.quantile:
        sorted_by_perf:List[Tuple] = sorted(perf_volatility.items(), key = lambda x: x[1][0], reverse = True)
        quantile:int = int(len(sorted_by_perf) / self.quantile)
        top_by_perf:List[Symbol] = [x[0] for x in sorted_by_perf[:quantile]]
        low_by_perf:List[Symbol] = [x[0] for x in sorted_by_perf[-quantile:]]
        
        sorted_by_vol:List[Tuple] = sorted(perf_volatility.items(), key = lambda x: x[1][1], reverse = True)
        quantile = int(len(sorted_by_vol) / self.quantile)
        top_by_vol:List[Symbol] = [x[0] for x in sorted_by_vol[:quantile]]
        low_by_vol:List[Symbol] = [x[0] for x in sorted_by_vol[-quantile:]]
        
        long = [x for x in top_by_perf if x in top_by_vol]
        short = [x for x in low_by_perf if x in top_by_vol]

    if len(long) != 0:
        long_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period / len(long)
        # symbol/quantity collection
        long_symbol_q:List = [(x, np.ceil(long_w / self.data[x].get_last_price())) for x in long]
    else:
        long_symbol_q:List = []

    if len(short) != 0:
        short_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period / len(short)
        # symbol/quantity collection
        short_symbol_q:List = [(x, -np.ceil(short_w / self.data[x].get_last_price())) for x in short]
    else:
        short_symbol_q:List = []
            
    self.managed_queue.append(RebalanceQueueItem(long_symbol_q + short_symbol_q))
    
    return long + short
    
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
   
    remove_item = None
    
    # Rebalance portfolio
    for item in self.managed_queue:
        if item.holding_period == self.holding_period:
            for symbol, quantity in item.symbol_q:
                    self.MarketOrder(symbol, -quantity)
            
            remove_item = item
        
        # Trade execution    
        if item.holding_period == 0:
            open_symbol_q = []
            
            for symbol, quantity in item.symbol_q:
                if symbol in data and data[symbol] and self.Securities[symbol].IsTradable:
                    self.MarketOrder(symbol, quantity)
                    open_symbol_q.append((symbol, quantity))
                        
            # Only opened orders will be closed        
            item.symbol_q = open_symbol_q
            
        item.holding_period += 1
        
    # We need to remove closed part of portfolio after loop. Otherwise it will miss one item in self.managed_queue.
    if remove_item:
        self.managed_queue.remove(remove_item)

def Selection(self) -> None:
    self.selection_flag = True

class RebalanceQueueItem():
def __init__(self, symbol_q:List):
    # symbol/quantity collections
    self.symbol_q:List = symbol_q  
    self.holding_period:int = 0

class SymbolData():
def __init__(self, symbol: Symbol, period: int):
    self._symbol:Symbol = symbol
    self._price:RollingWindow = RollingWindow[float](period)
    self._last_price:float = 0

def update(self, price: float) -> None:
    self._price.Add(price)
    self._last_price:float = price

def get_last_price(self) -> float:
    return self._last_price

def is_ready(self) -> bool:
    return self._price.IsReady

def volatility(self) -> float:
    closes:np.ndarray = np.array(list(self._price)[5:]) # Skip last week.
    daily_returns:np.ndarray = closes[:-1] / closes[1:] - 1
    return np.std(daily_returns) * np.sqrt(252 / (len(closes)))
    
def performance(self) -> float:
    closes:List[float] = list(self._price)[5:] # Skip last week.
    return (closes[0] / closes[-1] - 1)

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
