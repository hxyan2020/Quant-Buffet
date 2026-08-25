# Original QuantConnect / library Python
# locale=en slug="federal-open-market-committee-meeting-effect-in-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
from pandas.tseries.offsets import BDay
from datetime import datetime

class FederalOpenMarketCommitteeMeetingEffectinStocks(XXX):

def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.market:Symbol = self.AddEquity("SPY", Resolution.Minute).Symbol

    self.fed_days_symbol:Symbol = self.AddData(FedDays, 'fed_days', Resolution.Daily, TimeZones.NewYork).Symbol
    self.SetWarmUp(1, Resolution.Daily)
    FedDays.set_algo(self)
    
    self.recent_day:int = -1

def OnData(self, data: Slice) -> None:
    if self.IsWarmingUp: return

    if self.fed_days_symbol in data and data[self.fed_days_symbol]:
        self.Log(f"New FOMC meeting data arrived: {self.Time}; submitting an MOC order...")

        # new fed day data arrived
        quantity:float = self.CalculateOrderQuantity(self.market, 1.)
        self.MarketOnCloseOrder(self.market, quantity)

        self.recent_day = self.Time.day
    else:
        # other new minute resolution data arrived
        if self.Portfolio[self.market].Invested:
            if self.Time.day != self.recent_day:
                self.recent_day = self.Time.day

                self.Log(f"FOMC meeting day; submitting an MOC order to close opened position...")
            
                self.MarketOnCloseOrder(self.market, -self.Portfolio[self.market].Quantity)
    
class FedDays(PythonData):
algo = None

@staticmethod
def set_algo(algo):
    FedDays.algo = algo

def GetSource(self, config:SubscriptionDataConfig, date:datetime, isLiveMode:bool) -> SubscriptionDataSource:
    if isLiveMode:
        # FedDays.algo.Log(f"Edited GetSource date {FedDays.algo.Time}")
        return SubscriptionDataSource("https://data.quantpedia.com/backtesting_data/economic/fed_days.json", SubscriptionTransportMedium.RemoteFile, FileFormat.UnfoldingCollection)

    return SubscriptionDataSource("https://data.quantpedia.com/backtesting_data/economic/fed_days.csv", SubscriptionTransportMedium.RemoteFile)
    
def Reader(self, config:SubscriptionDataConfig, line:str, date:datetime, isLiveMode:bool) -> BaseData:
    if isLiveMode:
        try:
            # FedDays.algo.Log(f"Reader")

            objects = []
            data = json.loads(line)
            end_time = None

            for index, sample in enumerate(data):
                custom_data = FedDays()
                custom_data.Symbol = config.Symbol

                custom_data.Time = (datetime.strptime(str(sample["fed_date"]), "%Y-%m-%d") - BDay(1)).replace(hour=9, minute=31)
                # FedDays.algo.Log(f"{custom_data.Time}")

                end_time = custom_data.Time  
                objects.append(custom_data)

            return BaseDataCollection(end_time, config.Symbol, objects) 

        except ValueError:
            # FedDays.algo.Log(f"Reader Error")
            return None
    else:
        if not (line.strip() and line[0].isdigit()):
            return None
        
        custom = FedDays()
        custom.Symbol = config.Symbol

        custom.Time = (datetime.strptime(line, "%Y-%m-%d") - BDay(1)).replace(hour=9, minute=31)
        custom.Value = 0.
        custom["fed_date_str"] = line

        return custom
