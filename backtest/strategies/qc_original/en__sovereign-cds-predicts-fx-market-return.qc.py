# Original QuantConnect / library Python
# locale=en slug="sovereign-cds-predicts-fx-market-return"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
#endregion
class SovereignCDSPredictsFXMarketReturn(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2008, 1, 1)
    self.SetCash(100000)
    
    # forex pair symbol : (CDS country symbol, long-short switch position flag)
    self.symbols:Dict[str, Tuple[List[str], bool]] = {
        'AUDUSD' : (['AU'], False),
        'EURUSD' : (['ES', 'IT', 'GR'], False),
        'GBPUSD' : (['GB'], False),
        'USDTRY' : (['TR'], True),
        'RUBUSD' : (['RU'], False),
        'BRLUSD' : (['BR'], False),
        # 'USDCAD' : (['CA'], True),
        # 'USDMXN' : (['MX'], True),
    }
    self.cds_symbols:Dict[str, tuple] = {}
    for fx_symbol, (country_codes, _) in self.symbols.items():
        # subscribe forex symbol
        data:Forex = self.AddForex(fx_symbol, Resolution.Minute, Market.Oanda)
        data.SetLeverage(5)
        
        # subscribe CDS symbols
        for country_code in country_codes:
            cds_1y_symbol:Symbol = self.AddData(CDSData1Y, country_code, Resolution.Daily).Symbol
            cds_10y_symbol:Symbol = self.AddData(CDSData10Y, country_code, Resolution.Daily).Symbol
            self.cds_symbols[country_code] = (cds_1y_symbol, cds_10y_symbol)
    
    self.recent_month:int = -1
    self.quantile:int = 3
    
def OnData(self, data:Slice) -> None:
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    # end of custom data
    last_update_date_1Y:Dict[str, datetime.date] = CDSData1Y.get_last_update_date()
    last_update_date_10Y:Dict[str, datetime.date] = CDSData10Y.get_last_update_date()
    # store actual CDS
    actual_cds:Dict[str, float] = {}
    for fx_symbol, (country_codes, _) in self.symbols.items():
        # price data are available
        if fx_symbol in data and data[fx_symbol]:
            cds_values:List[float] = []
            for country_code in country_codes:
                # CDS data are available
                if self.Securities[self.cds_symbols[country_code][0]].GetLastData() and self.Securities[self.cds_symbols[country_code][1]].GetLastData():
                    if self.Time.date()  SubscriptionDataSource:
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/cds/{0}_CDS_1Y.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
_last_update_date:Dict[str, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[str, datetime.date]:
   return CDSData1Y._last_update_date
def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data = CDSData1Y()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    
    # store last date of the symbol
    if data.Symbol not in CDSData1Y._last_update_date:
        CDSData1Y._last_update_date[data.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > CDSData1Y._last_update_date[data.Symbol]:
        CDSData1Y._last_update_date[data.Symbol] = data.Time.date()
    data.Value = float(split[1])
    return data
# 10Y Credit Default Swap data.
# Source: https://www.investing.com/
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class CDSData10Y(PythonData):
def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/cds/{0}_CDS_10Y.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
_last_update_date:Dict[str, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[str, datetime.date]:
   return CDSData10Y._last_update_date
def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data = CDSData10Y()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    # store last date of the symbol
    if data.Symbol not in CDSData10Y._last_update_date:
        CDSData10Y._last_update_date[data.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > CDSData10Y._last_update_date[data.Symbol]:
        CDSData10Y._last_update_date[data.Symbol] = data.Time.date()
    data.Value = float(split[1])
    return data
