# Original QuantConnect / library Python
# locale=en slug="roa-effect-within-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class ROAEffectWithinStocks(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000) 

    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.quantile:int = 10
    self.leverage:int = 5
    self.sales_threshold:float = 1e7
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []

    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume

    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes and \
        x.ValuationRatios.SalesPerShare * x.EarningReports.DilutedAverageShares.Value > self.sales_threshold and \
        not np.isnan(x.OperationRatios.ROA.ThreeMonths) and x.OperationRatios.ROA.ThreeMonths != 0]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
                
    # Sorting by market cap.
    sorted_by_market_cap = sorted(selected, key = lambda x: x.MarketCap, reverse=True)
    half:int = int(len(sorted_by_market_cap) / 2)
    top_mc = [x for x in sorted_by_market_cap[:half]]
    bottom_mc = [x for x in sorted_by_market_cap[half:]]
    
    if len(top_mc) >= self.quantile and len(bottom_mc) >= self.quantile:
        # Sorting by ROA.
        sorted_top_by_roa:List[Fundamental] = sorted(top_mc, key = lambda x:(x.OperationRatios.ROA.Value), reverse=True)
        quantile:int = int(len(sorted_top_by_roa) / self.quantile)
        long_top:List[Symbol] = [x.Symbol for x in sorted_top_by_roa[:quantile*3]]
        short_top:List[Symbol] = [x.Symbol for x in sorted_top_by_roa[-(quantile*3):]]
        
        sorted_bottom_by_roa:List[Fundamental] = sorted(bottom_mc, key = lambda x:(x.OperationRatios.ROA.Value), reverse=True)
        quantile = int(len(sorted_bottom_by_roa) / self.quantile)
        long_bottom:List[Symbol] = [x.Symbol for x in sorted_bottom_by_roa[:quantile*3]]
        short_bottom:List[Symbol] = [x.Symbol for x in sorted_bottom_by_roa[-(quantile*3):]]
        
        self.long = long_top + long_bottom 
        self.short = short_top + short_bottom

    return self.long + self.short

def OnData(self, data: Slice) -> None:
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
