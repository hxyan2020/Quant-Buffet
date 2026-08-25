# Original QuantConnect / library Python
# locale=en slug="合理价格下的质量投资策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
from data_tools import SymbolData, CustomFeeModel
import statsmodels.api as sm
# endregion

class QualityAtReasonablePrice(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.quantile:int = 10

    self.prices_period:int = 12 * 21                    # n daily prices
    self.volumes_period:int = self.prices_period        # n daily volumes
    self.max_missing_days_fundamentals:int = 356 + 10
    self.max_missing_days_daily_data:int = 10           

    self.market_cap_threshold:int = 1e09

    self.profitability_metrics:List[str] = ['gp_to_ta', 'roe', 'fcfo_to_ta', 'gpm']
    self.growth_metrics:List[str] = ['sales', 'gp', 'EBITDA', 'EBIT']
    self.rischio_metrics:List[str] = ['dept_to_ta', 'market_beta', 'inverse_QR']
    self.liquidity_metrics:List[str] = ['turnover']
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.weights:Dict[Symbol, float] = {}

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.market_prices:RollingWindow = RollingWindow[float](self.prices_period)
    history = self.History(self.market, self.prices_period, Resolution.Daily)
    if not history.empty:
        closes = history.loc[self.market].close
        
        for (_, close) in closes.iteritems():
            self.market_prices.Add(close)

    self.selection_month:int = 6
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    
    self.Schedule.On(self.DateRules.MonthEnd(self.market), self.TimeRules.BeforeMarketClose(self.market, 0), self.Selection)

def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    for equity in coarse:
        symbol:Symbol = equity.Symbol

        if symbol in self.data:
            self.data[symbol].update_prices(equity.AdjustedPrice)

    if not self.selection_flag:
        return Universe.Unchanged
    
    selected_symbols:List[CoarseFundamental] = [x.Symbol for x in coarse if x.HasFundamentalData]

    for symbol in selected_symbols:
        if symbol in self.data:
            continue

        self.data[symbol] = SymbolData(self.prices_period, self.volumes_period)
        history = self.History(symbol, self.prices_period, Resolution.Daily)
        if not history.empty and all(column in history.columns for column in ['close', 'volume']):
            closes = history.loc[symbol].close
            volumes = history.loc[symbol].volume
            
            for (time, close), (_, volume) in zip(closes.iteritems(), volumes.iteritems()):
                self.data[symbol].update_prices(close)
                self.data[symbol].update_volumes(volume)
                self.data[symbol].set_last_daily_data_update(time.date())

    return selected_symbols

def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    fine:List[FineFundamental] = [x for x in fine if x.MarketCap != 0 and x.MarketCap >= self.market_cap_threshold \
        and x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths != 0 and x.FinancialStatements.IncomeStatement.GrossProfit.TwelveMonths != 0 \
        and x.OperationRatios.ROE.OneYear != 0 and x.FinancialStatements.CashFlowStatement.OperatingCashFlow.TwelveMonths != 0 \
        and x.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.TwelveMonths != 0 \
        and x.FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths != 0 and x.FinancialStatements.IncomeStatement.OperatingExpenseAsReported.TwelveMonths != 0 \
        and x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.TwelveMonths != 0 \
        and x.OperationRatios.QuickRatio.OneYear != 0 and x.ValuationRatios.PBRatio != 0
    ]

    stocks_with_metrics_counter:int = 0
    curr_date:datetime.date = self.Time.date()

    price_to_book:Dict[Symbol, float] = {}
    quality_metrics:Dict[Dict[str, Dict[Symbol, float]]] = {
        'Profitability': { minor_metric: {} for minor_metric in self.profitability_metrics },
        'Growth': { minor_metric: {} for minor_metric in self.growth_metrics },
        'Rischio': { minor_metric: {} for minor_metric in self.rischio_metrics },
        'Liquidity': { minor_metric: {} for minor_metric in self.liquidity_metrics }
    }

    market_daily_returns:List[float]|None = self.GetMarketDailyReturns() if self.market_prices.IsReady else None
    selected_symbols:List[Symbol] = []
    for stock in fine:
        symbol:Symbol = stock.Symbol

        gross_profit:float = stock.FinancialStatements.IncomeStatement.GrossProfit.TwelveMonths
        total_revenue:float = stock.FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths
        operating_expenses:float = stock.FinancialStatements.IncomeStatement.OperatingExpenseAsReported.TwelveMonths
        deprecation_amortization:float = stock.FinancialStatements.IncomeStatement.DepreciationAndAmortization.TwelveMonths

        EBIT:float = total_revenue - operating_expenses
        EBITDA:float = EBIT + deprecation_amortization

        symbol_data:SymbolData = self.data[symbol]

        # make sure fundamental data are consecutive, because of delta calculation in growth ratio
        if not symbol_data.fundamentals_still_coming(curr_date, self.max_missing_days_fundamentals):
            symbol_data.reset_fundamentals()

        # make sure daily data (prices, volumes) are still coming
        if not symbol_data.daily_data_still_coming(curr_date, self.max_missing_days_daily_data):
            symbol_data.reset_daily_data()

        # check if required data for metrics calculations are ready
        if symbol_data.fundamentals_ready() and symbol_data.prices_ready() and symbol_data.volumes_ready() \
            and market_daily_returns != None: # and symbol_data.spread_ready():

            # calculate minor metrics values
            market_cap:float = stock.MarketCap
            total_assets:float = stock.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths
            gross_profit:float = stock.FinancialStatements.IncomeStatement.GrossProfit.TwelveMonths
            roe:float = stock.OperationRatios.ROE.OneYear
            operating_cash_flow:float = stock.FinancialStatements.CashFlowStatement.OperatingCashFlow.TwelveMonths
            total_liabilities:float = stock.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.TwelveMonths
            total_revenue:float = stock.FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths
            quick_ratio:float = stock.OperationRatios.QuickRatio.OneYear

            # profitability
            quality_metrics['Profitability']['gp_to_ta'][symbol] = gross_profit / total_assets
            quality_metrics['Profitability']['roe'][symbol] = roe
            quality_metrics['Profitability']['fcfo_to_ta'][symbol] = operating_cash_flow / total_assets
            quality_metrics['Profitability']['gpm'][symbol] = gross_profit

            # Growth
            quality_metrics['Growth']['sales'][symbol] = symbol_data.get_sales_change(total_revenue)
            quality_metrics['Growth']['gp'][symbol] = symbol_data.get_gross_profit_change(gross_profit)
            quality_metrics['Growth']['EBITDA'][symbol] = symbol_data.get_EBITDA_change(EBITDA)
            quality_metrics['Growth']['EBIT'][symbol] = symbol_data.get_EBIT_change(EBIT)

            # Rischio
            quality_metrics['Rischio']['dept_to_ta'][symbol] = total_liabilities / total_assets
            daily_returns:np.array = symbol_data.get_daily_returns()
            regression_model = self.MultipleLinearRegression(market_daily_returns, daily_returns)
            quality_metrics['Rischio']['market_beta'][symbol] = regression_model.params[-1]
            quality_metrics['Rischio']['inverse_QR'][symbol] = 1 / quick_ratio
            
            # Liquidity
            # inverse_spread:float = 1 / symbol_data.get_spread()
            turnover:float = symbol_data.get_volumes_mean() / market_cap
            quality_metrics['Liquidity']['turnover'][symbol] = turnover

            price_to_book[symbol] = stock.ValuationRatios.PBRatio

        # update stock's fundamentals
        symbol_data.set_total_revenue(total_revenue)
        symbol_data.set_EBIT(EBIT)
        symbol_data.set_EBITDA(EBITDA)
        symbol_data.set_gross_profit(gross_profit)
        symbol_data.set_last_fundamentals_update(curr_date)

        selected_symbols.append(stock.Symbol)

    # make sure there are enough stocks for selection
    if len(price_to_book) >= self.quantile:
        quality_values:Dict[Symbol, float] = {}

        for main_metric, minor_metrics_data in quality_metrics.items():
            main_metric_values:Dict[Symbol, float] = {}

            for minor_metric, values_by_symbol in minor_metrics_data.items():
                # sort stocks by their minor metric values in descending order
                sorted_by_value:List[Symbol] = [x[0] for x in sorted(values_by_symbol.items(), key=lambda item: item[1], reverse=False)]

                # create array of stocks ranks and calculate it's mean and std
                arranged_array:np.array = np.arange(1, len(sorted_by_value) + 1)
                minor_metric_mean:float = np.mean(arranged_array)
                minor_metric_std:float = np.std(arranged_array)

                # calculate stock's minor metric z-score based on stock's rank
                for i, symbol in enumerate(sorted_by_value):
                    minor_metric_z_score:float = ((i + 1) - minor_metric_mean) / minor_metric_std

                    if symbol not in main_metric_values:
                        main_metric_values[symbol] = 0
                    # sum z-scores of minor metrics to get the main metric value
                    main_metric_values[symbol] += minor_metric_z_score
            
            main_metric_mean:float = np.mean(list(main_metric_values.values()))
            main_metric_std:float = np.std(list(main_metric_values.values()))

            # calculate z-scores of main metrics
            for symbol, value in main_metric_values.items():
                main_metric_z_score:float = (value - main_metric_mean) / main_metric_std
                main_metric_z_score = -main_metric_z_score if main_metric == 'Rischio' else main_metric_z_score

                if symbol not in quality_values:
                    quality_values[symbol] = 0
                # summ z-scores of main metrics to get the quality values
                quality_values[symbol] += main_metric_z_score

        # calculate quality score
        quality_values_mean:float = np.mean(list(quality_values.values()))
        quality_values_std:float = np.std(list(quality_values.values()))
        quality_scores:Dict[Symbol] = { symbol: (quality_value - quality_values_mean) / quality_values_std \
            for symbol, quality_value in quality_values.items() }

        # calculate price score
        sorted_by_pb:List[Symbol] = [x[0] for x in sorted(price_to_book.items(), key=lambda item: item[1], reverse=False)]
        
        # create array of stocks ranks and calculate it's mean and std
        arranged_array:np.array = np.arange(1, len(sorted_by_pb) + 1)
        price_to_book_score_mean:float = np.mean(arranged_array)
        price_to_book_score_std:float = np.mean(arranged_array)
        price_scores:Dict[Symbol] = { symbol: ((i + 1) - price_to_book_score_mean) / price_to_book_score_std \
            for i, symbol in enumerate(sorted_by_pb) }
        
        # calculate final score as quality score minus price score
        final_score:Dict[Symbol, float] = { symbol: quality_scores[symbol] - price_scores[symbol] \
            for symbol in price_scores }

        quantile:int = int(len(final_score) / self.quantile)
        sorted_by_final_score:List[Symbol] = [x[0] for x in sorted(final_score.items(), key=lambda item: item[1], reverse=True)]

        # go long on the first decile and short on the last decile
        long_leg:List[Symbol] = sorted_by_final_score[:quantile]
        short_leg:List[Symbol] = sorted_by_final_score[-quantile:]

        for symbol in long_leg:
            self.weights[symbol] = 1 / quantile

        for symbol in short_leg:
            self.weights[symbol] = -1 / quantile

    return selected_symbols
    
def OnData(self, data:Slice) -> None:
    curr_date:datetime.date = self.Time.date()

    for symbol, symbol_data in self.data.items():
        if symbol in data and data[symbol]:
            spread:float = self.Securities[symbol].BidPrice - self.Securities[symbol].AskPrice
            price:float = data[symbol].Value
            volume:float = data[symbol].Volume

            self.data[symbol].update_prices(price)
            self.data[symbol].update_volumes(volume)
            self.data[symbol].set_spread(spread)

            self.data[symbol].set_last_daily_data_update(curr_date)

    if self.market in data and data[self.market]:
        price:float = data[self.market].Value
        self.market_prices.Add(price)

    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.weights:
            self.Liquidate(symbol)
            
    for symbol, w in self.weights.items():
        self.SetHoldings(symbol, w)
            
    self.weights.clear()

def GetMarketDailyReturns(self) -> List[float]:
    market_daily_prices:np.array= np.array(list(self.market_prices))
    return list((market_daily_prices[:-1] - market_daily_prices[1:]) / market_daily_prices[1:])

def MultipleLinearRegression(self, x:np.array, y:np.array):
    x:np.array = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
    
def Selection(self):
    # rebalance at the end of selection month
    if self.selection_month == self.Time.month:
        self.selection_flag = True
