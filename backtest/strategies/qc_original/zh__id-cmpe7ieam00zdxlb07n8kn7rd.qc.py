# Original QuantConnect / library Python
# locale=zh slug="外汇期权中的历史波动率与隐含波动率策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
class HistoricalAndImpliedVolatilityInFXOptions(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(1000000)
    
    self.min_expiry = 20
    self.max_expiry = 60
    
    self.trade_count = 2 # trade n on long and n on short
    self.percentage_traded = 0.1 # trading 10% of portfolio
    
    self.period = 12 * 21 # need 12 months of daily prices
    
    self.prices = {} # storing daily prices
    self.contracts = {} # storing option contracts
    self.symbols_by_ticker = {} # storing symbols by their tickers
    
    self.tickers = ['FXY', 'FXE', 'FXF', 'FXC', 'FXB', 'FXA', 'FXI']
    for ticker in self.tickers:
        # subscribe to etf
        security = self.AddEquity(ticker, Resolution.Minute)
        
        # change normalization to raw to allow adding etf contracts
        security.SetDataNormalizationMode(DataNormalizationMode.Raw)
        # set fee model and leverage
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(5)
        
        # get etf symbol
        symbol = security.Symbol
        # store etf symbol by etf ticker
        self.symbols_by_ticker[ticker] = symbol
        # create RollingWindow for daily prices
        self.prices[symbol] = RollingWindow[float](self.period)
        # create object from Contracts class for etf symbol
        self.contracts[symbol] = Contracts(self.Time.date(), 0, [])
    
    self.day = -1
    self.selection_flag = False
    
def OnData(self, data):
    # execute once a day
    if self.day == self.Time.day:
        return
    self.day = self.Time.day
    
    for _, symbol in self.symbols_by_ticker.items():
        if symbol in self.contracts:
            if self.contracts[symbol].expiry_date  underlying_price], key=lambda x: abs(x-underlying_price))
    # put_strike:float = min([x for x in strikes if x
