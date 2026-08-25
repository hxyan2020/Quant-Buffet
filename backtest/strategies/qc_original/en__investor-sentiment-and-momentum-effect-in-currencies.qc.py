# Original QuantConnect / library Python
# locale=en slug="investor-sentiment-and-momentum-effect-in-currencies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from dateutil.relativedelta import relativedelta
#endregion
class InvestorSentiment(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2011, 1, 1)
    self.SetCash(100000)
    self.period:int = 21
    self.SetWarmUp(self.period, Resolution.Daily)
    
    self.symbols = [
        "USDAUD", "USDCAD", "USDCHF", "USDCZK", "USDDKK", "USDEUR",
        "USDGBP", "USDHKD", "USDHUF", "USDJPY", "USDMXN", "USDPLN", 
        "USDNOK", "USDSAR", "USDSGD", "USDTHB", "USDTRY", "USDTWD", 
        "USDZAR", "USDSEK"
    ] 
    
    self.data:dict[Symbol, SymbolData] = {}
    self.sentiment_warmup_period:int = 12
    self.sentiment_history = RollingWindow[float](self.sentiment_warmup_period)
    self.max_missing_days:int = 31
    self.quantile:int = 6
    
    for symbol in self.symbols:
        data = self.AddForex(symbol, Resolution.Daily, Market.Oanda)
        data.SetLeverage(5)
        
        self.data[symbol] = SymbolData(symbol, self.period)
    
    # Import custom data 
    self.sentimet_index:Symbol = self.AddData(SentimentData, "sentiment", Resolution.Daily).Symbol
    self.recent_month:int = -1

def OnData(self, data:Slice) -> None:
    perf:dict[str, float] = {}
    # store daily prices
    for symbol in self.symbols:
        if symbol in data and data[symbol]:
            self.data[symbol].Update(data[symbol].Value)
        
        if self.recent_month != self.Time.month and not self.IsWarmingUp:
            if self.data[symbol].IsReady():
                perf[symbol] = self.data[symbol].Return()
    if self.IsWarmingUp: return
    
    # monthly rebalance
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    # check sentiment index data arrival
    if self.Securities[self.sentimet_index].GetLastData() and (self.Time.date() - self.Securities[self.sentimet_index].GetLastData().Time.date()).days > self.max_missing_days:
        if self.Portfolio.Invested:
            self.Liquidate()
        self.sentiment_history.Reset()
    else:
        sentiment_index:float = self.Securities[self.sentimet_index].Price
        self.sentiment_history.Add(sentiment_index)
    
        if not self.sentiment_history.IsReady: return
        sorted_by_ret:List = sorted([x for x in self.data.items() if x[1].IsReady()], key=lambda x: x[1].Return(), reverse = True)
        if len(sorted_by_ret)  percentile_66:
            short = losers
        else:
            long = winners
            short = losers
        # liquidate
        invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
        for symbol in invested:
            if symbol not in long + short:
                self.Liquidate(symbol)
        # market execution
        for symbol in long:
            self.SetHoldings(symbol, 1 / len(long))
        for symbol in short:
            self.SetHoldings(symbol, -1 / len(short))
class SymbolData:
def __init__(self, symbol:str, lookback:int) -> None:
    self.Symbol:str = symbol
    self.History:RollingWindow = RollingWindow[float](lookback)
    self.Lookback = lookback
def Update(self, value:float) -> None:
    self.History.Add(value)
def IsReady(self) -> bool:
    return self.History.IsReady

# Monthly return
def Return(self) -> float:
    prices:List[float] = list(self.History)
    return (prices[0] / prices[self.Lookback - 1]) - 1
    
class SentimentData(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/index/baker_wurgler_sentiment_index.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    index = SentimentData()
    index.Symbol = config.Symbol
    
    try:
        data = line.split(';')
        index.Time = datetime.strptime(data[0], "%Y%m") + relativedelta(months=1)
        index.Value = data[1]
    except:
        return None
        
    return index
