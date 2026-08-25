# Original QuantConnect / library Python
# locale=zh slug="股票中的长期债务因素"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
import numpy as np
class LongTermDebtFactorWithinStocks(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2008, 1, 1)  
    self.SetCash(100_000) 
    self.UniverseSettings.Leverage = 10
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0
    
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']
    self.fundamental_count: int = 3_000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.fin_sector_code: int = 103
    self.rebalancing_month: int = 1
    self.quantile: int = 10
    self.selection_flag: bool = True
    
    self.last_year_liabilities: Dict[Symbol, float] = {}
    self.long_symbols: List[Symbol] = []
    self.short_symbols: List[Symbol] = []
    
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
    for security in changes.RemovedSecurities:
        if security.Symbol in self.last_year_liabilities:
            del self.last_year_liabilities[security.Symbol]
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
        
    filtered: List[Fundamental] = [
        f for f in fundamental if f.HasFundamentalData
        and f.SecurityReference.ExchangeId in self.exchange_codes
        and not np.isnan(f.MarketCap)
        and f.MarketCap != 0
        and not np.isnan(f.FinancialStatements.BalanceSheet.TradingandFinancialLiabilities.TwelveMonths)
        and f.FinancialStatements.BalanceSheet.TradingandFinancialLiabilities.TwelveMonths > 0
        and f.asset_classification.morningstar_industry_code != self.fin_sector_code
    ]
    sorted_filter: List[Fundamental] = sorted(filtered,
                                            key=self.fundamental_sorting_key,
                                            reverse=True)[:self.fundamental_count]
    
    change_in_liabilities: Dict[Symbol, float] = {}
    for f in sorted_filter:
        liabilities: float = f.FinancialStatements.BalanceSheet.TradingandFinancialLiabilities.TwelveMonths
        
        if f.Symbol not in self.last_year_liabilities:
            self.last_year_liabilities[f.Symbol] = liabilities
            continue
        
        change_in_liabilities[f.Symbol] = liabilities / self.last_year_liabilities[f.Symbol] - 1
    
    if len(change_in_liabilities) >= self.quantile:
        # Sorting by change in Longterm financial liabilities
        sorted_by_liabilities: List = sorted(change_in_liabilities.items(), key=lambda x: x[1], reverse=True)
        decile: int = int(len(sorted_by_liabilities) / self.quantile)
        self.long_symbols = [x[0] for x in sorted_by_liabilities[:decile]]
        self.short_symbols = [x[0] for x in sorted_by_liabilities[-decile:]]
    return self.long_symbols + self.short_symbols

def OnData(self, slice: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Trade execution
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long_symbols, self.short_symbols]):
        for symbol in portfolio:
            if slice.ContainsKey(symbol) and slice[symbol] is not None:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    self.SetHoldings(targets, True)
    self.long_symbols.clear()
    self.short_symbols.clear()

def Selection(self) -> None:
    if self.Time.month == self.rebalancing_month:
        self.selection_flag = True
        
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
