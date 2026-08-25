# Original QuantConnect / library Python
# locale=zh slug="盈利能力因子与价值因子结合"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
from numpy import isnan
class ProfitabilityCombinedWithValue(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2001, 1, 1)
    self.SetCash(100000)            
    market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    
    self.traded_count:int = 150
    self.leverage:int = 3
    self.min_share_price:int = 5
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    self.rebalance_month:int = 6
    self.selection_flag:bool = True
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.BeforeMarketClose(market), self.Rebalance)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and \
        x.AssetClassification.MorningstarSectorCode != MorningstarSectorCode.FinancialServices and not \
        # isnan(x.EarningReports.BasicAverageShares.ThreeMonths) and x.EarningReports.BasicAverageShares.ThreeMonths != 0 and not \
        isnan(x.FinancialStatements.IncomeStatement.GrossProfit.ThreeMonths) and x.FinancialStatements.IncomeStatement.GrossProfit.ThreeMonths != 0 and not \
        isnan(x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths) and x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths != 0 and not \
        isnan(x.ValuationRatios.PBRatio) and x.ValuationRatios.PBRatio != 0
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # sorted stocks in the top market-cap list by BM
    top_bm:List[Fundamental] = sorted(selected, key = lambda x: 1 / x.ValuationRatios.PBRatio)
    
    # sorted stocks in the top market-cap list by profits-to-assets
    top_pa:List[Fundamental] = sorted(selected, key = lambda x: x.FinancialStatements.IncomeStatement.GrossProfit.ThreeMonths / x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths)
    a:int = 0
    b:int = 0 
    for i in top_bm:
        a += 1
        i.bmrank = a 
    for i in top_pa:
        b += 1
        i.parank = b
    if len(selected) >= self.traded_count*2:
        sorted_by_pv:List[Fundamental] = sorted(selected, key = lambda x: x.bmrank + x.parank, reverse = True)
        
        self.long = [x.Symbol for x in sorted_by_pv[:self.traded_count]]
        self.short = [x.Symbol for x in sorted_by_pv[-self.traded_count:]]
    
    return self.long + self.short
    
def Rebalance(self) -> None:
    if self.Time.month == self.rebalance_month:
        self.selection_flag = True
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Trade execution
    invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.long + self.short:
            self.Liquidate(symbol)
    
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, ((-1) ** i) / len(portfolio))
    self.long.clear()
    self.short.clear()
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
