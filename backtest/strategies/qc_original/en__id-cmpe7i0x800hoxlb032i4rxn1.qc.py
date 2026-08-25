# Original QuantConnect / library Python
# locale=en slug="印度市场中的低风险异象策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
import data_tools
import statsmodels.api as sm
import numpy as np
# endregion
class LowRiskAnomalyinIndia(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(10000000) # INR
    self.price_period:int = 36 * 21
    self.data:Dict[Symbol, data_tools.SymbolData] = {}
    self.tickers_to_ignore:List[str] = ['TATAMTRDVR', 'LODHA']
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/india_stocks/nse_100_tickers.csv')
    ticker_lines:List[str] = ticker_file_str.split('\r\n')
    tickers = [ ticker_line.split(',')[0] for ticker_line in ticker_lines[1:] ]
    self.quantile:int = 3
    self.leverage:int = 5
    self.beta_p_target:float = 1.
    self.leverage_cap:float = 3.
    for t in tickers:
        # price data subscription
        if t in self.tickers_to_ignore:
            continue
        data:Security = self.AddData(data_tools.IndiaStocks, t, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        stock_symbol:Symbol = data.Symbol
        self.data[stock_symbol] = data_tools.SymbolData(stock_symbol, self.price_period)
    
    self.recent_month:int = -1
def OnData(self, data: Slice) -> None:
    price_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaStocks.get_last_update_date()
    # custom data still comming in
    if all([self.Securities[x].GetLastData() for x in list(self.data.keys())]) and any([self.Time.date() >= price_last_update_date[x] for x in price_last_update_date]):
        self.Liquidate()
        return
    # store daily price data
    for price_symbol, symbol_data in self.data.items():
        if price_symbol in data and data[price_symbol] and data[price_symbol].Value != 0:
            price:float = data[price_symbol].Value
            self.data[price_symbol].update_price(price)
    
    # montly rebalance
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    volatility_by_symbol:Dict[Symbol, float] = {symbol: symbol_data.get_volatility() for symbol, symbol_data in self.data.items() if symbol_data.prices_ready()}
    asset_returns_dict:Dict[Symbol, np.ndarray] = {symbol : symbol_data.get_returns() for symbol, symbol_data in self.data.items() if symbol_data.prices_ready()}
    asset_returns:List[float] = list(zip(*[[i for i in x] for x in asset_returns_dict.values()]))
    market_returns:List[float] = [np.average(x) for x in asset_returns]
    if len(asset_returns) == 0:
        return
    # run stock regression
    x:np.ndarray = np.array(market_returns)
    y:np.ndarray = np.array(asset_returns)
    model = self.multiple_linear_regression(x, y)
    beta_values:np.ndarray = model.params[1]
    # store betas
    beta_by_symbol:Dict[Symbol, float] = {sym : beta_values[n] for n, sym in enumerate(list(asset_returns_dict.keys()))}
    if len(volatility_by_symbol)
