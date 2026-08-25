# Original QuantConnect / library Python
# locale=en slug="long-term-reversal-combined-with-a-momentum-effect"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from math import floor
class LongTermReversalCombinedwithaMomentumEffect(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2004, 1, 1)
    self.SetCash(100000)     
    
    self.symbols = [
        "EWJ",  # iShares MSCI Japan Index ETF
        "EWA",  # iShares MSCI Australia ETF
        "EWG",  # iShares MSCI Germany ETF
        "EWU",  # iShares MSCI United Kingdom ETF
        "EWW",  # iShares MSCI Mexico Inv. Mt. Idx
        "EWS",  # iShares MSCI Singapore ETF
        "ERUS", # iShares MSCI Russia ETF
        "IVV",  # iShares S&P 500 Index
        "AAXJ", # iShares MSCI All Country Asia ex Japan Index ETF
        "EWQ",  # iShares MSCI France Index ETF
        "EWH",  # iShares MSCI Hong Kong Index ETF
        "EPI",  # WisdomTree India Earnings ETF
        "EIDO"  # iShares MSCI Indonesia Investable Market Index ETF
        "EWI",  # iShares MSCI Italy Index ETF
        "ENZL", # iShares MSCI New Zealand Investable Market Index Fund
        "NORW"  # Global X FTSE Norway 30 ETF
        "EWY",  # iShares MSCI South Korea Index ETF
        "EWP",  # iShares MSCI Spain Index ETF
        "EWD",  # iShares MSCI Sweden Index ETF
        "EWL",  # iShares MSCI Switzerland Index ETF
        "GXC",  # SPDR S&P China ETF
        "EWC",  # iShares MSCI Canada Index ETF
        "EWZ",  # iShares MSCI Brazil Index ETF
        "ARGT", # Global X FTSE Argentina 20 ETF
        "EWO",  # iShares MSCI Austria Investable Mkt Index ETF
        "EWK",  # iShares MSCI Belgium Investable Market Index ETF
        "ECH",  # iShares MSCI Chile Investable Market Index ETF
        "EGPT", # Market Vectors Egypt Index ETF
    ]
    self.holding_period = 6
    
    self.data = {}
    self.managed_queue = []
    
    self.long_period = 60*21
    self.short_period = 6*21
    self.SetWarmUp(self.long_period, Resolution.Daily)
    
    for symbol in self.symbols:
        data = self.AddEquity(symbol, Resolution.Daily)
        data.SetLeverage(10)
        data.SetFeeModel(CustomFeeModel())
        
        self.data[symbol] = SymbolData(symbol, self.long_period)
    
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.AfterMarketOpen(self.symbols[0]), self.Rebalance)

def OnData(self, data):
    for symbol in self.data:
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data and data[symbol_obj]:
            self.data[symbol].update(data[symbol_obj].Value)
                    
def Rebalance(self):
    # momentum pair - long and short period momentum.
    momentum = {
        x : (self.data[x].performance(self.long_period), self.data[x].performance(self.short_period)) for x in self.symbols if self.data[x].is_ready()
    }
    
    long = []
    short = []
    if len(momentum) != 0:
        sorted_long_mom = sorted(momentum.items(), key = lambda x: x[1][0])
        quartile = floor(len(sorted_long_mom) / 4)
        long_winners = sorted_long_mom[-quartile:]
        long_loosers = sorted_long_mom[:quartile]
        
        short_term_n = 3
        long_winners_sorted_short_mom = sorted(long_winners, key = lambda x: x[1][1])
        short = [x[0] for x in long_winners_sorted_short_mom][:short_term_n]
        
        long_loosers_sorted_short_mom = sorted(long_loosers, key = lambda x: x[1][1])
        long = [x[0] for x in long_loosers_sorted_short_mom][-short_term_n:]

        long_w = self.Portfolio.TotalPortfolioValue / self.holding_period / len(long)
        short_w = self.Portfolio.TotalPortfolioValue / self.holding_period / len(short)
        
        # symbol/quantity collection
        long_symbol_q = [(x, floor(long_w / self.Securities[x].Price)) for x in long]
        short_symbol_q = [(x, -floor(short_w / self.Securities[x].Price)) for x in short]
    
        self.managed_queue.append(RebalanceQueueItem(long_symbol_q + short_symbol_q))
        
    if len(self.managed_queue) == 0: return

    remove_item = None
    
    # Rebalance portfolio
    for item in self.managed_queue:
        if item.holding_period == self.holding_period:
            
            # liquidate
            for symbol, quantity in item.symbol_q:
                self.MarketOrder(symbol, -quantity)
            remove_item = item
            
        elif item.holding_period == 0:
            opened_symbol_q = []
            
            for symbol, quantity in item.symbol_q:
                self.MarketOrder(symbol, quantity)
                opened_symbol_q.append((symbol, quantity))
                        
            # Only opened orders will be closed        
            item.symbol_q = opened_symbol_q
            
        item.holding_period += 1
        
    # We need to remove closed part of portfolio after loop. Otherwise it will miss one item in self.managed_queue.
    if remove_item:
        self.managed_queue.remove(remove_item)
class RebalanceQueueItem():
def __init__(self, symbol_q):
    # symbol/quantity collections
    self.symbol_q = symbol_q
    self.holding_period = 0
class SymbolData():
def __init__(self, symbol, period):
    self.Symbol = symbol
    self.Price = RollingWindow[float](period)
    
def update(self, value):
    self.Price.Add(value)

def is_ready(self) -> bool:
    return self.Price.IsReady
    
def performance(self, days_to_count_in) -> float:
    closes = [x for x in self.Price][:days_to_count_in]
    return (closes[0] / closes[-1] - 1)
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
