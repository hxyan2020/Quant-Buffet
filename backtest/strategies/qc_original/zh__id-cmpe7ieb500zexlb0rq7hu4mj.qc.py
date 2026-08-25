# Original QuantConnect / library Python
# locale=zh slug="货币中的波动率风险溢价策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class VolatilityRiskPremiuminCurrencies(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.min_expiry = 30
    self.max_expiry = 45
    
    self.symbols = []
    self.contracts = {}
    
    tickers = ['FXE', 'FXB', 'FXY']
    
    for ticker in tickers:
        # equity data
        data = self.AddEquity(ticker, Resolution.Daily)
        data.SetLeverage(10)
        data.SetFeeModel(CustomFeeModel())
        
        # change normalization to raw to allow adding etf contracts
        data.SetDataNormalizationMode(DataNormalizationMode.Raw)
        
        self.symbols.append(data.Symbol)
    
    self.last_day:int = -1
    self.trade_flag = False
    
def OnData(self, data):
    # check once a day
    if self.Time.day == self.last_day:
        return
    self.last_day = self.Time.day
    # check contracs expiration
    for symbol in self.symbols:
        if symbol in self.contracts and self.contracts[symbol].expiry_date - timedelta(days=2)
