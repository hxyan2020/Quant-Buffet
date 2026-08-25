# Original QuantConnect / library Python
# locale=en slug="betting-against-uncertainty-beta-in-us-hedge-funds"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict, Tuple
import numpy as np
import data_tools
import statsmodels.api as sm
# endregion
class BettingAgainstUncertaintyBetainUSHedgeFunds(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.m_period:int = 36 + 1
    self.SetWarmUp(self.m_period * 31, Resolution.Daily)
    self.leverage:int = 3
    self.quantile:int = 10
    
    self.predictive_variables:List[Symbol] = [
        self.AddData(data_tools.NasdaqDataValue, 'FRED/GDP', Resolution.Daily).Symbol,                        # US GDP
        self.AddData(data_tools.FREDData, 'BAA10YM', Resolution.Daily).Symbol,                                # default spread
        self.AddData(data_tools.FREDData, 'REAINTRATREARAT1MO', Resolution.Daily).Symbol,                     # real interest rate
        self.AddData(data_tools.NasdaqDataValue, 'MULTPL/SP500_DIV_YIELD_MONTH', Resolution.Daily).Symbol,    # S&P 500 aggregate dividend yield
        self.AddData(data_tools.NasdaqDataValue, 'RATEINF/CPI_USA', Resolution.Daily).Symbol,                 # monthly inflation rate
        self.AddData(data_tools.NasdaqDataValue, 'FRED/T10Y3M', Resolution.Daily).Symbol,                     # term spread
        self.AddData(data_tools.NasdaqDataValue, 'FRED/UNRATE', Resolution.Daily).Symbol,                     # US monthly unemployment rate
    ]
    self.gdp_symbol:Symbol = self.predictive_variables[0]
    self.symbol_count:int = 500
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/mutual_funds/500_mutual_funds_tickers.csv')
    ticker_file_str = ticker_file_str.replace('\r', '')
    self.tickers:List[str] = ticker_file_str.split('\n')[:self.symbol_count]
    self.policy_uncertainty_symbol:Symbol = self.AddData(data_tools.EconomicPolicyUncertainty, 'US_ECONOMIC_POLICY_UNCERTAINTY', Resolution.Daily).Symbol
    
    self.max_missing_days:int = 31
    self.price_max_missing_days:int = 5
    self.gdp_max_missing_days:int = 3*31
    self.monthly_data:Dict[Symbol, data_tools.SymbolData] = {}
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.monthly_data[self.market] = data_tools.SymbolData(self.market, self.m_period)
    for t in self.tickers:
        data = self.AddData(data_tools.MutualFund, t, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        self.monthly_data[data.Symbol] = data_tools.SymbolData(data.Symbol, self.m_period)
    for symbol in self.predictive_variables + [self.policy_uncertainty_symbol]:
        self.monthly_data[symbol] = data_tools.SymbolData(data.Symbol, self.m_period)
    self.recent_month:int = -1
def OnData(self, data: Slice) -> None:
    rebalance_flag:bool = False
    # store monthly prices
    for ticker in self.tickers + [self.market]:
        if data.ContainsKey(ticker) and data[ticker] and data[ticker].Value != 0:
            # monthly rebalance
            if self.Time.month != self.recent_month and self.Time.day != 1: # self.Time.day -> wait for custom data load
                self.recent_month = self.Time.month
                rebalance_flag = True
            if rebalance_flag:
                price:float = data[ticker].Value
                symbol:Symbol = self.Symbol(ticker)
                self.monthly_data[symbol].update(price)
    if rebalance_flag and not self.IsWarmingUp:
        beta:Dict[Symbol, float] = {}
        # store regression data
        if all(self.Securities.ContainsKey(symbol) and self.Securities[symbol].Price != 0. for symbol in self.predictive_variables + [self.policy_uncertainty_symbol]):
            if all(self.monthly_data[symbol].data_still_comming_in(self, self.max_missing_days if symbol != self.gdp_symbol else self.gdp_max_missing_days)  for symbol in self.predictive_variables + [self.policy_uncertainty_symbol]):
                for symbol in self.predictive_variables + [self.policy_uncertainty_symbol]:
                    val:float = self.Securities[symbol].Price
                    self.monthly_data[symbol].update(val)
            else:
                for symbol in self.predictive_variables + [self.policy_uncertainty_symbol]:
                    self.monthly_data[symbol].reset()
            
            # perform EPU regression
            if all(self.monthly_data[symbol].is_ready() for symbol in self.predictive_variables + [self.policy_uncertainty_symbol]):
                y:np.ndarray = self.monthly_data[self.policy_uncertainty_symbol].get_regression_data(False)[::-1]
                x:np.ndarray = np.array([self.monthly_data[symbol].get_regression_data(False)[::-1] for symbol in self.predictive_variables])
                model = self.multiple_linear_regression(x, y)
                epu_index:np.ndarray = model.resid
                market_returns:np.ndarray = self.monthly_data[self.market].get_regression_data(True)
                for ticker in self.tickers:
                    symbol:Symbol = self.Symbol(ticker)
                    if self.monthly_data[symbol].is_ready() and self.monthly_data[symbol].data_still_comming_in(self, self.price_max_missing_days):
                        fund_returns:np.ndarray = self.monthly_data[symbol].get_regression_data(True)
                        
                        # perform EPU beta regression
                        model = self.multiple_linear_regression(np.array([market_returns, epu_index[-len(market_returns):]]), fund_returns)
                        beta[symbol] = model.params[-1]
        long:List[Symbol] = []
        if len(beta) >= self.quantile:
            # sort by beta
            sorted_by_beta:List[Tuple] = sorted(beta.items(), key=lambda x: x[1], reverse=True)
            quantile:int = int(len(sorted_by_beta) / self.quantile)
            long = [x[0] for x in sorted_by_beta[-quantile:]]
        # liquidate
        invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
        for symbol in invested:
            if symbol not in long:
                self.Liquidate(symbol)
        
        # order execution
        for symbol in long:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, 1 / len(long))
def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    x:np.ndarray = x.T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
