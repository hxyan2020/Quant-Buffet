# Original QuantConnect / library Python
# locale=zh slug="股票中的盈利加速效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
from numpy import isnan
class EarningsAccelerationEffectinStocks(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2004, 1, 1)
    self.SetCash(100000)
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']	
    
    self.leverage:int = 5
    self.quantile:int = 10
    self.min_share_price:int = 5
    self.quarters_count:int = 6       # Number of quarters to calculate the earning acceleration indicator
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.weight:Dict[Symbol, float] = {}
    self.eps_by_symbol:Dict[Symbol, RollingWindow] = {}       # Contains RollingWindow objects for every stock
    self.last_fundamental:List[Symbol] = []
    
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_flag:bool = False
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    '''Drop securities which have no fundamental data or have too low prices.
    Select those with the highest dollar volume'''
    
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.MarketCap != 0 \
        and not isnan(x.EarningReports.BasicEPS.ThreeMonths) and x.EarningReports.BasicEPS.ThreeMonths > 0 \
        and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    ea_by_stock:Dict[Symbol, float] = {}
    
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        # If stock wasn't in last_fundamental we need to reintialize it to make sure data are consecutive
        if symbol not in self.eps_by_symbol or symbol not in self.last_fundamental:
            self.eps_by_symbol[symbol] = RollingWindow[float](self.quarters_count)
            
        # update rolling window for every stock
        self.eps_by_symbol[symbol].Add(stock.EarningReports.BasicEPS.ThreeMonths)
        if self.eps_by_symbol[symbol].IsReady:
            rw:List[float] = [x for x in self.eps_by_symbol[symbol]]
            eps_fraction1:float = (rw[0] - rw[4]) / rw[1]
            eps_fraction2:float = (rw[1] - rw[5]) / rw[2]
            ea_by_stock[stock] = eps_fraction1 - eps_fraction2 # That's the earnings acceleration we want
    
    sorted_by_ea:List[Fundamental] = [x[0] for x in sorted(ea_by_stock.items(), key = lambda item: item[1], reverse = True)]
    # Create long and short quantile
    quantile:int = int(len(sorted_by_ea) / self.quantile)
    long:List[Fundamental] = sorted_by_ea[:quantile]
    short:List[Fundamental] = sorted_by_ea[-quantile:]

    # Calculate weight for each stock in portfolio
    for i, portfolio in enumerate([long, short]):
        mc_sum:float = sum(list(map(lambda stock: stock.MarketCap, portfolio)))
        for stock in portfolio:
            self.weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap /  mc_sum
    
    # Change last fundamental to make sure data are consecutive
    self.last_fundamental = [x.Symbol for x in fundamental]
        
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
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
