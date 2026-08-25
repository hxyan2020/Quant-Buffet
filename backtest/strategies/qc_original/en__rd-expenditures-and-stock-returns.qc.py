# Original QuantConnect / library Python
# locale=en slug="rd-expenditures-and-stock-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
from numpy import log, average
from scipy import stats
import numpy as np
#endregion

class RDExpendituresandStockReturns(XXX):

def Initialize(self) -> None:
    self.SetStartDate(1998, 1, 1)
    self.SetCash(100000)

    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.rebalance_month:int = 4
    self.quantile:int = 5
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    
    # R&D history.
    self.RD:Dict[Symbol, float] = {}
    self.rd_period:int = 5
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    data:Equity = self.AddEquity('XLK', Resolution.Daily)
    data.SetLeverage(self.leverage)
    self.technology_sector:Symbol = data.Symbol
  
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
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
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.AdjustedPrice > self.min_share_price and x.SecurityReference.ExchangeId in self.exchange_codes and x.MarketCap != 0 and \
        not np.isnan(x.FinancialStatements.IncomeStatement.ResearchAndDevelopment.TwelveMonths) and x.FinancialStatements.IncomeStatement.ResearchAndDevelopment.TwelveMonths != 0
        ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    selected_symbols:List[Symbol] = list(map(lambda x: x.Symbol, selected))
    
    ability:Dict[Fundamental, float] = {}
    updated_flag:List[Symbol] = []  # updated this year already
    
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        # prevent storing duplicated value for the same stock in one year
        if symbol not in updated_flag:
            # Update RD.
            if symbol not in self.RD:
                self.RD[symbol] = RollingWindow[float](self.rd_period)
            
            if self.RD[symbol].IsReady:
                coefs:np.ndarray = np.array([1, 0.8, 0.6, 0.4, 0.2])
                rds:np.ndarray = np.array([x for x in self.RD[symbol]])
                
                rdc:float = sum(coefs * rds)
                ability[stock] = rdc / stock.MarketCap
            
            rd:float = stock.FinancialStatements.IncomeStatement.ResearchAndDevelopment.TwelveMonths
            self.RD[symbol].Add(rd)
        
        # prevent storing duplicated value for the same stock in one year
        if selected_symbols.count(symbol) > 1:
            updated_flag.append(symbol)
    
    # Remove not updated symbols
    symbols_to_delete:List[Symbol] = []
    for symbol in self.RD.keys():
        if symbol not in selected_symbols:
            symbols_to_delete.append(symbol)    
    for symbol in symbols_to_delete:
        if symbol in self.RD:
            del self.RD[symbol]
    
    # starts trading after data storing period
    if len(ability) >= self.quantile:
        # Ability sorting.
        sorted_by_ability:List = sorted(ability.items(), key = lambda x: x[1], reverse = True)
        quantile:int = int(len(sorted_by_ability) / self.quantile)
        high_by_ability:List[Symbol] = [x[0].Symbol for x in sorted_by_ability[:quantile]]
        low_by_ability:List[Symbol] = [x[0].Symbol for x in sorted_by_ability[-quantile:]]
        
        self.long = high_by_ability
        self.short = low_by_ability
    
    return self.long + self.short

def Selection(self) -> None:
    if self.Time.month == self.rebalance_month:
        self.selection_flag = True
        
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
    
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
