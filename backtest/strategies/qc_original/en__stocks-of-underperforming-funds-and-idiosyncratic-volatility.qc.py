# Original QuantConnect / library Python
# locale=en slug="stocks-of-underperforming-funds-and-idiosyncratic-volatility"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import statsmodels.api as sm
from dateutil.relativedelta import relativedelta
from scipy import stats
from data_tools import CustomFeeModel, QuantpediaFamaFrench, FundHoldings, StockHolding
# endregion

class StocksOfUnderperformingFundsAndIdiosyncraticVolatility(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)

    self.leverage:int = 5

    self.max_missing_days:int = 5
    
    self.short_period:int = 21            # n - 1 daily performances will be calcualted from n daily prices
    self.long_period:int = 21 * 12        # need m daily prices, to calculate quarter period

    self.first_quantile:int = 5           # this quantile size is taken in first selection
    self.second_quantile:int = 10         # this quantile size is taken in second selection

    self.weights:dict[Symbol, float] = {}
    self.price_data:dict[str, RollingWindow] = {}

    # FF data
    self.ff_period:int = self.short_period - 1 # need n - 1 daily data
    self.SetWarmUp(self.short_period, Resolution.Daily)
    
    self.holdings_by_fund:dict[str, FundHoldings] = {}
    self.ticker_universe:set = set()  # every ticker stored in hedge fund holdings data

    self.funds_tickers:dict[str, dict[datetime.date, list]] = {}

    hedge_fund_file_content:str = self.Download('data.quantpedia.com/backtesting_data/equity/hedge_fund_holdings/hedge_funds_holdings.json')
    hedge_funds_data:dict = json.loads(hedge_fund_file_content)

    for index, hedge_fund_data in enumerate(hedge_funds_data):
        hedge_fund_names:list[str] = list(hedge_fund_data.keys())
        hedge_fund_names.remove('date')
        date:datetime.date = datetime.strptime(hedge_fund_data['date'], '%d.%m.%Y').date()

        for hedge_fund_name in hedge_fund_names:
            if hedge_fund_name not in self.holdings_by_fund:
                self.holdings_by_fund[hedge_fund_name] = FundHoldings(hedge_fund_name)

            holding_list:list[StockHolding] = []
            holdings:list[dict] = hedge_fund_data[hedge_fund_name]['stocks']
            for holding in holdings:
                ticker:str = holding['ticker']
                number_of_shares:int = int(holding['#_of_shares'])
                weight:float = float(holding['weight'])

                self.ticker_universe.add(ticker)

                if ticker not in self.funds_tickers:
                    # initialize dictionary for stock's ticker
                    self.funds_tickers[ticker] = {}

                if date not in self.funds_tickers[ticker]:
                    # initialize list, where will be all funds, which hold this stock in this date
                    self.funds_tickers[ticker][date] = []
                
                # add fund with stock weight in that fund to list == tuple (hedge_fund_name, weight)
                self.funds_tickers[ticker][date].append((hedge_fund_name, weight))

                holding_list.append(StockHolding(ticker, number_of_shares, weight))
            
            self.holdings_by_fund[hedge_fund_name].update_holdings_by_date(date, holding_list)

    self.market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

    self.fama_french:Symbol = self.AddData(QuantpediaFamaFrench, 'fama_french_3_factor', Resolution.Daily).Symbol
    self.fama_french_data:dict[str, RollingWindow] = {
        'market': RollingWindow[float](self.ff_period),
        'size': RollingWindow[float](self.ff_period),
        'value': RollingWindow[float](self.ff_period)
    }
    
    # universe selection
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.BeforeMarketClose(self.market), self.Selection)

def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse):
    # update the rolling window every day
    for stock in coarse:
        symbol:Symbol = stock.Symbol

        # Store monthly price.
        if symbol.Value in self.price_data:
            self.price_data[symbol.Value].Add(stock.AdjustedPrice)

    if not self.selection_flag:
        return Universe.Unchanged
    
    # fama french data has to be ready for regression and they still must coming
    if not self.fama_french_data['market'].IsReady or (self.Securities[self.fama_french].GetLastData() and \
         (self.Time.date() - self.Securities[self.fama_french].GetLastData().Time.date()).days >= self.max_missing_days):
        return Universe.Unchanged

    hedge_fund_symbols:list[Symbol] = [x.Symbol for x in coarse if x.Symbol.Value in self.ticker_universe]
    
    warmed_up_symbols:list[Symbol] = []
    # warmup price rolling windows
    for symbol in hedge_fund_symbols:
        ticker:str = symbol.Value

        if ticker not in self.price_data:
            self.price_data[ticker] = RollingWindow[float](self.long_period)
        
            history = self.History(symbol, self.long_period, Resolution.Daily)
            if not history.empty:
                closes = history.loc[symbol].close
                for time, close in closes.iteritems():
                    self.price_data[ticker].Add(close)

        if self.price_data[ticker].IsReady:
            warmed_up_symbols.append(symbol)
        
    return warmed_up_symbols  

def FineSelectionFunction(self, fine):
    # regression x for idiosyncratic volatility
    regression_x:list[list[float]] = [
        list(self.fama_french_data['market']),
        list(self.fama_french_data['size']),
        list(self.fama_french_data['value'])
    ]

    IVOL:dict[FineFundamental, float] = {}
    stock_level_fund_perf:dict[FineFundamental, float] = {}

    # get previous quarter holdings
    prev_quarter:datetime = self.Time.date() - timedelta(days=self.Time.day) - relativedelta(months=2)
    quarter_before_date:datetime = prev_quarter - relativedelta(months=3)

    for stock in fine:
        market_cap:float = stock.MarketCap

        if market_cap == 0:
            continue

        symbol:Symbol = stock.Symbol
        ticker:str = symbol.Value
        
        # at least one fund has to hold this stock in previous quarter
        if ticker in self.funds_tickers and prev_quarter in self.funds_tickers[ticker] and len(self.funds_tickers[ticker][prev_quarter]) > 0:
            stock_funds_weights:list[list] = self.funds_tickers[ticker][prev_quarter]

            # calculate fund performances multiplied by stock's weight
            fund_weighted_values: list[float] = []   # storing values of (fund_performance * stock_weight_in_fund)
            stocks_weights: list[float] = []        # storing stock weights in funds

            for fund, stock_weight in stock_funds_weights:
                # fund has to have holdings for quarter_before_date
                if not quarter_before_date in self.holdings_by_fund[fund].holdings_by_date:
                    continue
                
                # previous holdings period index and length
                prev_holdings_perf_period_start_i:int = np.busday_count(prev_quarter, self.Time.date())
                prev_holdings_perf_period_length:int = np.busday_count(quarter_before_date, prev_quarter)

                quarter_before_holdings:FundHoldings = self.holdings_by_fund[fund].holdings_by_date[quarter_before_date]
                fund_performance:float = np.mean([self.price_data[holding.ticker][prev_holdings_perf_period_start_i] / self.price_data[holding.ticker][prev_holdings_perf_period_start_i+prev_holdings_perf_period_length] - 1 for holding in quarter_before_holdings if holding.ticker in self.price_data and self.price_data[holding.ticker].IsReady])

                fund_weighted_values.append(fund_performance * stock_weight)
                stocks_weights.append(stock_weight)

            # at least one fund, which hold stock in prev_quarter must have data ready for stock-level fund performance
            if len(fund_weighted_values) = self.first_quantile and len(IVOL) >= (self.first_quantile * self.second_quantile):
        # perform first selection based on stock-level fund performances
        quantile:int = int(len(stock_level_fund_perf) / self.first_quantile)
        sorted_by_perf:list[FineFundamental] = [x[0] for x in sorted(stock_level_fund_perf.items(), key=lambda item: item[1])]

        # select lowest quantile
        lowest_quantile:list[FineFundamental] = sorted_by_perf[-quantile:]

        # filter stocks from lowest quantile of stock-level fund performances
        selected_IVOL:dict[FineFundamental, float] = {stock: IVOL_value for stock, IVOL_value in IVOL.items() if stock in lowest_quantile}

        # perform second selection
        quantile:int = int(len(selected_IVOL) / self.second_quantile)
        sorted_by_IVOL:list[FineFundamental] = [x[0] for x in sorted(selected_IVOL.items(), key=lambda item: item[1])]

        # long stocks with the highest IVOL
        long_leg:list[FineFundamental] = sorted_by_IVOL[-quantile:]
        # short stocks with lowest IVOL
        short_leg:list[FineFundamental] = sorted_by_IVOL[:quantile]

        total_long_cap:float = sum([x.MarketCap for x in long_leg])
        total_short_cap:float = sum([x.MarketCap for x in short_leg])

        for stock in long_leg:
            self.weights[stock.Symbol] = stock.MarketCap / total_long_cap

        for stock in short_leg:
            self.weights[stock.Symbol] = -stock.MarketCap / total_short_cap

        return list(self.weights.keys())

    else:
        return Universe.Unchanged

def OnData(self, data):
    # update fama french values on daily basis
    if self.fama_french in data and data[self.fama_french]:
        self.fama_french_data['value'].Add(data[self.fama_french].Value)
        self.fama_french_data['size'].Add(data[self.fama_french].Size)
        self.fama_french_data['market'].Add(data[self.fama_french].Market)
    
    # rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False

    # trade execution
    invested:list[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.weights:
            self.Liquidate(symbol)
    
    for symbol, w in self.weights.items():
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, w)

    self.weights.clear()

def Selection(self):
    # rabalance once a quarter
    if self.Time.month % 3 == 0:
        self.selection_flag = True

def MultipleLinearRegression(self, x, y):
    x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
