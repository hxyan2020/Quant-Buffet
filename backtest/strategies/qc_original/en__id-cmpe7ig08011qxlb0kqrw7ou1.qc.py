# Original QuantConnect / library Python
# locale=en slug="期限利差和期限溢价预测策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
# endregion

class TermSpreadandTermPremiumPredictUSGovernmentBondsReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2007, 6, 1) # BIL inception
    self.SetCash(100000)

    self.long_duration_bond:Symbol = self.AddEquity('IEF', Resolution.Daily).Symbol
    self.short_duration_bond:Symbol = self.AddEquity('BIL', Resolution.Daily).Symbol
    self.term_spread:Symbol = self.AddData(TermSpread, 'T10Y3M', Resolution.Daily).Symbol

    self.period:int = 40 * 21
    self.rebalance_flag:bool = False

    self.term_spread_sma = self.SMA(self.term_spread, self.period, Resolution.Daily)
    self.SetWarmup(self.period, Resolution.Daily)

    self.recent_month:int = -1

def OnData(self, data: Slice) -> None:
    if self.IsWarmingUp:
        return

    t10y3m_last_update_date:datetime.date = TermSpread._last_update_date

    # check if custom data is still arriving
    if self.Securities[self.term_spread].GetLastData() and self.Time.date() >= t10y3m_last_update_date:
        self.Liquidate()
        return

    # rebalance monthly
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month

    # compare latest value with 40-month moving average
    traded_asset:Symbol|None = None
    risk_flag:bool = False

    if self.term_spread in data and data[self.term_spread]:
        if data[self.term_spread].Price  Dict[Symbol, datetime.date]:
   return TermSpread._last_update_date

def Reader(self, config, line, date, isLiveMode):
    data = TermSpread()
    data.Symbol = config.Symbol

    if not line[0].isdigit(): return None
    split = line.split(';')
    
    # Parse the CSV file's columns into the custom data class
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    if split[1] != '.':
        data.Value = float(split[1])

    if data.Time.date() > TermSpread._last_update_date:
        TermSpread._last_update_date = data.Time.date()
    
    return data
