# Original QuantConnect / library Python
# locale=en slug="原油价格预测策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
import statsmodels.api as sm
# endregion
class ForecastingCrudeOilPrices(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    leverage:int = 3
    self.oil:Symbol = self.AddData(data_tools.QuantpediaFutures, 'CME_CL1', Resolution.Daily).Symbol
    self.Securities[self.oil].SetLeverage(leverage)
    self.gfu:Symbol = self.AddData(data_tools.GFU, 'GFU', Resolution.Daily).Symbol
    # self.test_size:float = 0.2
    self.min_period:int = 12
    self.price_storage:Dict[Symbol, List] = {}
    for symbol in [self.oil, self.gfu]:
        self.price_storage[symbol] = []
def OnData(self, data: Slice) -> None:
    rebalance = False
    # store daily price
    if self.gfu in data and data[self.gfu]:
        self.price_storage[self.gfu].append(data[self.gfu].Value)
        self.price_storage[self.oil].append(self.Securities[self.oil].Price)
        rebalance = True
    # rebalance once new GFU data arrived
    if rebalance:
        last_update_date = [c.get_last_update_date() for c in [data_tools.QuantpediaFutures, data_tools.GFU]]
        if all(self.Securities[symbol].GetLastData() and last_update_date[i] > self.Time.date() for i, symbol in enumerate([self.oil, self.gfu])):
            if all(len(self.price_storage[symbol]) >= self.min_period for symbol in [self.oil, self.gfu]):
                oil_prices:np.ndarray = np.array(self.price_storage[self.oil])
                x:np.ndarray = np.array(self.price_storage[self.gfu])[1:]
                y:np.ndarray = np.log(oil_prices[1:] / oil_prices[:-1]) # oil monthly log returns
                # run regression
                model = data_tools.multiple_linear_regression(x[:-1], y[1:])
                predicted_oil_return:float = model.predict([1, x[-1]])[0]
                # test_size:int = int(len(self.price_storage[self.oil]) * self.test_size)
                # model = data_tools.multiple_linear_regression(x[:-1][:-test_size], y[1:][:-test_size])
                # predicted_oil_return:float = model.predict(sm.add_constant(x[-test_size:]))[-1] if test_size > 1 else model_.predict([1, x[-test_size:]])[-1][0]
                # trade based on prediction
                if predicted_oil_return > 0:
                    self.SetHoldings(self.oil, 1)
                else:
                    # self.Liquidate(self.oil)
                    self.SetHoldings(self.oil, -1)
        else:
            self.Liquidate()
            return
