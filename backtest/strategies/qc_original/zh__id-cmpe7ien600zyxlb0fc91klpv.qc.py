# Original QuantConnect / library Python
# locale=zh slug="货币投资组合优化策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import data_tools
from scipy.optimize import minimize
#endregion
class OptimizedCurrencyPortfolios(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2007, 1, 1)
    self.SetCash(100000)
    
    # currency future symbol and interbank rate
    self.symbols:dict[str, str] = {
        'CME_AD1' : 'IR3TIB01AUM156N',   # Australian Dollar Futures, Continuous Contract #1
        'CME_CD1' : 'IR3TIB01CAM156N',   # Canadian Dollar Futures, Continuous Contract #1
        'CME_SF1' : 'IR3TIB01CHM156N',   # Swiss Franc Futures, Continuous Contract #1
        'CME_EC1' : 'IR3TIB01EZM156N',   # Euro FX Futures, Continuous Contract #1
        'CME_BP1' : 'LIOR3MUKM',         # British Pound Futures, Continuous Contract #1
        'CME_JY1' : 'IR3TIB01JPM156N',   # Japanese Yen Futures, Continuous Contract #1
        'CME_NE1' : 'IR3TIB01NZM156N',   # New Zealand Dollar Futures, Continuous Contract #1 # data are from 2006
        'CME_MP1' : 'IR3TIB01MXM156N',   # Mexican Peso Futures, Continuous Contract #1
        }
    self.m_momentum_period:int = 3+1
    self.m_reversal_period:int = 5*12+1
    self.SetWarmUp(self.m_reversal_period*21, Resolution.Daily)
    self.monthly_price_data:dict = {}
    self.gamma:float = 5.
    self.futures_max_missing_days:int = 5
    self.ir_max_missing_days:int = 31
    
    # characteristics names
    self.characteristics:list[str] = ['sign', 'fd', 'mom', 'rev']
    self.characteristics_by_symbol:dict[str, pd.DataFrame] = {}
    self.performance_df:pd.DataFrame = pd.DataFrame(columns=list(self.symbols.keys()))
    # optimalization setup
    self.opt_period:int = 60
    for currency_future, cash_rate_symbol in self.symbols.items():
        # currency futures data
        data:Security = self.AddData(data_tools.QuantpediaFutures, currency_future, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(10)
        
        # interbank rate data
        self.AddData(data_tools.InterestRate3M, cash_rate_symbol, Resolution.Daily)
        # price data
        self.monthly_price_data[currency_future] = RollingWindow[float](self.m_reversal_period)
        
        # characteristics by symbol
        self.characteristics_by_symbol[currency_future] = pd.DataFrame(columns=self.characteristics)
    # USD interbank rate data
    self.usd_ir:Symbol = self.AddData(data_tools.InterestRate3M, 'IR3TIB01USM156N', Resolution.Daily).Symbol
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.recent_month:int = -1
    self.month_counter:int = 0
def OnData(self, data):
    rebalance_flag:bool = False
    sign:dict[str, int] = {}
    fd_by_currency:dict[str, float] = {}
    fd:dict[str, float] = {}
    mom:dict[str, float] = {}
    rev:dict[str, float] = {}
    performance:dict[str, float] = {}
    ir_last_update_date:Dict[str, datetime.date] = data_tools.InterestRate3M.get_last_update_date()
    qp_futures_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()
    for currency, rate in self.symbols.items():
        if currency in data and data[currency]:
            foo=3
    if self.usd_ir in data and data[self.usd_ir]:
        # rebalance once a month, once new interbank data comes in
        if self.Time.month != self.recent_month:
            rebalance_flag = True
            for currency_future, cash_rate_symbol in self.symbols.items():
                # interbank rate data is present in the algorithm
                if cash_rate_symbol in data and data[cash_rate_symbol]:
                    # making sure custom futures data is still comming in
                    if not self.Securities[currency_future].GetLastData() and qp_futures_last_update_date[currency_future] > self.Time.date():
                        continue
                    
                    # store monthly price data
                    if self.Securities[currency_future].Price != 0:
                        self.monthly_price_data[currency_future].Add(self.Securities[currency_future].Price)
                    if self.monthly_price_data[currency_future].IsReady:
                        # calculate variables
                        sign[currency_future] = 1 if data[cash_rate_symbol].Value > data[self.usd_ir].Value else -1
                        # only partial information for fd variable
                        fd_by_currency[currency_future] = data[cash_rate_symbol].Value
                        mom[currency_future] = self.monthly_price_data[currency_future][0] / self.monthly_price_data[currency_future][self.m_momentum_period-1] - 1
                        
                        # three months is excluded to avoid unnecessary correlation with the momentum variable
                        rev[currency_future] = self.monthly_price_data[currency_future][self.m_momentum_period-1] / self.monthly_price_data[currency_future][self.m_reversal_period-1] - 1
                        
                        performance[currency_future] = self.monthly_price_data[currency_future][0] / self.monthly_price_data[currency_future][1] - 1
            
    else:
        # IR data stopped comming in
        if not any(self.Securities[x] for x in list(self.symbols.keys())) and any(ir_futures_last_update_date[x] = self.opt_period:
            # optimize portfolio policy and calculate weights for the next year
            opt = self.optimization_method(self.performance_df, self.characteristics_by_symbol, self.characteristics, self.opt_period, self.gamma)[1]
            weights = { symbol : np.sum(self.characteristics_by_symbol[symbol].iloc[-1].values * opt.values) / len(self.symbols) for symbol in self.symbols }
        # trade execution
        invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
        for symbol in invested:
            if symbol not in weights:
                self.Liquidate(symbol)
        
        for symbol, w in weights.items():
            self.SetHoldings(symbol, w)
def standardize_dict(self, dict_to_standardize:dict) -> dict:
    ''' cross-sectional standardization '''
    dict_values:list[float] = list(dict_to_standardize.values())
    result:dict = { key : (value - np.mean(dict_values)) / np.std(dict_values) for key, value in dict_to_standardize.items() }
    return result
def optimization_method(self, returns:pd.DataFrame, characteristics_dict:dict, characteristics:list, opt_period:int, gamma:float):
    ''' parametric portfolio policy optimization '''
    size:int = len(characteristics)
    
    # objective function
    fun = lambda weights: self.opt_fun(returns, characteristics_dict, weights, gamma, opt_period)
    # Constraint #1: The weights adds up to 1
    # constraints:list = [{'type': 'eq', 'fun': lambda w: 1 - np.sum(w)}]
    constraints:list = []
    bounds:tuple = tuple((-1, 1) for x in range(size))
    # initial parametric portfolio policy
    x0:np.ndarray = np.array(size * [1. / size])
    opt = minimize(fun,                         # Objective function
                   x0,                          # Initial guess
                   method='SLSQP',              # Optimization method:  Sequential Least Squares Programming
                   bounds = bounds,             # Bounds for variables 
                   constraints = constraints)   # Constraints definition
    return opt, pd.Series(opt['x'], index = characteristics)
    
def opt_fun(self, returns:pd.DataFrame, characteristics:dict, weights:np.ndarray, gamma:float, opt_period:int):
    symbols:list[str] = list(returns.columns)
    df_dict:dict[str, pd.Series] = {}
    for symbol in symbols:
        relevant_c:pd.DataFrame = characteristics[symbol].iloc[-opt_period:-1]
        # product of weights and performance
        adj_w:np.ndarray = (relevant_c.multiply(weights, axis=1).sum(axis=1) / len(symbols)).reset_index(drop=True)
        relevant_perf:pd.Series = returns[symbol].iloc[-(opt_period-1):].reset_index(drop=True)
        monthly_returns:pd.Series = adj_w * relevant_perf
        df_dict[symbol] = monthly_returns
    adj_perf_df:pd.DataFrame = pd.DataFrame(df_dict)
    portfolio_perf:float = np.sum(adj_perf_df, axis=1)
    
    # calculate equity
    init_eq:float = 1.
    eq:float = init_eq
    for ret in portfolio_perf.values:
        eq = eq * (1 + ret)
    portfolio_return:float = eq / init_eq - 1.
    
    # power utility as the objective function
    utility = ((portfolio_return) ** (1-gamma)) / (1-gamma)
    return -utility
