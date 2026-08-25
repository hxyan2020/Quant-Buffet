# Original QuantConnect / library Python
# locale=en slug="macd-v：波动性标准化动量"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion

class MACDVVolatilityNormalizedMomentum(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.short_period:int = 12
    self.long_period:int = 26
    self.short_hold_period:int = 15
    self.long_hold_period:int = 77
    
    self.target_limit:float = 1.0285
    self.macd_entry_threshold:int = 70

    self.price_at_trade:float = 0.
    self.holding_counter:int = 0

    future = self.AddData(QuantpediaFutures, 'EUREX_FDAX1', Resolution.Daily)
    future.SetFeeModel(CustomFeeModel())
    self.future = future.Symbol

    self.short_period_EMA:ExponentialMovingAverage = self.EMA(self.future, self.short_period)
    self.long_period_EMA:ExponentialMovingAverage = self.EMA(self.future, self.long_period)
    self.ATR:AverageTrueRange = self.ATR(self.future, self.long_period)

    self.SetWarmup(self.long_period, Resolution.Daily)

def OnData(self, data: Slice) -> None:
    if self.IsWarmingUp:
        return

    future_last_update_data:datetime.date = QuantpediaFutures._last_update_date

    # check if data is still coming
    if self.Securities[self.future].GetLastData() and self.Time.date() >= future_last_update_data:
        self.Liquidate()
        return

    if self.future in data and data[self.future]:
        if self.Portfolio.Invested:
            self.holding_counter += 1
            if (data[self.future].Value > (self.price_at_trade * self.target_limit)) and (self.holding_counter == 1):
                self.Liquidate()
            
            elif (data[self.future].Value > self.price_at_trade) and (self.holding_counter == self.short_hold_period):
                self.Liquidate()

            elif self.holding_counter == self.long_hold_period:
                self.Liquidate()

        if all(x.IsReady for x in [self.short_period_EMA, self.long_period_EMA, self.ATR]):
            MACD_V:float = ((self.short_period_EMA.Current.Value - self.long_period_EMA.Current.Value) / self.ATR.Current.Value) * 100

            if MACD_V > self.macd_entry_threshold and (not self.Portfolio.Invested):
                # buy future
                self.SetHoldings(self.future, 1)
                self.price_at_trade = data[self.future].Value
                self.holding_counter = 0

# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
_last_update_date:datetime.date = datetime(1,1,1).date()

@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
    return QuantpediaFutures._last_update_date

def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/EUREX_FDAX1.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)

def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['back_adjusted'] = float(split[1])
    data['spliced'] = float(split[2])
    data.Value = float(split[1])

    if data.Time.date() > QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date = data.Time.date()

    return data

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
