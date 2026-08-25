# Original QuantConnect / library Python
# locale=en slug="relative-value-factor-in-us"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
import statsmodels.api as sm
from numpy import isnan
from pandas.core.frame import DataFrame
from functools import reduce
class RelativeValueFactorInUS(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.period:int = 12 # need n of monthly data
    self.daily_period:int = 21
    self.daily_price_period:int = self.period * self.daily_period
    self.market_risk_regression_period:int = 73 # days
    self.m_trading_liquidity_period:int = self.period
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.market_cap_threshold:float = 2e8
    self.total_assets_threshold:float = 1e8
    self.quantile:int = 5
    
    self.last_fine:List[Symbol] = []
    self.data:Dict[Symbol, data_tools.SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}
    self.financial_statement_names:List[str] = [
        'OperationRatios.ROA.ThreeMonths',
        'FinancialStatements.IncomeStatement.DepreciationAndAmortization.ThreeMonths',
        'FinancialStatements.BalanceSheet.RetainedEarnings.ThreeMonths',
        'FinancialStatements.BalanceSheet.CurrentAssets.ThreeMonths',
        'FinancialStatements.BalanceSheet.CurrentLiabilities.ThreeMonths',
        'OperationRatios.TotalDebtEquityRatio.ThreeMonths',
        'FinancialStatements.BalanceSheet.Cash.ThreeMonths',
        'FinancialStatements.BalanceSheet.OtherShortTermInvestments.ThreeMonths',
        'FinancialStatements.BalanceSheet.AccountsReceivable.ThreeMonths',
        'FinancialStatements.BalanceSheet.Inventory.ThreeMonths',
    ]
    sectors_etfs_tickers:Dict[MorningstarSectorCode, str] = {
        MorningstarSectorCode.RealEstate: 'VNQ',  # Vanguard Real Estate Index Fund
        MorningstarSectorCode.Technology: 'XLK',  # Technology Select Sector SPDR Fund
        MorningstarSectorCode.Energy: 'XLE',  # Energy Select Sector SPDR Fund
        MorningstarSectorCode.Healthcare: 'XLV',  # Health Care Select Sector SPDR Fund
        MorningstarSectorCode.FinancialServices: 'XLF',  # Financial Select Sector SPDR Fund
        MorningstarSectorCode.Industrials: 'XLI',  # Industrials Select Sector SPDR Fund
        MorningstarSectorCode.BasicMaterials :'XLB',  # Materials Select Sector SPDR Fund
        MorningstarSectorCode.ConsumerCyclical: 'XLY',  # Consumer Discretionary Select Sector SPDR Fund
        MorningstarSectorCode.ConsumerDefensive: 'XLP',  # Consumer Staples Select Sector SPDR Fund
        MorningstarSectorCode.Utilities: 'XLU'   # Utilities Select Sector SPDR Fund    
    }
    
    self.etfs_data:Dict[Symbol, data_tools.ETFData] = {}
    self.sectors_etf_symbols:Dict[MorningstarSectorCode, Symbol] = {} # storing symbols of subscribed etfs keyed by MorningstarSectorCode
    
    for sector, etf_ticker in sectors_etfs_tickers.items():
        symbol = self.AddEquity(etf_ticker, Resolution.Daily).Symbol
        self.sectors_etf_symbols[sector] = symbol
        
        self.etfs_data[symbol] = data_tools.ETFData(self.daily_period)
        
        # warm up prices
        history:DataFrame = self.History(symbol, self.daily_period * self.period, Resolution.Daily)
        if history.empty:
            continue
        
        counter:int = 1
        closes:pd.Series = history.loc[symbol].close
        for time, close in closes.items():
            self.etfs_data[symbol].update_daily_prices(close)
            
            if counter % 21 == 0:
                self.etfs_data[symbol].update_monthly_returns()
                
            counter += 1
    
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.data[self.market] = data_tools.SymbolData(self, self.market, self.period, self.daily_price_period, self.m_trading_liquidity_period)
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']	
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.BeforeMarketClose(self.market, 0), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update prices of subscribed equities and stocks on daily basis
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        # etfs    
        if symbol in self.etfs_data:
            self.etfs_data[symbol].update_daily_prices(stock.AdjustedPrice)
        # stocks with SPY
        else:
            if symbol in self.data:
                self.data[symbol].update_price(stock.AdjustedPrice)
                
                # update volume once a month
                if self.selection_flag:
                    self.data[symbol].update_dvolume(stock.DollarVolume)
    
    # rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
    
    # update etfs monthly returns   
    for _, etf_data_obj in self.etfs_data.items():
        if etf_data_obj.are_daily_prices_ready():
            etf_data_obj.update_monthly_returns()
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price > self.min_share_price and \
        (x.AssetClassification.MorningstarSectorCode in self.sectors_etf_symbols) and x.MarketCap >= self.market_cap_threshold and \
        x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths >= self.total_assets_threshold and x.SecurityReference.ExchangeId in self.exchange_codes and \
        all((not isnan(self.rgetattr(x, statement_name)) and self.rgetattr(x, statement_name) != 0) for statement_name in self.financial_statement_names)
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    if not self.data[self.market].prices_are_ready():
        return Universe.Unchanged
    last_residual:Dict[Symbol, float] = {} # storing last residuals from regression keyed by stock's symbol
    # warmup price rolling windows
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(self, symbol, self.period, self.daily_price_period, self.m_trading_liquidity_period)
        
        if not self.data[symbol].prices_are_ready() or not self.data[symbol].dvolumes_are_ready():
            continue
        sector:MorningstarSectorCode = stock.AssetClassification.MorningstarSectorCode
        # get data for MV calculation
        total_assets:float = stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths
        book_common_equity:float = total_assets - stock.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.ThreeMonths
        
        # make sure stock's data are consecutive
        if len(self.last_fine) != 0 and symbol not in self.last_fine:
            self.data[symbol].reset_fundamental_data()
        
        # calculate MV
        MV:float = total_assets - book_common_equity + stock.MarketCap
        q:float = np.log(MV / total_assets)
        
        self.data[symbol].q_values.append(q)
        
        # update independent variables in regression
        self.data[symbol].roa_values.append(stock.OperationRatios.ROA.ThreeMonths)
        depreciation_value = stock.FinancialStatements.IncomeStatement.DepreciationAndAmortization.ThreeMonths / total_assets
        self.data[symbol].depreciation_values.append(depreciation_value)
        retained_earnings_value = stock.FinancialStatements.BalanceSheet.RetainedEarnings.ThreeMonths / total_assets
        self.data[symbol].retained_earnings_values.append(retained_earnings_value)
        current_assets_value = stock.FinancialStatements.BalanceSheet.CurrentAssets.ThreeMonths
        current_liabilities_value = stock.FinancialStatements.BalanceSheet.CurrentLiabilities.ThreeMonths
        working_capital = (current_assets_value - current_liabilities_value) / total_assets
        self.data[symbol].working_capital_values.append(working_capital)
        self.data[symbol].size_values.append(np.log(total_assets))
        self.data[symbol].leverage_values.append(stock.OperationRatios.TotalDebtEquityRatio.ThreeMonths)
        short_term_investments = stock.FinancialStatements.BalanceSheet.OtherShortTermInvestments.ThreeMonths
        cash = stock.FinancialStatements.BalanceSheet.Cash.ThreeMonths
        self.data[symbol].slack_ratio_values.append((short_term_investments + cash) / total_assets)
        self.data[symbol].cash_ratio_values.append((short_term_investments + cash) / current_liabilities_value)
        accounts_receivable = stock.FinancialStatements.BalanceSheet.AccountsReceivable.ThreeMonths
        self.data[symbol].quick_ratio_values.append((short_term_investments + cash + accounts_receivable) / current_liabilities_value)
        inventory = stock.FinancialStatements.BalanceSheet.Inventory.ThreeMonths
        self.data[symbol].current_ratio_values.append((short_term_investments + cash + accounts_receivable + inventory) / current_liabilities_value)
        
        # 6M and 1Y momentum
        st_perf:float = self.data[symbol].momentum(self.daily_price_period / 2)
        lt_perf:float = self.data[symbol].momentum(self.daily_price_period)
        self.data[symbol].short_term_momentum_values.append(st_perf)
        self.data[symbol].long_term_momentum_values.append(lt_perf)
        
        # market risk
        stock_prices:np.ndarray = np.array(list(self.data[symbol].prices))
        market_prices:np.ndarray = np.array(list(self.data[self.market].prices))
        
        r_stock_prices:np.ndarray = stock_prices[:self.market_risk_regression_period]
        r_market_prices:np.ndarray = market_prices[:self.market_risk_regression_period]
        r_stock_returns:np.ndarray = r_stock_prices[:-1] / r_stock_prices[1:] - 1
        r_market_returns:np.ndarray = r_market_prices[:-1] / r_market_prices[1:] - 1
        market_risk_model = self.MultipleLinearRegression(r_market_returns, r_stock_returns)
        market_risk:float = market_risk_model.params[1]
        self.data[symbol].market_risk_values.append(market_risk)
        
        # trading liquidity
        i_stock_returns:np.ndarray = stock_prices[:-1] / stock_prices[1:] - 1
        i_market_returns:np.ndarray = market_prices[:-1] / market_prices[1:] - 1
        i_model = self.MultipleLinearRegression(i_market_returns, i_stock_returns)
        idiosyncratic_volatility:float = np.std(market_risk_model.resid)
        
        # The average dollar trading volume is computed based on monthly observations on trading volume and closing stock prices over the past year. 
        # The stock return volatility is computed on the regression residual of the daily stock returns on value-weighed market portfolio returns over the same period.
        tl:float = np.log(np.mean([x for x in self.data[symbol].monthly_dollar_volumes]) / idiosyncratic_volatility)
        self.data[symbol].trading_liquidity_values.append(tl)
        
        # calculate regression only when data are ready
        if not self.data[symbol].is_ready():
            continue
        
        regression_y:float = self.data[symbol].q_values
        
        # get etf symbol based on stock's sector
        etf_symbol:Symbol = self.sectors_etf_symbols[sector]
        
        # make sure etf has ready monthly returns
        if len(self.etfs_data[etf_symbol].monthly_returns)  len(etf_monthly_returns):
            regression_y = regression_y[-len(etf_monthly_returns):]
        else:
            etf_monthly_returns = etf_monthly_returns[-len(regression_y):]
            
        max_available_length:int = len(etf_monthly_returns)
        
        regression_x:List = [
            etf_monthly_returns, # dummy variable
            self.Preprocessing(self.data[symbol].roa_values, max_available_length),
            self.Preprocessing(self.data[symbol].depreciation_values, max_available_length),
            self.Preprocessing(self.data[symbol].retained_earnings_values, max_available_length),
            self.Preprocessing(self.data[symbol].working_capital_values, max_available_length),
            self.Preprocessing(self.data[symbol].size_values, max_available_length),
            self.Preprocessing(self.data[symbol].leverage_values, max_available_length),
            self.Preprocessing(self.data[symbol].slack_ratio_values, max_available_length),
            self.Preprocessing(self.data[symbol].cash_ratio_values, max_available_length),
            self.Preprocessing(self.data[symbol].quick_ratio_values, max_available_length),
            self.Preprocessing(self.data[symbol].current_ratio_values, max_available_length),
            # self.Preprocessing(self.data[symbol].capex_values, max_available_length),
            self.Preprocessing(self.data[symbol].short_term_momentum_values, max_available_length),
            self.Preprocessing(self.data[symbol].long_term_momentum_values, max_available_length),
            self.Preprocessing(self.data[symbol].market_risk_values, max_available_length),
            self.Preprocessing(self.data[symbol].trading_liquidity_values, max_available_length),
        ]
        
        # regression
        regression_model = self.MultipleLinearRegression(regression_x, regression_y, False)
        last_residual_value:float = regression_model.resid[-1]
        
        # store last residual from regression keyed by stock's symbol
        last_residual[symbol] = last_residual_value
    
    self.last_fine = list(map(lambda stock: stock.Symbol, selected))
    
    # make sure there 
    if len(last_residual)  None:
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [
        PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]
    ]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Preprocessing(self, values, max_available_length):
    values = values[-max_available_length:]
    
    standardized_values = self.Standardize(values)
    winsorized_values = self.Winsorize(standardized_values)
    capped_values = list(map(lambda value: self.CapValues(value, -2, 2), winsorized_values))
    return capped_values
def Standardize(self, values):
    mean_value = np.mean(values)
    std_value = np.std(values)
    
    if std_value != 0:
        # standardize each value in list
        values = list(map(lambda value: (value - mean_value) / std_value, values))
    
    return values
    
def Winsorize(self, values):
    first_percentile = np.percentile(values, 1)
    ninetieth_percentile = np.percentile(values, 99)
    values = list(map(lambda value: self.CapValues(value, first_percentile, ninetieth_percentile), values))
    
    return values
    
def CapValues(self, value, low_cap, high_cap):
    if value  high_cap:
        value = high_cap
    
    return value
    
def MultipleLinearRegression(self, x, y, use_intercept:bool = True):
    x = np.array(x).T
    
    if use_intercept:
        x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
    
def Selection(self):
    self.selection_flag = True
# https://gist.github.com/wonderbeyond/d293e7a2af1de4873f2d757edd580288
def rgetattr(self, obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))
