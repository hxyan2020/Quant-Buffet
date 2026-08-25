# Original QuantConnect / library Python
# locale=en slug="pure-growth-strategy"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
import data_tools
from pandas.core.frame import DataFrame
from numpy import isnan
from functools import reduce
class PureGrowthStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data = {} # storing data for factors in SymbolData object
    self.prices = {} # storing daily prices for stocks in StockPrices object
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.last_selection:List[Symbol] = [] # list of stock symbols, which were selected in previous selection
    self.financial_statement_names:List[str] = [
        'FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths',
        'EarningReports.NormalizedBasicEPS.TwelveMonths',
        'EarningReports.BasicEPS.TwelveMonths',
        'ValuationRatios.SalesPerShare',
        'ValuationRatios.PBRatio',
    ]
    self.period:int = 12 * 21 # storing n of daily prices
    self.factor_period:int = 3 # storing n of needed data for each factor
    self.quantile:int = 10
    self.leverage:int = 5
    self.min_share_price:float = 5.
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.months_counter:int = 0
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market, 0), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # updating prices on daily basis
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        if symbol in self.prices:
            self.prices[symbol].update(stock.AdjustedPrice)
    
    # annual rebalance
    if not self.selection_flag:
        return Universe.Unchanged
    
    # selecting top n liquid stocks
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price >= self.min_share_price and \
        all((not isnan(self.rgetattr(x, statement_name)) \
        and self.rgetattr(x, statement_name) != 0) for statement_name in self.financial_statement_names)
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # dictionaries for factors
    ear_per_share_to_price = {}
    sales_per_share = {}
    book_value_to_price = {}
    earnings_to_price = {}
    sales_to_price = {}
    momentum = {}
    # warm up stock prices
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        if symbol not in self.prices:
            self.prices[symbol] = data_tools.StockPrices(self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                continue
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.prices[symbol].update(close)
        
        if self.prices[symbol].is_ready():
            # check if data are consecutive
            if symbol not in self.last_selection:
                self.data[symbol] = data_tools.SymbolData(self.factor_period)
            
            if symbol not in self.data:
                continue
            
            # update data for each factor
            last_price = self.prices[symbol].last_price
            self.data[symbol].update(stock, last_price)
            
            # check if data for each factor are ready    
            if not self.data[symbol].is_ready():
                continue
            
            # get symbol data object
            symbol_obj = self.data[symbol]
            
            # calculate and store each factor for current stock
            ear_per_share_to_price[symbol] = symbol_obj.calc_ear_per_share_to_price()
            sales_per_share[symbol] = symbol_obj.calc_sales_per_share()
            book_value_to_price[symbol] = symbol_obj.calc_book_value_to_price()
            earnings_to_price[symbol] = symbol_obj.calc_earnings_to_price()
            sales_to_price[symbol] = symbol_obj.calc_sales_to_price()
            momentum[symbol] = self.prices[symbol].momentum()
        
    # make sure data are consecutive    
    self.last_selection = [x.Symbol for x in selected]
    
    # can't perform decile selection after winsorization 
    if len(ear_per_share_to_price)  None:
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
    
def WinsorizeAndStandardize(self, stock_dict):
    # check if dictionary can be divided into 5% segments
    if len(stock_dict)  float:
    score = {}
    
    # calculate score for each stock as mean of values in dictionaries
    for symbol in dict_1:
        # calculate score value
        score_value = np.mean([dict_1[symbol], dict_2[symbol], dict_3[symbol]])
        # store score value in score dictionary under stock symbol
        score[symbol] = score_value
        
    # return dictionary with score values and stock keys
    return score
    
def Selection(self) -> None:
    # yearly selection
    if self.months_counter % 12 == 0:
        self.selection_flag = True
    self.months_counter += 1
# https://gist.github.com/wonderbeyond/d293e7a2af1de4873f2d757edd580288
def rgetattr(self, obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))
