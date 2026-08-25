# Original QuantConnect / library Python
# locale=zh slug="国际政府债券回报中的横截面季节性效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from collections import deque
class SeasonalitiesBondReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = {
        "ASX_XT1",       # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1 (Australia)
        "MX_CGB1",       # Ten-Year Government of Canada Bond Futures, Continuous Contract #1 (Canada)
        "EUREX_FOAT1",   # Euro-OAT Futures, Continuous Contract #1 (France)
        "EUREX_FGBL1",   # Euro-Bund (10Y) Futures, Continuous Contract #1 (Germany)
        "LIFFE_R1",      # Long Gilt Futures, Continuous Contract #1 (U.K.)
        "EUREX_FBTP1",   # Long-Term Euro-BTP Futures, Continuous Contract #1 (Italy)
        "CME_TY1",       # 10 Yr Note Futures, Continuous Contract #1 (USA)
        "SGX_JB1"        # SGX 10-Year Mini Japanese Government Bond Futures, Continuous Contract #1 (Japan)
    }
    # daily price data
    self.data = {}
    
    # monthly returns
    self.monthly_return = {}
    
    self.daily_period = 21
    self.monthly_period = 20 * 12
    self.traded_count = 1
    for symbol in self.symbols:
        # Bond future data.
        data = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(5)
        
        self.data[symbol] = RollingWindow[float](self.daily_period)
        self.monthly_return[symbol] = deque(maxlen=self.monthly_period)
    
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.settings.daily_precise_end_time = False
    self.rebalance_flag: bool = False
    self.Schedule.On(self.DateRules.MonthEnd('ASX_XT1'), self.TimeRules.At(0, 0), self.Rebalance)

def OnData(self, data):
    # store monthly future returns
    for symbol in self.symbols:
        if symbol in data and data[symbol]:
            price = data[symbol].Value
            self.data[symbol].Add(price)
    
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    curr_month = self.Time.month
    SAME = {}
    
    # store monthly returns
    for symbol in self.symbols:
        if self.Securities[symbol].GetLastData() and self.Time.date() = self.monthly_period / 2:
                    next_month = curr_month+1 if curr_month = self.traded_count * 2:
        # decile = int(len(SAME) / self.quantile)
        # count = decile
    
        # sorting by SAME
        sorted_by_SAME = sorted(SAME.items(), key = lambda x: x[1], reverse = True)
        long = [x[0] for x in sorted_by_SAME[:self.traded_count]]
        short = [x[0] for x in sorted_by_SAME[-self.traded_count:]]
    # order execution
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([long, short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / self.traded_count))
    
    self.SetHoldings(targets, True)
def Rebalance(self):
    self.rebalance_flag = True
