# Original QuantConnect / library Python
# locale=zh slug="何时持有股票，何时持有黄金"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from scipy import stats
from typing import List, Dict
import data_tools
class WhentoOwnStocksandWhentoOwnGold(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(1996, 1, 1)
    self.SetCash(100000)
    self.warmpup_period: int = 100*12*21
    data: Securities = self.AddEquity('SPY', Resolution.Daily)
    self.spy_symbol: Symbol = data.Symbol
    
    self.SetWarmUp(timedelta(self.warmpup_period), Resolution.Daily)    # Load data from 100 years ago.
    
    self.smi: List[float] = []       # SMI indicator historical values.
    self.cape_symbol: Symbol = self.AddData(data_tools.QuantpediaMonthlyData, 'SHILLER_PE_RATIO_MONTH', Resolution.Daily).Symbol
    
    data: Security = self.AddData(data_tools.QuantpediaFutures, 'CME_GC1', Resolution.Daily)
    data.SetFeeModel(data_tools.CustomFeeModel())
    self.gold_symbol: Symbol = data.Symbol
    
    stockPlot: Chart = Chart('SMI')
    stockPlot.AddSeries(Series('SMI', SeriesType.Line, 0))
    
    # self.last_month = 0
    self.rebalance_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.spy_symbol), self.TimeRules.AfterMarketOpen(self.spy_symbol), self.Rebalance)
    self.settings.daily_precise_end_time = False
def OnData(self, data: Slice) -> None:
    custom_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.LastDateHandler.get_last_update_date()
    if (self.Securities[self.cape_symbol].GetLastData() and self.Time.date() > custom_data_last_update_date[self.cape_symbol]) or \
        (self.Securities[self.gold_symbol].GetLastData() and self.Time.date() > custom_data_last_update_date[self.gold_symbol]):
        self.Liquidate()
        return
    # Cape value comes at the start of the month
    if self.cape_symbol in data and data[self.cape_symbol] and self.gold_symbol in data and data[self.gold_symbol]:
        gold_price: float = data[self.gold_symbol].Value
        cape: float = data[self.cape_symbol].Value
        
        if cape == 0:
            return
        
        if gold_price == 0:
            gold_price = 19.25
            
        smi: float = cape / np.log(gold_price)
        self.Plot('SMI', 'SMI', smi)
        self.smi.append(smi)
    if not self.rebalance_flag:
        return
    # if self.spy_symbol in data and data[self.spy_symbol] and self.gold_symbol in data and data[self.gold_symbol]:
    self.rebalance_flag = False 
    if len(self.smi) != 0:
        data_points = [x for x in range(0, len(self.smi))]
        slope, intercept, r_value, p_value, std_err = stats.linregress(data_points, self.smi)
        # Linear regression - X = independent, Y = dependent
        # y = alpha + beta.x
        alpha = intercept
        beta = slope
        x = data_points[-1]
        y = alpha + (beta*x)
        
        smi = self.smi[-1]
        if self.spy_symbol in data and data[self.spy_symbol] and self.gold_symbol in data and data[self.gold_symbol]:
            if smi > y + 1*std_err:
                self.Liquidate(self.spy_symbol)
                self.SetHoldings(self.gold_symbol, 1)
            elif smi  None:
    self.rebalance_flag = True
