# Original QuantConnect / library Python
# locale=en slug="asset-growth-effect"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
import numpy as np
#endregion

class AssetGrowthEffect(XXX):

def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    
    self.UniverseSettings.Leverage = 5
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0

    # Latest assets data.
    self.total_assets: dict[Symbol, float] = {}
    self.long_symbols: list[Symbol] = []
    self.short_symbols: list[Symbol] = []
    self.selection_flag: bool = False
    
    # Filter Parameters
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']
    self.quantile: int = 10
    self.rebalancing_month: int = 6
    # self.fin_sector_code: int = 103
    
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    
    self.exchange: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthEnd(self.exchange), 
                    self.TimeRules.AfterMarketOpen(self.exchange), 
                    self.Selection)

def FundamentalFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged

    filtered: List[Fundamental] = [f for f in fundamental if f.HasFundamentalData
                            and f.SecurityReference.ExchangeId in self.exchange_codes
                            # and f.AssetClassification.MorningstarSectorCode != self.fin_sector_code
                            and not np.isnan(f.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths)
                            and f.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths > 0]

    if len(filtered) > self.fundamental_count:
        filtered = [x for x in sorted(filtered, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    assets_growth: dict[Symbol, float] = {}
    for security in filtered:
        symbol: Symbol = security.Symbol
        
        if symbol not in self.total_assets:
            self.total_assets[symbol] = None
            
        current_assets: float = security.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths
        
        # There is not previous assets data.
        if not self.total_assets[symbol]:
            self.total_assets[symbol] = current_assets
            continue
        
        # Assets growth calc.
        assets_growth[symbol] = (current_assets - self.total_assets[symbol]) / self.total_assets[symbol]
        
        # Update data.
        self.total_assets[symbol] = current_assets
    
    # Asset growth sorting.
    if len(assets_growth) >= self.quantile:
        sorted_by_assets_growth: dict[Symbol, float] = sorted(assets_growth.items(), 
                                                            key = lambda x: x[1], 
                                                            reverse = True)
        quantile: int = int(len(sorted_by_assets_growth) / self.quantile)
        self.long_symbols = [x[0] for x in sorted_by_assets_growth[-quantile:]]
        self.short_symbols = [x[0] for x in sorted_by_assets_growth[:quantile]]
    
    return self.long_symbols + self.short_symbols
    
def OnData(self, slice: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long_symbols, self.short_symbols]):
        for symbol in portfolio:
            if slice.ContainsKey(symbol) and slice[symbol] is not None:
                targets.append(PortfolioTarget(
                    symbol, ((-1) ** i) / len(portfolio)))

    self.SetHoldings(targets, True)
    self.long_symbols.clear()
    self.short_symbols.clear()
        
def Selection(self) -> None:
    if self.Time.month == self.rebalancing_month:
        self.selection_flag = True
        
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
