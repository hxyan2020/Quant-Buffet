# Original QuantConnect / library Python
# locale=en slug="impact-of-overnight-returns-and-daytime-reversals-to-future-stock-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
import pandas as pd
from pandas.core.frame import DataFrame
class ImpactOfOvernightReturnsDaytimeReversals(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.period:int = 13 * 21
    self.quantile:int = 10
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    self.selection_flag = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price >= self.min_share_price and \
        x.Market == 'usa' and x.MarketCap != 0
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    AB_NR:Dict[Fundamental, float] = {}
    
    for stock in selected:
        symbol:Symbol = stock.Symbol
        hist:DataFrame = self.History([symbol], self.period, Resolution.Daily)
        if 'close' in hist.columns and 'open' in hist.columns:
            closes:pd.Series = hist['close']
            opens:pd.Series = hist['open']
            if len(closes) == self.period and len(opens) == self.period:
                # Calculate overnight and daily returns                    
                RET_OC:pd.Series = pd.Series(closes / opens - 1)         # Open to close return
                RET:pd.Series = pd.Series(closes).pct_change()        # Close to close return
                RET_CO:pd.Series = ((1 + RET) / (1 + RET_OC)) - 1
                
                # Negative daytime reversal signal for last year                    
                reversal_vector:List = [1 if co > 0 and oc = np.percentile(market_cap_values, 66)]

        abnr_values:List[float] = list(AB_NR.values())
        high_by_abnr:List[Fundamental] = [x[0] for x in AB_NR.items() if x[1] >= np.percentile(abnr_values, 80)]
        low_by_abnr:List[Fundamental] = [x[0] for x in AB_NR.items() if x[1]  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # order execution
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
		
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()
        
def Selection(self) -> None:
    self.selection_flag = True
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
