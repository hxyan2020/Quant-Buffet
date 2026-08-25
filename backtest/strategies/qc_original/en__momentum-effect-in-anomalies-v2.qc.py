# Original QuantConnect / library Python
# locale=en slug="momentum-effect-in-anomalies-v2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
import statsmodels.api as sm
from typing import Dict, List
from numpy import isnan

class MomentumEffectInAnomaliesV2(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.quantile:int = 3
    self.quantile_2:int = 10
    self.min_share_price:int = 1
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']

    self.days_in_month:int = 21
    self.period:int = 6 * self.days_in_month # 6 months of daily closes
    self.anomalies_count:int = 1 # Change to three  # Investor goes long on the three best-performing anomalies and short on the three worst-performing anomalies
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.traded_quantity:Dict[Symbol, float] = {}
    self.accruals_data:Dict[Symbol, StockData] = {}
    
    # If this list contains anomaly key, then select top quantile based on anomaly values 
    self.highest:List[str] = ['MOM', 'GP', 'ROA', 'BM'] # SUE
    
    self.anomalies:Dict[str, dict] = {
        # Failure probability # Too complicated
        # O-score
        # Composite Equity Issuance
        # Abnormal Capital Investment
        "IV": {},# Idiosyncratic Volatility
        # Analyst Dispersion # fine.EarningReports.BasicEPS.OneMonth # 
        # Market Illiquidity
        "AG": {}, # AssetsGrowth is name of the anomaly and it's value is stored in TotalAssets
        "BM": {}, # Book to market = 1 / PBRatio
        "GP": {}, # Gross Profitability = (TotalRevenue + CostOfGoods) / TotalAssets
        "MOM": {}, # Momentum from m-6 to m-m 1
        "NSI": {}, # Net stock issuance
        "ACC": {}, # Accruals
        "ROA": {}, # Return on assets
        #  "SUE": {} Standardized unexpected earnings,
        # NOA = {} # Net operating assets. Missing Total Debt in current Liabilities, TotalPreferredStock(capital), TotalCommonStockEquity
    }
    
    # Needed for Idiosyncratic Volatility
    self.last_market_factor:Union[None, dict] = None # long only dict
    self.last_size_factor:Union[None, List[Symbol]] = None # long/short list
    self.last_value_factor:Union[None, List[Symbol]] = None # long /short list
    
    self.symbol:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 500

    self.selection_flag:bool = False
    self.start_month:int = self.Time.month
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)

    self.settings.daily_precise_end_time = False

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update RollingWindow each day
    for stock in fundamental:
        symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    
    # Select each month
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected: List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.Market == 'usa'
        and not isnan(x.ValuationRatios.CFOPerShare) and x.ValuationRatios.CFOPerShare > 0
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentAssets.Value) and x.FinancialStatements.BalanceSheet.CurrentAssets.Value > 0
        and not isnan(x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value) and x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value > 0
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentLiabilities.Value) and x.FinancialStatements.BalanceSheet.CurrentLiabilities.Value > 0
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentDebt.Value) and x.FinancialStatements.BalanceSheet.CurrentDebt.Value > 0
        and not isnan(x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value) and x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value > 0
        and not isnan(x.FinancialStatements.BalanceSheet.GrossPPE.Value) and x.FinancialStatements.BalanceSheet.GrossPPE.Value > 0
        and not isnan(x.ValuationRatios.TotalAssetPerShare) and x.ValuationRatios.TotalAssetPerShare > 0
        and not isnan(x.FinancialStatements.BalanceSheet.AccountsReceivable.Value) and x.FinancialStatements.BalanceSheet.AccountsReceivable.Value > 0
        and not isnan(x.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value) and x.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value > 0
        and not isnan(x.MarketCap) and x.MarketCap != 0
        and not isnan(x.ValuationRatios.PBRatio) and x.ValuationRatios.PBRatio != 0
        and not isnan(x.FinancialStatements.BalanceSheet.TotalAssets.Value) and x.FinancialStatements.BalanceSheet.TotalAssets.Value != 0
        and not isnan(x.OperationRatios.ROA.Value) and x.OperationRatios.ROA.Value != 0
        and not isnan(x.FinancialStatements.IncomeStatement.CostOfRevenue.Value) and x.FinancialStatements.IncomeStatement.CostOfRevenue.Value != 0
        and not isnan(x.FinancialStatements.IncomeStatement.TotalRevenue.Value) and x.FinancialStatements.IncomeStatement.TotalRevenue.Value != 0
        and x.SecurityReference.ExchangeId in self.exchange_codes
    ]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    market_cap:Dict[Symbol, float] = {}
    value_factor:Dict[Symbol, float] = {}
    
    for stock in selected:
        symbol:Symbol = stock.Symbol

        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)

        if not self.data[symbol].is_ready():
            continue
    
        # Store monthly market capitalizations.
        # Store stock's data for next factor creation
        market_cap[symbol] = stock.MarketCap
        value_factor[symbol] = stock.ValuationRatios.PBRatio
        
        # Storing last accruals data
        if symbol not in self.accruals_data:
            self.accruals_data[symbol] = None
                    
        # Accrual calc.
        current_accruals_data:StockData = StockData(stock.FinancialStatements.BalanceSheet.CurrentAssets.Value, stock.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value,
                                                stock.FinancialStatements.BalanceSheet.CurrentLiabilities.Value, stock.FinancialStatements.BalanceSheet.CurrentDebt.Value, stock.FinancialStatements.BalanceSheet.IncomeTaxPayable.Value,
                                                stock.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value, stock.FinancialStatements.BalanceSheet.TotalAssets.Value,
                                                stock.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value)
            
        # There is not previous accruals data.
        if not self.accruals_data[symbol]:
            self.accruals_data[symbol] = current_accruals_data
            
        # Calculate current accruals.
        current_accruals = self.CalculateAccruals(current_accruals_data, self.accruals_data[symbol])
        self.accruals_data[symbol] = current_accruals_data
        
        # Store accruals only if it is possible
        if self.accruals_data[symbol]:
            self.anomalies['ACC'][symbol] = current_accruals
        
        # Calculate Idiosyncracti Volatilty only if it is possible
        if self.last_market_factor and self.last_size_factor and self.last_value_factor:
            self.anomalies['IV'][symbol] = self.CalculateIdiosyncraticVolatility(symbol)
            
        self.anomalies['AG'][symbol] = stock.FinancialStatements.BalanceSheet.TotalAssets.Value
        self.anomalies['BM'][symbol] = 1 / stock.ValuationRatios.PBRatio
        self.anomalies['MOM'][symbol] = self.data[symbol].momentum(self.period)
        self.anomalies['NSI'][symbol] = stock.FinancialStatements.CashFlowStatement.NetCommonStockIssuance.Value
        self.anomalies['ROA'][symbol] = stock.OperationRatios.ROA.Value
        # Gross Profitability = (TotalRevenue + CostOfGoods) / TotalAssets
        self.anomalies['GP'][symbol] = (stock.FinancialStatements.IncomeStatement.CostOfRevenue.Value + \
                                        stock.FinancialStatements.IncomeStatement.TotalRevenue.Value) / \
                                        stock.FinancialStatements.BalanceSheet.TotalAssets.Value
    
    # Firstly store new factors for Idyosincratic Volatility
    self.StoreNewFactors(market_cap, value_factor)
    
    # Storing anomaly representants under anomaly key from self.anomalies dictionary
    anomaly_representants:Dict[str, float] = {}
    # Storing anomaly performacne for each anomaly representants
    anomaly_performances:Dict[str, float] = {}
    
    for anomaly_key, symbols_dict in self.anomalies.items():
        # Make sure there are enough stocks for quantile selection
        if len(symbols_dict)  None:
    self.selection_flag = True
    
# Fuction stores new factors for Idiosyncratic Volatility
def StoreNewFactors(self, market_cap:dict, value_factor:dict):
    # Firstly check if there are enough data for quantile selection
    if len(market_cap)  float:
    # Calculate daily returns for n + 1 period, to get n daily returns
    regression_y = self.data[symbol].daily_returns(self.days_in_month + 1)
    
    # Create regression x from last market factor, size factor, and value factor
    regression_x = [
            self.DailyPerformanceValueWeight(self.last_market_factor),
            self.FactorDailyPerformance(self.last_size_factor[0], self.last_size_factor[1]),
            self.FactorDailyPerformance(self.last_value_factor[0], self.last_value_factor[1])
    ]
    
    regression_model = self.MultipleLinearRegression(regression_x, regression_y)
    # return result of Idiosyncratic Volatility
    return np.std(regression_model.resid)

# Function calculates daily performacne of market factor 
def DailyPerformanceValueWeight(self, market_cap:dict) -> np.ndarray:
    # Create numpy array with zeros
    total_daily_returns = np.zeros(self.days_in_month)
    
    total_cap = sum([x[1] for x in market_cap.items()])
    for symbol, cap in market_cap.items():
        # Calculate weight for current stock
        weight:float = cap / total_cap
        # Get daily returns of current stock
        # Calculate daily returns for n + 1 period, to get n daily returns
        daily_returns:np.ndarray = self.data[symbol].daily_returns(self.days_in_month + 1)
        # Multiply each daily return by weight
        daily_returns = daily_returns * weight
        # Add daily returns of current stock to total_daily_returns of portfolio
        total_daily_returns += daily_returns
    
    return total_daily_returns
    
# Function calculates daily performance for size or value factor
def FactorDailyPerformance(self, long:List[Symbol], short:List[Symbol]) -> np.ndarray:
    # Create numpy array with zeros
    total_daily_returns:np.ndarray = np.zeros(self.days_in_month)
    
    # Go through each long and short stock.
    # Add daily returns of long stocks and sub daily returns of short stocks.
    for long_sym, short_sym in zip(long, short):
        # Calculate daily returns for n + 1 period, to get n daily returns
        total_daily_returns += self.data[long_sym].daily_returns(self.days_in_month + 1)
        total_daily_returns -= self.data[short_sym].daily_returns(self.days_in_month + 1)
        
    return total_daily_returns
    
def SelectAnomalyRepresentants(self, anomaly_key:dict, symbols_dict:dict) -> List[Symbol]:
    quantile:int = int(len(symbols_dict) / self.quantile_2)
    # Sort dictionary by anomaly values
    sorted_by_dict_value:List[Symbol] = [x[0] for x in sorted(symbols_dict.items(), key=lambda item: item[1])]
    
    # Select top or bottom quantile based on highest or lowest signal in strategy description
    if anomaly_key in self.highest:
        return sorted_by_dict_value[-quantile:]
    else:
        return sorted_by_dict_value[:quantile]
        
def CalculateAnomalyPerformance(self, anomaly_representants:List[Symbol]) -> float:
    stocks_momentums:List[float] = []
    
    # Calculate stock's momentum for each stock in anomaly_representants
    for symbol in anomaly_representants:
        momentum = self.data[symbol].momentum(self.days_in_month)
        stocks_momentums.append(momentum)
        
    return np.mean(stocks_momentums)
    
def CreatePortfolioFromAnomalies(self, anomalies, anomaly_representants):
    portfolio_symbols = []
    
    # Go through each anomaly and add their representants into portfolio_symbols
    for anomaly_key in anomalies:
        for symbol in anomaly_representants[anomaly_key]:
            portfolio_symbols.append(symbol)
            
    return portfolio_symbols
    
def MultipleLinearRegression(self, x, y):
    x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
    
# Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3188172                
def CalculateAccruals(self, current_accrual_data, prev_accrual_data) -> float:
    delta_assets:float = current_accrual_data.CurrentAssets - prev_accrual_data.CurrentAssets
    delta_cash:float = current_accrual_data.CashAndCashEquivalents - prev_accrual_data.CashAndCashEquivalents
    delta_liabilities:float = current_accrual_data.CurrentLiabilities - prev_accrual_data.CurrentLiabilities
    delta_debt:float = current_accrual_data.CurrentDebt - prev_accrual_data.CurrentDebt
    dep:float = current_accrual_data.DepreciationAndAmortization
    total_assets_prev_year:float = prev_accrual_data.TotalAssets
    
    acc:float = (delta_assets - delta_liabilities - delta_cash + delta_debt - dep) / total_assets_prev_year
    return acc
    
class SymbolData():
def __init__(self, period:int):
    self.closes:RollingWindow = RollingWindow[float](period)
    self.last_price:Union[None, float] = None
    
def update(self, close:float):
    self.closes.Add(close)
    self.last_price = close
    
def is_ready(self) -> bool:
    return self.closes.IsReady
    
def momentum(self, period) -> float:
    closes = [x for x in self.closes][:period]
    # Calculate momentum for period
    return (closes[0] - closes[-1]) / closes[-1]
    
def daily_returns(self, period) -> np.ndarray:
    closes = np.array([x for x in self.closes][:period])
    # Calculate daily returns
    return (closes[:-1] - closes[1:]) / closes[1:]
    
class StockData():
def __init__(self, current_assets:float, cash_and_cash_equivalents:float, current_liabilities:float, current_debt:float, income_tax_payable:float, 
                    depreciation_and_amortization:float, total_assets:float, sales:float):
    self.CurrentAssets:float = current_assets
    self.CashAndCashEquivalents:float = cash_and_cash_equivalents
    self.CurrentLiabilities:float = current_liabilities
    self.CurrentDebt:float = current_debt
    self.IncomeTaxPayable:float = income_tax_payable
    self.DepreciationAndAmortization:float = depreciation_and_amortization
    self.TotalAssets:float = total_assets
    
    self.Sales:float = sales
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
