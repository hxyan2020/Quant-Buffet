# Original QuantConnect / library Python
# locale=en slug="lunar-monthly-effect-in-chinese-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import CustomFeeModel, GregorianLunarDates, ChinaIndexData
# endregion

class LunarMonthlyEffectInChineseStocks(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5

    self.liquidate_period:int = 28
    self.liquidate_on_date_flag:bool = False
    self.open_date:Union[datetime.date, None] = None
    self.liquidate_date:Union[datetime.date, None] = None

    self.fxi_flag:bool = True

    data = self.AddEquity('FXI', Resolution.Daily) if self.fxi_flag else self.AddData(ChinaIndexData, 'HANG_SENG', Resolution.Daily)
    data.SetFeeModel(CustomFeeModel())
    data.SetLeverage(self.leverage)
    self.china_market:Symbol = data.Symbol

    self.gregorian_dates:Symbol = self.AddData(GregorianLunarDates, 'gregorian_lunar_dates', Resolution.Daily).Symbol

def OnData(self, data: Slice):
    if self.gregorian_dates in data and data[self.gregorian_dates]:
        date:str = data[self.gregorian_dates].GetProperty('gregorian_date_end_first_lunar_month')
        self.liquidate_date = datetime.strptime(date, '%d.%m.%Y').date()
        self.open_date = self.Time.date()

        if self.Time.year != 2005: # data error prevention
            if self.Securities[self.china_market].Price != 0 and self.Securities[self.china_market].IsTradable:
                self.SetHoldings(self.china_market, 1)

    if self.Portfolio.Invested:
        if self.liquidate_on_date_flag and self.Time.date() >= self.liquidate_date:
            self.Liquidate()

        elif not self.liquidate_on_date_flag and (self.Time.date() - self.open_date).days >= self.liquidate_period:
            self.Liquidate()
