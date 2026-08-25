# Original QuantConnect / library Python
# locale=en slug="overnight-intraday-weekly-reversal-in-currency-futures"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class OvernightIntradayWeeklyReversalCurrency(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = [
                    "CME_AD1", # Australian Dollar Futures, Continuous Contract #1
                    "CME_BP1", # British Pound Futures, Continuous Contract #1
                    "CME_CD1", # Canadian Dollar Futures, Continuous Contract #1
                    "CME_EC1", # Euro FX Futures, Continuous Contract #1
                    "CME_JY1", # Japanese Yen Futures, Continuous Contract #1
                    "CME_MP1", # Mexican Peso Futures, Continuous Contract #1
                    "CME_NE1", # New Zealand Dollar Futures, Continuous Contract #1
                    "CME_SF1"  # Swiss Franc Futures, Continuous Contract #1
                    ]
    
    self.friday_close = {}
    self.leverage = 1
    
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(5)
        self.friday_close[symbol] = 0
        
def OnData(self, data):
    # Saturday -> Friday close available
    if self.Time.date().weekday() == 5:
        for symbol in self.symbols:
            if symbol in data and data[symbol]:
                price = data[symbol].Value
                if price != 0:
                    self.friday_close[symbol] = price
                
        self.Liquidate()
    # Tuesday -> Monday close available
    elif self.Time.date().weekday() == 1:
        returns = {}
        
        for symbol in self.symbols:
            # Check if data is still coming.
            if self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol]:
                self.liquidate(symbol)
                continue
            if symbol in data and data[symbol]:
                price = data[symbol].Value
                if price != 0 and symbol in self.friday_close and self.friday_close[symbol] != 0:
                    returns[symbol] = price / self.friday_close[symbol] - 1
        
        self.friday_close.clear()
        if len(returns) == 0: 
            return
        
        ret_mean = np.mean([x[1] for x in returns.items()])
        
        weight = {}
        N = len(returns)
        for symbol in returns:
            weight[symbol] = -(1/N) * (returns[symbol] - ret_mean) * 100

        for symbol in weight:
            self.SetHoldings(symbol, self.leverage * weight[symbol])
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
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
    if config.Symbol.Value not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol.Value]:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = data.Time.date()
        
    return data
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
