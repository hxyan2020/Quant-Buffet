# Original QuantConnect / library Python
# locale=en slug="momentum-factor-combined-with-asset-growth-effect"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
import numpy as np
from pandas.core.frame import DataFrame
from pandas.core.series import Series

class MomentumFactorAssetGrowthEffect(XXX):

def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)

    self.UniverseSettings.Leverage = 5
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0

    self.exchange_codes: list[str] = ['NYS', 'NAS', 'ASE']
    self.fundamental_count: int = 1_000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.months_in_year: int = 12
    self.days_in_month: int = 21
    self.total_assets_history_period: int = 2
    self.decile: int = 10
    self.quintile: int = 5
    self.excluded_month: int = 1
    
    # Monthly close prices and total assets
    self.symbol_data: dict[Symbol, SymbolData] = {}
    self.long_symbols: dict[Symbol] = []
    self.short_symbols: dict[Symbol] = []
    self.selection_flag: bool = False

    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol        
    self.Schedule.On(self.DateRules.MonthStart(market), 
                    self.TimeRules.AfterMarketOpen(market), 
                    self.Selection)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged

    # Update the rolling window every month.
    for security in fundamental:
        if security.Symbol in self.symbol_data:
            self.symbol_data[security.Symbol].update_price(security.AdjustedPrice)

    filtered: list[Fundamental] = [f for f in fundamental if f.HasFundamentalData
                                    and f.SecurityReference.ExchangeId in self.exchange_codes
                                    and not np.isnan(f.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths)
                                    and f.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths > 0]

    sorted_filter: List[Fundamental] = sorted(filtered, 
                                            key=self.fundamental_sorting_key, 
                                            reverse=True)[:self.fundamental_count]

    # Warmup price rolling windows.
    for f in sorted_filter:
        if f.Symbol in self.symbol_data:
            continue
        
        self.symbol_data[f.Symbol] = SymbolData(f.Symbol, self.months_in_year, self.total_assets_history_period)
        history: DataFrame = self.History(f.Symbol, self.months_in_year * self.days_in_month, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {f.Symbol} yet.")
            continue
        closes: Series = history.loc[f.Symbol].close
        
        # Find monthly closes.
        for index, time_close in enumerate(closes.iteritems()):
            # index out of bounds check.
            if index + 1  None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())

def OnData(self, slice: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long_symbols, self.short_symbols]):
        for symbol in portfolio:
            if slice.ContainsKey(symbol) and slice[symbol] is not None:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))

    self.SetHoldings(targets, True)
    self.long_symbols.clear()
    self.short_symbols.clear()

def Selection(self) -> None:
    # Exclude January trading.
    if self.Time.month != self.excluded_month:
        self.selection_flag = True
    else:
        self.Liquidate()

class SymbolData():
def __init__(self, symbol: Symbol, period: int, total_assets_history_period: int) -> None:
    self.Symbol: Symbol = symbol
    self.Price: RollingWindow = RollingWindow[float](period)
    self.TotalAssets: RollingWindow = RollingWindow[float](total_assets_history_period)

def update_price(self, value) -> None:
    self.Price.Add(value)

def update_assets(self, assets_value) -> None:
    self.TotalAssets.Add(assets_value)

def asset_data_is_ready(self) -> bool:
    return self.TotalAssets.IsReady

def asset_growth(self) -> float:
    asset_values: list[float] = [x for x in self.TotalAssets]
    return (asset_values[0] - asset_values[1]) / asset_values[1]

def price_is_ready(self) -> bool:
    return self.Price.IsReady
    
# Performance, one month skipped.
def performance(self, values_to_skip: int = 1) -> float:
    closes: list[float] = [x for x in self.Price][values_to_skip:]
    return (closes[0] / closes[-1] - 1)

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
