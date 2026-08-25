# Original QuantConnect / library Python
# locale=en slug="基于收益差距的美股择时策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from collections import deque
from AlgoLib import *
import numpy as np
from scipy import stats

class FED_Model(XXX):
   def Initialize(self):
       self.SetStartDate(2000, 1, 1)
       self.SetCash(100000)
       self.data = {}
       self.period = 12 * 21
       self.SetWarmUp(self.period)
       self.market = self.AddEquity('SPY', Resolution.Daily).Symbol
       self.market_data = deque()
       self.cash = self.AddEquity('SHY', Resolution.Daily).Symbol
       self.risk_free_rate = self.AddData(QuandlValue, 'FRED/DGS3MO', Resolution.Daily).Symbol
       self.bond_yield = self.AddData(QuantpediaBondYield, 'US10YT', Resolution.Daily).Symbol
       self.sp_earnings_yield = self.AddData(QuandlValue, 'MULTPL/SP500_EARNINGS_YIELD_MONTH', 
Resolution.Daily).Symbol
       self.yield_gap = deque()
       self.recent_month = -1

   def OnData(self, data):
       rebalance_flag = False
       if self.sp_earnings_yield in data and data[self.sp_earnings_yield]:
           if self.Time.month != self.recent_month:
               self.recent_month = self.Time.month
               rebalance_flag = True
       if not rebalance_flag:
           if self.Securities[self.sp_earnings_yield].GetLastData():
               if (self.Time
.date() - self.Securities[self.sp_earnings_yield].GetLastData().Time.date()).days > 31:
                   self.Liquidate()
           if self.market in data and self.risk_free_rate in data and self.bond_yield in data:
               if data[self.market] and data[self.risk_free_rate] and data[self.bond_yield]:
                   market_price = data[self.market].Value
                   rf_rate = data[self.risk_free_rate].Value
                   bond_yield = data[self.bond_yield].Value
                   sp_ey = data[self.sp_earnings_yield].Value
                   if market_price != 0 and rf_rate != 0 and bond_yield != 0 and sp_ey != 0:
                       self.market_data.append((market_price, rf_rate))
                       yield_gap = np.log(sp_ey) - np.log(bond_yield)
                       self.yield_gap.append(yield_gap)
                       rebalance_flag = True
       min_count = 6
       if len(self.market_data) >= min_count:
           market_closes = np.array([x[0] for x in self.market_data])
           market_returns = (market_closes[1:] - market_closes[:-1]) / market_closes[:-1]
           rf_rates = np.array([x[1] for x in self.market_data][1:])
           excess_returns = market_returns - rf_rates
           yield_gaps = [x for x in self.yield_gap]
           beta, alpha, r_value, p_value, std_err = stats.linregress(yield_gaps[1:-1],
market_returns[1:])
           X = yield_gaps[-1]
           Y = alpha + (beta * X)
           if Y > 0:
               if self.Portfolio[self.cash].Invested:
                   self.Liquidate(self.cash)
               self.SetHoldings(self.market, 1)
           else:
               if self.Portfolio[self.market].Invested:
                   self.Liquidate(self.market)
               self.SetHoldings(self.cash, 1)
