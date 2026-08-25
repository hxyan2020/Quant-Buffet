# Original QuantConnect / library Python
# locale=en slug="gold-to-oil-ratio-predicts-aggregate-stock-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import statsmodels.api as sm
import data_tools
# endregion

class GoldToOilRatioPredictsAggregateStockReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.min_monthly_prices:int = 15
    self.regression_period:int = 5 * 12 + 1 # need n months of data

    self.min_market_alloc:float = 0.
    self.max_market_alloc:float = 1.5
    self.risk_aversion_coefficient:int = 3

    self.spy_daily_prices:list[float] = []
    self.latest_go_predictor:float = None

    self.regression_data:RegressionData = data_tools.RegressionData(self.regression_period)

    security = self.AddEquity('SPY', Resolution.Daily)
    security.SetLeverage(5)
    self.spy_symbol:Symbol = security.Symbol

    security = self.AddEquity('BIL', Resolution.Daily)
    security.SetLeverage(5)
    self.bil_symbol:Symbol = security.Symbol

    self.oil_symbol:Symbol = self.AddCfd('WTICOUSD', Resolution.Daily).Symbol
    self.gold_symbol:Symbol = self.AddCfd('XAUUSD', Resolution.Daily).Symbol

    self.recent_month:int = -1

def OnData(self, data: Slice):
    # rebalance monthly
    if self.recent_month != self.Time.month:
        self.recent_month = self.Time.month
    
        if len(self.spy_daily_prices) >= self.min_monthly_prices and self.latest_go_predictor:
            monthly_return:float = (self.spy_daily_prices[-1] - self.spy_daily_prices[0]) / self.spy_daily_prices[0]
            self.regression_data.update(monthly_return, self.latest_go_predictor)

            if self.regression_data.is_ready():
                x_train, x_predict = self.regression_data.get_x_data()
                y_train:list[float] = self.regression_data.get_y_data()

                regression_model = self.MultipleLinearRegression(x_train, y_train)
                market_return_prediction:float = regression_model.predict([1, x_predict])[0]
                sse:float = np.sum(regression_model.resid ** 2) # regression_model.ssr
                variance:float = sse / ((self.regression_period - 1) - 2)

                market_allocation:float = (1 / self.risk_aversion_coefficient) * (market_return_prediction / variance)
                market_allocation:float = max(self.min_market_alloc, min(market_allocation, self.max_market_alloc))

                if self.bil_symbol in data and self.spy_symbol in data and data[self.bil_symbol] and data[self.spy_symbol]:
                    self.SetHoldings(self.spy_symbol, market_allocation)
                    self.SetHoldings(self.bil_symbol, 1 - market_allocation)
        else:
            # reset regresion data, because they stopped being consecutive
            self.regression_data.reset_data()
            self.Liquidate()

        # reset
        self.latest_go_predictor = None
        self.spy_daily_prices.clear()

    # update GO predictor
    if self.oil_symbol in data and self.gold_symbol in data and data[self.oil_symbol] and data[self.gold_symbol]:
        oil_price:float = data[self.oil_symbol].Value
        gold_price:float = data[self.gold_symbol].Value

        go_predictor:float = np.log(gold_price / oil_price)

        self.latest_go_predictor = go_predictor

    # update spy daily prices
    if self.spy_symbol in data and data[self.spy_symbol]:
        price:float = data[self.spy_symbol].Value
        self.spy_daily_prices.append(price)

def MultipleLinearRegression(self, x:list, y:list):
    x:np.array = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
