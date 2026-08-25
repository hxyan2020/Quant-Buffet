# Original QuantConnect / library Python
# locale=en slug="fx-value-v2-real-exchange-rate-changes"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Dict
class FXValuev2RealExchangeRateChanges(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data:Dict[str, RollingWindow[float]] = {}
    
    self.leverage:int = 3
    self.period:int = 12 * 5            # five years of monthly values
    self.selected_currencies:int = 3    # select these many of forex futures for long and short each rebalance
    
    # currency future symbol and PPP yearly symbol
    self.symbols:Dict[str, str] = {
        "CME_AD1" : "AUS_PPP", # Australian Dollar Futures, Continuous Contract #1
        "CME_BP1" : "GBR_PPP", # British Pound Futures, Continuous Contract #1
        "CME_CD1" : "CAN_PPP", # Canadian Dollar Futures, Continuous Contract #1
        "CME_EC1" : "DEU_PPP", # Euro FX Futures, Continuous Contract #1
        "CME_JY1" : "JPN_PPP", # Japanese Yen Futures, Continuous Contract #1
        "CME_NE1" : "NZL_PPP", # New Zealand Dollar Futures, Continuous Contract #1
        "CME_SF1" : "CHE_PPP"  # Swiss Franc Futures, Continuous Contract #1
    }
    
    self.last_ppp:Dict[str, Union[None, str]] = {
        "AUS_PPP" : None,
        "GBR_PPP" : None,
        "CAN_PPP" : None,
        "DEU_PPP" : None,
        "JPN_PPP" : None,
        "NZL_PPP" : None,
        "CHE_PPP" : None,
        "USA_PPP" : None
    }
    
    for symbol, ppp_symbol in self.symbols.items():
        data = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        # PPP data
        self.AddData(data_tools.PPPData, ppp_symbol, Resolution.Daily)
        self.data[symbol] = RollingWindow[float](self.period)
        
    self.AddData(data_tools.PPPData, 'USA_PPP', Resolution.Daily).Symbol
    
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.selection_flag:bool = False
    self.Schedule.On(self.DateRules.MonthStart('CME_AD1'), self.TimeRules.At(0, 0), self.Selection)
def OnData(self, data):
    ppp_last_update_date:Dict[str, datetime.date] = data_tools.PPPData.get_last_update_date()
    future_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()
    # store PPP values, when they are available
    for ppp_symbol, _ in self.last_ppp.items():
        if ppp_symbol in data and data[ppp_symbol]:
            # only last PPP for each country is stored
            self.last_ppp[ppp_symbol] = data[ppp_symbol].Value
    
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    symbols_to_delete:List[str] = []
    # store monthly data
    for symbol, ppp_symbol in self.symbols.items():
        # data is still coming
        if self.Securities[symbol].GetLastData() and self.Time.date() > future_last_update_date[symbol] \
            or self.Securities[ppp_symbol].GetLastData() and self.Time.date() > ppp_last_update_date[ppp_symbol]:
            symbols_to_delete.append(symbol)
            continue
        # check if all data are ready for calculation
        if symbol in data and data[symbol] and self.last_ppp[ppp_symbol] and self.last_ppp['USA_PPP']:
            # forex future price * (forex future PPP / USA PPP)
            self.data[symbol].Add(data[symbol].Value * (self.last_ppp[ppp_symbol] / self.last_ppp['USA_PPP']))
    
    if len(symbols_to_delete) != 0:
        [self.symbols.pop(symbol) for symbol in symbols_to_delete]
    # rebalance            
    years_return:Dict[Symbol, float] = {}
    
    for symbol, _ in self.symbols.items():
        if not self.data[symbol].IsReady:
            continue
        
        # calculate years return
        values = [x for x in self.data[symbol]]
        years_return[symbol] = (values[0] - values[-1]) / values[-1]
    
    if len(years_return) == 0:
        return
    
    # sort forex futures by years return
    sorted_by_years_return:List[Symbol] = [x[0] for x in sorted(years_return.items(), key=lambda item: item[1])]
    
    # long self.selected_currencies with the lowest past years return
    long:List[Symbol] = sorted_by_years_return[:self.selected_currencies]
    
    # short self.selected_currencies with the highest past years return
    short:List[Symbol] = sorted_by_years_return[-self.selected_currencies:]
    
    # trade execution
    invested:List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    for i, portfolio in enumerate([long, short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, ((-1) ** i) / self.selected_currencies)
def Selection(self):
    self.selection_flag = True
