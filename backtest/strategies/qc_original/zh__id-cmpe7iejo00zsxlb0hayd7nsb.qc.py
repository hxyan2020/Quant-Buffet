# Original QuantConnect / library Python
# locale=zh slug="美国假日效应在欧盟市场的应用"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class USHolidayEUMarkets(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2012, 1, 1)
    self.SetCash(100000)           
    
    data = self.AddData(QuantpediaFutures, "EUREX_FDAX1", Resolution.Daily)
    data.SetFeeModel(CustomFeeModel())
    self.symbol = data.Symbol
    
def OnData(self, data):
    if self.securities[self.symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[self.symbol]:
        self.liquidate()
        return
    calendar1 = self.TradingCalendar.GetDaysByType(TradingDayType.PublicHoliday, self.Time, self.Time)
    calendar2 = self.TradingCalendar.GetDaysByType(TradingDayType.Weekend, self.Time, self.Time + timedelta(days=2))
    
    holidays = [i.Date for i in calendar1]
    weekends = [i.Date for i in calendar2]
    
    # subtract weekends in all holidays
    public_holidays = list(set(holidays) - set(weekends))
    if data.contains_key(self.symbol) and data[self.symbol]:
        if not self.Portfolio.Invested and len(public_holidays) > 0:
            self.SetHoldings(self.symbol, 1)
        if self.Portfolio.Invested and len(public_holidays) == 0:
            self.Liquidate()
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
    if config.Symbol not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol]:
        QuantpediaFutures._last_update_date[config.Symbol] = data.Time.date()
    return data
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
