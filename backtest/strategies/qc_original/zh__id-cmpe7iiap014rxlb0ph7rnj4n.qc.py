# Original QuantConnect / library Python
# locale=zh slug="将价值策略的基本面成分和暂时性成分相结合"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import statsmodels.api as sm
from typing import List, Dict
from numpy import isnan
#endregion
 
class CombiningFundamentalAndTransitoryComponentOfValueStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']
    self.tickers_to_ignore: List[str] = ['SGA']
    self.period: int = 2 # need n values for regression
    
    self.data: Dict[Symbol, SymbolData] = {}
    self.quantities: Dict[Symbol, int] = {}
    self.last_selection: List[Symbol] = []
    
    self.min_share_price: int = 5
    self.leverage: int = 5
    self.quantile: int = 5
    self.month_counter: int = 0
    self.fundamental_count: int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.selection_flag: bool = False
    self.symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol, 0), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List:
    # selection yearly
    if not self.selection_flag:
        return Universe.Unchanged
    
    # filter top n stocks by dollar volume
    selected: List[Fundamental] = [
        x for x in fundamental \
        if x.HasFundamentalData and \
        x.Market == 'usa' and \
        x.Price > self.min_share_price and not \
        isnan(x.ValuationRatios.PBRatio) and x.ValuationRatios.PBRatio != 0 and not\
        isnan(x.FinancialStatements.IncomeStatement.GrossProfit.TwelveMonths) and x.FinancialStatements.IncomeStatement.GrossProfit.TwelveMonths != 0 and not\
        isnan(x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths) and x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths != 0 and \
        x.MarketCap != 0 and \
        x.SecurityReference.ExchangeId in self.exchange_codes and \
        x.Symbol.Value not in self.tickers_to_ignore
    ]
    if len(selected) > self.fundamental_count:
                selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
                    
    HMLFundamental: Dict[Fundamental, float] = {} 
    HMLTransitory: Dict[Fundamental, float] = {}
    
    # store current stocks prices for trenching
    for stock in selected:
        symbol: Symbol = stock.Symbol
        
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
        
        # update price
        self.data[symbol].update_price(stock.AdjustedPrice)
   
        # symbol = stock.Symbol
        pb_ratio: float = stock.ValuationRatios.PBRatio
        total_assets: float = stock.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths
        gross_profit: float = stock.FinancialStatements.IncomeStatement.GrossProfit.TwelveMonths
        
        # make sure data are consecutive
        if symbol not in self.last_selection:
            self.data[symbol] = SymbolData(self.period)
            
        self.data[symbol].update_regression_data(pb_ratio, total_assets, gross_profit)
            
        # make sure data for regression are ready
        if not self.data[symbol].is_data_ready():
            continue
        
        # calculate stock's Y and Xs for regression
        regression_y: List[float] = self.data[symbol].get_regression_y()
        regression_x: List[List[float]] = self.data[symbol].get_regression_x()
        
        regression_model: RegressionResultWrapper = self.MultipleLinearRegression(regression_x, regression_y)
        
        # calculate fit value
        fit_value: float = regression_model.params[0]
        # iterate through betas - handles missing beta value if profit growth value is 0
        for i, beta in enumerate(regression_model.params[1:]):
            corresponding_x: float = regression_x[i][1]
            fit_value += corresponding_x * beta
        
        # store fit value keyed by stock
        HMLFundamental[stock] = fit_value
        
        # last residual from regression is needed for HMLTransitory strategy    
        last_residual: float = regression_model.resid[-1]
        # store last residual keyed by stock
        HMLTransitory[stock] = last_residual
        
    # change last selection, to make data consecutive
    self.last_selection = [x.Symbol for x in selected]
    
    # there has to be enough stocks for quintile selections    
    if len(HMLFundamental)  None:
    # rebalance yearly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    self.Liquidate()
            
    for symbol, quantity in self.quantities.items():
        if symbol in data and data[symbol]:
            self.MarketOrder(symbol, quantity)
        
    self.quantities.clear()
    
def MultipleLinearRegression(self, x: List[List[float]], y: List[float]):
    x: np.ndarray = np.array(x).T
    x = sm.add_constant(x)
    result: RegressionResultWrapper = sm.OLS(endog=y, exog=x).fit()
    return result
    
def CalculateQuantities(self, stock_list: List[Fundamental], weight: float, long_flag: bool) -> None:
    total_cap: float = sum([stock.MarketCap for stock in stock_list])
    
    for stock in stock_list:
        price: float = self.data[stock.Symbol].price
        market_cap: float = stock.MarketCap
        
        # calculate quantity
        quantity: int = np.floor((weight * (market_cap / total_cap)) / price) 
        
        # stock goes short
        if not long_flag:
            quantity = -1 * quantity
        
        self.quantities[stock.Symbol] = quantity
    
def Selection(self) -> None:
    # rebalance yearly
    if self.month_counter % 12 == 0:
        self.selection_flag = True
    self.month_counter += 1
        
class SymbolData():
def __init__(self, period: int) -> None:
    self.pb_ratio: RollingWindow = RollingWindow[float](period)
    self.gross_profit: RollingWindow = RollingWindow[float](period + 1) 
    self.total_assets: RollingWindow = RollingWindow[float](period + 1)
    self.price: Union[None, float] = None
    
def update_price(self, price: float) -> None:
    self.price = price
    
def update_regression_data(self, pb_ratio: float, total_assets: float, gross_profit: float) -> None:
    self.pb_ratio.Add(pb_ratio)
    self.total_assets.Add(total_assets)
    self.gross_profit.Add(gross_profit)
    
def is_data_ready(self) -> bool:
    # return self.pb_ratio.IsReady and self.gross_profit.IsReady and \
    #         self.total_assets.IsReady and self.market_cap != None and self.price != None
    return self.pb_ratio.IsReady and self.gross_profit.IsReady and self.total_assets.IsReady

def get_regression_y(self) -> List[float]:
    return [x for x in self.pb_ratio][::-1]
            
def get_regression_x(self) -> List[List[float]]:
    gross_profit_values: np.ndarray = np.array([x for x in self.gross_profit])
    total_assets_values: np.ndarray = np.array([x for x in self.total_assets])
    
    x1: List[float] = [gpv / tav for gpv, tav in zip(gross_profit_values[:-1], total_assets_values[:-1])]
    x2: List[float] = (gross_profit_values[:-1] / gross_profit_values[1:] - 1) / total_assets_values[1:]     # profit growth / total assets from previous year
    
    return [x1[::-1], x2[::-1]]

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
