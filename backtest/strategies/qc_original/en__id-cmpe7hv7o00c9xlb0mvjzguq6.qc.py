# Original QuantConnect / library Python
# locale=en slug="基于文本分析的经济衰退预测策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List
from data_tools import FREDData, Data, IndexMRI, IndexNBER, MultipleLinearRegression
# endregion

class TextBasedRecessionDetectionStrategy(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    
    self.leverage: int = 5
    self.recent_month: int = -1
    self.regression_period: int = 6
    self.max_missing_days: int = 35
    self.min_values: int = 15
    self.threshold: float = 0.5

    self.data: Data = Data(self.regression_period)

    security: Equity = self.AddEquity('SPY', Resolution.Daily)
    security.SetLeverage(self.leverage)

    self.spy: Symbol = security.Symbol

    security: Equity = self.AddEquity('BIL', Resolution.Daily)
    security.SetLeverage(self.leverage)

    self.bil: Symbol = security.Symbol

    self.baa10ym: Symbol = self.AddData(FREDData, 'BAA10YM', Resolution.Daily).Symbol
    self.t10y3m: Symbol = self.AddData(FREDData, 'T10Y3M', Resolution.Daily).Symbol

    self.mri: Symbol = self.AddData(IndexMRI, 'MRI', Resolution.Daily).Symbol
    self.nber: Symbol = self.AddData(IndexNBER, 'NBER', Resolution.Daily).Symbol

def OnData(self, slice: Slice) -> None:
    if self.baa10ym in slice and slice[self.baa10ym]:
        # monthly data
        curr_date:datetime.date = self.Time.date()

        # make sure data still coming
        if not self.data.baa10ym_data_still_coming(curr_date, self.max_missing_days):
            self.data.reset_baa10ym()

        self.data.update_baa10ym(curr_date, slice[self.baa10ym].Value)

    if self.t10y3m in slice and slice[self.t10y3m]:
        # daily data
        self.data.update_t10y3m(slice[self.t10y3m].Value)

    if self.mri in slice and slice[self.mri]:
        # daily data
        self.data.update_mri(slice[self.mri].Value)

    if self.nber in slice and slice[self.nber]:
        # monthly data
        curr_date:datetime.date = self.Time.date()

        # make sure data still coming
        if not self.data.nber_data_still_coming(curr_date, self.max_missing_days):
            self.data.reset_nber()

        self.data.update_nber(self.Time.date(), slice[self.nber].Value)

    # rebalance monthly
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month

    # if there aren't enough daily data, monthly data for regresion will be reset
    self.data.update_monthly_values(self.min_values)
    self.data.reset_daily_values()

    if not self.data.regression_data_ready():
        self.Liquidate()
    else:
        train_y: List[float] = self.data.get_train_regression_y()
        train_x: List[List[float]] = self.data.get_train_regression_x()

        regression_model = MultipleLinearRegression(train_x, train_y)
        
        test_x: List[List[float]] = self.data.get_test_regression_x()
        predicted_value: float = regression_model.predict(test_x)[0]

        if predicted_value > self.threshold:
            self.Liquidate(self.spy)
            if self.bil in slice and slice[self.bil]:
                self.SetHoldings(self.bil, 1)

        else:
            self.Liquidate(self.bil)
            if self.spy in slice and slice[self.spy]:
                self.SetHoldings(self.spy, 1)
