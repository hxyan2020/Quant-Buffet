# Original QuantConnect / library Python
# locale=zh slug="中国石油波动性影响行业动量效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
#endregion
class OilVolatilityAffectsIndustryMomentumInChina(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2014, 1, 1) # China indexes starts since 2012
    self.SetCash(100000)
    
    self.tickers = [
        'SZAI', 'SZBSI',
        'SZC50', 'SZCCIP',
        'SZCDSI', 'SZCI',
        'SZCOI', 'SZCPI',
        'SZCSI', 'SZCSSI',
        'SZD50', 'SZDII',
        'SZEMI', 'SZEPI',
        'SZESI', 'SZEXT50',
        'SZFSI', 'SZHC50',
        'SZHCI', 'SZHCSI',
        'SZIBIP', 'SZICI',
        'SZIFI', 'SZISI',
        'SZITI', 'SZMAI',
        'SZMEI', 'SZMII',
        'SZMNI', 'SZMSI',
        'SZPI', 'SZRDI',
        'SZREI', 'SZSRIP',
        'SZTRI', 'SZTSI',
        'SZTSSI', 'SZUII',
        'SZUSI', 'SZWHI'
    ]
    
    self.data = {}
    self.symbols = []
    
    self.period = 12 * 21       # 12 months of daily closes
    self.oil_period = 36 * 21   # 3 years of daily closes
    self.SetWarmUp(2*self.oil_period)
    
    self.months_skip = 1        # Calculating performance of period from month t-12 to month t-2.
    
    for ticker in self.tickers:
        security = self.AddData(QuantpediaIndexChina, ticker, Resolution.Daily)
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(5)
        
        symbol = security.Symbol
        self.symbols.append(symbol)
        self.data[symbol] = SymbolData(self.period)
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.oil_symbol = self.AddData(QuantpediaFutures, 'CME_CL1', Resolution.Daily).Symbol
    self.data[self.oil_symbol] = SymbolData(self.oil_period)
    
    self.max_missing_days:int = 5
    self.selection_flag = False
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
def OnData(self, data):
    for symbol in self.symbols + [self.oil_symbol]:
        if symbol in data:
            if data[symbol]:
                self.data[symbol].update(data[symbol].Value)
    
    if self.IsWarmingUp: return

    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # oil data is still comming in
    if self.Securities[self.oil_symbol].GetLastData() and (self.Time.date() - self.Securities[self.oil_symbol].GetLastData().Time.date()).days > self.max_missing_days:
        self.Liquidate()
        return
    if self.data[self.oil_symbol].is_ready():
        short_term_volatility = self.data[self.oil_symbol].volatility(self.period)
        long_term_volatility = self.data[self.oil_symbol].volatility(self.oil_period)
    
        performances = {}
        
        for symbol in self.symbols:
            # futures data is still comming in
            if self.Securities[symbol].GetLastData() and (self.Time.date() - self.Securities[symbol].GetLastData().Time.date()).days = performances_median]
        losers = [x[0] for x in performances.items() if performances[x[0]]  long_term_volatility: # High volatility
            long = losers
            short = winners
        else: # Small volatility
            long = winners
            short = losers
            
        # Trade Execution
        stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
        for symbol in stocks_invested:
            if symbol not in long + short:
                self.Liquidate(symbol)
        
        long_length = len(long)
        short_length = len(short)
        
        for symbol in long:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, 1 / long_length)
                
        for symbol in short:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, -1 / short_length)
    
def Selection(self):
    self.selection_flag = True
class SymbolData():
def __init__(self, period):
    self.closes = RollingWindow[float](period)
    
def update(self, close):
    self.closes.Add(close)
    
def is_ready(self):
    return self.closes.IsReady
    
def performance(self, months_skip):
    closes = [x for x in self.closes]
    closes = closes[months_skip * 21:] # 21 are total closes in one month
    return (closes[0] - closes[-1]) / closes[-1]
    
def volatility(self, period):
    closes = [x for x in self.closes]
    monthly_closes = np.array(closes[:period])
    monthly_returns = (monthly_closes[:-1] - monthly_closes[1:]) / monthly_closes[1:]
    vol = np.std(monthly_returns)
    return vol
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
    
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['back_adjusted'] = float(split[1])
    data['spliced'] = float(split[2])
    data.Value = float(split[1])
    return data
    
# Quantpedia data
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaIndexChina(PythonData):
def GetSource(self, config, date, isLiveMode):
    source = "data.quantpedia.com/backtesting_data/index/china/{0}.csv".format(config.Symbol.Value)
    return SubscriptionDataSource(source, SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaIndexChina()
    data.Symbol = config.Symbol
    
    try:
        if not line[0].isdigit(): return None
        split = line.split(',')
        
        data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
        data['Price'] = float(split[1])
        data.Value = float(split[1])
    except:
        return None
        
    return data
