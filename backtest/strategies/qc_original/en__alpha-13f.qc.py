# Original QuantConnect / library Python
# locale=en slug="alpha克隆策略-跟踪13f文件"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
import numpy as np
from dateutil.relativedelta import relativedelta

class ManagerBestPicksFrom13FFilings(XXX):

def Initialize(self):
    self.SetStartDate(2011, 1, 1)  # Starting date
    self.SetCash(100000)  # Initial capital

    self.UniverseSettings.Leverage = 5  # Leverage
    self.UniverseSettings.Resolution = Resolution.Daily  # Data resolution
    self.AddUniverse(self.SelectStocksBasedOn13F)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0
    
    self.delay_months: int = 2  # Delay in months to consider 13F filings
    self.update_period: datetime.date

    self.stock_weights: dict[Symbol, float] = {}
    self.manager_selections: dict[datetime, dict[str, int]] = self.LoadManagerSelections()
    self.update_flag: bool = False

    reference: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthStart(reference), self.TimeRules.AfterMarketOpen(reference), self.DecideToUpdate)

def OnSecuritiesChanged(self, changes: SecurityChanges):
    for security in changes.AddedSecurities:
        security.SetFeeModel(AdjustedFeeModel())
        
def SelectStocksBasedOn13F(self, fundamentals: List[Fundamental]):
    if not self.update_flag:
        return Universe.Unchanged
    
    target_selection: dict[str, int] = None
    lookback_date: datetime.date = self.Time.date() - relativedelta(months=self.delay_months + 1)
    current_date: datetime.date = self.Time.date()
    
    # Finding the most recent manager selections
    for date, selections in self.manager_selections.items():
        if lookback_date  Dict[datetime, Dict[str, int]]:
    selections: dict[datetime, dict[str, int]] = {}
    data = self.Download('path_to_13F_filings_data.csv')
    for line in data.split('\n')[1:]:
        parts = line.split(',')
        date = datetime.strptime(parts[0], "%Y-%m-%d").date()
        
        if date not in selections:
            selections[date] = {}
        
        for ticker in parts[1:]:
            if ticker not in selections[date]:
                selections[date][ticker] = 0
            selections[date][ticker] += 1
            
        self.update_period = date  # Last update

    return selections

class AdjustedFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
