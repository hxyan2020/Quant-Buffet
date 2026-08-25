# Original QuantConnect / library Python
# locale=zh slug="政治不确定性与商品价格"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class PoliticalUncertainty(QCAlgorithm):
def Initialize(self):
    self.set_start_date(1996, 1, 1)
    self.set_cash(100_000)
    
    self.symbol: Symbol = self.add_data(QuantpediaFutures, 'CME_GI1', Resolution.DAILY).symbol
    self.securities[self.symbol].set_fee_model(CustomFeeModel())
    self.securities[self.symbol].set_leverage(2)
    
    self.schedule.on(self.date_rules.month_end(self.symbol), self.time_rules.at(0, 0), self.rebalance)
def rebalance(self) -> None:
    if self.time.date() > QuantpediaFutures.get_last_update_date()[self.symbol.value]:
        self.liquidate()
        return
    year = self.time.year
    if year % 4 == 0:   # every 4th year
        if self.time.month == 6:
            self.set_holdings(self.symbol, -1)
        elif self.time.month == 9:
            if self.portfolio.invested:
                self.liquidate()
        
# Quantpedia data
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
_last_update_date: Dict[str, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[str, datetime.date]:
   return QuantpediaFutures._last_update_date
def GetSource(self, config:SubscriptionDataConfig, date:datetime, isLiveMode:bool) -> SubscriptionDataSource:
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config:SubscriptionDataConfig, line:str, date:datetime, isLiveMode:bool) -> BaseData:
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['back_adjusted'] = float(split[1])
    data['spliced'] = float(split[2])
    data.Value = float(split[1])
    # store last update date
    if config.Symbol.Value not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol.Value]:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = data.Time.date()
    return data
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
