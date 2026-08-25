# Original QuantConnect / library Python
# locale=en slug="instititutional-ownership-effect-during-earnings-announcements"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
from AlgorithmImports import *
import numpy as np
from pandas.tseries.offsets import BDay
class InstititutionalOwnershipEffectDuringEarningsAnnouncements(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2009, 1, 1) # earnings dates starts at 2010
    self.SetCash(100_000)
    self.period: int = 21
    self.lookup_period: int = 2
    self.holding_period: int = 2
    self.min_share_price: int = 5
    self.leverage: int = 5
    self.quantile: int = 5
    self.total_long_num: int = 15
    self.total_short_num: int = 15
    
    self.long: Set(Symbol) = set()
    self.short: Set(Symbol) = set()
    self.data: Dict[Symbol, data_tools.SymbolData] = {}
    self.earnings_data: Dict[datetime.date, list[str]] = {}
    
    self.first_date: Union[None, datetime.date] = None
    earnings_set: Set(str) = set()
    earnings_data: str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json: List[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date: datetime.date = datetime.strptime(obj['date'], "%Y-%m-%d").date()
        if not self.first_date: self.first_date = date
        self.earnings_data[date] = []
        
        for stock_data in obj['stocks']:
            ticker: str = stock_data['ticker']
            self.earnings_data[date].append(ticker)
            earnings_set.add(ticker)
    
    self.tickers: List[str] = list(earnings_set)
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    # equally weighted brackets for traded symbols. - n symbols long, m symbols short, 2 days of holding
    self.trade_manager: data_tools.TradeManager = data_tools.TradeManager(
        self, self.total_long_num, self.total_short_num, self.holding_period)
    
    self.fundamental_count: int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.selection_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        if symbol in self.data:
            self.data[symbol].update(stock.Volume)
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    selected: List[Fundamental] = [
        x for x in fundamental if x.Symbol.Value in self.tickers \
        and x.HasFundamentalData and x.MarketCap != 0 and x.Market == 'usa' and x.Price > self.min_share_price
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    warmed_up_symbols:List[Symbol] = []
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(symbol, self.period)
            history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                continue
            if not hasattr(history.loc[symbol], 'volume'):
                continue
            volumes: Series = history.loc[symbol].volume
            for _, volume in volumes.items():
                self.data[symbol].update(volume)
        if self.data[symbol].is_ready():
            warmed_up_symbols.append(symbol)
    
    if len(warmed_up_symbols)  None:
    # liquidate opened symbols after self.holding_period days.
    self.trade_manager.TryLiquidate()
    
    # long two days before earnings annoucement
    date_to_lookup_long: datetime.date = (self.Time + BDay(self.lookup_period)).date()
    # short two days after earnings annoucement
    date_to_lookup_short: datetime.date = (self.Time - BDay(self.lookup_period)).date()
    
    if date_to_lookup_long  None:
    self.selection_flag = True
