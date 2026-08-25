# Original QuantConnect / library Python
# locale=en slug="interest-rate-momentum-in-global-yield-curve"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class InterestRateMomentuminGlobalYieldCurves(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = [
                    "ASX_XT1",        # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1 (Australia)
                    "MX_CGB1",        # Ten-Year Government of Canada Bond Futures, Continuous Contract #1 (Canada)
                    "EUREX_FGBL1",    # Euro-Bund (10Y) Futures, Continuous Contract #1 (Germany)
                    "LIFFE_R1",       # Long Gilt Futures, Continuous Contract #1 (U.K.)
                    "EUREX_FBTP1",    # Long-Term Euro-BTP Futures, Continuous Contract #1 (Italy)
                    "SGX_JB1",        # SGX 10-Year Mini Japanese Government Bond Futures, Continuous Contract #1 (Japan)
                    "CME_TY1"         # 10 Yr Note Futures, Continuous Contract #1 (USA)
                    ]
                
    # Daily ROC data.
    self.data = {}
    self.period = 252
    self.SetWarmUp(self.period)
    
    self.leverage = 5
    
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        self.data[symbol] = self.ROC(symbol, self.period, Resolution.Daily)
def OnData(self, data):
    #  Custom data is still coming.
    if any([self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol] for symbol in self.symbols]):
        self.liquidate()
        return
    # Momentum sorting.
    long = [x[0] for x in self.data.items() if x[1].IsReady and x[1].Current.Value > 0 and x[0] in data and data[x[0]]]
    short = [x[0] for x in self.data.items() if x[1].IsReady and x[1].Current.Value  Dict[Symbol, datetime.date]:
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
