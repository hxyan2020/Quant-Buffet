# Original QuantConnect / library Python
# locale=en slug="using-baltic-dry-index-to-trade-tanker-shipping-companies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class UsingBalticDryIndexTankerShippingCompanies(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2013, 1, 1)
    self.SetCash(100000)
    
    data = self.AddData(QuantpediaEquity, 'BADI', Resolution.Daily)
    data.SetFeeModel(CustomFeeModel())
    self.symbol = data.Symbol
    
    self.period = 6*5
    self.SetWarmUp(self.period)
    
    self.sma_6 = self.SMA(self.symbol, self.period, Resolution.Daily)
    self.sma_1 = self.SMA(self.symbol, 5, Resolution.Daily)
    
def OnData(self, data):
    if self.IsWarmingUp: return
    
    if self.sma_6.IsReady and self.sma_1.IsReady:
        if self.sma_1.Current.Value > self.sma_6.Current.Value:
            if not self.Portfolio[self.symbol].IsLong:
                self.SetHoldings(self.symbol, 1)
        else:
            if not self.Portfolio[self.symbol].IsShort:
                self.SetHoldings(self.symbol, -1)
                
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaEquity(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/index/BADI.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaEquity()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%m/%d/%Y")
    data['settle'] = float(split[1])
    data.Value = float(split[1])
    return data
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
