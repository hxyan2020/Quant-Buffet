# Original QuantConnect / library Python
# locale=en slug="中国的投资效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from numpy import isnan

class InvestmentEffectInChina(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}
    
    self.percentile_size:int = 5
    self.portfolio_size:float = 0.1
    
    self.TA_period:int = 2
    self.TA_growth_period:int = 2
    self.leverage:int = 5
    
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.rebalance_flag:bool = False
    self.selection_flag:bool = False
    self.rebalance_months:List[int] = [5, 11]
    self.selection_months:List[int] = [2, 5, 8, 11]
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.BeforeMarketClose(self.market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> None:
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    # filter stocks, which symbols isn't SPY equity symbol and has fundamental data
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Symbol != self.market and x.CompanyReference.BusinessCountryID == 'CHN' and \
        not isnan(x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths) and x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths != 0 and x.MarketCap != 0
        ]

    AAG:Dict[Fundamental, float] = {}
    
    for stock in selected:
        symbol:Symbol = stock.Symbol
        total_assets:float = stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths
       
        if symbol not in self.data or symbol not in self.previous_fine:
            self.data[symbol] = SymbolData(self.TA_period, self.TA_growth_period)
        
        symbol_obj:SymbolData = self.data[symbol]  
        symbol_obj.update_TA(total_assets)
        
        # update Total Assets growth only in May and November
        if self.Time.month in self.rebalance_months:
            if symbol_obj.TA_growths_ready() and symbol_obj.TA_ready():
                # calculate stock's AAG
                curr_TA_growth:float = symbol_obj.calculate_TA_growth()
                prev_TA_growths:List[float] = [x for x in symbol_obj._total_assets_growths]
                
                AAG_value:float = curr_TA_growth - np.mean(prev_TA_growths)
                
                AAG[stock] = AAG_value
                
                # update stock's total assets growth 
                symbol_obj.update_TA_growths(curr_TA_growth)
                
            elif symbol_obj.TA_ready():
                # update stock's total assets growth
                curr_TA_growth:float = symbol_obj.calculate_TA_growth()
                symbol_obj.update_TA_growths(curr_TA_growth)
        
    self.previous_fine = list(map(lambda stock: stock.Symbol, selected))
      
    # make sure there are enough data for selection
    if len(AAG)  None:
    # rebalancing only in May and November
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()
    
def Selection(self) -> None:
    # perform selection on February, May, August and November
    if self.Time.month in self.selection_months:
        self.selection_flag = True
        
    # perform rebalance in April, May, October and November 
    if self.Time.month in self.rebalance_months:
        self.rebalance_flag = True
    
class SymbolData():
def __init__(self, TA_period: int, TA_growth_period: int) -> None:
    self._total_assets:RollingWindow = RollingWindow[float](TA_period)
    self._total_assets_growths:RollingWindow = RollingWindow[float](TA_growth_period)
    
def update_TA(self, total_assets: float) -> None:
    self._total_assets.Add(total_assets)
    
def update_TA_growths(self, total_assets_growths) -> None:
    self._total_assets_growths.Add(total_assets_growths)
    
def calculate_TA_growth(self) -> float:
    total_assets:List[float] = list(self._total_assets)
    return (total_assets[0] - total_assets[-1]) / total_assets[-1] 

def TA_ready(self) -> bool:
    return self._total_assets.IsReady
    
def TA_growths_ready(self) -> bool:
    return self._total_assets_growths.IsReady
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
