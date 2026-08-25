# Original QuantConnect / library Python
# locale=zh slug="基于cape的行业选择策"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class CAPESectorPickingStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1) 
    self.SetCash(100000)  
    
    self.symbols = [
        "XLC", # Community Services
        "XLRE", # Real Estate
        "XLV", # Health Care
        "XLI", # Industrial
        "XLY", # Consumer Cyclical    
        "XLP", # Consumer Defensive    
        "XLB", # Basic Materials    
        "XLK", # Technology    
        "XLU", # Utilities    
        "XLE", # Energy    
        "XLF", # Financial Services  
    ]
    
    # Daily prices.
    self.data = {}
    
    self.period = 21 * 12
    self.max_missing_days = 5
    self.min_symbol_count = 5
    
    for symbol in self.symbols:
        data = self.AddEquity(symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(5)
        
        self.data[symbol] = SymbolData(self.period)
        
        self.AddData(QuantpediaSectorCAPE, symbol, Resolution.Daily)
    
    self.recent_month = -1
    
def OnData(self, data):
    for symbol in self.symbols:
        if symbol in data and data[symbol]:
            self.data[symbol].update(data[symbol].Value)
    
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    # CAPE data are available since 2010
    cape_values = {}
    for symbol in self.symbols:
        cape_data = self.Securities[symbol + '.QuantpediaSectorCAPE'].GetLastData()
        if cape_data and (self.Time.date() - cape_data.Time.date()).days = self.min_symbol_count:
        # sorted by cape, selecting 5 lowest
        five_lowest = [(x[0], x[1][0]) for x in sorted(performance_cape.items(), key=lambda item: item[1][1])][:self.min_symbol_count]
        # choosing five with highest 12 month momentum
        long = [x[0] for x in sorted(five_lowest, key=lambda item: item[1], reverse=True)][:(self.min_symbol_count-1)]
        
    # Trade execution
    invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long:
            self.Liquidate(symbol)
    length = len(long)
    for symbol in long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, 1 / length)
class SymbolData():
def __init__(self, period):
    self.Price = RollingWindow[float](period)
        
def update(self, value):
    self.Price.Add(value)
        
def is_ready(self):
    return self.Price.IsReady

def performance(self):
    prices = [x for x in self.Price]
    return prices[0] / prices[-1] - 1
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
    
# Quantpedia Sectors
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaSectorCAPE(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/economic/sector_cape/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaSectorCAPE()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    # Own formatting based on CSV file structure
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    if split[1] != '' and split[2] != '':
        data['Shiller'] = float(split[1])
        data['Regular'] = float(split[2])
        data.Value = float(split[1])
    else:
        return None
        
    return data
