# Original QuantConnect / library Python
# locale=zh slug="股票市场中现金效应的生产力"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from numpy import isnan
class ProductivityCashEffectStockMarket(QCAlgorithm):
def Initialize(self)  -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.quantile:int = 10
    self.leverage:int = 10
    self.min_share_price:int = 5
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    self.selection_month:int = 4
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetLeverage(self.leverage)
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price > self.min_share_price and not \
        isnan(x.FinancialStatements.BalanceSheet.TotalDebt.TwelveMonths) and x.FinancialStatements.BalanceSheet.TotalDebt.TwelveMonths != 0 and not \
        isnan(x.FinancialStatements.BalanceSheet.TotalEquity.TwelveMonths) and x.FinancialStatements.BalanceSheet.TotalEquity.TwelveMonths != 0 and not \
        isnan(x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths) and x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths != 0 and not \
        isnan(x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.TwelveMonths) and x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.TwelveMonths != 0 and
        x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    if len(selected) >= self.quantile:
        # Sorting by productivity of cash.    
        sorted_by_poc:List[Fundamental] = sorted(selected, key = lambda x:((x.FinancialStatements.BalanceSheet.TotalDebt.TwelveMonths + x.FinancialStatements.BalanceSheet.TotalEquity.TwelveMonths - \
                                                                            x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths) / \
                                                                            x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.TwelveMonths), reverse=True)
        quantile = int(len(sorted_by_poc) / self.quantile)
        self.long = [x.Symbol for x in sorted_by_poc[-quantile:]]
        self.short = [x.Symbol for x in sorted_by_poc[:quantile]]
    return self.long + self.short

def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Trade execution.
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()

def Selection(self) -> None:
    if self.Time.month == self.selection_month:
        self.selection_flag = True
        
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
