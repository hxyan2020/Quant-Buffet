# Original QuantConnect / library Python
# locale=en slug="option-factor-momentum"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
from typing import List, Dict
#endregion

class MultiRiskPremiaStrategy(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)

    self.period:int = 12 * 21
    self.leverage:int = 3
    self.quantile:int = 5

    self.data:Dict[str, float] = {}

    self.equity_ids:List[str] = [
        '173',    # Volatility Term Structure Predicts Option Returns
        '20',     # Volatility Risk Premium Effect
        '216',    # Active Collar Strategy
        '233',    # Using Straddles to Trade on Earnings Announcements
        '237',    # Dispersion Trading
        '257',    # Cloning Hedge Fund Indexes
        '280',    # Trading the VIX Futures Roll and Volatility Premiums with VIX Options
        '329',    # Portfolio Hedging Using VIX Options
        '335',    # Cross-Sectional One-Month Equity ATM Straddle Trading Strategy
        '336',    # Cross-Sectional Six-Month Equity ATM Straddle Trading Strategy
        '337',    # Cross-Sectional Six- Minus One-Month Equity ATM Straddle Calendar Trading Strategy
        '338',    # Timing of Option Returns
        '347',    # Mispricing of Equity Options With Different Time To Maturity
        '349',    # Trading Options During Expiration Weekends
        '402',    # International Volatility Arbitrage
        '405',    # Using VIX to Time Options Writing
        '41',     # Turn of the Month in Equity Indexes
        '481',    # Holding Artificial VIX in a Portfolio
        '511',    # Cheap Options Are Expensive
        '599',    # Barbell Strategy
        '604',    # Reversal on Straddles
        '605',    # Momentum on Straddles
        '627',    # Hedging Portfolio
        '63',     # Trendfollowing Combined with Volatility Premium 
        '72',     # Combined Mean Reversion and Momentum in Foreign Exchange Markets
        '786',    # Option Trading and Returns versus the 52-Week High
        '787',    # Option Trading and Returns versus the 52-Week Low
        '855',    # Avoid Equity Bear Markets with a Market Timing Strategy
    ]

    for equity_id in self.equity_ids:
        data:Security = self.AddData(QuantpediaEquity, equity_id, Resolution.Daily)
        data.SetLeverage(self.leverage)
        data.SetFeeModel(CustomFeeModel())

        self.data[equity_id] = self.ROC(equity_id, self.period, Resolution.Daily)

    self.SetWarmUp(self.period)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

    self.recent_month:int = -1

def OnData(self, data: Slice) -> None:
    if self.IsWarmingUp:
        return
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month

    _last_update_date:Dict[str, datetime.date] = QuantpediaEquity.get_last_update_date()
    
    # calculate performance
    performance:Dict[str, float] = { x : self.data[x].Current.Value for x in self.data \
                if self.data[x].IsReady and \
                x in data and data[x] and \
                _last_update_date[x] > self.Time.date() }

    long:List[str] = []
    short:List[str] = []
    
    # performance sorting
    if len(performance) >= self.quantile:
        sorted_by_perf:List[str] = sorted(performance.items(), key = lambda x: x[1], reverse = True)
        quantile:int = int(len(sorted_by_perf) / self.quantile)
        long = [x[0] for x in sorted_by_perf[:quantile]]
        short = [x[0] for x in sorted_by_perf[-quantile:]]

    # trade execution
    invested:List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    
    for symbol in long:
        self.SetHoldings(symbol, 1 / len(long))
    for symbol in short:
        self.SetHoldings(symbol, -1 / len(short))
    
# Quantpedia strategy equity curve data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaEquity(PythonData):
def GetSource(self, config:SubscriptionDataConfig, date:datetime, isLiveMode:bool) -> SubscriptionDataSource:
    return SubscriptionDataSource(f"data.quantpedia.com/backtesting_data/equity/quantpedia_strategies/925_related/{config.Symbol.Value}.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)

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
