# Original QuantConnect / library Python
# locale=en slug="cross-sectional-momentum-in-futures"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class MomentumInFutures(QCAlgorithm):
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
        "CME_SF1", # Swiss Franc Futures, Continuous Contract #1
        "CME_ES1",      # E-mini S&P 500 Futures, Continuous Contract #1
        "EUREX_FSMI1",  # SMI Futures, Continuous Contract #1
        "EUREX_FSTX1",  # STOXX Europe 50 Index Futures, Continuous Contract #1
        "LIFFE_FCE1",   # CAC40 Index Futures, Continuous Contract #1
        "LIFFE_Z1",     # FTSE 100 Index Futures, Continuous Contract #1
        "SGX_NK1",      # SGX Nikkei 225 Index Futures, Continuous Contract #1
        
        "CME_TY1",      # 10 Yr Note Futures, Continuous Contract #1
        "CME_FV1",      # 5 Yr Note Futures, Continuous Contract #1
        "CME_TU1",      # 2 Yr Note Futures, Continuous Contract #1
        "EUREX_FGBL1",  # Euro-Bund (10Y) Futures, Continuous Contract #1
        "SGX_JB1"       # SGX 10-Year Mini Japanese Government Bond Futures
        ]
    self.period = 6 * 21
    self.count = 6
    self.SetWarmup(self.period)
    
    # Daily RoC data.
    self.data = {}
    
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(5)
        
        self.data[symbol] = self.ROC(symbol, self.period, Resolution.Daily)
    
    self.rebalance_flag: bool = False
    self.month = 1
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.At(0, 0), self.Rebalance)
def on_data(self, data: Slice) -> None:
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    self.month += 1
    if self.month > 6:
        self.month = 1
    
    if self.month != 6: return
    # Return sorting.
    long = []
    short = []
    sorted_by_return = sorted([x for x in self.data.items() if x[1].IsReady and self.Securities[x[0]].GetLastData() and self.Time.date() = self.count * 2:
        long = [x[0] for x in sorted_by_return[:self.count]]
        short = [x[0] for x in sorted_by_return[-self.count:]]
    # Trade execution.
    invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
            
    for symbol in long:
        if data.contains_key(symbol) and data[symbol]:
            self.SetHoldings(symbol, 1 / len(long))
    for symbol in short:
        if data.contains_key(symbol) and data[symbol]:
            self.SetHoldings(symbol, -1 / len(short))
def Rebalance(self):
    self.rebalance_flag = True
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
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
