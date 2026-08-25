# Original QuantConnect / library Python
# locale=zh slug="股票中的质量因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import math
from AlgorithmImports import *
import numpy as np
import statsmodels.api as sm
import pandas as pd
from numpy import isnan
from functools import reduce
import data_tools
class QualityFactorInStocks(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.weight:Dict[Symbol, float] = {}
    self.data:Dict[Symbol, Dict] = {}
    self.prices:Dict[Symbol, RollingWindow] = {}
    self.symbol_data = {}
    
    self.last_fine:List[Symbol] = []
    self.financial_statement_names:List[str] = [
        'FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths',
        'ValuationRatios.CFOPerShare',
        'OperationRatios.GrossMargin.ThreeMonths',
        'FinancialStatements.IncomeStatement.GrossProfit.ThreeMonths',
        'FinancialStatements.CashFlowStatement.Depreciation.ThreeMonths',
        'FinancialStatements.CashFlowStatement.ChangeInWorkingCapital.ThreeMonths',
        'OperationRatios.ROE.ThreeMonths',
        'OperationRatios.ROA.ThreeMonths',
        'FinancialStatements.BalanceSheet.TotalDebt.ThreeMonths',
        'EarningReports.BasicAverageShares.ThreeMonths',
        'ValuationRatios.PayoutRatio',
    ]
    self.period:int = 12
    self.five_year_change_period:int = 12 * 5
    self.regression_period:int = 3 * 12 * 21
    self.targeted_volatility:float = 0.10
    self.vol_target_period:int = 60
    self.leverage_cap:int = 4
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.leverage:int = 5
    self.min_share_price:float = 5.
    
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.prices[self.symbol] = RollingWindow[float](self.regression_period)
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
   
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)   
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # store daily price
        if symbol in self.prices:
            self.prices[symbol].Add(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected: List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Symbol != self.symbol
        and x.Price > self.min_share_price and x.SecurityReference.ExchangeId in self.exchange_codes 
        and all((not isnan(self.rgetattr(x, statement_name)) and self.rgetattr(x, statement_name) != 0) for statement_name in self.financial_statement_names)
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # Create dictionary with list for each rank values from stocks
    total_ranks = {
        'CFOA': [], 'GM': [],
        'GPOA': [], 'LA': [],
        'ROA': [], 'ROE': [],
        'NDI': [], 'NEI': [],
        'TNPOP': [], 'CFOA5': [],
        'GM5': [], 'GPOA5': [],
        'LA5': [], 'ROA5': [],
        'ROE5': [],
    }
    symbols_with_anomalies = [] # Storing symbols of stocks, which have anomalies
    # warmup price rolling windows
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.prices:
            self.prices[symbol] = RollingWindow[float](self.regression_period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes = history.loc[symbol].close
            for time, close in closes.items():
                self.prices[symbol].Add(close)
        
        if self.prices[symbol].IsReady:
            # Create dictionary for stock if it doesn't exist
            if symbol not in self.data:
                self.data[symbol] = {}
            
            # Create SymbolData object for storing mutiple needed data for anomalies calculation
            # SymbolData object has to be create, when symbol isn't in self.last_fine, to make data consecutive
            if symbol not in self.symbol_data or symbol not in self.last_fine:
                self.symbol_data[symbol] = data_tools.SymbolData(self.period, self.five_year_change_period)
                
            # Compute current anomalies
            current_ta = stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths
            current_cfoa = stock.ValuationRatios.CFOPerShare / current_ta
            current_gm = stock.OperationRatios.GrossMargin.ThreeMonths
            current_gpoa = stock.FinancialStatements.IncomeStatement.GrossProfit.ThreeMonths / current_ta
            current_la = (stock.FinancialStatements.CashFlowStatement.Depreciation.ThreeMonths - stock.FinancialStatements.CashFlowStatement.ChangeInWorkingCapital.ThreeMonths) / current_ta
            current_roa = stock.OperationRatios.ROA.ThreeMonths
            current_roe = stock.OperationRatios.ROE.ThreeMonths
            
            # Update values in SymbolData object
            self.symbol_data[symbol].update(
                current_ta,
                current_cfoa,
                current_gm,
                current_gpoa,
                current_la,
                current_roa,
                current_roe,
                stock.FinancialStatements.BalanceSheet.TotalDebt.ThreeMonths,
                stock.EarningReports.BasicAverageShares.ThreeMonths
            )
            
            # Check if data in SymbolData object are ready, then check if data are consecutive    
            if not self.symbol_data[symbol].is_ready() or symbol not in self.last_fine:
                continue
            # If stock has data ready, add it's symbol to list
            symbols_with_anomalies.append(symbol)
            
            # Calculate factors for current stocks
            # Cash flow over asset
            self.data[symbol]['CFOA'] = current_cfoa
            # Gross margin
            self.data[symbol]['GM'] = current_gm
            # Gross profit over assets
            self.data[symbol]['GPOA'] = current_gpoa
            # Low accruals
            self.data[symbol]['LA'] = current_la
            # Return on assets
            self.data[symbol]['ROA'] = current_roa
            # Return on equity
            self.data[symbol]['ROE'] = current_roe
            # # Net debt issuance
            self.data[symbol]['NDI'] = self.symbol_data[symbol].net_debt_issuance()
            # # Net equity issuance
            self.data[symbol]['NEI'] = self.symbol_data[symbol].net_equity_issuance()
            # Total net payouts over profits
            self.data[symbol]['TNPOP'] = stock.ValuationRatios.PayoutRatio
            # Cash flow over assets (5y change)
            self.data[symbol]['CFOA5'] = self.symbol_data[symbol].cfoa_change()
            # Gross margin (5y change)
            self.data[symbol]['GM5'] = self.symbol_data[symbol].gm_change()
            # Gross profits over assets (5y change)
            self.data[symbol]['GPOA5'] = self.symbol_data[symbol].gpoa_change()
            # Low accruals (5y change)
            self.data[symbol]['LA5'] = self.symbol_data[symbol].la_change()
            # Return on assets (5y change)
            self.data[symbol]['ROA5'] = self.symbol_data[symbol].roa_change()
            # Return on equity (5y change)
            self.data[symbol]['ROE5'] = self.symbol_data[symbol].roe_change()
            
            self.AddValuesToRanks(total_ranks, self.data[symbol])
    
    # Change last fine, to make sure data are consecutive
    self.last_fine = [x.Symbol for x in selected]
    
    # Check if there was at least one stock with all anomalies
    if len(symbols_with_anomalies) == 0:
        return Universe.Unchanged
    
    z_score = {}
        
    for symbol in symbols_with_anomalies:
        # Storing z score for each rank for current stock
        z_score[symbol] = []
        
        for rank_symbol, stock_rank in self.data[symbol].items():
            # μr is the mean of ranks 
            mean_of_ranks = np.mean(total_ranks[rank_symbol])
            # σr is the standard deviation of ranks
            std_of_ranks = np.std(total_ranks[rank_symbol])
            # z = (r – μr)/ σr
            z_score[symbol].append((stock_rank - mean_of_ranks) / std_of_ranks)
    
    avg_z_score = {} # Storing average z-score for each stock
    avg_z_scores = []  # Storing all average z-scores for next calculation
    
    for symbol in z_score:
        # Compute and store average z-score for each stock
        average_z_score = np.mean(z_score[symbol])
        avg_z_score[symbol] = average_z_score
        avg_z_scores.append(average_z_score)
    
    long = [] # There goes stocks with positive final z-score
    short = [] # There goes stocks with negative final z-score
    
    betas = {} # Storing beta from regression for each stock
    final_z_score = {} # Storing final z-score for each stock
    
    if self.prices[self.symbol].IsReady:
        
        # Compute final z_score for weighting
        for symbol, avg_z_score in avg_z_score.items():
            # μr is the mean of average z-scores 
            mean_of_avg_z_scores = np.mean(avg_z_scores)
            # σr is the standard deviation of average z-scores
            std_of_avg_z_scores = np.std(avg_z_scores)
            # z = (r – μr)/ σr
            res_z_score = (avg_z_score - mean_of_avg_z_scores) / std_of_avg_z_scores
            
            # Based on last z-score of stock go long or short
            if res_z_score >= 0:
                long.append(symbol)
            else:
                short.append(symbol)
            
            # Store final z-score under stock symbol
            final_z_score[symbol] = res_z_score
            
            # Compute beta for each stock in regression, where y = stock price and x = market price
            regression_model = self.MultipleLinearRegression([x for x in self.prices[self.symbol]], [x for x in self.prices[symbol]])
            # Store beta
            betas[symbol] = regression_model.params[-1]
            
    # BetaLong = sum(z-score * beta)
    beta_long = sum([(final_z_score[x] * betas[x]) for x in long])
    # BetaShort = -sum(z-score * beta)
    beta_short = -sum([(final_z_score[x] * betas[x]) for x in short])
    
    # Volatility weighting long and short leg separately.
    ls_leverage = [] # long and short leverage
    daily_returns = { x : pd.Series([x for x in self.prices[x]][:self.vol_target_period][::-1]).pct_change().dropna() for x in long+short if self.prices[x].IsReady}
    volatility = { x :  np.std(daily_returns[x]) * np.sqrt(252) for x in long+short if x in daily_returns}
    
    # Compute weights for stocks
    for symbols in [long, short]:
        df = pd.DataFrame()
        i = 0
        for symbol in symbols:
            self.weight[symbol] = betas[symbol] / beta_long
            df[str(symbol)] = [x for x in daily_returns[symbol]]
            i += 1
        # volatility targeting
        weights = np.array([self.weight[x] for x in symbols])  # releveant long or short weights
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(df.cov() * 252, weights.T)))
        leverage = self.targeted_volatility / portfolio_vol
        leverage = min(self.leverage_cap, leverage) # cap max leverage
        ls_leverage.append(leverage)
    
    # adjust weights by leverage
    for symbol in long:
        self.weight[symbol] *= ls_leverage[0]  # long leverage
    for symbol in short:
        self.weight[symbol] *= ls_leverage[1]  # short leverage
    
    return long + short
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
def AddValuesToRanks(self, total_ranks, symbol_dict):
    # Append each value of stock rank into dictionary with all ranks values from fine universe
    for rank_symbol, stock_rank in symbol_dict.items():
        total_ranks[rank_symbol].append(stock_rank)
        
def MultipleLinearRegression(self, x, y):
    x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
def rgetattr(self, obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))
