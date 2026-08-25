# Original QuantConnect / library Python
# locale=en slug="黄金市场时机选择"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
from AlgorithmImports import *
class GoldMarketTiming(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1) 
    self.SetCash(100000)
    self.leverage: int = 5
    # United States Government 10-Year Bond Yield
    self.bond_yield: str = "US10YT"
    self.AddData(data_tools.QuantpediaBondYield, self.bond_yield, Resolution.Daily)
    # S&P 500 Earnings Yield. Earnings Yield = trailing 12 month earnings divided by index price 
    self.earnings_yield: str = "SP500_EARNINGS_YIELD_MONTH"
    self.AddData(data_tools.QuantpediaMonthlyData, self.earnings_yield, Resolution.Daily)
    # Gold Prices (Daily) - Currency USD (All values are national currency units per troy ounce)
    self.gold: str = "CME_GC1"
    data: Securities = self.AddData(data_tools.QuantpediaFutures, self.gold, Resolution.Daily)
    data.SetLeverage(self.leverage)
    data.SetFeeModel(data_tools.CustomFeeModel())
    # Custom chart.
    yieldPlot: Chart = Chart("Yield Plot")
    yieldPlot.AddSeries(Series("Bond Yield", SeriesType.Line, 0))
    yieldPlot.AddSeries(Series("Earnings Yield", SeriesType.Line, 0))
    self.AddChart(yieldPlot)
    
def OnData(self, data: Slice) -> None:
    custom_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.LastDateHandler.get_last_update_date()
    # monthly rebalance
    if self.earnings_yield in data and data[self.earnings_yield]:
        if self.Securities.ContainsKey(self.bond_yield) and self.Securities.ContainsKey(self.gold):
            by_data = self.Securities[self.bond_yield].GetLastData()
            gold_data = self.Securities[self.gold].GetLastData()
        
            if by_data and gold_data:
                if self.Time.date()  self.Securities[self.bond_yield].Price * 1.15:
                        self.SetHoldings(self.gold, 1)
                    else:
                        self.Liquidate()
                else:
                    self.Liquidate()
    if self.Securities.ContainsKey(self.earnings_yield):
        ey_data = self.Securities[self.earnings_yield].GetLastData()
        if ey_data:
            if self.Time.date() > custom_data_last_update_date[self.earnings_yield]:
                self.Liquidate()
                return
