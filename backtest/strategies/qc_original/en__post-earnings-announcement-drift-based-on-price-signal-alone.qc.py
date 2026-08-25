# Original QuantConnect / library Python
# locale=en slug="post-earnings-announcement-drift-based-on-price-signal-alone"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from data_tools import CustomFeeModel, TradeManager, SymbolData
from AlgorithmImports import *
import numpy as np
from collections import deque
from typing import Dict, List, Set
from pandas.tseries.offsets import BDay
class PostEarningsAnnouncementDrift(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1) # earnings data start in 2010
    self.SetCash(100000)
    self.period:int = 61
    self.leverage:int = 5
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.long_count:int = 5
    self.short_count:int = 5
    self.holding_period:int = 40
    
    # monthly selected universe
    self.last_selection:List[Symbol] = []
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.tickers:Set(str) = set()
    # EPS quarterly data
    self.eps:Dict[Symbol, deque] = {}
    self.earnings_data:Dict[datetime.date, List[str]] = {} 
    earnings_data:str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json:list[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date:datetime.date = datetime.strptime(obj['date'], '%Y-%m-%d').date()
        year:int = date.year
        month:int = date.month
        self.earnings_data[date] = []
        for stock_data in obj['stocks']:
            ticker:str = stock_data['ticker']
            self.earnings_data[date].append(ticker)
            self.tickers.add(ticker)
    
    # equally weighted brackets for traded symbols
    self.trade_manager:TradeManager = TradeManager(self, self.long_count, self.short_count, self.holding_period)
    
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 500
    self.last_month:int = -1
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
    
    for security in changes.RemovedSecurities:
        if security.Symbol in self.data:
            if security.Symbol != self.market:
                del self.data[security.Symbol]
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if self.Time.month != self.last_month:
        self.last_month = self.Time.month
    
        # in fundamental always select whole universe (stocks, which are in QP earnings data),
        # because prices of each stock in this universe are updated in OnData (due to open price)
        selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Symbol.Value in self.tickers]
        if len(selected) > self.fundamental_count:
            selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        self.last_selection = [x.Symbol for x in selected]
    # warm up prices
    for symbol in self.last_selection + [self.market]:
        if symbol in self.data:
            continue
        
        self.data[symbol] = SymbolData(self.period)
        history:DataFrame = self.History(symbol, self.period+1, Resolution.Daily)
        if history.empty:
            continue
        
        closes:Series = history.close
        opens:Series = history.open
        
        for (_, open_price), (_, close) in zip(opens.items(), closes.items()):
            self.data[symbol].update(close, open_price)
    
    # market prices has to be ready
    if self.market not in self.data or not self.data[self.market].is_ready(): 
        return self.last_selection
    prev_business_day:datetime.date = (self.Time - BDay(1)).date()
    if prev_business_day not in self.earnings_data:
        return self.last_selection
    # filter stocks, which had earnings on prev business day
    prev_bussiness_day_earnings:List[str] = self.earnings_data[prev_business_day]
    selected_fundamental:List[Symbol] = [x for x in self.last_selection if x.Value in prev_bussiness_day_earnings]
    
    market_intraday_returns:List[float] = [x if x != 0.0 else 1.0 for x in self.data[self.market].get_intraday_returns()]
    
    for symbol in selected_fundamental:
        # symbol:Symbol = stock.Symbol
        if not self.data[symbol].is_ready():
            continue
        stock_intraday_returns:List[float] = self.data[symbol].get_intraday_returns()
        daily_moves:List[float] = [(stock_intrady_ret / market_intraday_ret) for stock_intrady_ret, market_intraday_ret \
            in zip(stock_intraday_returns, market_intraday_returns)]
            
        std:float = np.std(daily_moves)
        mean:float = np.mean(daily_moves)
    
        if daily_moves[0] > mean + 5 * std:
            self.long.append(symbol)
        elif daily_moves[0]  None:
    # update stock data for current universe
    for symbol in self.last_selection + [self.market]:
        if symbol in self.data and symbol in data and data[symbol]:
            close:float = data[symbol].Close
            open:float = data[symbol].Open
            self.data[symbol].update(close, open)
    
    self.trade_manager.TryLiquidate()
    # open new trades
    for symbol in self.long:
        if symbol in data and data[symbol]:
            self.trade_manager.Add(symbol, True)
    for symbol in self.short:
        if symbol in data and data[symbol]:
            self.trade_manager.Add(symbol, False)
    self.long.clear()
    self.short.clear()
