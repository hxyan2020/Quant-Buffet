# Original QuantConnect / library Python
# locale=zh slug="固定收益领域的避险因素"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
class FlighttoQualityFactor(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = {
                    "EWA" : "ASX_XT1",        # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1 (Australia)
                    "EWC" : "MX_CGB1",        # Ten-Year Government of Canada Bond Futures, Continuous Contract #1 (Canada)
                    "EWG" : "EUREX_FGBL1",    # Euro-Bund (10Y) Futures, Continuous Contract #1 (Germany)
                    "EWJ" : "SGX_JB1",        # SGX 10-Year Mini Japanese Government Bond Futures, Continuous Contract #1 (Japan)
                    "EWU" : "LIFFE_R1",       # Long Gilt Futures, Continuous Contract #1 (U.K.)
                    "SPY" : "CME_TY1"         # 10 Yr Note Futures, Continuous Contract #1 (USA)
                    }
    self.data = {}
    self.period = 12 * 21
    leverage: int = 2
    self.SetWarmUp(self.period)
    for symbol in self.symbols:
        bond = self.symbols[symbol]
        
        self.AddEquity(symbol, Resolution.Daily)
        self.data[symbol] = RollingWindow[float](self.period)
        data = self.AddData(QuantpediaFutures, bond, Resolution.Daily)
        data.set_leverage(leverage)
        data.SetFeeModel(CustomFeeModel())
        
def OnData(self, data):
    for symbol, bond in self.symbols.items():
        if self.securities[bond].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[bond]:
            self.liquidate(bond)
            self.data[symbol].reset()
            continue
        if symbol in data and data[symbol]:
            price = data[symbol].Value
            self.data[symbol].Add(price)
    if self.IsWarmingUp: return

    volatility = {}
    for symbol in self.symbols:
        if self.data[symbol].IsReady:
            prices = np.array([x for x in self.data[symbol]])
            returns = prices[:-1] / prices[1:] - 1
            volatility[symbol] = np.std(returns)
    
    if len(volatility)  Dict[Symbol, datetime.date]:
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
