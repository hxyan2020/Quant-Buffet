# Original QuantConnect / library Python
# locale=en slug="intraday-momentum-in-fixed-income"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from datetime import time
EXPIRY_MIN_DAYS = 90
EXPIRY_LIQUIDATE_DAYS = 5
class IntradayMomentuminFixedIncome(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2008, 1, 1)
    self.SetCash(100000)
    self.symbols = [
                    Futures.Financials.Y30TreasuryBond,
                    Futures.Financials.Y10TreasuryNote,
                    Futures.Financials.Y5TreasuryNote,
                    Futures.Financials.Y2TreasuryNote,
                    ]
                
    self.close_price = {}
    self.active_future = {}
    
    for symbol in self.symbols:
        future = self.AddFuture(symbol)
        future.SetFilter(EXPIRY_LIQUIDATE_DAYS, EXPIRY_MIN_DAYS)
        self.active_future[symbol] = None
    
    self.Schedule.On(self.DateRules.EveryDay(future.Symbol), self.TimeRules.BeforeMarketClose(future.Symbol, 1), self.Close)
    self.Schedule.On(self.DateRules.EveryDay(future.Symbol), self.TimeRules.BeforeMarketClose(future.Symbol, 30), self.Purchase)

def OnData(self, slice):
    for chain in slice.FutureChains:
        contracts = [contract for contract in chain.Value]
        
        sym = chain.Value.Symbol.Value
        if len(contracts) == 0:
            self.active_future[sym] = None
            continue
        
        contract = sorted(contracts, key=lambda k : k.OpenInterest, reverse=True)[0]
        if sym in self.active_future and self.active_future[sym] is not None and contract.Symbol == self.active_future[sym].Symbol:
            continue
        
        self.active_future[sym] = contract
        self.Securities[contract.Symbol].SetFeeModel(CustomFeeModel(self))
        
def Purchase(self):
    if len(self.close_price) == 0: return
    
    performance_until_purchase = {}
    for symbol, close_price in self.close_price.items():
        if symbol in self.active_future:
            current_price = (self.active_future[symbol].AskPrice + self.active_future[symbol].BidPrice) / 2 if self.active_future[symbol].LastPrice == 0 else self.active_future[symbol].LastPrice
            sym = self.active_future[symbol].Symbol
            
            if current_price != 0 and close_price != 0:
                performance_until_purchase[sym] = current_price / close_price - 1
            
    self.close_price.clear()
    
    if len(performance_until_purchase) == 0: return
    
    long = [x[0] for x in performance_until_purchase.items() if x[1] > 0]
    short = [x[0] for x in performance_until_purchase.items() if x[1]
