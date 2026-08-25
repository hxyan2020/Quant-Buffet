# Original QuantConnect / library Python
# locale=zh slug="行业轮动通过信用相对价值"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from scipy import stats
from typing import List, Dict
import data_tools
class SectorRotationViaCreditRelativeValue(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols: List[str] = [
        "XLK",  # Technology Select Sector SPDR Fund
        "XLE",  # Energy Select Sector SPDR Fund
        "XLV",  # Health Care Select Sector SPDR Fund
        "XLF",  # Financial Select Sector SPDR Fund
        "XLI",  # Industrials Select Sector SPDR Fund
        "XLB",  # Materials Select Sector SPDR Fund
        "XLY",  # Consumer Discretionary Select Sector SPDR Fund
        "XLP",  # Consumer Staples Select Sector SPDR Fund
        "XLU"   # Utilities Select Sector SPDR Fund
    ]
    
    self.regression_period: int = 26 * 5 # Need 26 weeks data
    self.leverage: int = 5
    self.segment: int = 6
    self.regression_data: Dict[str, data_tools.SymbolData] = {}
    
    for symbol in self.symbols:
        self.AddEquity(symbol, Resolution.Daily)
        self.regression_data[symbol] = data_tools.SymbolData(self.regression_period)
    
    self.rf_asset: Symbol = self.AddEquity('BIL', Resolution.Daily).Symbol
    self.symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.HYB: Symbol = self.AddData(data_tools.QuantpediaDailyData, 'BAMLH0A2HYBEY', Resolution.Daily).Symbol
    self.regression_data[self.HYB.Value] = data_tools.SymbolData(self.regression_period)
    
    self.selection_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Schedule.On(self.DateRules.WeekStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
    
def OnData(self, data: Slice) -> None:
    custom_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.LastDateHandler.get_last_update_date()
    ETF_market: Dict[str, float] = {}
    
    # check if data is still coming
    if self.Securities[self.HYB].GetLastData() and self.Time.date() > custom_data_last_update_date[self.HYB]:
        self.Liquidate()
        return
    # Each day storing data about symbols in self.symbols and HYB index
    for symbol in self.symbols: 
        if symbol in data and data[symbol]:
            price: float = data[symbol].Value
            if price != 0:
                ETF_market[symbol] = price
                self.regression_data[symbol].update(price)
    
    if self.HYB in data and data[self.HYB]:
        ETF_market[self.HYB.Value] = data[self.HYB].Value
        self.regression_data[self.HYB.Value].update(data[self.HYB].Value)
    # Rebalance weekly 
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    ETF_disconnect: Dict[str, float] = {}
    # If HYB data aren't ready, we can't calculate any regression
    if self.regression_data[self.HYB.Value].is_ready():
        X: list[float] = [x for x in self.regression_data[self.HYB.Value].RegressionData][::-1]
        
        for symbol in self.symbols:
            if self.regression_data[symbol].is_ready():
                if symbol in ETF_market and self.HYB.Value in ETF_market:
                    Y: float = [x for x in self.regression_data[symbol].RegressionData][::-1]
                    slope, intercept, r_value, p_value, std_err = stats.linregress(X, Y)
                    ETF_fair: float = slope * ETF_market[self.HYB.Value] + intercept
                    ETF_disconnect[symbol] = (ETF_fair - ETF_market[symbol]) / ETF_market[symbol]
    
    long: List[str] = []
    negative_disconnect: List[str] = []
    rf_weight: float = .0
    if len(ETF_disconnect) != 0:
        # Sorted descending
        sorted_by_disconnect: Dict[str, float] = {k: v for k, v in sorted(ETF_disconnect.items(), key=lambda item: item[1], reverse=True)}
        for symbol, disc in sorted_by_disconnect.items():
            if disc > 0:
                long.append(symbol)
            else:
                negative_disconnect.append(symbol)
        
        long = long[:self.segment]
            
        total_count: int = len(long) + len(negative_disconnect)
        long_weight: float = len(long) / total_count
        rf_weight = len(negative_disconnect) / total_count
            
    # Trade execution.
    invested: List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long:
            self.Liquidate(symbol)
        
    for symbol in long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, long_weight / len(long))
        
    if rf_weight != 0:
        if self.rf_asset in data and data[self.rf_asset]:
            self.SetHoldings(self.rf_asset.Value, rf_weight)
    
def Selection(self) -> None:
    self.selection_flag = True
