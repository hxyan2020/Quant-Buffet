# Original QuantConnect / library Python
# locale=en slug="小规模投资组合中的股票动量效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class MomentumEffectinStocksinSmallPortfolios(XXX):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)

    self.coarse_count = 500
    
    self.long = []
    self.short = []
    
    # Daily data.
    self.data = {}
    self.period = 12 * 21
    self.quantile = 10
    self.leverage = 5
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_flag = True
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    
    self.month = 11
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)

def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse):
    # Update the rolling window every day.
    for stock in coarse:
        symbol = stock.Symbol

        if symbol in self.data:
            # Store daily price.
            self.data[symbol].update(stock.AdjustedPrice)
    
    # Selection once a month.
    if not self.selection_flag:
        return Universe.Unchanged
    
    # selected = [x.Symbol for x in coarse if x.HasFundamentalData and x.Market == 'usa']
    selected = [x.Symbol
        for x in sorted([x for x in coarse if x.HasFundamentalData and x.Market == 'usa'],
            key = lambda x: x.DollarVolume, reverse = True)[:self.coarse_count]]
    
    # Warmup price rolling windows.
    for symbol in selected:
        if symbol in self.data:
            continue
        
        self.data[symbol] = SymbolData(symbol, self.period)
        history = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet")
            continue
        closes = history.loc[symbol].close
        for time, close in closes.iteritems():
            self.data[symbol].Price.Add(close)
            
    return [x for x in selected if self.data[x].is_ready()]
    
def FineSelectionFunction(self, fine):
    fine = [x for x in fine if x.MarketCap != 0]
    
    # if len(fine) > self.coarse_count:
    #     sorted_by_market_cap = sorted(fine, key = lambda x: x.MarketCap, reverse=True)
    #     top_by_market_cap = sorted_by_market_cap[:self.coarse_count]
    # else:
    #     top_by_market_cap = fine
    
    # Performance sorting.
    performance = {x.Symbol : self.data[x.Symbol].performance() for x in fine}

    if len(performance) >= self.quantile:
        decile = int(len(performance) / self.quantile)
        sorted_by_perf = sorted(performance.items(), key = lambda x: x[1], reverse = True)
        self.long = [x[0] for x in sorted_by_perf[:decile]]
        self.short = [x[0] for x in sorted_by_perf[-decile:]]
    
    return self.long + self.short
        
def OnData(self, data):
    if not self.selection_flag:
        return
    self.selection_flag = False

    # Trade execution.
    long_count = len(self.long)
    short_count = len(self.short)
    
    invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.long + self.short:
            self.Liquidate(symbol)        
            
    for symbol in self.long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, 1 / long_count)

    for symbol in self.short:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, -1 / short_count)
    
def Selection(self):
    # Rebalance every 12 months.
    if self.month == 12:
        self.selection_flag = True

    self.month += 1
    if self.month > 12: 
        self.month = 1

class SymbolData():
def __init__(self, symbol, period):
    self.Symbol = symbol
    self.Price = RollingWindow[float](period)

def update(self, value):
    self.Price.Add(value)

def is_ready(self):
    return self.Price.IsReady
    
def performance(self):
    closes = [x for x in self.Price]
    return (closes[0] / closes[-1] - 1)

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
