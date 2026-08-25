# Original QuantConnect / library Python
# locale=zh slug="价值-成长择时"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from numpy import average, std, isnan
from typing import List, Dict, Tuple
#endregion    
class ValueGrowthTiming(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    # Monthly spread data.
    self.period:int = 12
    self.spread:RollinWindow = RollingWindow[float](self.period)
    self.standardized_spread:RollingWindow = RollingWindow[float](self.period)
    self.quantile:int = 10
    self.leverage:int = 10
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.weight:Union[None, int] = None
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' \
            and not isnan(x.AssetClassification.MorningstarIndustryGroupCode) and x.AssetClassification.MorningstarIndustryGroupCode != 0 \
            and not isnan(x.ValuationRatios.PBRatio) and x.ValuationRatios.PBRatio != 0 and x.MarketCap != 0]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    group:Dict[str, Tuple[Symbol, float, float]] = {}

    # Stocks returns calc.
    for stock in selected:
        symbol = stock.Symbol
        
        industry_group_code:float = stock.AssetClassification.MorningstarIndustryGroupCode
        book_market:float = 1 / stock.ValuationRatios.PBRatio
        
        # Adding stock in group.
        if not industry_group_code in group:
            group[industry_group_code] = []
        group[industry_group_code].append((symbol, book_market, stock.MarketCap))
    
    # Group's value weighted average calc.
    group_bm_average:Dict[str, float] = {}
    for industry_group_code, symbols in group.items():
        total_market_cap:float = sum([x[2] for x in symbols])
        
        weighted_items:Dict[Symbol, float] = {x[0] : (x[1] * (x[2] / total_market_cap)) for x in symbols}
        group_bm_average[industry_group_code] = average([x[1] for x in weighted_items.items()])
    
    # Symbol's adjusted bm calc.
    adjusted_bm:Dict[Symbol, float] = {}
    for industry_group_code, symbols in group.items():
        for symbol in symbols:
            symbol_bm:float = symbol[1]
            adjusted_bm[symbol] = symbol_bm - group_bm_average[industry_group_code]
    if len(adjusted_bm)  1:
                self.weight = 1
            self.long = [x[0][0] for x in value_portfolio]
            self.short = [x[0][0] for x in growth_portfolio]
        
    return self.long + self.short
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    targets:List[PortfolioTarget] = []
    if self.weight:
        for i, portfolio in enumerate([self.long, self.short]):
            for symbol in portfolio:
                if symbol in data and data[symbol]:
                    targets.append(PortfolioTarget(symbol, ((-1) ** i) * (self.weight / len(portfolio))))
    
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()
    self.weight = None
def Selection(self) -> None:
    self.selection_flag = True
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
