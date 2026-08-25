# Original QuantConnect / library Python
# locale=zh slug="通过全面就业与部分就业指标来择时的标普500策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import pandas as pd
class Full_Partial_Employment(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetEndDate(2019, 7, 1)
    self.SetCash(100000)
    
    self.employment_data = pd.read_csv('https://docs.google.com/spreadsheets/d/1P0E8_ZUAm1NhqaMB1PK1Bc5uB2wL3f6W/export?format=csv', dtype={'date':str}, index_col='date') #   header=None)
    
    symbols = ['SPY', 'IEF']
    for symbol in symbols:
        self.AddEquity(symbol, Resolution.Daily)
    self.Schedule.On(self.DateRules.MonthStart(symbols[0]), self.TimeRules.AfterMarketOpen(symbols[0]), self.Rebalance)
def Rebalance(self):
    date = str(self.Time.month) + '/' + str(self.Time.year)
    current_row_index = self.employment_data.index.get_loc(date)
    
    #one month lag due to employment data reporting
    this_month = self.employment_data.iloc[current_row_index-1]
    last_month = self.employment_data.iloc[current_row_index-2]
    full_time_diff = this_month['full_time'] - last_month['full_time']
    part_time_diff = this_month['part_time'] - last_month['part_time']
    if full_time_diff > part_time_diff:
        if not self.Portfolio['SPY'].Invested:
            self.Liquidate('IEF')
            self.SetHoldings('SPY', 1)
    else:
        if not self.Portfolio['IEF'].Invested:
            self.Liquidate('SPY')
            self.SetHoldings('IEF
