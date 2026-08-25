# Original QuantConnect / library Python
# locale=en slug="global-cross-asset-time-series-momentum-in-bond-and-equity-markets"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
class GlobalCrossAssetTimeSeriesMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = {
        "ASX_YAP1" : "ASX_XT1",        # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1 (Australia)
        "LIFFE_FCE1" : "MX_CGB1",       # Ten-Year Government of Canada Bond Futures, Continuous Contract #1 (Canada)
        "EUREX_FSTX1" : "EUREX_FGBL1",  # Euro-Bund (10Y) Futures, Continuous Contract #1 (Germany)
        "SGX_NK1" : "SGX_JB1",          # SGX 10-Year Mini Japanese Government Bond Futures, Continuous Contract #1 (Japan)
        "LIFFE_Z1" : "LIFFE_R1",        # Long Gilt Futures, Continuous Contract #1 (U.K.)
        "CME_ES1" : "CME_TY1"           # 10 Yr Note Futures, Continuous Contract #1 (USA)
    }
    self.data = {}
    self.period = 12*21
    self.SetWarmUp(self.period)
    self.leverage_cap = 5
    
    for eq in self.symbols:
        bond = self.symbols[eq]
        
        data = self.AddData(QuantpediaFutures, eq, Resolution.Daily)
        self.data[eq] = RollingWindow[float](self.period)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage_cap)
        
        data = self.AddData(QuantpediaFutures, bond, Resolution.Daily)
        self.data[bond] = RollingWindow[float](self.period)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage_cap)
        
    first_key = [x for x in self.symbols.keys()][0]
    self.rebalance_flag: bool = False
    self.Schedule.On(self.DateRules.MonthStart(first_key), self.TimeRules.At(0, 0), self.Rebalance)
def OnData(self, data):
    for eq in self.symbols:
        bond = self.symbols[eq]
        
        if eq in data and bond in data:
            if data[eq] and data[bond]:
                eq_price = data[eq].Value
                bond_price = data[bond].Value
                if eq_price != 0 and bond_price != 0:
                    self.data[eq].Add(eq_price)
                    self.data[bond].Add(bond_price)
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    volatility = {}
    for eq in self.symbols:
        bond = self.symbols[eq]
        
        if all([self.data[x].IsReady and self.Securities[x].GetLastData() and self.Time.date()  0:
                bond_returns = bond_prices[:-1] / bond_prices[1:] - 1
                volatility[bond] = np.std(bond_returns) * np.sqrt(252)
            elif eq_return > 0 and bond_return > 0:
                eq_returns = eq_prices[:-1] / eq_prices[1:] - 1
                volatility[eq] = np.std(eq_returns) * np.sqrt(252)
    
    if len(volatility) == 0: return
    
    mean_vol = np.mean([x[1] for x in volatility.items()])
    # leverage = (0.0833 / total_vol_annualized) * 100
    leverage = min((0.1 / mean_vol), self.leverage_cap)
    
    self.Liquidate()
    count = len(volatility)
    
    for symbol in volatility:
        if data.contains_key(symbol) and data[symbol]:
        # self.SetHoldings(symbol, 0.1667 * (1/count) * leverage)
            self.SetHoldings(symbol, leverage / count)
def Rebalance(self):
    self.rebalance_flag = True
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
