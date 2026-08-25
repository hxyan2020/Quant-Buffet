# Original QuantConnect / library Python
# locale=en slug="quarterly-investment-spikes-predict-stock-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *

class QuarterlyInvestmentSpikesPredictStockReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.period:int = 4             # need n quarterly capex growths
    self.leverage:int = 10
    self.quantile:int = 3
    self.selection_months = [4, 7, 10, 1]   # MonthStart
    self.total_asset_threshold:int = 1e7
    self.capex_threshold:int = 1e5

    self.weight:Dict[Symbol, float] = {}
    self.capex:Dict[Symbol, RollingWindow] = {}
    self.last_fine:List[Symbol] = []
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.rebalance_flag:bool = False
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    # filter stock symbols
    selected:List[Fundamental] = [x for x in fundamental if x.MarketCap != 0 and \
        x.FinancialStatements.CashFlowStatement.CapExReported.ThreeMonths >= self.capex_threshold and \
        x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths >= self.total_asset_threshold
        ]

    qspikes:Dict[Fundamental, float] = {} # storing stocks qspike keyed by stocks objects
        
    for stock in selected:
        symbol:Symbol = stock.Symbol
        capex:float = stock.FinancialStatements.CashFlowStatement.CapExReported.ThreeMonths
        
        # make sure data are consecutive
        if symbol not in self.last_fine:
            self.capex[symbol] = RollingWindow[float](self.period)
        self.capex[symbol].Add(capex)
        
        # calculate qspike only on rebalance and when data are ready
        if self.rebalance_flag and self.capex[symbol].IsReady:
            capexes:List[float] = list(self.capex[symbol])
            
            # get last quarter of capex growth
            last_capex:float = capexes[0]
            # calculate average from first three quarters of capex growth
            avg_from_first_three:float = np.average(capexes[1:4])
            
            # calculate and store stock's qspike
            qspikes[stock] = last_capex / avg_from_first_three
    
    # change last fine universe based on current fine
    self.last_fine = list(map(lambda x: x.Symbol, selected))
            
    # not enough stocks for selection
    if len(qspikes)  None:
    # rebalance yearly
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()
    
def Selection(self) -> None:
    if self.Time.month in self.selection_months:
        self.selection_flag = True
    
    # rebalance yearly on last selection month
    if self.Time.month == self.selection_months[-1]:
        self.rebalance_flag = True
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
