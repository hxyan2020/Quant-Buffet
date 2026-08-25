# Original QuantConnect / library Python
# locale=en slug="value-in-anomalies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
import data_tools
from functools import reduce
class ValueInAnomalies(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data:Dict[Symbol, data_tools.SymbolData] = {}
    self.traded_quantity:Dict[Symbol, float] = {}
    self.accruals_data:Dict[Symbol, data_tools.StockData] = {}
    
    # Creating long and short portfolio according this list.
    self.positive:List[str] = ['PEAD', 'ROA', 'GP', 'BM', 'MOM']
    
    self.anomalies:Dict[str, Dict] = {
        "AG": {}, # TotalAssets
        "BM": {}, # Book to market = 1 / PBRatio
        "GP": {}, # Gross Profitability = (TotalRevenue + CostOfGoods) / TotalAssets
        "MOM": {}, # Twelve month momentum with first month skipped
        "CEI": {}, # log(ME t/ ME t-5) – Return t-5
        "NSI": {}, # Net stock issuance
        "ACC": {}, # Accruals
        "IVA": {}, # Investments to assets = (GrossPPE + ChangeInInventory) / TotalAssets
        "ROA": {}, # Return on assets
        "SIZE": {} # Market capitalization
        # NOA = {} # Net operating assets. Missing Total Debt in current Liabilities, TotalPreferredStock(capital), TotalCommonStockEquity
        # PEAD = {} # PEAD # Too complicated because of periods and missing data.
    }
    
    # Storing anomaly BM ratio for each year
    self.anomalies_bm_ratio:Dict[str, RollingWindow] = {
        "AG": RollingWindow[float](5),
        "BM": RollingWindow[float](5),
        "GP": RollingWindow[float](5),
        "MOM": RollingWindow[float](5),
        "CEI": RollingWindow[float](5),
        "NSI": RollingWindow[float](5),
        "ACC": RollingWindow[float](5),
        "IVA": RollingWindow[float](5), 
        "ROA": RollingWindow[float](5),
        "SIZE": RollingWindow[float](5) 
    }
    
    self.month:int = 0 # Months counter
    self.period:int = 12 * 21 # This is period for momentum
    self.anomalies_count:int = 7 # Number of selected anomalies for trading
    self.book_to_market_period:int = 12 # Each month storing book to market values for one year
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    
    market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.financial_statement_names:List[str] = [
        'FinancialStatements.BalanceSheet.CurrentAssets.TwelveMonths',
        'FinancialStatements.BalanceSheet.CashAndCashEquivalents.TwelveMonths',
        'FinancialStatements.BalanceSheet.CurrentLiabilities.TwelveMonths',
        'FinancialStatements.BalanceSheet.CurrentDebt.TwelveMonths',
        'FinancialStatements.IncomeStatement.DepreciationAndAmortization.TwelveMonths',
        'FinancialStatements.BalanceSheet.GrossPPE.TwelveMonths',
        'ValuationRatios.CFOPerShare',
        'ValuationRatios.TotalAssetPerShare',
        'FinancialStatements.BalanceSheet.AccountsReceivable.TwelveMonths',
        'FinancialStatements.IncomeStatement.TotalRevenueAsReported.TwelveMonths',
        'ValuationRatios.PBRatio',
        'MarketCap',
        'FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths',
        'FinancialStatements.IncomeStatement.CostOfRevenue.TwelveMonths',
        'FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths',
    ]
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.rebalance_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update RollingWindow each day
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    
    # Select each month
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
 
    selected: List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price >= self.min_share_price and x.Market == 'usa' 
        and x.SecurityReference.ExchangeId in self.exchange_codes 
        and all((not np.isnan(self.rgetattr(x, statement_name)) \
        and self.rgetattr(x, statement_name) != 0) for statement_name in self.financial_statement_names)
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(self.period, self.book_to_market_period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        
        if self.data[symbol].is_ready():
            self.data[symbol].update_market_caps(stock.MarketCap)
            self.data[symbol].update_book_to_market(1 / stock.ValuationRatios.PBRatio)
            if self.rebalance_flag:
                if symbol not in self.accruals_data:
                    # Data for previous year.
                    self.accruals_data[symbol] = None
                            
                # Accrual calc.
                current_accruals_data:data_tools.StockData = data_tools.StockData(stock.FinancialStatements.BalanceSheet.CurrentAssets.Value, stock.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value,
                                                        stock.FinancialStatements.BalanceSheet.CurrentLiabilities.Value, stock.FinancialStatements.BalanceSheet.CurrentDebt.Value, stock.FinancialStatements.BalanceSheet.IncomeTaxPayable.Value,
                                                        stock.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value, stock.FinancialStatements.BalanceSheet.TotalAssets.Value,
                                                        stock.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value)
                    
                # There is not previous accruals data.
                if not self.accruals_data[symbol]:
                    self.accruals_data[symbol] = current_accruals_data
                    continue
                    
                # Calculate current accruals.
                current_accruals = self.CalculateAccruals(current_accruals_data, self.accruals_data[symbol])
                # Store current accruals into dictionary for next calculations.
                self.accruals_data[symbol] = current_accruals_data
                    
                # Start storing values for each anomaly only if book to market values are ready.
                if not self.data[symbol].is_ready_book_to_market():    
                    continue
                
                # Store values for each anomaly 
                self.anomalies['ACC'][symbol] = current_accruals
                self.anomalies['AG'][symbol] = stock.FinancialStatements.BalanceSheet.TotalAssets.Value
                self.anomalies['BM'][symbol] = 1 / stock.ValuationRatios.PBRatio
                self.anomalies['MOM'][symbol] = self.data[symbol].performance()
                self.anomalies['CEI'][symbol] = self.data[symbol].cei(5) # Momentum for fifth month
                self.anomalies['NSI'][symbol] = stock.FinancialStatements.CashFlowStatement.NetCommonStockIssuance.Value
                self.anomalies['ROA'][symbol] = stock.OperationRatios.ROA.Value
                self.anomalies['SIZE'][symbol] = stock.MarketCap
                # Gross Profitability = (TotalRevenue + CostOfGoods) / TotalAssets
                self.anomalies['GP'][symbol] = (stock.FinancialStatements.IncomeStatement.CostOfRevenue.Value + stock.FinancialStatements.IncomeStatement.TotalRevenue.Value) / stock.FinancialStatements.BalanceSheet.TotalAssets.Value
                # Investments to assets = (GrossPPE + ChangeInInventory) / TotalAssets
                self.anomalies['IVA'][symbol] = (stock.FinancialStatements.BalanceSheet.GrossPPE.Value + stock.FinancialStatements.CashFlowStatement.ChangeInInventory.Value) / stock.FinancialStatements.BalanceSheet.TotalAssets.Value
    # Rebalance yearly
    if not self.rebalance_flag:
        return Universe.Unchanged
    
    # There are no data in dictionaries, because book_to_market isn't warmed up.
    if len(self.anomalies['AG']) == 0:
        self.ClearAnomalies()
        return Universe.Unchanged
        
    # Store BM ratio for each anomaly
    self.anomalies_bm_ratio['AG'].Add(self.CalculateAnomalyBMRatio(self.anomalies['AG'], 'AG'))
    self.anomalies_bm_ratio['BM'].Add(self.CalculateAnomalyBMRatio(self.anomalies['BM'], 'BM'))
    self.anomalies_bm_ratio['MOM'].Add(self.CalculateAnomalyBMRatio(self.anomalies['MOM'], 'MOM'))
    self.anomalies_bm_ratio['CEI'].Add(self.CalculateAnomalyBMRatio(self.anomalies['CEI'], 'CEI'))
    self.anomalies_bm_ratio['NSI'].Add(self.CalculateAnomalyBMRatio(self.anomalies['NSI'], 'NSI'))
    self.anomalies_bm_ratio['ROA'].Add(self.CalculateAnomalyBMRatio(self.anomalies['ROA'], 'ROA'))
    self.anomalies_bm_ratio['SIZE'].Add(self.CalculateAnomalyBMRatio(self.anomalies['SIZE'], 'SIZE'))
    self.anomalies_bm_ratio['GP'].Add(self.CalculateAnomalyBMRatio(self.anomalies['GP'], 'GP'))
    self.anomalies_bm_ratio['IVA'].Add(self.CalculateAnomalyBMRatio(self.anomalies['IVA'], 'IVA'))
    self.anomalies_bm_ratio['ACC'].Add(self.CalculateAnomalyBMRatio(self.anomalies['ACC'], 'ACC'))
    
    # Check if anomalies bm ratio values are ready.
    if not self.anomalies_bm_ratio['AG'].IsReady:
        self.ClearAnomalies() # Function clears each anomaly dictionary.
        return Universe.Unchanged
    
    history_adjusted_bm_ratio = {}
    for anomaly, bm_ratios in self.anomalies_bm_ratio.items():
        history_adjusted_bm_ratio[anomaly] = self.CalculateHistoryAdjustedBMRatio(bm_ratios)
    
    # Sort anomalies based on their history_adjusted_bm_ratio.
    sorted_by_hist_adj_bm_ratio = [x[0] for x in sorted(history_adjusted_bm_ratio.items(), key=lambda item: item[1])]
    # Select highest anomalies for trading.
    selected_anomalies = sorted_by_hist_adj_bm_ratio[-self.anomalies_count:]
    
    # Create trading portfolio for each selected anomaly
    for anomaly in selected_anomalies:
        self.CreateLongAndShort(self.anomalies[anomaly], anomaly)
    
    self.ClearAnomalies()
    
    return list(self.traded_quantity.keys())
def OnData(self, data: Slice) -> None:
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    
    # Trade execution
    self.Liquidate()
    
    # Trade stock with MarketOrder based on their quantity.
    for symbol, quantity in self.traded_quantity.items():
        if symbol in data and data[symbol]:
            self.MarketOrder(symbol, quantity)
    
    self.traded_quantity.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    if self.month != 12:
        self.rebalance_flag = True        
        # Reset rebalance period
        self.month = 0
    self.month += 1

# Function calculates anomaly BM ratio
def CalculateAnomalyBMRatio(self, dictionary, anomaly):
    quintile = int(len(dictionary) / 5)
    # Sort dictionary by value and create list of symbols.
    sorted_by_value = [x[0] for x in sorted(dictionary.items(), key=lambda item: item[1])]
    
    long, short = self.SelectLongAndShort(sorted_by_value, quintile, anomaly)
    
    bm_ratio = 0
    total_anomaly_cap = sum([self.anomalies['SIZE'][symbol] for symbol in long + short])

    # Sum BM weight for each stock in long and short 
    for symbol in long + short:
        # self.anomalies['BM'][symbol] * market_cap / total_market_cap
        bm_ratio += (self.anomalies['BM'][symbol] * (self.anomalies['SIZE'][symbol] / total_anomaly_cap))
    
    return bm_ratio

# Function calculates history adjusted BM ratio for each anomaly.   
def CalculateHistoryAdjustedBMRatio(self, bm_ratios_roll_window):
    bm_ratios_values = [x for x in bm_ratios_roll_window]
    
    # History adjusted BM ratio = current BM ratio - average from others BM ratios
    return bm_ratios_values[0] - np.mean(bm_ratios_values[1:])

# Function creates long and short portfolio for each anomaly.
def CreateLongAndShort(self, dictionary, anomaly):
    quintile = int(len(dictionary) / 5)
    # Sort dictionary by value and create list of symbols.
    sorted_by_value = [x[0] for x in sorted(dictionary.items(), key=lambda item: item[1])]
    
    long, short = self.SelectLongAndShort(sorted_by_value, quintile, anomaly)
        
    long_w = self.Portfolio.TotalPortfolioValue / self.anomalies_count
    short_w = self.Portfolio.TotalPortfolioValue / self.anomalies_count
    
    # Create anomaly long portfolio weighted by market cap
    total_cap_long = sum([self.anomalies['SIZE'][symbol] for symbol in long])
    for symbol in long:
        # Each weight needs to be divided by total anomalies in portfolio
        self.traded_quantity[symbol] = np.floor((long_w * (self.anomalies['SIZE'][symbol] / total_cap_long)) / self.data[symbol].last_price())
    
    # Create anomaly short portfolio weighted by market cap
    total_cap_short = sum([self.anomalies['SIZE'][symbol] for symbol in short])
    for symbol in short:
        # Each weight needs to be divided by total anomalies in portfolio
        self.traded_quantity[symbol] = -np.floor((short_w * (self.anomalies['SIZE'][symbol] / total_cap_short)) / self.data[symbol].last_price())

def SelectLongAndShort(self, sorted_symbols, quintile, anomaly):
    long = []
    short = []
    
    if anomaly in self.positive:
        long = sorted_symbols[-quintile:] # Long top quintile
        short = sorted_symbols[:quintile] # Short bottom quintile
    else:
        short = sorted_symbols[-quintile:] # Short top quintile
        long = sorted_symbols[:quintile] # Long bottom quintile

    return long, short
    
# Function clear each anomaly dictionary stored in self.anomalies dictionary.
def ClearAnomalies(self):
    for _, dictionary in self.anomalies.items():
        dictionary.clear()
        
# Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3188172                
def CalculateAccruals(self, current_accrual_data, prev_accrual_data):
    delta_assets = current_accrual_data.CurrentAssets - prev_accrual_data.CurrentAssets
    delta_cash = current_accrual_data.CashAndCashEquivalents - prev_accrual_data.CashAndCashEquivalents
    delta_liabilities = current_accrual_data.CurrentLiabilities - prev_accrual_data.CurrentLiabilities
    delta_debt = current_accrual_data.CurrentDebt - prev_accrual_data.CurrentDebt
    dep = current_accrual_data.DepreciationAndAmortization
    total_assets_prev_year = prev_accrual_data.TotalAssets
    
    acc = (delta_assets - delta_liabilities - delta_cash + delta_debt - dep) / total_assets_prev_year
    return acc
# https://gist.github.com/wonderbeyond/d293e7a2af1de4873f2d757edd580288
def rgetattr(self, obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))
