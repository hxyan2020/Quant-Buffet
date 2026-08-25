# Original QuantConnect / library Python
# locale=zh slug="中国的规模因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from numpy import isnan
from typing import List, Dict
#endregion
class SizeFactorInChina(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100000)
    
    self.leverage: int = 5
    self.market_cap_portion: float = 0.3
    self.quantile: int = 3
    self.traded_portion: float = 0.2
    self.weight: Dict[Symbol, float] = {}
    
    symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(symbol), self.TimeRules.AfterMarketOpen(symbol), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.MarketCap != 0 
        and x.CompanyReference.BusinessCountryID == 'CHN'
        and not isnan(x.ValuationRatios.PERatio) and x.ValuationRatios.PERatio != 0 
    ]
    
    # exclude 30% of lowest stocks by MarketCap
    selected = sorted(selected, key = lambda x: x.MarketCap)[int(len(selected) * self.market_cap_portion):]
    
    market_cap: Dict[Symbol, float] = {}
    earnings_price_ratio: Dict[Symbol, float] = {}
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
            
        market_cap[symbol] = stock.MarketCap
        earnings_price_ratio[symbol] = 1 / stock.ValuationRatios.PERatio
        
    median_market_value: float = np.median([market_cap[x] for x in market_cap])
    
    # according to median split into BIG and SMALL
    B: List[Symbol] = [x for x in market_cap if market_cap[x] >= median_market_value]
    S: List[Symbol] = [x for x in market_cap if market_cap[x]  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w * self.traded_portion) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
