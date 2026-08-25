# Original QuantConnect / library Python
# locale=en slug="demographic-changes-predict-stock-market-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
#endregion
class DemographicChanges(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.symbols = {'AU':'EWA', 'AT':'EWO', 'BE':'EWK', 'CA':'EWC', 'FR':'EWQ', 'DE':'EWG', 'IT':'EWI', 'JP':'EWJ', 'NL':'EWN', 'ES':'EWP', 'SE':'EWD', 'CH':'EWL', 'GB':'EWU', 'US':'SPY'}
    
    for symbol in self.symbols:
        data = self.AddEquity(self.symbols[symbol], Resolution.Daily)
        data.SetLeverage(10)
    
    self.demographic_data:Symbol = self.AddData(DemographicData, 'DemographicData').Symbol
    
    self.recent_month:int = -1
def OnData(self, data:Slice) -> None:
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    # rebalance once a year
    if self.Time.month != 1: return
    age_data = {}
    if self.demographic_data in data and data[self.demographic_data]:
        for symbol in self.symbols:
            age_data[symbol] = data[self.demographic_data].GetProperty(symbol)
    if len(age_data) == 0: 
        self.Liquidate()
        return
    
    age_data_values = [x[1] for x in age_data.items()]
    age_data_mean = np.mean(age_data_values)
    age_data_std = np.std(age_data_values)
    
    long = []
    short = []
    for symbol in self.symbols:
        if age_data[symbol]  age_data_mean + age_data_std:
            short.append(self.symbols[symbol])
    
    # liquidate
    invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    # trade exxecution
    long_count = len(long)
    short_count = len(short)
    
    for symbol in long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, 1 / long_count)
    for symbol in short:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, -1 / short_count)
# Demographic data - population 65+ yo
# NOTE: IMPORTANT: Data order must be ascending (date-wise)
from dateutil.relativedelta import relativedelta
class DemographicData(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/economic/population_65_over.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = DemographicData()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    # Data example:
    # year;AU;AT;BE;CA;FR;DE;IT;JP;NL;ES;SE;CH;GB;US
    # 2000;12.4;15.4;16.7;12.5;16.2;16.2;18.1;17.4;13.5;16.5;17.3;15.2;15.8;12.4
    #
    # YEARLY DATA
    
    data.Time = datetime.strptime(split[0], "%Y") + relativedelta(months=12)  # NOTE: Preventing of look ahaead bias. Add 12 months so this year we see last year's data.
    data['AU'] = float(split[1])
    data['AT'] = float(split[2])
    data['BE'] = float(split[3])
    data['CA'] = float(split[4])
    data['FR'] = float(split[5])
    data['DE'] = float(split[6])
    data['IT'] = float(split[7])
    data['JP'] = float(split[8])
    data['NL'] = float(split[9])
    data['ES'] = float(split[10])
    data['SE'] = float(split[11])
    data['CH'] = float(split[12])
    data['GB'] = float(split[13])
    data['US'] = float(split[14])
        
    data.Value = float(split[1])
    return data
