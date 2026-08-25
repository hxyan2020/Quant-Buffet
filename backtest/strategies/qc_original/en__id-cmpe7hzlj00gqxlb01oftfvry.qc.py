# Original QuantConnect / library Python
# locale=en slug="石油贝塔不确定性与全球股票收益策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import statsmodels.api as sm
import data_tools
# endregion

class CasualApricotSalamander(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)

    tickers:list[str] = [
        'EWA',  # iShares MSCI Australia Index ETF
        'EWO',  # iShares MSCI Austria Investable Mkt Index ETF
        'EWK',  # iShares MSCI Belgium Investable Market Index ETF
        'EWZ',  # iShares MSCI Brazil Index ETF
        'EWC',  # iShares MSCI Canada Index ETF
        'FXI',  # iShares China Large-Cap ETF
        'EWQ',  # iShares MSCI France Index ETF
        'EWG',  # iShares MSCI Germany ETF 
        'EWH',  # iShares MSCI Hong Kong Index ETF
        'EWI',  # iShares MSCI Italy Index ETF
        'EWJ',  # iShares MSCI Japan Index ETF
        'EWM',  # iShares MSCI Malaysia Index ETF
        'EWW',  # iShares MSCI Mexico Inv. Mt. Idx
        'EWN',  # iShares MSCI Netherlands Index ETF
        'EWS',  # iShares MSCI Singapore Index ETF
        'EZA',  # iShares MSCI South Africe Index ETF
        'EWY',  # iShares MSCI South Korea ETF
        'EWP',  # iShares MSCI Spain Index ETF
        'EWD',  # iShares MSCI Sweden Index ETF
        'EWL',  # iShares MSCI Switzerland Index ETF
        'EWT',  # iShares MSCI Taiwan Index ETF
        'THD',  # iShares MSCI Thailand Index ETF
        'EWU',  # iShares MSCI United Kingdom Index ETF
        'SPY',  # SPDR S&P 500 ETF
    ]

    self.min_prices:int = 15
    self.regression_period:int = 24

    self.beta_index:int = 2 # relevant regression beta position
    self.t:float = 2.074    # https://www.sjsu.edu/faculty/gerstman/StatPrimer/t-table.pdf

    self.quantile:int = 5
    self.data:dict[Symbol, data_tools.SymbolData] = {}

    for ticker in tickers:
        security = self.AddEquity(ticker, Resolution.Daily)
        security.SetLeverage(5)

        self.data[security.Symbol] = data_tools.SymbolData(self.regression_period)
    
    self.msci_world:Symbol = self.AddEquity('URTH', Resolution.Daily).Symbol
    self.data[self.msci_world] = data_tools.SymbolData(self.regression_period)

    self.oil:Symbol = self.AddData(data_tools.QuantpediaFutures, 'CME_CL1', Resolution.Daily).Symbol
    self.data[self.oil] = data_tools.SymbolData(self.regression_period)

    self.recent_month:int = -1

def OnData(self, data: Slice):
    # update prices
    for symbol, symbol_obj in self.data.items():
        if symbol in data and data[symbol] and data[symbol].Value != 0:
            symbol_obj.update_prices(data[symbol].Value)

    # monthly rebalance
    if self.recent_month != self.Time.month:
        self.recent_month = self.Time.month
        curr_date:datetime.date = self.Time.date()

        # update all regression data
        for symbol, symbol_obj in self.data.items():
            if symbol_obj.prices_ready(self.min_prices):
                symbol_obj.update_regression_data(curr_date)
            else:
                # reset regression data in case of missing month -> makes sure data are consecutive
                symbol_obj.reset_regression_data()

            # clear space for next month prices
            symbol_obj.reset_prices()

        # get regression_x if possible
        regression_x:list[list[float]] = [
            self.data[self.msci_world].get_regression_data(),
            self.data[self.oil].get_regression_data()
        ] if self.data[self.msci_world].regression_data_ready() and \
             self.data[self.oil].regression_data_ready() else None

        if regression_x == None:
            # liquidate when regression x isn't ready
            self.Liquidate()
            return 

        oil_beta_uncertainty:dict[Symbol, float] = {}

        for symbol, symbol_obj in self.data.items():
            if symbol_obj.regression_data_ready() and symbol not in [self.msci_world, self.oil]:
                # calculate the measure of the oil beta uncertainty for stock market i in month t as a difference between the highest and lowest 95% confidence interval
                regression_y:list[float] = symbol_obj.get_regression_data()

                regression_model = self.MultipleLinearRegression(regression_x, regression_y)

                oil_beta:float = regression_model.params[self.beta_index]
                SE:float = regression_model.bse[self.beta_index]
                
                top_conf_interval:float = oil_beta + (self.t * SE)
                bottom_conf_interval:float = oil_beta - (self.t * SE)

                intervals_diff:float = top_conf_interval - bottom_conf_interval

                oil_beta_uncertainty[symbol] = intervals_diff

        # perform selection and trade
        if len(oil_beta_uncertainty) >= self.quantile:
            quantile:int = int(len(oil_beta_uncertainty) / self.quantile)
            sorted_by_uncertainty:list[Symbol] = [x[0] for x in sorted(oil_beta_uncertainty.items(), key=lambda item: item[1])]

            # buy quantile with highest values
            long_leg:list[Symbol] = sorted_by_uncertainty[-quantile:]
            # short quantile with lowest values
            short_leg:list[Symbol] = sorted_by_uncertainty[:quantile]

            # trade execution
            invested = [x.Key for x in self.Portfolio if x.Value.Invested]
            for symbol in invested:
                if symbol not in long_leg + short_leg:
                    self.Liquidate(symbol)

            long_length:int = len(long_leg)
            for symbol in long_leg:
                if symbol in data and data[symbol]:
                    self.SetHoldings(symbol, 1 / long_length)

            short_length:int = len(short_leg)
            for symbol in short_leg:
                if symbol in data and data[symbol]:
                    self.SetHoldings(symbol, -1 / short_length)
        else:
            self.Liquidate()

def MultipleLinearRegression(self, x:list, y:list):
    x:np.ndarray = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
