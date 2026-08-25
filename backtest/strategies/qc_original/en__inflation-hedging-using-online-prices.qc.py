# Original QuantConnect / library Python
# locale=en slug="inflation-hedging-using-online-prices"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List
from data_tools import CustomFeeModel, QuantpediaInflationUS, InflationData
# endregion

class InflationHedgingUsingOnlinePrices(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2008, 1, 1)
    self.SetEndDate(2015, 8, 1)
    self.SetCash(100000)

    self.leverage:int = 5

    self.index_ps_period:int = 60
    self.median_period:int = 21 * 12
    self.SetWarmUp(self.median_period, Resolution.Daily)

    self.upper_percentile_threshold:int = 80
    self.lower_percentile_threshold:int = 20

    data = self.AddEquity('TIP', Resolution.Daily)
    data.SetFeeModel(CustomFeeModel())
    data.SetLeverage(self.leverage)

    self.tip:Symbol = data.Symbol

    data = self.AddEquity('IEF', Resolution.Daily)
    data.SetFeeModel(CustomFeeModel())
    data.SetLeverage(self.leverage)

    self.ief:Symbol = data.Symbol

    # Source: http://www.thebillionpricesproject.com/datasets/
    self.inflation_index:Symbol = self.AddData(
        QuantpediaInflationUS, 'US_ONLINE_INFLATION', Resolution.Daily).Symbol

    self.inflation_data:InflationData = InflationData(self.index_ps_period, self.median_period)

def OnData(self, data: Slice):
    self.Liquidate()

    if not (self.inflation_index in data and data[self.inflation_index]):
        self.Liquidate()
    else:
        index_ps:float = data[self.inflation_index].Value

        self.inflation_data.update_index_ps_values(index_ps)

        if self.inflation_data.index_ps_values_ready():
            self.inflation_data.update_medians()

            if self.inflation_data.medians_ready():
                online_inflation_trend:float = self.inflation_data.get_latest_median()
                median_values:List[float] = self.inflation_data.get_medians()

                upper_threshold:float = np.percentile(median_values, self.upper_percentile_threshold)
                lower_threshold:float = np.percentile(median_values, self.lower_percentile_threshold)

                if online_inflation_trend > upper_threshold:
                    # if Online Inflation Trend > 80%, then we go long breakeven index (long 100% TIPS, short 100% nominal Treasuries)
                    self.SetHoldings(self.tip, 1)
                    self.SetHoldings(self.ief, -1)
                elif online_inflation_trend
