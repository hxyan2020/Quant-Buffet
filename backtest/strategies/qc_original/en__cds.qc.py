# Original QuantConnect / library Python
# locale=en slug="主权信用违约掉期（cds）货币因子策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
#endregion

class SovereignCDSCurrencyFactor(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2008, 1, 1)
    self.SetCash(100000)
    
    # forex pair symbol : (CDS country symbol, GDP symbol, long-short switch position flag)
    self.symbols:Dict[str, Tuple[List[str], bool]] = {
        'AUDUSD' : (['AU'], False),
        'USDCAD' : (['CA'], True),
        'EURUSD' : (['ES', 'FR', 'IT', 'GR'], False),
        'GBPUSD' : (['GB'], False),
        'USDMXN' : (['MX'], True),
        'USDTRY' : (['TR'], True),
        'RUBUSD' : (['RU'], False),
        'BRLUSD' : (['BR'], False),
    }

    self.cds_symbols:Dict[str, tuple] = {}

    for fx_symbol, (country_codes, _) in self.symbols.items():
        # subscribe forex symbol
        data = self.AddForex(fx_symbol, Resolution.Minute, Market.Oanda)
        data.SetLeverage(5)
        
        # subscribe CDS symbols
        for country_code in country_codes:
            cds_symbol:Symbol = self.AddData(CDSData5Y, country_code, Resolution.Daily).Symbol
            self.cds_symbols[country_code] = cds_symbol
    
    self.quantile:int = 3
    self.recent_month:int = -1
    
def OnData(self, data):
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month

    # store actual CDS
    actual_cds:Dict[str, float] = {}

    # end of custom data
    last_update_date_5Y:Dict[str, datetime.date] = CDSData5Y.get_last_update_date()

    for fx_symbol, (country_codes, _) in self.symbols.items():
        # price data are available
        if fx_symbol in data and data[fx_symbol]:
            cds_values:List[float] = []
            for country_code in country_codes:
                # CDS data are available
                if self.Securities[self.cds_symbols[country_code]].GetLastData():
                    if self.Time.date()  SubscriptionDataSource:
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/cds/{0}_CDS_5Y.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)

_last_update_date:Dict[str, datetime.date] = {}

@staticmethod
def get_last_update_date() -> Dict[str, datetime.date]:
   return CDSData5Y._last_update_date

def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data = CDSData5Y()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)

    # store last date of the symbol
    if data.Symbol not in CDSData5Y._last_update_date:
        CDSData5Y._last_update_date[data.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > CDSData5Y._last_update_date[data.Symbol]:
        CDSData5Y._last_update_date[data.Symbol] = data.Time.date()

    data.Value = float(split[1])

    return data
