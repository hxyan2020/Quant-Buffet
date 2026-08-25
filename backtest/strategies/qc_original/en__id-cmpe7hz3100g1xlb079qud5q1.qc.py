# Original QuantConnect / library Python
# locale=en slug="规模因子与货币政策策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion

class SizeFactorvsMonetaryPolicyRegime(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(1999, 1, 1)
    self.SetCash(100000)

    self.large_cap:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.small_cap:Symbol = self.AddEquity("IWM", Resolution.Daily).Symbol
    self.leverage:int = 5

    for symbol in [self.large_cap] + [self.small_cap]:
        self.Securities[symbol.Value].SetLeverage(self.leverage)
    
    # changes in FED policy
    dates_str_restrictive:List[str] = ["24.08.1999", "30.06.2004", "14.12.2016"]
    dates_str_expansive:List[str] = ["03.01.2001", "18.09.2007", "31.7.2019"]
    self.dates_res:List[datetime.date] = [datetime.strptime(x, "%d.%m.%Y").date() for x in dates_str_restrictive]   # datetime type
    self.dates_exp:List[datetime.date] = [datetime.strptime(x, "%d.%m.%Y").date() for x in dates_str_expansive]     # datetime type

    self.easing_flag:bool = None
    self.selection_flag:bool = False
    self.last_target_rate:float = None
    self.target_rate:Symbol = self.AddData(FederalTargetRange, 'DFEDTARU', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthStart(self.large_cap), self.TimeRules.AfterMarketOpen(self.large_cap), self.Selection)

def OnData(self, data: Slice) -> None:
    curr_date:datetime.date = self.Time.date()
    if curr_date in self.dates_exp:
        self.easing_flag = True
    if curr_date in self.dates_res:
        self.easing_flag = False

    # monthly rebalance
    if self.selection_flag:
        self.selection_flag = False

        # check target rate data arrival
        ftr_last_update_date:Dict[Symbol, datetime.date] = FederalTargetRange.get_last_update_date()
        if self.Securities[self.target_rate].GetLastData():
            if self.target_rate in ftr_last_update_date and self.Time.date() >= ftr_last_update_date[self.target_rate]: 
                self.Liquidate()
                return

            curr_target_rate = self.Securities[self.target_rate].Price

            # switch to external data source
            if curr_date > self.dates_exp[-1]:
                if self.last_target_rate:
                    if curr_target_rate > self.last_target_rate:
                        self.easing_flag = False
                    elif curr_target_rate  None:
    self.selection_flag = True

# source: https://fred.stlouisfed.org/series/DFEDTARU
class FederalTargetRange(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource('data.quantpedia.com/backtesting_data/economic/DFEDTARU.csv', SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)

_last_update_date:Dict[Symbol, datetime.date] = {}

@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return FederalTargetRange._last_update_date

def Reader(self, config, line, date, isLiveMode):
    data = FederalTargetRange()
    data.Symbol = config.Symbol

    if not line[0].isdigit(): return None
    split = line.split(';')
    
    # Parse the CSV file's columns into the custom data class
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    data.Value = float(split[1])

    if config.Symbol not in FederalTargetRange._last_update_date:
        FederalTargetRange._last_update_date[config.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > FederalTargetRange._last_update_date[config.Symbol]:
        FederalTargetRange._last_update_date[config.Symbol] = data.Time.date()
    
    return data
