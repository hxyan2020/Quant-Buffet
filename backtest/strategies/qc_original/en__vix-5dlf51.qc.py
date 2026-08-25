# Original QuantConnect / library Python
# locale=en slug="利用vix期货的期限结构"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
import pandas as pd
import statsmodels.api as sm
from collections import deque

class ExploitingTermStructureVIXFutures(XXX):

def Initialize(self):
    self.SetStartDate(2011, 1, 1)
    self.SetCash(100000)

    self.vix = self.AddData(QuandlVix, "CBOE/VIX", Resolution.Daily).Symbol              # Add Quandl VIX price (daily)
    self.vx1 = self.AddData(QuandlFutures, "CHRIS/CBOE_VX1", Resolution.Daily).Symbol    # Add Quandl VIX front month futures data (daily)
    self.es1 = self.AddData(QuandlFutures, "CHRIS/CME_ES1", Resolution.Daily).Symbol     # Add Quandl E-mini S&P500 front month futures data (daily)

    vx_data = self.AddFuture(Futures.Indices.VIX)
    vx_data.SetFilter(timedelta(0), timedelta(days=180))
    vx_data.MarginModel = BuyingPowerModel(5) # leverage
    
    es_data = self.AddFuture(Futures.Indices.SP500EMini)
    es_data.SetFilter(timedelta(0), timedelta(days=180))
    es_data.MarginModel = BuyingPowerModel(5) # leverage

    self.front_VX = None
    self.front_ES = None

    # request the history to warm-up the price and time-to-maturity 
    hist = self.History([self.vx1, self.es1], timedelta(days=450), Resolution.Daily)
    settle = hist['settle'].unstack(level=0)
    
    # the rolling window to save the front month VX future price
    self.price_VX = deque(maxlen=252)   
    # the rolling window to save the front month ES future price
    self.price_ES = deque(maxlen=252)   
    # the rolling window to save the time-to-maturity of the contract
    self.days_to_maturity = deque(maxlen=252) 
    
    expiry_date = self.get_expiry_calendar()
    df = pd.concat([settle, expiry_date], axis=1, join='inner')

    for index, row in df.iterrows():
        self.price_VX.append(row[str(self.vx1) + ' 2S'])
        self.price_ES.append(row[str(self.es1) + ' 2S'])
        self.days_to_maturity.append((row['expiry']-index).days)
        
    self.Schedule.On(self.DateRules.EveryDay(self.vix), self.TimeRules.AfterMarketOpen(self.vix), self.Rebalance)

def OnData(self, data):
    # select the nearest VIX and E-mini S&P500 futures with at least 10 trading days to maturity 
    # if the front contract expires, roll forward to the next nearest contract
    for chain in data.FutureChains:
        future_indices = chain.Key.Value[1:] # First letter in this variable is '/'
        
        if future_indices == Futures.Indices.VIX:
            if self.front_VX is None or ((self.front_VX.Expiry-self.Time).days = self.Time + timedelta(days = 10), chain.Value))
                self.front_VX = sorted(contracts, key = lambda x: x.Expiry)[0]
        if future_indices == Futures.Indices.SP500EMini:
            if self.front_ES is None or ((self.front_ES.Expiry-self.Time).days = self.Time + timedelta(days = 10), chain.Value))
                self.front_ES = sorted(contracts, key = lambda x: x.Expiry)[0]

def Rebalance(self):
    if self.Securities.ContainsKey(self.vx1) and self.Securities.ContainsKey(self.es1):
        # update the rolling window price and time-to-maturity series every day
        if self.front_VX and self.front_ES:
            self.price_VX.append(float(self.Securities[self.vx1].Price))
            self.price_ES.append(float(self.Securities[self.es1].Price))
            self.days_to_maturity.append((self.front_VX.Expiry-self.Time).days)
        
            # calculate the daily roll
            daily_roll = (self.Securities[self.vx1].Price - self.Securities[self.vix].Price)/(self.front_VX.Expiry-self.Time).days

            if not self.Portfolio[self.front_VX.Symbol].Invested:
                # Short if the contract is in contango with adaily roll greater than 0.10 
                if daily_roll > 0.1:
                    hedge_ratio = self.CalculateHedgeRatio()
                    self.SetHoldings(self.front_VX.Symbol, -0.4)
                    self.SetHoldings(self.front_ES.Symbol, -0.4*hedge_ratio)
                # Long if the contract is in backwardation with adaily roll less than -0.10
                elif daily_roll  -0.05:
                self.Liquidate()
                self.front_VX = None
                self.front_ES = None
                return
            
    if self.front_VX and self.front_ES:
        # if these exit conditions are not triggered, trades are exited two days before it expires
        if self.Portfolio[self.front_VX.Symbol].Invested and self.Portfolio[self.front_ES.Symbol].Invested: 
            if (self.front_VX.Expiry-self.Time).days
