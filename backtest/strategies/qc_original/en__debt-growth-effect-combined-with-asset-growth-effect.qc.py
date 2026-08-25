# Original QuantConnect / library Python
# locale=en slug="debt-growth-effect-combined-with-asset-growth-effect"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from numpy import isnan
class DebtGrowthEffectCombinedwithAssetGrowthEffect(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.quantile:int = 10
    self.sec_quantile:int = 4
    self.traded_percentage:float = .5
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    # Last year's debt value.
    self.latest_debt:List[Symbol, float] = {}
    self.weight:Dict[Symbol, float] = {}
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
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
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and \
        x.Price >= self.min_share_price and x.SecurityReference.ExchangeId in self.exchange_codes and \
        not isnan(x.OperationRatios.TotalAssetsGrowth.OneYear) and x.OperationRatios.TotalAssetsGrowth.OneYear != 0 and \
        not isnan(x.FinancialStatements.BalanceSheet.TotalDebt.TwelveMonths) and x.FinancialStatements.BalanceSheet.TotalDebt.TwelveMonths != 0
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    growth_data:Dict[Fundamental, float] = {}
    
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.latest_debt:
            # Previous year's data.
            self.latest_debt[symbol] = None
        
        asset_growth:float = stock.OperationRatios.TotalAssetsGrowth.OneYear
        debt:float = stock.FinancialStatements.BalanceSheet.TotalDebt.TwelveMonths
        
        # Previous year's data is ready.
        if self.latest_debt[symbol]:
            debt_growth:float = (debt - self.latest_debt[symbol]) / self.latest_debt[symbol]
            growth_data[stock] = (asset_growth, debt_growth)
            
        self.latest_debt[symbol] = debt
    
    # Remove not updated symbols.
    updated_symbols:List[Symbol] = [x.Symbol for x in selected]
    not_updated:List[Symbol] = [x for x in self.latest_debt if x not in updated_symbols]
    for symbol in not_updated:
        del self.latest_debt[symbol]
    
    if len(growth_data) >= self.sec_quantile * self.quantile:
        # Sort by asset and debt growth.
        sorted_by_asset_growth:List = sorted(growth_data.items(), key = lambda x: x[1][0], reverse = True)
        quantile:int = int(len(sorted_by_asset_growth) / self.quantile)
        high_by_asset_growth = [x for x in sorted_by_asset_growth[:quantile]]
        
        sorted_by_debt_growth:List = sorted(high_by_asset_growth, key = lambda x: x[1][1], reverse = True)
        quantile = int(len(sorted_by_debt_growth) / self.sec_quantile)
        short:List[Fundamental] = [x for x in sorted_by_debt_growth[:quantile]]
        
        total_market_cap:float = sum([x[0].MarketCap for x in short])
        for stock, _ in short:
            self.weight[stock.Symbol] = -(stock.MarketCap / total_market_cap) * self.traded_percentage
    
    return list(self.weight.keys())

def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
