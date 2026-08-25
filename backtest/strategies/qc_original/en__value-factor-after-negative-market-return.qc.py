# Original QuantConnect / library Python
# locale=en slug="value-factor-after-negative-market-return"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from numpy import floor
#endregion
class ValueFactorAfterNegativeMarketReturn(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.coarse_count = 500
    
    self.period = 24 * 21
    self.SetWarmUp(self.period, Resolution.Daily)
    self.quantile = 10
    # Trenching
    self.holding_period = 6
    self.managed_queue = []
    
    self.symbol = self.AddEquity('VTI', Resolution.Daily).Symbol
    self.data = RollingWindow[float](self.period)
    self.selection_flag = False
    
    self.recent_price = {}  # recent stock prices
    
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    
def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(10)
def CoarseSelectionFunction(self, coarse):
    for stock in coarse:
        symbol = stock.Symbol
        # append recent price to market symbol
        if symbol == self.symbol:
            self.data.Add(stock.AdjustedPrice)
        # store monthly stock prices
        if self.selection_flag:
            self.recent_price[symbol] = stock.AdjustedPrice
        
    if not self.selection_flag:
        return Universe.Unchanged
    selected = sorted([x for x in coarse if x.HasFundamentalData and x.Price > 5],
        key=lambda x: x.DollarVolume, reverse=True)[:self.coarse_count]
    return [x.Symbol for x in selected]
def FineSelectionFunction(self, fine):
    fine = [x for x in fine if x.MarketCap != 0 and x.ValuationRatios.PBRatio != 0]
    
    # market data is ready
    if self.data.IsReady:
        market_ret:float = self.data[0] / self.data[self.period-1] - 1
        if market_ret >= 0:
            return Universe.Unchanged
    else:
        return Universe.Unchanged
    bm_ratio = {}
    market_cap = {}
    for stock in fine:
        symbol = stock.Symbol
        
        market_cap[symbol] = stock.MarketCap
        bm_ratio[symbol] = 1 / stock.ValuationRatios.PBRatio
    
    long:list = []
    short:list = []
    
    if len(bm_ratio) >= self.quantile:
        # BM ratio sorting 
        sorted_by_bm = sorted(bm_ratio.items(), key=lambda x: x[1], reverse=True)
        decile = int(len(sorted_by_bm) / self.quantile)
        
        # Long the highest decile portfolio 
        # Short the lowest decile portolio
        long = [x[0] for x in sorted_by_bm[:decile]]
        short = [x[0] for x in sorted_by_bm[-decile:]]
    
        # Market cap weighting
        equity = self.Portfolio.TotalPortfolioValue / self.holding_period
        
        weights = {}
        
        total_market_cap_long = sum([market_cap[sym] for sym in long if sym in market_cap])
        for symbol in long:
            if symbol in market_cap:
                weights[symbol] = market_cap[symbol] / total_market_cap_long
        
        total_market_cap_short = sum([market_cap[sym] for sym in short if sym in market_cap])
        for symbol in short:
            if symbol in market_cap:
                weights[symbol] = -market_cap[symbol] / total_market_cap_short
        
        symbol_q = [(symbol, floor((equity*symbol_w) / self.recent_price[symbol])) for symbol,symbol_w in weights.items()]
        self.managed_queue.append(RebalanceQueueItem(symbol_q))
            
    return long + short
def OnData(self, data):
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution
    remove_item = None
    
    # Rebalance portfolio
    for item in self.managed_queue:
        if item.holding_period == self.holding_period:
            for symbol, quantity in item.symbol_q:
                self.MarketOrder(symbol, -quantity)
                        
            remove_item = item
            
        elif item.holding_period == 0:
            open_symbol_q = []
            
            for symbol, quantity in item.symbol_q:
                if symbol in data and data[symbol]:
                    self.MarketOrder(symbol, quantity)
                    open_symbol_q.append((symbol, quantity))
            
            # Only opened orders will be closed        
            item.symbol_q = open_symbol_q
            
        item.holding_period += 1
        
    # We need to remove closed part of portfolio after loop. Otherwise it will miss one item in self.managed_queue.
    if remove_item:
        self.managed_queue.remove(remove_item)
def Selection(self):
    self.selection_flag = True
class RebalanceQueueItem():
def __init__(self, symbol_q):
    # symbol/quantity collections
    self.symbol_q = symbol_q  
    self.holding_period = 0
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
