# Original QuantConnect / library Python
# locale=en slug="market-sentiment-and-an-overnight-anomaly"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
# endregion

class MarketSentimentAndAnOvernightAnomaly(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.period:int = 20 # sma period

    self.weight:float = 0
    self.price_data:dict = {}

    self.spy_symbol:Symbol = self.AddEquity('SPY', Resolution.Minute).Symbol
    self.vix_symbol:Symbol = self.AddData(QuandlVix, 'CBOE/VIX', Resolution.Daily).Symbol       # starts in 2004
    self.bms_symbol:Symbol = self.AddData(QuantpediaBMS, 'BMS_GLOBAL', Resolution.Daily).Symbol # starts in 2018

    for symbol in [self.spy_symbol, self.vix_symbol, self.bms_symbol]:
        self.price_data[symbol] = RollingWindow[float](self.period)

def OnData(self, data: Slice):
    # calculate signal from SPY 16 minutes before close
    if self.spy_symbol in data and data[self.spy_symbol] and self.Time.hour == 15 and self.Time.minute == 44:
        weight:float = 0.

        for symbol in [self.spy_symbol, self.vix_symbol, self.bms_symbol]:
            # trade only sub-strategies with underlying data available
            if self.Securities[symbol].GetLastData() and (self.Time.date() - self.Securities[symbol].GetLastData().Time.date()).days  bool:
    prices:list[float] = [x for x in rolling_window]
    moving_average:float = sum(prices) / len(prices)

    result:bool = False
    if signal_above_sma and (curr_value > moving_average):
        result = True
    elif not signal_above_sma and (curr_value
