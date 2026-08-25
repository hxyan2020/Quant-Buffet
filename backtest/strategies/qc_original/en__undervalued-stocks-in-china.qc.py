# Original QuantConnect / library Python
# locale=en slug="undervalued-stocks-in-china"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
from numpy import isnan
import data_tools
from functools import reduce
class UndervaluedStocksinChina(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    # earnings parameters
    self.earnings_surprise:Dict = {}
    self.min_seasonal_eps_period:int = 4
    self.min_surprise_period:int = 4
    self.leverage:int = 5
    self.quantile:int = 10
    
    self.financial_statement_names:List[str] = [
        'MarketCap',
        'FinancialStatements.BalanceSheet.CurrentAssets.ThreeMonths',
        'FinancialStatements.BalanceSheet.CashAndCashEquivalents.ThreeMonths',
        'FinancialStatements.BalanceSheet.CurrentLiabilities.ThreeMonths',
        'FinancialStatements.BalanceSheet.CurrentDebt.ThreeMonths',
        'FinancialStatements.BalanceSheet.IncomeTaxPayable.ThreeMonths',
        'FinancialStatements.IncomeStatement.DepreciationAndAmortization.ThreeMonths',
        'FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths',
        'FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths',
        'FinancialStatements.IncomeStatement.GrossProfit.TwelveMonths'
    ]
    self.weight:Dict[Symbol, float] = {}
    
    # EPS data keyed by tickers, which are keyed by dates
    self.eps_by_ticker = {}
    
    # last months accruals data
    self.accural_data = {}
    
    self.data:Dict = {}
    self.price_period:int = 12 * 21
    self.dvolume_period:int = 21    
    self.illiquidity_period_m:int = 12   # monthly period
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # parse earnings dataset
    self.first_date:Union[None, datetime.date] = None
    earnings_data:str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json:list[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date:datetime.date = datetime.strptime(obj['date'], "%Y-%m-%d").date()
        
        if not self.first_date: self.first_date = date
        for stock_data in obj['stocks']:
            ticker:str = stock_data['ticker']
            if stock_data['eps'] == '':
                continue
            # initialize dictionary for dates for specific ticker
            if ticker not in self.eps_by_ticker:
                self.eps_by_ticker[ticker] = {}
            
            # store EPS value keyed date, which is keyed by ticker
            self.eps_by_ticker[ticker][date] = float(stock_data['eps'])
    
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.monthly_flag = False
    self.selection_flag = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
    
    # remove earnings surprise data so it remains consecutive
    for security in changes.RemovedSecurities:
        symbol = security.Symbol
        if symbol in self.earnings_surprise:
            del self.earnings_surprise[symbol]

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update daily data
    for stock in fundamental:
        symbol = stock.Symbol
        if symbol in self.data:
            # update daily data
            self.data[symbol].update_price(stock.AdjustedPrice)
            self.data[symbol].update_dollar_volume(stock.DollarVolume)
    
            # calculate illiquidity once month
            if self.monthly_flag:
                if self.data[symbol].can_calculate_illiquidity():
                    ill = self.data[symbol].illiquidity()
                    self.data[symbol].update_illiquidity(ill)
    
    if self.monthly_flag:
        self.monthly_flag = False
        
    if not self.selection_flag:
        return Universe.Unchanged
    
    # filter only symbols, which have earnings data from csv
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Symbol.Value in self.eps_by_ticker and \
        all((not isnan(self.rgetattr(x, statement_name)) and self.rgetattr(x, statement_name) != 0) for statement_name in self.financial_statement_names)
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    current_date = self.Time.date()
    prev_month = current_date - relativedelta(months=3)
    
    current_accurals_data = {}
    sue:Dict[Fundamental, float] = {}
    accruals:Dict[Fundamental, float] = {}
    roa:Dict[Fundamental, float] = {}
    momentum:Dict[Fundamental, float] = {}
    liquidity_shock:Dict[Fundamental, float] = {}
    # warmup price data
    for stock in selected:
        symbol:Symbol = stock.Symbol
        ticker:str = symbol.Value
        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(self.price_period, self.dvolume_period, self.illiquidity_period_m)
            history = self.History(symbol, self.price_period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update_price(close)
        
        if self.data[symbol].prices_are_ready():
            # accurals calc
            current_accurals_data[symbol] = data_tools.AccuralsData(stock.FinancialStatements.BalanceSheet.CurrentAssets.ThreeMonths, stock.FinancialStatements.BalanceSheet.CashAndCashEquivalents.ThreeMonths,
                                                        stock.FinancialStatements.BalanceSheet.CurrentLiabilities.ThreeMonths, stock.FinancialStatements.BalanceSheet.CurrentDebt.ThreeMonths, stock.FinancialStatements.BalanceSheet.IncomeTaxPayable.ThreeMonths,
                                                        stock.FinancialStatements.IncomeStatement.DepreciationAndAmortization.ThreeMonths, stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths)
            recent_eps_data = None
            # store all EPS data for previous month
            for date in self.eps_by_ticker[ticker]:
                if date = prev_month:
                    EPS_value = self.eps_by_ticker[ticker][date]
                    
                    # create tuple (EPS date, EPS value of specific stock)
                    recent_eps_data = (date, EPS_value)
                    break
            
            # stock had earnings previous month
            if recent_eps_data:
                last_earnings_date = recent_eps_data[0]
                
                # get earnings history until previous earnings
                earnings_eps_history = [(x, self.eps_by_ticker[ticker][x]) for x in self.eps_by_ticker[ticker] if x = self.min_seasonal_eps_period:
                    # make sure we have a consecutive seasonal data. Same months with one year difference
                    year_diff = np.diff([x[0].year for x in seasonal_eps_data])
                    if all(x == 1 for x in year_diff):
                        # SUE calculation
                        seasonal_eps = [x[1] for x in seasonal_eps_data]
                        diff_values = np.diff(seasonal_eps)
                        drift = np.average(diff_values)
                        
                        last_earnings_eps = seasonal_eps[-1]
                        expected_earnings = last_earnings_eps + drift
                        actual_earnings = recent_eps_data[1]
                        
                        earnings_surprise = actual_earnings - expected_earnings
                        
                        # initialize suprise data
                        if symbol not in self.earnings_surprise:
                            self.earnings_surprise[symbol] = []
                        
                        # data for every variable calculation are ready
                        elif len(self.earnings_surprise[symbol]) >= self.min_surprise_period and \
                            symbol in self.accural_data and self.data[symbol].prices_are_ready() and \
                            self.data[symbol].illiquidities_are_ready():
                        
                            earnings_surprise_std = np.std(self.earnings_surprise[symbol])
                            sue[stock] = earnings_surprise / earnings_surprise_std
                            accruals[stock] = self.CalculateAccurals(current_accurals_data[symbol], self.accural_data[symbol])
                            roa[stock] = stock.FinancialStatements.IncomeStatement.GrossProfit.TwelveMonths / stock.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths
                            momentum[stock] = self.data[symbol].momentum()
                            liquidity_shock[stock] = self.data[symbol].liquidity_shock()
                        self.earnings_surprise[symbol].append(earnings_surprise)
    # clear old accruals and set new ones 
    self.accural_data.clear()
    for symbol in current_accurals_data:
        self.accural_data[symbol] = current_accurals_data[symbol]
    # make sure there will be enough stocks for decile selection
    if len(roa)  None:
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
def Selection(self) -> None:
    self.monthly_flag = True
    if self.Time.month % 3 == 0:
        self.selection_flag = True
    
def CalculateAccurals(self, current_accural_data, prev_accural_data):
    delta_assets = current_accural_data.CurrentAssets - prev_accural_data.CurrentAssets
    delta_cash = current_accural_data.CashAndCashEquivalents - prev_accural_data.CashAndCashEquivalents
    delta_liabilities = current_accural_data.CurrentLiabilities - prev_accural_data.CurrentLiabilities
    delta_debt = current_accural_data.CurrentDebt - prev_accural_data.CurrentDebt
    delta_tax = current_accural_data.IncomeTaxPayable - prev_accural_data.IncomeTaxPayable
    dep = current_accural_data.DepreciationAndAmortization
    avg_total = (current_accural_data.TotalAssets + prev_accural_data.TotalAssets) / 2
    
    bs_acc = ((delta_assets - delta_cash) - (delta_liabilities - delta_debt-delta_tax) - dep) / avg_total
    return bs_acc
# https://gist.github.com/wonderbeyond/d293e7a2af1de4873f2d757edd580288
def rgetattr(self, obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))
