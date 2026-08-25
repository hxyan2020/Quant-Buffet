# Original QuantConnect / library Python
# locale=en slug="estimating-hedge-funds-returns-out-of-sample"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Dict
from pandas.core.frame import DataFrame
import numpy as np
import statsmodels.api as sm
# endregion

class EstimatingHedgeFundsReturnsOutofSample(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2011, 1, 1)
    self.SetCash(100000)

    self.leverage:int = 5

    self.max_missing_days:int = 90
    self.selection_month:int = 1
    self.t_stats_value_threshold:int = 2
    
    self.period:int = 36
    self.month_period:int = 21 
    self.quantile:int = 5

    self.traded_portfolio_portion:Dict[Symbol, float] = {}
    self.data:Dict[Symbol, SymbolData] = {}
    self.fund_performance:Dict[str, RollingWindow] = {}
    
    self.holdings_by_fund:Dict[str, FundHoldings] = {}
    self.ticker_universe:set = set()  # every ticker stored in hedge fund holdings data

    self.funds_tickers:Dict[str, Dict[datetime.date, list]] = {}

    hedge_fund_file_content:str = self.Download('data.quantpedia.com/backtesting_data/equity/hedge_fund_holdings/hedge_funds_holdings.json')
    hedge_funds_data:Dict = json.loads(hedge_fund_file_content)

    for index, hedge_fund_data in enumerate(hedge_funds_data):
        hedge_fund_names:list[str] = list(hedge_fund_data.keys())
        hedge_fund_names.remove('date')
        date:datetime.date = datetime.strptime(hedge_fund_data['date'], '%d.%m.%Y').date()

        for hedge_fund_name in hedge_fund_names:
            if hedge_fund_name not in self.holdings_by_fund:
                self.holdings_by_fund[hedge_fund_name] = data_tools.FundHoldings(hedge_fund_name)

            holding_list:list[StockHolding] = []
            holdings:list[Dict] = hedge_fund_data[hedge_fund_name]['stocks']
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

                holding_list.append(data_tools.StockHolding(ticker, number_of_shares, weight))
            
            self.holdings_by_fund[hedge_fund_name].update_holdings_by_date(date, holding_list)

    self.market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.vix:Symbol = self.AddEquity("SVXY", Resolution.Daily).Symbol

    # universe selection
    self.selection_flag:bool = False
    self.rebalance_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.BeforeMarketClose(self.market), self.Selection)

def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
    
    for security in changes.RemovedSecurities:
        if security.Symbol in self.data:
            self.data.pop(security.Symbol)

def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False

    # update the price every month
    for stock in coarse:
        symbol:Symbol = stock.Symbol
        ticker:str = symbol.Value

        if ticker in self.ticker_universe:
            if symbol in self.data:
                self.data[symbol].update_data(stock.AdjustedPrice)
    
    if self.vix in self.data:
        if not self.Securities[self.vix].Price == 0:
            self.data[self.vix].update_data(self.Securities[self.vix].Price)

    # selected = [x.Symbol for x in coarse if x.HasFundamentalData and x.Market == 'usa' and x.AdjustedPrice >= 1 and x.Symbol.Value in self.ticker_universe]
    selected:List[Symbol] = [x.Symbol
        for x in sorted([x for x in coarse if x.HasFundamentalData and x.Market == 'usa' and x.AdjustedPrice >= 1 and x.Symbol.Value in self.ticker_universe],
            key = lambda x: x.DollarVolume, reverse = True)]
    
    # warmup price rolling windows
    for symbol in selected + [self.vix]:
        if symbol in self.data:
            continue

        if symbol.Value in self.ticker_universe or symbol == self.vix:
            self.data[symbol] = data_tools.SymbolData(self.period)
            history:DataFrame = self.History(symbol, self.period * self.month_period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes:pd.Series = history.loc[symbol].close.groupby(pd.Grouper(freq='M')).last()
            for time, close in closes.iteritems():
                self.data[symbol].update_data(close)

    return [x for x in selected if self.data[x].is_ready()]

def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    fine = [x for x in fine if x.MarketCap != 0 and x.AssetClassification.MorningstarSectorCode != MorningstarSectorCode.FinancialServices and \
            (x.SecurityReference.ExchangeId == 'NYS') or (x.SecurityReference.ExchangeId == 'NAS') or (x.SecurityReference.ExchangeId == 'ASE')]

    fine:Dict[Symbol, FineFundamental] = {x.Symbol.Value: x for x in fine}

    if len(fine) != 0:
        performance_by_stock:Dict[str, float] = {ticker: self.data[fine[ticker].Symbol].get_last_return() for ticker in self.ticker_universe \
            if ticker in fine and self.data[fine[ticker].Symbol].is_ready()}

        for fund, fund_data in self.holdings_by_fund.items():
            last_date = fund_data.get_latest_date(self.Time.date())
            if last_date is None:
                continue

            fund_performance:float = sum([(x.weight / 100) * performance_by_stock[x.ticker] for x in fund_data.holdings_by_date[last_date] if x.ticker in fine])

            if fund not in self.fund_performance:
                self.fund_performance[fund] = RollingWindow[float](self.period)
            self.fund_performance[fund].Add(fund_performance)

    if not self.rebalance_flag:
        return Universe.Unchanged
    # self.rebalance_flag = False

    if not self.data[self.vix].is_ready():
        return Universe.Unchanged

    vix_returns:np.ndarray = np.array(self.data[self.vix].get_returns())
    selected_funds:Dict[str, FundHoldings] = {}

    # run regression on every fund
    for fund, fund_data in self.holdings_by_fund.items():
        if fund not in self.fund_performance:
            continue
        if not self.fund_performance[fund].IsReady:
            continue

        x:np.ndarray = vix_returns
        y:np.ndarray = np.array(list(self.fund_performance[fund])[::-1])

        model = self.multiple_linear_regression(x, y)

        # check alpha and t stats values
        if model.params[0] > 0 and abs(model.tvalues[0]) >= self.t_stats_value_threshold and abs(model.tvalues[1]) >= 2:
            selected_funds[fund] = fund_data

    # calculate portions on stocks
    if len(selected_funds) != 0:
        for fund, fund_data in selected_funds.items():
            last_date = fund_data.get_latest_date(self.Time.date())

            if last_date is None or (self.Time.date() - last_date).days >= self.max_missing_days:
                continue
            for data in fund_data.holdings_by_date[last_date]:
                if data.ticker not in fine:
                    continue
                portion:float = ((self.Portfolio.TotalPortfolioValue / len(selected_funds)) * (data.weight / 100))
                if data.ticker not in self.traded_portfolio_portion:
                    self.traded_portfolio_portion[fine[data.ticker].Symbol] = 0
                self.traded_portfolio_portion[fine[data.ticker].Symbol] += portion
                
    return list(self.traded_portfolio_portion.keys())

def OnData(self, data: Slice):
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False

    # trade execution
    stocks_invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in self.traded_portfolio_portion:
            self.Liquidate(symbol)

    for symbol, portion in self.traded_portfolio_portion.items():
        if symbol in data and data[symbol]:
            quantity:float = (portion // data[symbol].Price) - self.Portfolio[symbol].Quantity
            self.MarketOrder(symbol, quantity)

    self.traded_portfolio_portion.clear()

def Selection(self):
    if self.Time.month != self.selection_month:
        self.selection_flag = True
        return
    self.rebalance_flag = True
    self.selection_flag = True

def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    x = sm.add_constant(x, has_constant='add')
    result = sm.OLS(endog=y, exog=x).fit()
    return result
