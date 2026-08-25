# Original QuantConnect / library Python
# locale=en slug="多重风险溢价策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
#endregion
class MultiRiskPremiaStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    # Carry Quantpedia Strategies:
    # ID 234 - Carry Factor within Asset Classes - 4 different universes
    # Momentum Quantpedia Strategies:
    # Commodities - ID 21
    # Equity Index - ID 15
    # Equity Single Stocks - ID 14
    # Bonds - ID 426
    # FX - ID 8
    # Volatility Risk Strategies:
    # Commodities - ID 506
    # Equity Single Stocks - ID 20
    # FX - ID 507
    # Value Strategies:
    # Commodities - ID 424
    # FX - ID 9
    # Equity Index - ID 26
    # Bonds - ID 6
    self.tickers:List[str] = [
        '234_commodity', '234_equity',
        '234_fx', '234_bonds',
        '21', '15',
        '14', '426',
        '8', '506',
        '20', '507',
        '424', '6',
        '9', '26',
    ]
    self.volatility_period:int = 21
    self.volatility_target:float = 0.1
    self.leverage_cap:float = 5.
    for ticker in self.tickers:
        data:Security = self.AddData(QuantpediaEquity, ticker, Resolution.Daily)
        data.SetLeverage(self.leverage_cap * 3)
        data.SetFeeModel(CustomFeeModel())
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.recent_month:int = -1

def OnData(self, data:Slice) -> None:
    if self.IsWarmingUp:
        return
    # quarterly rebalance
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    if self.Time.month % 3 != 0: return
    
    # rebalance
    _last_update_date:Dict[str, datetime.date] = QuantpediaEquity.get_last_update_date()
    tickers_to_trade:List[str] = [ticker for ticker in self.tickers if \
            ticker in _last_update_date and \
            self.Time.date()  SubscriptionDataSource:
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/equity/quantpedia_strategies/911_related/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
_last_update_date:Dict[str, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[str, datetime.date]:
   return QuantpediaEquity._last_update_date
def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLive: bool) -> BaseData:
    data:config = QuantpediaEquity()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split:List[str] = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    data['close'] = float(split[1])
    data.Value = float(split[1])
    
    # store last update date
    if config.Symbol.Value not in QuantpediaEquity._last_update_date:
        QuantpediaEquity._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaEquity._last_update_date[config.Symbol.Value]:
        QuantpediaEquity._last_update_date[config.Symbol.Value] = data.Time.date()
    
    return data
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
