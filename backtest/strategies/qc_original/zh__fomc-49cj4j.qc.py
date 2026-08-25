# Original QuantConnect / library Python
# locale=zh slug="在fomc目标利率变化之前的美元"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.tseries.offsets import BDay
from dateutil.relativedelta import relativedelta
#endregion
class TheDollarAheadOfFOMCTargetRateChanges(QCAlgorithm):
def initialize(self) -> None:
    self.set_start_date(2000, 1, 1)
    self.set_cash(100000)
    self.spread:float|None = None
    self.last_target_rate:float|None = None
    self.last_target_rate_update:datetime.date|None = None
    self.max_missing_days_target_rate:int = 5
    self.days_counter:int = 0
    self.holding_period: int = 3
    self.spread_threshold: float = 0.125
    self.leverage:int = 5
    data = self.add_data(QuantpediaFutures, 'ICE_DX1', Resolution.DAILY)
    data.set_fee_model(CustomFeeModel())
    data.set_leverage(self.leverage)
    
    self.symbol:Symbol = data.symbol
    self.fed_fund_futures:Symbol = self.add_data(NasdaqFedFuture, 'CHRIS/CME_FF3', Resolution.DAILY).symbol
    self.fed_fund_rate:Symbol = self.add_data(FedRate, 'FEDFUNDS', Resolution.DAILY).symbol
    
    csv_string_file:str = self.download('data.quantpedia.com/backtesting_data/economic/fed_days.csv')
    dates:list[str] = csv_string_file.split('\r\n')
    fed_dates:list[datetime.date] = [datetime.strptime(x, '%Y-%m-%d') for x in dates]
    self.three_days_before_fed:list[datetime.date] = [(x - BDay(3)).date() for x in fed_dates]
def on_data(self, data: Slice) -> None:
    curr_date:datetime.date = self.time.date()
    custom_data_last_update_date: Dict[Symbol, datetime.date] = LastDateHandler.get_last_update_date()
    if all((self.securities[symbol].get_last_data() and self.time.date() > custom_data_last_update_date[symbol]) for symbol in [self.symbol, self.fed_fund_rate]):
        self.liquidate()
        return
    # coming on daily basis
    if self.fed_fund_futures in data and data[self.fed_fund_futures]:
        fed_fund_futures_value = data[self.fed_fund_futures].value
        self.last_target_rate = 100 - fed_fund_futures_value
        self.last_target_rate_update = curr_date
    # coming on monthly basis
    if self.fed_fund_rate in data and data[self.fed_fund_rate]:
        self.last_fed_rate = data[self.fed_fund_rate].Value
    if self.last_target_rate_update != None and (curr_date - self.last_target_rate_update).days > self.max_missing_days_target_rate:
        self.last_target_rate = None
        self.last_target_rate_update = None
    # Three days before fed calculate expected target rate and spread
    if curr_date in self.three_days_before_fed and self.last_target_rate != None and self.last_fed_rate != None:
        self.spread = self.last_target_rate - self.last_fed_rate
    
    if self.symbol in data and data[self.symbol]:
        # Buy dollar future two days before fed. Emit insight and let it expire (liquidate) by itself.
        if self.spread:
            if self.spread >= self.spread_threshold:
                self.set_holdings(self.symbol, 1)
            elif self.spread = self.holding_period:
        self.days_counter = 0
        self.liquidate()
class NasdaqFedFuture(NasdaqDataLink):
def __init__(self) -> None:
    self.ValueColumnName = "Value"
    
class LastDateHandler():
_last_update_date:Dict[Symbol, datetime.date] = {}

@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return LastDateHandler._last_update_date
 
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['back_adjusted'] = float(split[1])
    data['spliced'] = float(split[2])
    data.Value = float(split[1])
    if config.Symbol not in LastDateHandler._last_update_date:
        LastDateHandler._last_update_date[config.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > LastDateHandler._last_update_date[config.Symbol]:
        LastDateHandler._last_update_date[config.Symbol] = data.Time.date()
    return data
# Quantpedia monthly custom data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class FedRate(PythonData):
def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
    return SubscriptionDataSource(f'data.quantpedia.com/backtesting_data/economic/{config.Symbol.Value}.csv', SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data = FedRate()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split: str = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + relativedelta(months=1)
    data.Value = float(split[1])
    if config.Symbol not in LastDateHandler._last_update_date:
        LastDateHandler._last_update_date[config.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > LastDateHandler._last_update_date[config.Symbol]:
        LastDateHandler._last_update_date[config.Symbol] = data.Time.date()
    return data
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
