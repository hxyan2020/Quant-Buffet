# Original QuantConnect / library Python
# locale=en slug="halloween-effect-during-low-and-high-cape-months"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
class HalloweenEffectCAPEMonths(QCAlgorithm):
def initialize(self) -> None:
    self.set_start_date(2000, 1, 1)
    self.set_cash(100_000)
    self._period: int = 36
    self._traded_symbol: Symbol = self.add_equity('SPY', Resolution.Daily).symbol
    
    self.cape: Symbol = self.add_data(QuantpediaMonthlyData, 'SHILLER_PE_RATIO_MONTH').symbol
    self.cape_data: RollingWindow = RollingWindow[float](self._period)
    
    self._rebalance_flag: bool = False
    self._close_month: int = 0
    self._trading_month: int = 11
    
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.settings.daily_precise_end_time = False
    self.schedule.on(
        self.date_rules.month_start(self._traded_symbol), 
        self.time_rules.after_market_open(self._traded_symbol), 
        self._rebalance
    )
def on_data(self, slice: Slice) -> None:
    custom_data_last_update_date: Dict[Symbol, datetime.date] = LastDateHandler.get_last_update_date()
    if self.securities[self.cape].get_last_data() and self.time.date() > custom_data_last_update_date[self.cape]:
        self.liquidate()
        return
    
    if self.cape in slice and slice[self.cape]:
        cape: float = slice[self.cape].value
        self.cape_data.add(cape)
        
    if slice.contains_key(self._traded_symbol) and slice[self._traded_symbol]:
        if not self.cape_data.is_ready: return
        
        if self.time.month == self._close_month:
            self.liquidate(self._traded_symbol)
        
        if self.time.month == self._trading_month:
            if self._rebalance_flag:
                self.set_holdings(self._traded_symbol, 1)
                self._rebalance_flag = False
def _rebalance(self) -> None:
    self._rebalance_flag = True
    # Trade in October in order to have September CAPE data.
    if self.time.month != 10: return

    cape_values: List[float] = list(self.cape_data)
    cape_median: float = median(cape_values)
    cape: float = self.cape_data[0]
    
    if cape  Dict[Symbol, datetime.date]:
   return LastDateHandler._last_update_date
# Quantpedia monthly custom data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaMonthlyData(PythonData):
def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
    return SubscriptionDataSource(f'data.quantpedia.com/backtesting_data/economic/{config.Symbol.Value}.csv', SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data = QuantpediaMonthlyData()
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
