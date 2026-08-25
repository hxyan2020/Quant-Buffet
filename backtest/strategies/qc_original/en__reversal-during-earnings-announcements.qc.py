# Original QuantConnect / library Python
# locale=en slug="reversal-during-earnings-announcements"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
from AlgoLib import *
import numpy as np
from typing import Dict, List
from collections import deque

class ReversalDuringEarningsAnnouncements(XXX):

def Initialize(self):
    self.SetStartDate(2010, 1, 1) # earnings dates start in 2010
    self.SetCash(100000)

    self.long_count:int = 20
    self.short_count:int = 20
    self.holding_period:int = 3

    self.leverage:int = 5
    self.ear_period:int = 4
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # Daily price data.
    self.data:Dict[Symbol, RollingWindow] = {}
    
    # Import earnigns data.
    self.earnings_data:Dict[datetime, List[str]] = {}
    
    # Available symbols from earning_dates dataset.
    self.tickers:Set(str) = set()
    
    self.first_date:Union[None, datetime.date] = None

    earnings_data:str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json:list[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date:datetime.date = datetime.strptime(obj['date'], "%Y-%m-%d").date()
        self.earnings_data[date] = []
        
        if not self.first_date: self.first_date = date

        for stock_data in obj['stocks']:
            ticker:str = stock_data['ticker']

            self.earnings_data[date].append(ticker)
            self.tickers.add(ticker)

    # EAR history for previous quarter used for statistics. 
    self.ear_previous_quarter:List[float] = []
    self.ear_actual_quarter:List[float] = []

    # 5 equally weighted brackets for traded symbols. - 20 symbols long , 20 for short, 3 days of holding.
    self.trade_manager = data_tools.TradeManager(self, self.long_count, self.short_count, self.holding_period)
    
    self.month:int = 0
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 1000
    self.selection_flag = False
    self.rebalance_flag = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update daily prices
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)
    
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False

    selected:List[Symbol] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Symbol.Value in self.tickers]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            continue
        
        self.data[symbol] = RollingWindow[float](self.ear_period)
        history:DataFrame = self.History(symbol, self.ear_period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet")
            continue
        
        closes:Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].Add(close)
    
    return list(map(lambda x: x.Symbol, selected))

def OnData(self, data: Slice) -> None:
    date_to_lookup = (self.Time + timedelta(days=1)).date()
    
    # Liquidate opened symbols after three days.
    self.trade_manager.TryLiquidate()
    
    ret_t4_t2 = {}
    
    for symbol in self.data:
        # Data is ready.
        if self.data[symbol].IsReady:
            # Earnings is in next two day for the symbol.
            if date_to_lookup in self.earnings_data and symbol.Value in self.earnings_data[date_to_lookup]:
                closes = [x for x in self.data[symbol]]
                if closes[-1] != 0:
                    # Calculate t-4 to t-2 return.
                    ret = (closes[0] - closes[-1]) / closes[-1]
                    ret_t4_t2[symbol] = ret
                    
                    # Store return in this month's history.
                    self.ear_actual_quarter.append(ret)
        
    # Wait until we have history data for previous three months.
    if len(self.ear_previous_quarter) != 0:
        # Sort by EAR.
        ear_values = self.ear_previous_quarter
        top_ear_quintile = np.percentile(ear_values, 80)
        bottom_ear_quintile = np.percentile(ear_values, 20)
        
        # Store symbol to set.
        long = [x[0] for x in ret_t4_t2.items() if x[1] = top_ear_quintile and x[0] in data and data[x[0]]]
        
        # Open new trades.
        for symbol in long:
            self.trade_manager.Add(symbol, True)
        for symbol in short:
            self.trade_manager.Add(symbol, False)

def Selection(self) -> None:
    # There is no earnings data yet.
    if self.Time.date()
