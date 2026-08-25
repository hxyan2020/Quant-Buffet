# Original QuantConnect / library Python
# locale=en slug="lunar-cycle-in-precious-metals"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from QuantConnect.Data import SubscriptionDataSource
from QuantConnect.Python import PythonData
#endregion
class LunarCycleinPreciousMetals(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2004, 1, 1)
    self.SetCash(100000)
    self.lunar_phase:Symbol = self.AddData(MoonPhase, "phase", Resolution.Daily).Symbol
    self.symbol = self.AddEquity("GLD", Resolution.Daily).Symbol
    self.settings.daily_precise_end_time = False

def OnData(self, data):
    if self.Securities[self.lunar_phase].GetLastData() and self.Time.date() > MoonPhase.get_last_update_date():
        self.Liquidate(self.symbol)
    if self.symbol in data and data[self.symbol]:
        if self.securities[self.lunar_phase].get_last_data():
            # long in emerging market index ETF 7 days before the new moon (It's the Last Quarter)
            if self.securities[self.lunar_phase].get_last_data().value == 3 and not self.Portfolio[self.symbol].IsLong:
                self.SetHoldings(self.symbol, 1)
        
            # short on emerging market index ETF 7 days before the full moon (It's the First Quarter)
            elif self.securities[self.lunar_phase].get_last_data().value == 1 and not self.Portfolio[self.symbol].IsShort:
                self.SetHoldings(self.symbol, -1)
    
class MoonPhase(PythonData):
_last_update_date:datetime.date = datetime(1,1,1).date()
@staticmethod
def get_last_update_date() -> datetime.date:
   return MoonPhase._last_update_date
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/calendar/moon_phase.csv", SubscriptionTransportMedium.RemoteFile)
def Reader(self, config, line, date, isLiveMode):
    index = MoonPhase()
    index.Symbol = config.Symbol
    try:
        # Source: https://www.timeanddate.com/moon/phases/?year=2023
        # Example File Format: (Data starts from 01/07/2004)
        # date;phase
        # 2004-01-07;Full Moon
        # 2004-01-15;Last Quarter
        data = line.split(';')
        if data[0] == "date": return None
        index.Time = datetime.strptime(data[0], "%Y-%m-%d")
        if data[1] == "New Moon":
            index.Value = 0
        elif data[1] == "First Quarter":
            index.Value = 1
        elif data[1] == "Full Moon":
            index.Value = 2
        elif data[1] == "Last Quarter":
            index.Value = 3
        if index.Time.date() > MoonPhase._last_update_date:
            MoonPhase._last_update_date = index.Time.date()
    except:
        return None
        
    return index
