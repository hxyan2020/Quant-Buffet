# Original QuantConnect / library Python
# locale=en slug="seasonality-in-treasury-auctions-strategy"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.tseries.offsets import BDay
from typing import List
from datetime import datetime
#endregion
class SeasonalityTreasuryAuctions(QCAlgorithm):
def initialize(self):
    self.set_start_date(2000, 1, 1)
    self.set_cash(100000)
    
    data: Security = self.add_data(QuantpediaFutures, 'CME_TY1', Resolution.DAILY)
    data.set_fee_model(CustomFeeModel())
    self.symbol: Symbol = data.symbol
    # Auction days are estimated to happen either on Thrusday after second Wednesday of the month
    # Secondary Source: https://home.treasury.gov/
    csv_string_file: str = self.download('data.quantpedia.com/backtesting_data/calendar/treasury_auction_dates.csv')
    dates: List[str] = csv_string_file.split('\r\n')
    self.auction_days: List[datetime.date] = [(datetime.strptime(x, "%Y-%m-%d") + BDay(1)).date() for x in dates]     # treasury auction date closes
    
    self.holding_days: int = 0
    self.days_to_hold: int = 2

def on_data(self, data: Slice) -> None:
    if self.time.date() >= QuantpediaFutures.get_last_update_date()[self.symbol.value]:
        self.liquidate()
        return
    # auction day close
    if self.time.date() in self.auction_days:
        self.set_holdings(self.symbol, 1)
        return
    
    # liquidate
    if self.portfolio.invested:
        self.holding_days += 1
        if self.holding_days == self.days_to_hold:
            self.holding_days = 0
            self.liquidate(self.symbol)
    
# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
    
# quantpedia data
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
