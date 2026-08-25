# Original QuantConnect / library Python
# locale=zh slug="交易vix交易所交易基金（vix-etfs）"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class TradingVIXETFs(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.symbols = ["SVXY", "VXX", "ZIV", "VXZ"]
    self.data = {}
    self.period = 83
    self.SetWarmUp(self.period)
    for symbol in self.symbols:
        data = self.AddEquity(symbol, Resolution.Daily)
        self.data[symbol] = RollingWindow[float](self.period)
def OnData(self, data):
    for symbol in self.data:
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data.Keys:
            if data[symbol_obj]:
                price = data[symbol_obj].Value
                if price != 0:
                    self.data[symbol].Add(price)
    
    if self.IsWarmingUp: return
    self.Liquidate()
    returns = {}
    for symbol in self.symbols:
        if self.data[symbol].IsReady:
            prices = [x for x in self.data[symbol]]
            returns[symbol] = prices[0] / prices[-1] - 1
    
    if len(returns) != 0:
        sorted_by_return = sorted(returns.items(), key = lambda x: x[1], reverse = True)
        
        symbols = [x[0] for x in sorted_by_return]
        top_symbol = symbols[0]
        top_val = returns[top_symbol]

        # if self.Portfolio.Invested:
        #     if not self.Securities[top_symbol].Invested:
        #         self.Liquidate()
        #         if top_val > 0:
        #             self.SetHoldings(top_symbol, 1/2)
        # else:
        #     self.SetHoldings(top_symbol, 1/2)
        
        if top_val > 0:
            if self.Securities[top_symbol] != 0:
                self.SetHoldings(top_symbol, 1/2)
