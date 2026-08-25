# Original QuantConnect / library Python
# locale=en slug="predicting-bond-returns-with-equity-return"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from collections import deque
from AlgorithmImports import *
class PredictingBondReturnswithEquityReturn(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    # Bond future and equity etf.
    self.symbols = [
                    ("ASX_XT1", 'EWA'),       # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1 (Australia)
                    ("MX_CGB1",  'EWC'),      # Ten-Year Government of Canada Bond Futures, Continuous Contract #1 (Canada)
                    ("EUREX_FGBL1", 'EWG'),   # Euro-Bund (10Y) Futures, Continuous Contract #1 (Germany)
                    ("LIFFE_R1", 'EWU'),      # Long Gilt Futures, Continuous Contract #1 (U.K.)
                    ("SGX_JB1", 'EWJ'),       # SGX 10-Year Mini Japanese Government Bond Futures, Continuous Contract #1 (Japan)
                    ("CME_TY1",  'SPY')       # 10 Yr Note Futures, Continuous Contract #1 (USA)
                    ]
                
    # Monthly price data.
    self.data = {}
    
    self.month_period = 5
    self.period = self.month_period * 12 + 1
    
    self.SetWarmUp(self.period * 21)
    
    for bond_future, equity_etf in self.symbols:
        data = self.AddData(QuantpediaFutures, bond_future, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(10)
        
        # Equity data.
        self.AddEquity(equity_etf, Resolution.Daily)
        self.data[equity_etf] = deque(maxlen = self.period)
    
    self.last_month = -1
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0][1]), self.TimeRules.At(0, 0), self.Rebalance)
    
def OnData(self, data):
    # Update only on new month start.
    if self.Time.month == self.last_month:
        return
    self.last_month = self.Time.month

    # Store monthly data.
    for bond_future, equity_etf in self.symbols:
        if equity_etf in data and data[equity_etf]:
            price = data[equity_etf].Value
            self.data[equity_etf].append(price)
    
def Rebalance(self):
    # Z score calc.
    weight = {}
    for bond_future, equity_etf in self.symbols:
        if self.Securities[bond_future].GetLastData() and self.time.date() = minimum_data_count:
                closes = [x for x in self.data[equity_etf]]
                separete_yearly_returns = [Return(closes[x:x+13]) for x in range(0, len(closes),1)]
                return_mean = np.mean(separete_yearly_returns)
                return_std = np.std(separete_yearly_returns)
                z_score = (separete_yearly_returns[-1] - return_mean) / return_std
                
                if z_score > 1: z_score = 1
                elif z_score  Dict[Symbol, datetime.date]:
   return QuantpediaFutures._last_update_date
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['back_adjusted'] = float(split[1])
    data['spliced'] = float(split[2])
    data.Value = float(split[1])
    if config.Symbol.Value not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol.Value]:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = data.Time.date()
    return data
def Return(values):
return (values[-1] - values[0]) / values[0]
