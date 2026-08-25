# Original QuantConnect / library Python
# locale=en slug="accruals-seasonality"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from dateutil.relativedelta import relativedelta
from AlgorithmImports import *

class AccrualsSeasonality(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1) # earnings dates starts in 2010
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.quantile:int = 5
    self.period:int = 5     # need n years of stock seasonal accruals values
    
    self.weight:Dict[Symbol, float] = {}
    self.accrual_data:Dict[Symbol, AccrualsData] = {}  # last accruals values keyed by stocks symbols
    self.tickers:Set(str) = set()
    self.earnings_data:Dict[int, Dict[int, List[str]]] = {}
    self.accruals_values = {}
    self.min_share_price:float = 5.

    earnings_set:Set(str) = set()
    earnings_data:str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json:List[Dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date:datetime.date = datetime.strptime(obj['date'], "%Y-%m-%d").date()
        year:int = date.year
        month:int = date.month

        if year not in self.earnings_data:
            self.earnings_data[year] = {}
            
        if month not in self.earnings_data[year]:
            self.earnings_data[year][month] = []
        
        for stock_data in obj['stocks']:
            ticker:str = stock_data['ticker']

            self.earnings_data[year][month].append(ticker)
            self.tickers.add(ticker)
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> None:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and \
        x.Symbol.Value in self.tickers and x.MarketCap != 0 and x.AdjustedPrice > self.min_share_price and \
        not np.isnan(x.FinancialStatements.BalanceSheet.CurrentAssets.ThreeMonths) and x.FinancialStatements.BalanceSheet.CurrentAssets.ThreeMonths != 0 and \
        not np.isnan(x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.ThreeMonths) and x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.ThreeMonths != 0 and \
        not np.isnan(x.FinancialStatements.BalanceSheet.CurrentLiabilities.ThreeMonths) and x.FinancialStatements.BalanceSheet.CurrentLiabilities.ThreeMonths != 0 and \
        not np.isnan(x.FinancialStatements.BalanceSheet.CurrentDebt.ThreeMonths) and x.FinancialStatements.BalanceSheet.CurrentDebt.ThreeMonths != 0 and \
        not np.isnan(x.FinancialStatements.BalanceSheet.IncomeTaxPayable.ThreeMonths) and x.FinancialStatements.BalanceSheet.IncomeTaxPayable.ThreeMonths != 0 and \
        not np.isnan(x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.ThreeMonths) and x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.ThreeMonths != 0 and \
        not np.isnan(x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths) and x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths != 0
    ]

    curr_date:datetime.date = self.Time.date()
    prev_month:datetime.date = curr_date - relativedelta(months=1)
    
    curr_year, curr_month = curr_date.year, curr_date.month
    prev_months_year, prev_months_month = prev_month.year, prev_month.month 
    
    seasonal_accruals_values:Dict[FineFundamental, dict[int, float]] = {}
    current_accruals_data = {}
    
    for stock in selected:
        symbol:Symbol = stock.Symbol
        ticker:str = symbol.Value
        
        # accruals calculation
        current_accruals_data[symbol] = AccrualsData(stock.FinancialStatements.BalanceSheet.CurrentAssets.ThreeMonths, stock.FinancialStatements.BalanceSheet.CashAndCashEquivalents.ThreeMonths,
                                                    stock.FinancialStatements.BalanceSheet.CurrentLiabilities.ThreeMonths, stock.FinancialStatements.BalanceSheet.CurrentDebt.ThreeMonths,
                                                    stock.FinancialStatements.BalanceSheet.IncomeTaxPayable.ThreeMonths, stock.FinancialStatements.IncomeStatement.DepreciationAndAmortization.ThreeMonths,
                                                    stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths)
        
        # check if stock had earnings in previous month and make sure stock has accruals data from previous selection
        if symbol in self.accrual_data and prev_months_year in self.earnings_data and prev_months_month in self.earnings_data[prev_months_year] \
            and ticker in self.earnings_data[prev_months_year][prev_months_month]:
                
            accrual_value:float = self.CalculateAccruals(current_accruals_data[symbol], self.accrual_data[symbol])
            
            if symbol not in self.accruals_values:
                self.accruals_values[symbol] = {}
                
            if prev_months_year not in self.accruals_values[symbol]:
                self.accruals_values[symbol][prev_months_year] = {}
            
            # store stock's accrual keyed by previous date month, year and stock's symbol
            self.accruals_values[symbol][prev_months_year][prev_months_month] = accrual_value
            
        # check if stock will have earnings in current month
        if symbol in self.accruals_values and curr_year in self.earnings_data \
            and curr_month in self.earnings_data[curr_year] and ticker in self.earnings_data[curr_year][curr_month]:
                
            stock_seasonal_accruals:Dict[int, float] = self.GetSeasonalAccruals(symbol, curr_year, curr_month)
            
            # make sure stock has seasonal accruals for 5 years
            if len(stock_seasonal_accruals) == self.period:
                # store stock's seasonal accruals keyed by stock's object
                seasonal_accruals_values[stock] = stock_seasonal_accruals 
    
    # set new accruals
    self.accrual_data = current_accruals_data
    
    # make sure there are enough data for selection
    if len(seasonal_accruals_values)  None:
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()
    
def CalculateAccruals(self, current_accural_data, prev_accural_data) -> float:
    delta_assets:float = current_accural_data.CurrentAssets - prev_accural_data.CurrentAssets
    delta_cash:float = current_accural_data.CashAndCashEquivalents - prev_accural_data.CashAndCashEquivalents
    delta_liabilities:float = current_accural_data.CurrentLiabilities - prev_accural_data.CurrentLiabilities
    delta_debt:float = current_accural_data.CurrentDebt - prev_accural_data.CurrentDebt
    delta_tax:float = current_accural_data.IncomeTaxPayable - prev_accural_data.IncomeTaxPayable
    dep:float = current_accural_data.DepreciationAndAmortization
    avg_total:float = (current_accural_data.TotalAssets + prev_accural_data.TotalAssets) / 2
    
    bs_acc:float = ((delta_assets - delta_cash) - (delta_liabilities - delta_debt-delta_tax) - dep) / avg_total
    return bs_acc
    
def GetSeasonalAccruals(self, symbol:Symbol, year:int, month:int) -> Dict:
    stock_accruals = self.accruals_values[symbol]
    
    seasonal_accruals_values:Dict[int, float] = {}
    
    for index in range(self.period):
        look_up_year:int = year - index - 1
        
        # make sure stock has accrual value in looking year and month
        if look_up_year in stock_accruals and month in stock_accruals[look_up_year]:
            stock_accrual_value = stock_accruals[look_up_year][month]
            
            # store stock's accrual value under looking year
            seasonal_accruals_values[look_up_year] = stock_accrual_value
        else:
            # stock doesn't have all seasonal accruals value, so return blank dictionary
            return {}
            
    return seasonal_accruals_values
    
def CalcSeasonalMeanRank(self, seasonal_accruals_values) -> Dict:
    acc_values:Dict[int, List[List[FineFundamental, float]]] = {}
    
    # firstly create data structure, which lists with tuples (stock, stock acc) are keyed by year
    for stock in seasonal_accruals_values:
        stock_seasonal_acc = seasonal_accruals_values[stock]
        
        for year in stock_seasonal_acc: 
            if year not in acc_values:
                # initialize new list for year
                acc_values[year] = []
            
            stock_acc_value = stock_seasonal_acc[year]    
            
            # store tuple (stock, stock's acc value) keyed by year
            acc_values[year].append((stock, stock_acc_value))
    
    seasonal_ranks = {}
    
    # get stocks ranks for each year
    for year in acc_values:
        # sort stocks by accruals values in curr year
        sorted_by_acc = sorted(acc_values[year], key=lambda item: item[1])
        
        for index in range(len(sorted_by_acc)):
            stock_object = sorted_by_acc[index][0]
            
            if stock_object not in seasonal_ranks:
                seasonal_ranks[stock_object] = []
            
            # append stock's rank in list keyed by stock's object    
            seasonal_ranks[stock_object].append(index)
    
    mean_seasonal_ranks = dict(map(lambda kv: (kv[0], np.mean(kv[1])), seasonal_ranks.items()))
    
    return mean_seasonal_ranks
    
def Selection(self):
    self.selection_flag = True
    
class AccrualsData():
def __init__(self, current_assets, cash_and_cash_equivalents, current_liabilities, current_debt, income_tax_payable, depreciation_and_amortization, total_assets):
    self.CurrentAssets = current_assets
    self.CashAndCashEquivalents = cash_and_cash_equivalents
    self.CurrentLiabilities = current_liabilities
    self.CurrentDebt = current_debt
    self.IncomeTaxPayable = income_tax_payable
    self.DepreciationAndAmortization = depreciation_and_amortization
    self.TotalAssets = total_assets
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
