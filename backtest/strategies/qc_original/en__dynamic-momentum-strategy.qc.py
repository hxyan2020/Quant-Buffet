# Original QuantConnect / library Python
# locale=en slug="dynamic-momentum-strategy"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class DynamicMomentumStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.slow_period = 12*21
    self.fast_period = 21
    
    # subscribe 
    data = self.AddData(QuantpediaFutures, 'CME_ES1', Resolution.Daily)     # E-mini S&P 500 Futures, Continuous Contract #1
    data.SetFeeModel(CustomFeeModel())
    data.SetLeverage(5)
    self.market = data.Symbol
    
    # daily price data
    self.price_data = RollingWindow[float](self.slow_period)
    self.recent_month:int = -1
def OnData(self, data):
    # check if data is still coming.
    if self.securities[self.market].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[self.market]:
        self.liquidate()
        return
    # store daily market price
    if self.market in data and data[self.market]:
        self.price_data.Add(data[self.market].Value)
        if self.recent_month != self.Time.month:
            self.recent_month = self.Time.month
            
            if self.price_data.IsReady:
                slow_momentum = self.price_data[0] / self.price_data[self.price_data.Count-1] - 1
                fast_momentum = self.price_data[0] / self.price_data[21] - 1
                
                slow_signal = 1 if slow_momentum >= 0 else -1
                fast_signal = 1 if fast_momentum >= 0 else -1
                
                # market cycles
                # A month ending at date t is classified as Bull if both the trailing 12-month return (arithmetic average monthly return), rt−12,t, is nonnegative and
                # the trailing 1-month return, rt−1,t, is nonnegative. A month is classified as Correction if rt−12,t ≥ 0 but rt−1,t  Dict[Symbol, datetime.date]:
   return QuantpediaFutures._last_update_date
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
    if config.Symbol not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol]:
        QuantpediaFutures._last_update_date[config.Symbol] = data.Time.date()
    return data
