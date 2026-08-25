# Original QuantConnect / library Python
# locale=en slug="credit-informed-tactical-asset-allocation"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from math import exp
import statsmodels.api as sm
from typing import List, Dict
import data_tools
# endregion

class CreditInformedTacticalAssetAllocation(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.T: float = 5.               # maturity assumption
    self.RR: float = .4              # recovery rate assumption
    self.r: float = .123             # annual premium rate; source: Source paper
    self.traded_weight: float = 1.2
    self.leverage: int = 5

    self.market_index: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    data: Security = self.AddData(data_tools.QuantpediaFutures, 'CME_ES1', Resolution.Daily)
    data.SetLeverage(self.leverage)
    data.SetFeeModel(data_tools.CustomFeeModel())
    self.market_futures: Symbol = data.Symbol
    
    self.HYB: Symbol = self.AddData(data_tools.QuantpediaDailyData, 'BAMLH0A2HYB', Resolution.Daily).Symbol

    # regression data
    self.regression_period: int = 3*21
    self.default_probability_values: RollingWindow = RollingWindow[float](self.regression_period)
    self.index_values: RollingWindow = RollingWindow[float](self.regression_period)

    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

def OnData(self, data: Slice) -> None:
    custom_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.LastDateHandler.get_last_update_date()

    if (self.Securities[self.market_futures].GetLastData() and self.Time.date() > custom_data_last_update_date[self.market_futures]) or \
        (self.Securities[self.HYB].GetLastData() and self.Time.date() > custom_data_last_update_date[self.HYB]):
        self.Liquidate()
        return

    # all needed data are present in the algorithm
    if data.ContainsKey(self.market_index) and data.ContainsKey(self.market_futures) and data.ContainsKey(self.HYB):
        oas: float = data[self.HYB].Value / 10000
        hazard_rate: float = oas * (1 / (1-self.RR))
        default_probability: float = 1 - exp(-self.T * hazard_rate)

        self.default_probability_values.Add(default_probability)

        # apply the equity premium rate
        I: float = data[self.market_index].Value
        I_adjusted: float = I * exp(self.r * self.T)
        self.index_values.Add(I_adjusted)
        
        # data for regression are ready
        if self.default_probability_values.IsReady and self.index_values.IsReady:
            model: RegressionResultsWrapper = self.MultipleLinearRegression(list(self.default_probability_values), list(self.index_values))
            if model.resid[0]
