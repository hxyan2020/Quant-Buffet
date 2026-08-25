# Original QuantConnect / library Python
# locale=en slug="value-effect-within-countries-v2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class ValueEffectwithinCountries(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.symbols = {
        'Argentina' : 'ARGT',
        'Australia' : 'EWA',
        'Austria' : 'EWO',
        'Belgium' : 'EWK',
        'Brazil' : 'EWZ',
        'Canada' : 'EWC',
        'Chile' : 'ECH',
        'China' : 'FXI',
        'Egypt' : 'EGPT',
        'France' : 'EWQ',
        'Germany' : 'EWG',
        'Hong Kong' : 'EWH',
        'India' : 'INDA',
        'Indonesia' : 'EIDO',
        'Ireland' : 'EIRO',
        'Israel' : 'EIS',
        'Italy' : 'EWI',
        'Japan' : 'EWJ',
        'Malaysia' : 'EWM',
        'Mexico' : 'EWW',
        'Netherlands' : 'EWN',
        'New Zealand' : 'ENZL',
        'Norway' : 'NORW',
        'Philippines' : 'EPHE',
        'Poland' : 'EPOL',
        'Russia' : 'ERUS',
        'Saudi Arabia' : 'KSA',
        'Singapore' : 'EWS',
        'South Africa' : 'EZA',
        'South Korea' : 'EWY',
        'Spain' : 'EWS',
        'Sweden' : 'EWD',
        'Switzerland' : 'EWL',
        'Taiwan' : 'EWT',
        'Thailand' : 'THD',
        'Turkey' : 'TUR',
        'United Kingdom' : 'EWU',
        'United States' : 'SPY'
    }
    
    for symbol in self.symbols:
        data = self.AddEquity(self.symbols[symbol], Resolution.Daily)
        data.SetLeverage(5)
    
    self.country_pb_data:Symbol = self.AddData(CountryPB, 'CountryData').Symbol
    self.quantile:int = 3
    self.recent_month:int = -1
    self.max_missing_days:int = 365
def OnData(self, data:Slice) -> None:
    # rebalance once a month
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    if self.Securities[self.country_pb_data].GetLastData() and (self.Time.date() - self.Securities[self.country_pb_data].GetLastData().Time.date()).days > self.max_missing_days:
        self.Liquidate()
        return
    bm_data:dict[str, float] = {}
    country_pb_data = self.Securities[self.country_pb_data].GetLastData()
    if country_pb_data:
        for symbol in self.symbols:
            pb:float = country_pb_data[symbol]
            bm_data[symbol] = 1 / pb
    long:List[str] = []
    short:List[str] = []
    if len(bm_data) >= self.quantile:
        sorted_by_bm:List = sorted(bm_data.items(), key = lambda x: x[1], reverse = True)
        quantile:int = int(len(bm_data) / self.quantile)
        long = [x[0] for x in sorted_by_bm[:quantile]]
        short = [x[0] for x in sorted_by_bm[-quantile:]]
    
    # liquidate
    invested:List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    # trade execution
    long_count:int = len(long)
    short_count:int = len(short)
    
    for symbol in long:
        traded_symbol:str = self.symbols[symbol]
        if traded_symbol in data and data[traded_symbol]:
            self.SetHoldings(traded_symbol, 1 / long_count)
    for symbol in short:
        traded_symbol:str = self.symbols[symbol]
        if traded_symbol in data and data[traded_symbol]:
            self.SetHoldings(traded_symbol, -1 / short_count)
# Country PB data
# NOTE: IMPORTANT: Data order must be ascending (date-wise)
from dateutil.relativedelta import relativedelta
class CountryPB(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/economic/country_pb.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = CountryPB()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%Y") + relativedelta(years=1)
    self.symbols = ['Argentina','Australia','Austria','Belgium','Brazil','Canada','Chile','China','Egypt','France','Germany','Hong Kong','India','Indonesia','Ireland','Israel','Italy','Japan','Malaysia','Mexico','Netherlands','New Zealand','Norway','Philippines','Poland','Russia','Saudi Arabia','Singapore','South Africa','South Korea','Spain','Sweden','Switzerland','Taiwan','Thailand','Turkey','United Kingdom','United States']
    index = 1
    for symbol in self.symbols:
        data[symbol] = float(split[index])
        index += 1
        
    data.Value = float(split[1])
    return data
