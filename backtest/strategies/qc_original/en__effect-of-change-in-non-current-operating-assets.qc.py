# Original QuantConnect / library Python
# locale=en slug="effect-of-change-in-non-current-operating-assets"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class EffectofChangeinNonCurrentOperatingAssets(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    # Non-Current Operating Assets.
    self.operating_assets:Dict[Symbol, float] = {}
    self.quantile:int = 10
    self.leverage:int = 5
    self.rebalance_month:int = 12
    self.min_share_price:float = 5.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
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
        x for x in fundamental if x.HasFundamentalData and x.Price >= self.min_share_price and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes and \
        not np.isnan(x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths) and x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths != 0 and \
        not np.isnan(x.FinancialStatements.BalanceSheet.CurrentAssets.TwelveMonths) and x.FinancialStatements.BalanceSheet.CurrentAssets.TwelveMonths != 0 and \
        not np.isnan(x.FinancialStatements.BalanceSheet.InvestmentsAndAdvances.TwelveMonths) and x.FinancialStatements.BalanceSheet.InvestmentsAndAdvances.TwelveMonths != 0 and \
        x.AssetClassification.MorningstarSectorCode != MorningstarSectorCode.FinancialServices
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    d_assets:Dict[Symbol, float] = {}
    for stock in selected:
        symbol:Symbol = stock.Symbol
    
        if symbol not in self.operating_assets:
            self.operating_assets[symbol] = -1.
        
        assets:float = stock.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths - \
                stock.FinancialStatements.BalanceSheet.CurrentAssets.TwelveMonths - \
                stock.FinancialStatements.BalanceSheet.InvestmentsAndAdvances.TwelveMonths
        if symbol in self.operating_assets and self.operating_assets[symbol] not in [-1, 0]:
            d_assets[symbol] = assets / self.operating_assets[symbol] - 1
        # Update assets value.
        self.operating_assets[symbol] = assets
        
    # NOTE: Get rid of old advertisment records so we work with latest values.
    for symbol in self.operating_assets:
        if symbol not in [x.Symbol for x in selected]:
            self.operating_assets[symbol] = -1
    
    if len(d_assets) >= self.quantile:
        sorted_by_assets:List = sorted(d_assets.items(), key = lambda x: x[1], reverse = True)
        quantile:int = int(len(sorted_by_assets) / self.quantile)
        self.long = [x[0] for x in sorted_by_assets[-quantile:]]
        self.short = [x[0] for x in sorted_by_assets[:quantile]]
    
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
    if self.Time.month == self.rebalance_month:
        self.selection_flag = True        
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
