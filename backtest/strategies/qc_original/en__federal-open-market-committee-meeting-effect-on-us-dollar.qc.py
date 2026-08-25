# Original QuantConnect / library Python
# locale=en slug="federal-open-market-committee-meeting-effect-on-us-dollar"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.tseries.offsets import BDay
class FederalOpenMarketCommitteeMeetingEffectUSDollar(QCAlgorithm):
def initialize(self):
    self.set_start_date(2004, 1, 1)
    self.set_cash(100_000)
    
    # fed days
    csv_string_file: str = self.download('data.quantpedia.com/backtesting_data/economic/fed_days.csv')
    dates: List[str] = csv_string_file.split('\r\n')
    dates: List[datetime.date] = [(datetime.strptime(x, "%Y-%m-%d") - BDay(1)).date() for x in dates]
    # import futures data 
    data: Security = self.add_data(QuantpediaFutures, "ICE_DX1", Resolution.DAILY)
    data.set_fee_model(CustomFeeModel())
    self.symbol: Symbol = data.symbol
    self.close_next_day: bool = False
    self.schedule.on(self.date_rules.on(dates), self.time_rules.at(0, 0), self.day_before_fed)
    self.schedule.on(self.date_rules.every_day(self.symbol), self.time_rules.at(0, 0), self.rebalance)

def day_before_fed(self) -> None:
    if self.time.date() >= QuantpediaFutures.get_last_update_date()[self.symbol.value]:
        return
    if not self.portfolio[self.symbol].is_short:
        self.set_holdings(self.symbol, -1)
        
def rebalance(self) -> None:
    if self.close_next_day:
        self.liquidate(self.symbol)
        self.close_next_day = False
    if self.portfolio[self.symbol].is_short:
        self.close_next_day = True
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
    
# Quantpedia data.
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
