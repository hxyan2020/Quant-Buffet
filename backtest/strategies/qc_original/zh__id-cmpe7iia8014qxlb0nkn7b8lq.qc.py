# Original QuantConnect / library Python
# locale=zh slug="低价效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class LowPriceEffect(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.weight:Dict[Symbol, float] = {}
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.quantile:int = 10
    self.leverage:int = 5
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    
    self.settings.daily_precise_end_time = False
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId == "NYS" and x.MarketCap != 0]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    long:List[Fundamental] = []
    short:List[Fundamental] = []
    # Store stock adjusted price.
    price:Dict[Fundamental, float] = { x : x.AdjustedPrice for x in selected }
    if len(price) >= self.quantile:
        sorted_by_price:List[Fundamental] = sorted(price, key = price.get, reverse = True)
        quantile:int = int(len(sorted_by_price) / self.quantile)
        long = sorted_by_price[-quantile:]
        short = sorted_by_price[:quantile]
    
        # Market cap weighting.
        for i, portfolio in enumerate([long, short]):
            mc_sum:float = sum(map(lambda x: x.MarketCap, portfolio))
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum
    return list(self.weight.keys())

def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Trade execution.
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
def Selection(self) -> None:
    self.selection_flag = True
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
