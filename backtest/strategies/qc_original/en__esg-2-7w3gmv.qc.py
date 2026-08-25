# Original QuantConnect / library Python
# locale=en slug="esg-水平因子投资策略-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
from numpy import floor
#endregion

class ESGFactorInvestingStrategy(XXX):

def Initialize(self):
    self.SetStartDate(2009, 6, 1)
    self.SetCash(100000)

    # Decile weighting.
    # True - Value weighted
    # False - Equally weighted
    self.value_weighting = True
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.esg_data = self.AddData(ESGData, 'ESG', Resolution.Daily)
    
    # All tickers from ESG database.
    self.tickers = []
    
    self.ticker_deciles = {}
    
    self.holding_period = 12
    self.managed_queue = []
    
    self.latest_price = {}
    
    self.selection_flag = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)

def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(10)

def CoarseSelectionFunction(self, coarse):
    if not self.selection_flag:
        return Universe.Unchanged
    
    self.latest_price.clear()
    
    selected = [x for x in coarse if (x.Symbol.Value).lower() in self.tickers]
    
    for stock in selected:
        symbol = stock.Symbol
        self.latest_price[symbol] = stock.AdjustedPrice

    return [x.Symbol for x in selected]

def FineSelectionFunction(self, fine):
    fine = [x for x in fine if x.MarketCap != 0]

    # Store symbol/market cap pair.
    long = [x for x in fine if (x.Symbol.Value in self.ticker_deciles) and                                                       \
                                    (self.ticker_deciles[x.Symbol.Value] is not None) and                                               \
                                    (self.ticker_deciles[x.Symbol.Value] >= 0.8)]
    
    short = [x for x in fine if (x.Symbol.Value in self.ticker_deciles) and                                                      \
                                    (self.ticker_deciles[x.Symbol.Value] is not None) and                                               \
                                    (self.ticker_deciles[x.Symbol.Value] = 1:
                        self.MarketOrder(symbol, quantity)
                        open_symbol_q.append((symbol, quantity))
                        
            # Only opened orders will be closed        
            item.symbol_q = open_symbol_q
            
        item.holding_period += 1
        
    if remove_item:
        self.managed_queue.remove(remove_item)

class RebalanceQueueItem():
def __init__(self, symbol_q):
    # symbol/quantity collections
    self.symbol_q = symbol_q  
    self.holding_period = 0
    
# ESG data.
class ESGData(PythonData):
def __init__(self):
    self.tickers = []

def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/economic/esg_deciles_data.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)

def Reader(self, config, line, date, isLiveMode):
    data = ESGData()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit():
        self.tickers = [x for x in line.split(';')][1:]
        return None
        
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    
    index = 1
    for ticker in self.tickers:
        data[ticker] = float(split[index])
        index += 1
        
    data.Value = float(split[1])
    return data
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
