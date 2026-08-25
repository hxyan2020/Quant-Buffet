# Original QuantConnect / library Python
# locale=en slug="accrual-anomaly"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
import numpy as np
from typing import List, Dict

class AccrualsBasedStrategy(XXX):

def Initialize(self):
    self.SetStartDate(2006, 1, 1)
    self.SetCash(100000)
    
    self.UniverseSettings.Leverage = 5
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.ScreenStocks)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0

    # Configuration
    self.stock_exchanges: List[str] = ['NYS', 'NAS', 'ASE']
    self.stock_limit: int = 3000
    self.rebalance_month: int = 5
    self.accruals: Dict[Symbol, float] = {}
    self.buy_list: List[Symbol] = []
    self.sell_list: List[Symbol] = []
    self.is_selection_time: bool = False
    
    self.spy_symbol: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthStart(self.spy_symbol), 
                     self.TimeRules.AfterMarketOpen(self.spy_symbol), 
                     self.DecideRebalance)

def ScreenStocks(self, fundamentals: List[Fundamental]) -> List[Symbol]:
    if not self.is_selection_time:
        return Universe.Unchanged

    eligible_stocks = [f for f in fundamentals if f.HasFundamentalData and
                       f.SecurityReference.ExchangeId in self.stock_exchanges and
                       all(not np.isnan(x) for x in [
                           f.FinancialStatements.BalanceSheet.CurrentAssets.TwelveMonths,
                           f.FinancialStatements.BalanceSheet.CashAndCashEquivalents.TwelveMonths,
                           f.FinancialStatements.BalanceSheet.CurrentLiabilities.TwelveMonths,
                           f.FinancialStatements.BalanceSheet.CurrentDebt.TwelveMonths,
                           f.FinancialStatements.BalanceSheet.IncomeTaxPayable.TwelveMonths,
                           f.FinancialStatements.IncomeStatement.DepreciationAndAmortization.TwelveMonths])]

    if len(eligible_stocks) > self.stock_limit:
        eligible_stocks = sorted(eligible_stocks, key=lambda x: x.MarketCap, reverse=True)[:self.stock_limit]

    for stock in eligible_stocks:
        symbol = stock.Symbol
        accruals_data = self.ComputeAccruals(stock)
        self.accruals[symbol] = accruals_data

    sorted_accruals = sorted(self.accruals.items(), key=lambda item: item[1])
    decile_size = len(sorted_accruals) // 10
    self.buy_list = [symbol for symbol, _ in sorted_accruals[:decile_size]]
    self.sell_list = [symbol for symbol, _ in sorted_accruals[-decile_size:]]

    return self.buy_list + self.sell_list

def ComputeAccruals(self, stock: Fundamental) -> float:
    delta_assets = stock.FinancialStatements.BalanceSheet.CurrentAssets.TwelveMonths - stock.FinancialStatements.BalanceSheet.CashAndCashEquivalents.TwelveMonths
    delta_liabilities = stock.FinancialStatements.BalanceSheet.CurrentLiabilities.TwelveMonths - stock.FinancialStatements.BalanceSheet.CurrentDebt.TwelveMonths - stock.FinancialStatements.BalanceSheet.IncomeTaxPayable.TwelveMonths
    depreciation = stock.FinancialStatements.IncomeStatement.DepreciationAndAmortization.TwelveMonths
    total_assets = stock.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths
    accruals = (delta_assets - delta_liabilities - depreciation) / total_assets
    return accruals

def DecideRebalance(self):
    self.is_selection_time = self.Time.month == self.rebalance_month

def OnSecuritiesChanged(self, changes: SecurityChanges):
    for removed in changes.RemovedSecurities:
        if removed.Symbol in self.accruals:
            del self.accruals[removed.Symbol]

def OnData(self, data: Slice):
    if not self.is_selection_time:
        return
    
    self.is_selection_time = False
    self.ExecuteTrades(data)

def ExecuteTrades(self, data: Slice):
    targets = [PortfolioTarget(symbol, 1 / len(self.buy_list)) for symbol in self.buy_list if data.ContainsKey(symbol)] + \
              [PortfolioTarget(symbol, -1 / len(self.sell_list)) for symbol in self.sell_list if data.ContainsKey(symbol)]
    self.SetHoldings(targets)
    self.buy_list.clear()
    self.sell_list.clear()

# Example custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee = parameters.Security.Price
