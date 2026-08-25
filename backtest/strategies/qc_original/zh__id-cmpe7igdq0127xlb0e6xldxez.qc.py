# Original QuantConnect / library Python
# locale=zh slug="股息公告效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import trade_manager
from AlgorithmImports import *
from typing import Dict, List
import data_tools
class DividendAnnouncementEffect(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.universe_assets:List[Symbol] = []
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 500
    self.leverage:int = 10
    
    self.data:Dict[Symbol, data_tools.SymbolData] = {}
    
    # self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    spy_data = self.AddData(data_tools.QuantpediaFutures, 'CME_ES1', Resolution.Daily)
    spy_data.SetLeverage(self.leverage)
    self.symbol:Symbol = spy_data.Symbol
    
    self.period:int = 12
    self.holding_period:int = 12 * 30
    self.long_count:int = 40
    self.short_count:int = 0
    
    # 40 symbols long, one year of holding.
    self.trade_manager:TradeManager = trade_manager.TradeManager(self, self.long_count, self.short_count, self.holding_period)
    
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.At(0, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
    
    for security in changes.RemovedSecurities:
        symbol:Symbol = security.Symbol
        if symbol in self.data:
            del self.data[symbol]
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    self.universe_assets = [x.Symbol for x in selected]
    for symbol in self.universe_assets:
        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(self.period)
    
    return self.universe_assets
def OnData(self, data: Slice):
    if self.Securities[self.symbol].GetLastData() and self.Time.date() >= data_tools.QuantpediaFutures.get_last_update_date()[self.symbol]:
        self.Liquidate()
        return
    # Liquidate opened symbols after one year.
    self.trade_manager.TryLiquidate()
    
    # Update dividends data
    for kvp in data.Dividends:
        div_ticker:str = kvp.Key
        if div_ticker in self.data:
            # Storing dividends data
            month_year:str = self.Time.strftime("%m-%Y")
            self.data[div_ticker].update_dividends(month_year)
    
    # If only SPY is invested, we liquidate it        
    if self.Portfolio.Count == 1 and self.Portfolio[self.symbol].Invested is True:
        self.Liquidate(self.symbol)
    
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Check stocks for trades
    for symbol in self.universe_assets:
        if symbol in self.data:
            if symbol in data and data[symbol]:
                if self.data[symbol].is_included_long_enough():
                    current_date:datetime.date = self.Time.date()
                    
                    # Trade execution
                    if self.data[symbol].check_dividends_paying(current_date) and self.Securities[symbol].Invested is False:
                        # We short SPY if we invest into at least one stock from universe.
                        if not self.Portfolio[self.symbol].Invested:
                            self.SetHoldings(self.symbol, -1)
                        
                        self.trade_manager.Add(symbol, True)
                    
                self.data[symbol].increment_inclusion_period()
            
def Selection(self) -> None:
    self.selection_flag = True
