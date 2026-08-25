# Original QuantConnect / library Python
# locale=zh slug="外汇价值-v3-实际汇率水平"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import Dict, List
from dateutil.relativedelta import relativedelta
class FXValuev3RealExchangeRateLevels(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 3
    self.selected_currencies:int = 3 # We select these many of forex futures for long and short each rebalance.
    
    # Currency future symbol and PPP yearly symbol.
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
        
        # PPP quandl data.
        self.AddData(data_tools.PPPData, ppp_symbol, Resolution.Daily)
        
    self.AddData(data_tools.PPPData, 'USA_PPP', Resolution.Daily).Symbol
    
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.WeekStart('CME_AD1'), self.TimeRules.At(0, 0), self.Selection)
def OnData(self, data: Slice) -> None:
    ppp_last_update_date:Dict[str, datetime.date] = data_tools.PPPData.get_last_update_date()
    future_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()
    # Store PPP values, when they are available.
    for ppp_symbol, _ in self.last_ppp.items():
        if ppp_symbol in data and data[ppp_symbol]:
            # Only last PPP for each country is stored.
            self.last_ppp[ppp_symbol] = data[ppp_symbol].Value
    
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    exchange_ratio:Dict[str, float] = {}
    symbols_to_delete:List[str] = []
    
    for symbol, ppp_symbol in self.symbols.items():
        # data is still coming
        if self.Securities[symbol].GetLastData() and self.Time.date() > future_last_update_date[symbol] \
            or self.Securities[ppp_symbol].GetLastData() and self.Time.date() > ppp_last_update_date[ppp_symbol] + relativedelta(months=12):
            symbols_to_delete.append(symbol)
            continue
        # Check if all data are ready for calculation
        if symbol in data and data[symbol] and self.last_ppp[ppp_symbol] and self.last_ppp['USA_PPP']:
            
            # real exchange rate = forex future price * (forex future PPP / USA PPP)
            real_exchange_rate:float = data[symbol].Value * (self.last_ppp[ppp_symbol] / self.last_ppp['USA_PPP'])
            nominal_exchange_rate:float = data[symbol].Value
                
            exchange_ratio[symbol] = nominal_exchange_rate / real_exchange_rate
    if len(symbols_to_delete) != 0:
        [self.symbols.pop(symbol) for symbol in symbols_to_delete]
    # currency with the highest (lowest) past 5-year return is considered most overvalued (undervalued)
    sorted_by_ratio:List[str] = [x[0] for x in sorted(exchange_ratio.items(), key=lambda item: item[1])]
    # Investor ranks all currencies from the most undervalued to the most overvalued and goes long top 20% (the most undervalued) currencies and
    # goes short 20% (the most overvalued) currencies.
    
    # Go long self.selected_currencies with the lowest ratio
    long:List[str] = sorted_by_ratio[:self.selected_currencies]
    
    # Go short self.selected_currencies with the highest ratio
    short:List[str] = sorted_by_ratio[-self.selected_currencies:]
    
    # Trade execution
    invested:List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
            
    for i, portfolio in enumerate([long, short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, ((-1) ** i) / self.selected_currencies) 
    
def Selection(self) -> None:
    self.selection_flag = True
