# Original QuantConnect / library Python
# locale=en slug="通过市场价格预测国家估值策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from dateutil.relativedelta import relativedelta
from pandas.core.frame import DataFrame
from io import StringIO
import statsmodels.api as sm
# endregion
class PriceBasedQuantitativeStrategyforCountryValuation(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.period:int = 1
    self.look_back_period:int = 5
    self.leverage:int = 4
    self.holding_period:int = 4
    self.stocks_to_liquidate:List[HoldingItem] = []
    etf_list:List[str] = ['EWU', 'EWG', 'EWQ', 'EWI', 'EWD', 'EWN', 'EWP', 'EWK', 'EWL', 'EWC', 'EWJ', 'EWW', 'EWM', 'EWA', 'EWS', 'EWY', 'EWT', 'EWZ', 'EZA', 'FXI', 'INDY']
    # subscribe data
    self.etf_symbols:List[Symbol] = [self.AddEquity(ticker, Resolution.Daily).Symbol for ticker in etf_list]
    [self.Securities[symbol].SetLeverage(self.leverage) for symbol in self.etf_symbols]
    
    # load data from csv
    load:str = self.Download(f'data.quantpedia.com/backtesting_data/equity/msci.csv')
    self.etf_df:DataFrame = pd.read_csv(StringIO(load), delimiter=';')
    self.etf_df['Date (performance k)'] = pd.to_datetime(self.etf_df['Date (performance k)'])
    self.etf_df = self.etf_df.groupby(pd.Grouper(key='Date (performance k)', freq='MS')).last()
    self.current_month:int = -1
def OnData(self, data: Slice):
    # quarterly rebalance
    if self.Time.month % 3 != 0: 
        return
    if self.Time.month == self.current_month:
        return
    self.current_month = self.Time.month
    # check if all etf data are available from QC
    if not all(symbol in data and data[symbol] for symbol in self.etf_symbols):
        return
    
    # get last 5 years of data
    qc_history:DataFrame = self.History(self.etf_symbols, start=self.Time.date() - relativedelta(years=self.look_back_period), end=self.Time.date()).close.unstack(level=0)
    df_custom_data:DataFrame = self.etf_df.loc[self.Time.date() - relativedelta(years=self.look_back_period):self.Time.date()]
    qc_history:DataFrame = qc_history.groupby(pd.Grouper(freq='MS')).last()
    qc_history = qc_history.pct_change()[1:]
    y:np.ndarray = qc_history.values if len(qc_history.dropna(axis=1, how='any').columns) >= len(self.etf_symbols) else df_custom_data.values
    x:np.ndarray = qc_history.mean(axis=1).values if len(qc_history.dropna(axis=1, how='any').columns) >= len(self.etf_symbols) else df_custom_data.mean(axis=1).values
    # run stock regression
    model = self.multiple_linear_regression(x, y)
    alpha_values:np.ndarray = model.params[0]
    # store alpha
    alpha_by_symbol:Dict[Symbol, float] = {sym : alpha_values[n] for n, sym in enumerate(list(qc_history.columns))}
    if len(alpha_by_symbol) == 0:
        return
    # sort by alpha
    sorted_alpha:List[Symbol] = sorted(alpha_by_symbol, key=alpha_by_symbol.get)
    long:List[Symbol] = [sorted_alpha[0]]
    short:List[Symbol] = [sorted_alpha[-1]]
    traded_portfolio_portion:Dict[Symbol, float] = {}
    for symbol in long:
        traded_portfolio_portion[symbol] = (1 / len(long)) * (self.Portfolio.TotalPortfolioValue / self.holding_period)
    
    for symbol in short:
        traded_portfolio_portion[symbol] = (-1 / len(short)) * (self.Portfolio.TotalPortfolioValue / self.holding_period)
    items_to_remove:List[HoldingItem] = []
    # execute order and hold for holding period
    for item in self.stocks_to_liquidate:
        item._holding_period += 1
        if item._holding_period >= self.holding_period:
            self.MarketOrder(item._symbol, -item._quantity)
            items_to_remove.append(item)    
    # remove from collection
    for item in items_to_remove:
        self.stocks_to_liquidate.remove(item)  
    # execute order
    for price_symbol, portfolio_portion in traded_portfolio_portion.items():
        if price_symbol in data and data[price_symbol]:
            final_quantity:int = portfolio_portion // data[price_symbol].Price
            if portfolio_portion != 0:
                self.MarketOrder(price_symbol, final_quantity)
                self.stocks_to_liquidate.append(HoldingItem(price_symbol, final_quantity))
def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    x = sm.add_constant(x, has_constant='add')
    result = sm.OLS(endog=y, exog=x).fit()
    return result

class HoldingItem():
def __init__(self, symbol:Symbol, quantity:float):
    self._symbol = symbol  
    self._quantity = quantity
    self._holding_period = 0
