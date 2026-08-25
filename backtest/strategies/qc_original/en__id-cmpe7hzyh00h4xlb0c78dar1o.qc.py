# Original QuantConnect / library Python
# locale=en slug="水星逆行交易策略在中国市场的应用"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from pandas.tseries.offsets import BDay
# endregion

class MercuryRetrogradeAstrologyTradingStrategyinChineseMarket(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.lag:int = 5
    self.counter:Union[None, int] = None
    self.trade_direction:Union[None, int] = None

    # load custom data
    self.mercury_retrograde_calendar:Symbol = self.AddData(data_tools.MercuryRetrogradeCalendar, 'mercury_retrograde_calendar', Resolution.Daily).Symbol
    self.market:Symbol = self.AddData(data_tools.QuantpediaCSI300, 'CSI_300', Resolution.Daily).Symbol
    self.Securities[self.market].SetLeverage(self.leverage)
    self.Securities[self.market].SetFeeModel(data_tools.CustomFeeModel())

def OnData(self, data: Slice):
    market_last_update_date:datetime.date = data_tools.QuantpediaCSI300._last_update_date
    calendar_last_update_date:datetime.date = data_tools.MercuryRetrogradeCalendar._last_update_date

    # check if data is still coming
    if self.Securities[self.market].GetLastData() and self.Time.date() >= market_last_update_date \
        or self.Securities[self.mercury_retrograde_calendar].GetLastData() and self.Time.date() >= calendar_last_update_date:
        self.Liquidate()
        return

    if self.counter is not None:
        if self.market in data and data[self.market]:
            self.counter += 1
            if self.counter == self.lag:
                self.SetHoldings(self.market, self.trade_direction)
                self.trade_direction = None

    if self.mercury_retrograde_calendar in data and data[self.mercury_retrograde_calendar] and self.Securities[self.market].GetLastData():
        if self.trade_direction is None:
            self.trade_direction = -1 if data[self.mercury_retrograde_calendar].status == 'start' else 1
            self.counter = 0
