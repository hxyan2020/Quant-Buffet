# Original QuantConnect / library Python
# locale=zh slug="股票中的广告效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
import numpy as np
class AdvertisingEffect(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    self.UniverseSettings.Leverage = 10
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']
    self.fundamental_count: int = 3_000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.min_market_cap: int = 20_000_000
    self.quantile: int = 10
    self.buy_month: int = 6
    self.sell_month: int = 12
    self.selection_flag: bool = False
    self.adv_expenses: Dict[Symbol, float] = {}
    self.long_symbols: List[Symbol] = []
    self.short_symbols: List[Symbol] = []
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
    
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    filtered: List[Fundamental] = [
        f for f in fundamental if f.HasFundamentalData
        and f.SecurityReference.ExchangeId in self.exchange_codes
        and f.MarketCap > self.min_market_cap
        and not np.isnan(f.FinancialStatements.IncomeStatement.SellingAndMarketingExpense.ThreeMonths)
        and f.FinancialStatements.IncomeStatement.SellingAndMarketingExpense.ThreeMonths > 0
    ]
    sorted_filter: List[Fundamental] = sorted(filtered,
                                            key=self.fundamental_sorting_key,
                                            reverse=True)[:self.fundamental_count]
    d_adv: Dict[Symbol, float] = {}
    for f in sorted_filter:        
        if f.Symbol not in self.adv_expenses:
            self.adv_expenses[f.Symbol] = -1
        
        adv_expenses: float = f.FinancialStatements.IncomeStatement.SellingAndMarketingExpense.ThreeMonths
        if f.Symbol in self.adv_expenses and self.adv_expenses[f.Symbol] != -1:
            d_adv[f.Symbol] = adv_expenses / self.adv_expenses[f.Symbol] - 1
        # Update adv expense value
        self.adv_expenses[f.Symbol] = adv_expenses
        
    # NOTE: Get rid of old advertisment records so we work with latest values
    for symbol in self.adv_expenses:
        if symbol not in [x.Symbol for x in sorted_filter]:
            self.adv_expenses[symbol] = -1
    
    if len(d_adv) >= self.quantile:
        sorted_by_adv: list = sorted(d_adv.items(), key=lambda x: x[1], reverse=True)
        decile: int = int(len(sorted_by_adv) / self.quantile)
        self.long_symbols = [x[0] for x in sorted_by_adv[-decile:]]
        self.short_symbols = [x[0] for x in sorted_by_adv[:decile]]
    
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
    if self.Time.month == self.buy_month:
        self.selection_flag = True
    elif self.Time.month == self.sell_month:
        self.Liquidate()
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
