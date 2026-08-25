# Original QuantConnect / library Python
# locale=en slug="momentum-stock-picking-strategy-using-rsi-indicator"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class MomentumStockPickingRSIIndicator(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.AddUniverse(self.Universe.QC500)   # monthly selected proxy SP500 universe
    
    self.rsi = {}
    self.rsi_history = {}
    self.period = 25
    
    # monthly updated stock selection
    self.selection = []
    
    symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        symbol = security.Symbol
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(10)
        
        if symbol not in self.selection:
            self.selection.append(symbol)
    
    for security in changes.RemovedSecurities:
        symbol = security.Symbol
        if symbol in self.selection:
            self.selection.remove(symbol)
    
def OnData(self, data):
    long = []
    
    # calculate signal
    for symbol in self.selection:
        if not symbol in self.rsi:
            self.rsi[symbol] = self.RSI(symbol, 14, MovingAverageType.Simple, Resolution.Daily)
            self.rsi_history[symbol] = RollingWindow[float](self.period)
    
        if not self.rsi[symbol].IsReady: continue
    
        self.rsi_history[symbol].Add(self.rsi[symbol].Current.Value)
        
        if self.rsi_history[symbol].IsReady:
            rsi_values = [x for x in self.rsi_history[symbol]]
            max_rsi = max(rsi_values)
            bull_range = sum([x > 40 for x in rsi_values]) == self.period
            
            if max_rsi > 70 and bull_range:
                long.append(symbol)
    
    # liquidate
    invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long:
            self.Liquidate(symbol)
    # open new trades
    long_count = len(long)
    
    for symbol in long:
        if self.Securities[symbol].Price != 0 and self.Securities[symbol].IsTradable:
            self.SetHoldings(symbol, 1 / long_count)
        
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
