# Original QuantConnect / library Python
# locale=en slug="房地产投资信托基金（reits）中的动量因子效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class MomentumFactorEffectinREITs(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000) 

    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # EW Trenching.
    self.holding_period:int = 3
    self.managed_queue:List[RebalanceQueueItem] = []

    self.data:Dict[Symbol, SymbolData] = {}
    self.period:int = 12 * 21
    self.quantile:int = 3
    self.leverage:int = 5
    
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume

    self.selection_flag = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged

    # Update the rolling window every month.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)

    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.CompanyReference.IsREIT == 1]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    momentum:Dict[Symbol, float] = {}

    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol

        if symbol not in self.data:
            self.data[symbol] = SymbolData(symbol, 13)
            history = self.History(symbol, self.period * 30, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes = history.loc[symbol].close
            
            closes_len = len(closes.keys())
            # Find monthly closes.
            for index, time_close in enumerate(closes.items()):
                # index out of bounds check.
                if index + 1 = self.quantile:
        sorted_by_momentum:List = sorted(momentum.items(), key = lambda x: x[1], reverse = True)
        quantile:int = int(len(sorted_by_momentum) / self.quantile)
        long = [x[0] for x in sorted_by_momentum[:quantile]]
        
        weight:float = self.Portfolio.TotalPortfolioValue / self.holding_period / len(long)
        long_symbol_q:List = [(symbol, np.floor(weight / self.data[symbol].get_recent_price())) for symbol in long]
        
        self.managed_queue.append(RebalanceQueueItem(long_symbol_q))

    return long
    
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False

    # rebalance portfolio
    remove_item:Union[RebalanceQueueItem, None] = None
    
    for item in self.managed_queue:
        if item.holding_period == self.holding_period: # all portfolio parts are held for n months
            for symbol, quantity in item.opened_symbol_q:
                self.MarketOrder(symbol, -quantity)
                        
            remove_item = item
        
        # trade execution    
        if item.holding_period == 0: # all portfolio parts are held for n months
            opened_symbol_q = []
            
            for symbol, quantity in item.opened_symbol_q:
                if symbol in data and data[symbol]:
                    self.MarketOrder(symbol, quantity)
                    opened_symbol_q.append((symbol, quantity))
                        
            # only opened orders will be closed        
            item.opened_symbol_q = opened_symbol_q
            
        item.holding_period += 1
        
    # need to remove closed part of portfolio after loop. Otherwise it will miss one item in self.managed_queue
    if remove_item:
        self.managed_queue.remove(remove_item)

def Selection(self) -> None:
    self.selection_flag = True

class SymbolData():
def __init__(self, symbol: Symbol, period: int):
    self._symbol:Symbol = symbol
    self._prices:RollingWindow = RollingWindow[float](period)

def update(self, value: float) -> None:
    self._prices.Add(value)

def is_ready(self) -> bool:
    return self._prices.IsReady

def get_recent_price(self) -> float:
    return self._prices[0]

# Performance, one month skipped.
def performance(self, values_to_skip = 0) -> float:
    closes = [x for x in self._prices][values_to_skip:]
    return (closes[0] / closes[-1] - 1)
    
class RebalanceQueueItem():
def __init__(self, symbol_q):
    # symbol/quantity collections
    self.opened_symbol_q = symbol_q  
    self.holding_period = 0
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
