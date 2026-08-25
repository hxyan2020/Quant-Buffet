# Original QuantConnect / library Python
# locale=en slug="trading-commodity-etfs-versus-equity-etfs"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class TradingCommodityVersusEquity(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    data = self.AddEquity('SPY', Resolution.Daily)
    data.SetLeverage(5)
    self.market:Symbol = data.Symbol
    
    data = self.AddEquity('DBC', Resolution.Daily)
    data.SetLeverage(5)
    self.commodities:Symbol = data.Symbol
    
    self.data:RollingWindow = RollingWindow[float](2)
    
def OnData(self, data):
    # store market price
    if self.market in data and data[self.market] and self.commodities in data and data[self.commodities]:
        market_price:float = data[self.market].Value
        self.data.Add(market_price)
        
        if self.data.IsReady:
            prevoius_day_return:float = self.data[0] / self.data[1] - 1
            if prevoius_day_return > 0:
                self.SetHoldings(self.commodities, 1)
                self.SetHoldings(self.market, -1)
            else:
                self.Liquidate()
