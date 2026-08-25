# Original QuantConnect / library Python
# locale=en slug="隔夜效应在高波动性比特币交易日的表现"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List
from pandas.core.frame import DataFrame
# endregion
class OvernightEffectduringHighVolatilityDaysinBitcoin(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    self.volatility_period:int = 30 * 24
    self.history_period:int = 365
    self.warmup_period:int = self.history_period * 24
    self.btc:Symbol = self.AddCrypto('BTCUSD', Resolution.Hour, Market.Bitfinex).Symbol
    self.Securities[self.btc].SetFeeModel(CustomFeeModel())
    self.calculation_hour:int = 0               # calculation at 00:00
    self.traded_window:List[int] = [21, 23]     # trading from 21:00 to 23:00
    self.trade_flag:bool = False
    self.btc_volatility:RollingWindow = RollingWindow[float](self.history_period)
    self.SetWarmup(self.warmup_period, Resolution.Hour)
def OnData(self, data: Slice) -> None:
    if self.UtcTime.hour == self.calculation_hour:
        monthly_volatility:float = self.History(self.btc, self.volatility_period, Resolution.Hour).close.unstack(level=0).pct_change().std().values[0]
        self.btc_volatility.Add(monthly_volatility)
    if self.IsWarmingUp:
        return
    if not self.btc_volatility.IsReady:
        return
    if self.btc_volatility[0] > np.median(list(self.btc_volatility)[1:]):
        self.trade_flag = True
    # trade execution
    if self.UtcTime.hour == self.traded_window[0]:
        if not self.trade_flag:
            return
    
        self.trade_flag = False
        if self.btc in data and data[self.btc]:
            self.SetHoldings(self.btc, 1)
    
    if self.UtcTime.hour == self.traded_window[1] and self.Portfolio[self.btc].Invested:
        self.Liquidate()
# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
