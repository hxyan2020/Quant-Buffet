# Original QuantConnect / library Python
# locale=zh slug="主动领口策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
class ActiveCollarStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    # collar settings
    self.targets = np.array([0.95, 1.05])   # initial target
    self.vix_signal = 0
    self.sma_signal_set = False
    self.vix_signal_set = False 
    self.macro_signal_set = False        
    
    option = self.AddOption("QQQ", Resolution.Minute)
    option.SetFilter(-60, +60, timedelta(0), timedelta(35))
    
    # index and sma
    data = self.AddEquity("QQQ", Resolution.Minute)
    data.SetLeverage(10)
    self.symbol = data.Symbol
    
    self.sma_5 = self.SMA(self.symbol, 5, Resolution.Daily)
    self.sma_50 = self.SMA(self.symbol, 50, Resolution.Daily)
    self.sma_150 = self.SMA(self.symbol, 150, Resolution.Daily)
    self.sma_200 = self.SMA(self.symbol, 200, Resolution.Daily)
    
    self.index_smas = [
        (None, self.sma_50),
        (self.sma_5, self.sma_150),
        (None, self.sma_200)
        ]
        
    # vix and SMAs
    self.vix = self.AddData(CBOE, 'VIX', Resolution.Daily).Symbol
    self.vix_sma_5 = self.SMA(self.vix, 5, Resolution.Daily)
    self.vix_std_5 = self.STD(self.vix, 5, Resolution.Daily)
    self.vix_sma_150 = self.SMA(self.vix, 150, Resolution.Daily)
    self.vix_std_150 = self.STD(self.vix, 150, Resolution.Daily)
    self.vix_sma_250 = self.SMA(self.vix, 250, Resolution.Daily)
    self.vix_std_250 = self.STD(self.vix, 250, Resolution.Daily)
    
    self.vix_sma_std = [
        (self.vix_sma_5, self.vix_std_5),
        (self.vix_sma_150, self.vix_std_150),
        (self.vix_sma_250, self.vix_std_250)
        ]
    # recession indicator, claims data and SMAs
    self.us_recession = self.AddData(FREDData, 'USREC', Resolution.Daily).Symbol     # monthly data  
    self.initial_claims = self.AddData(FREDData, 'ICSA', Resolution.Daily).Symbol    # weekly data
    self.claims_sma_10 = self.SMA(self.initial_claims, 10, Resolution.Daily)
    self.claims_sma_30 = self.SMA(self.initial_claims, 30, Resolution.Daily)
    self.claims_sma_40 = self.SMA(self.initial_claims, 40, Resolution.Daily)
    self.claims_smas = [
        self.claims_sma_10,
        self.claims_sma_30,
        self.claims_sma_40
        ]        
    
    self.SetWarmUp(250, Resolution.Daily)
    
    # Next expiry date.
    self.expiry_date = None
    self.recession_signal_lagged = RollingWindow[float](2)
    self.recession_signal_lagged.Add(-1)
    
    self.last_day = -1
    
def OnData(self, slice: Slice) -> None:
    # Open new trades only on market close.
    if not (self.Time.hour == 15 and self.Time.minute == 59):
        return
    
    last_update_date:Dict[str, datetime.date] = FREDData.get_last_update_date()
    # data stopped comming in
    if not all( self.Securities[x].GetLastData() and x.Value in last_update_date and self.Time.date()  long_sma:
                                self.targets += np.array([-0.01, 0.01])
                                # sma_signal += 1
                            else:
                                self.targets += np.array([+0.01, -0.01])
                                # sma_signal -= 1
                    else:
                        price = self.Securities[self.symbol].Price
                        if price > long_sma:
                            self.targets += np.array([-0.01, 0.01])
                            # sma_signal += 1
                        else:
                            # sma_signal -= 1
                            self.targets += np.array([+0.01, -0.01])
    
            # VIX signal calculation - quantity
            for sma_std in self.vix_sma_std:
                if sma_std[0].IsReady and sma_std[1].IsReady:
                    sma = sma_std[0].Current.Value
                    std = sma_std[1].Current.Value
                    current_vix = self.Securities[self.vix].Price
                    self.vix_signal_set = True
                    if current_vix > sma + 1*std:
                        self.vix_signal += 0.75
                    elif current_vix  claims_sma.Current.Value:
                                if recession_signal == 1:
                                    self.targets += np.array([0.01])
                                else:
                                    self.targets -= np.array([0.01])                
    
    for i in slice.OptionChains:
        chains = i.Value
        if not self.Portfolio.Invested:
            calls = list(filter(lambda x: x.Right == OptionRight.Call, chains))
            puts = list(filter(lambda x: x.Right == OptionRight.Put, chains))
            if not calls or not puts: return
        
            underlying_price = self.Securities[self.symbol].Price
            call_expiries = [i.Expiry for i in calls]
            call_strikes = [i.Strike for i in calls]
            # 1-month to expiration call
            call_expiry = min(call_expiries, key=lambda x: abs((x.date() - self.Time.date()).days - 30))
            put_expiries = [i.Expiry for i in puts]
            put_strikes = [i.Strike for i in puts]
            # 6-months to expiration put
            # put_expiry = min(put_expiries, key=lambda x: abs((x.date()-self.Time.date()).days-180))
            put_expiry = min(put_expiries, key=lambda x: abs((x.date()-self.Time.date()).days-30))  # one month expiration is used instead of 6 months
            # determine strikes
            put_strike = min(put_strikes, key = lambda x:abs(x - float(self.targets[0]) * underlying_price))    # changed by macro
            call_strike = min(call_strikes, key = lambda x:abs(x - float(self.targets[1]) * underlying_price))    # changed by macro
            
            put = [i for i in puts if i.Expiry == put_expiry and i.Strike == put_strike]
            call = [i for i in calls if i.Expiry == call_expiry and i.Strike == call_strike]
            
            if call_expiry:
                self.expiry_date = call_expiry   # store shorter expiry date
            
            if put and call:
                # All three signals were set to trade.
                if self.sma_signal_set and self.vix_signal_set and self.macro_signal_set:
                    options_q:int = int(self.Portfolio.TotalPortfolioValue / (underlying_price * 100))  # changed by vix
                    if options_q >= 1:
                        # buy index.
                        self.SetHoldings(self.symbol, 1)
                        
                        # sell call
                        self.Sell(call[0].Symbol, self.vix_signal)
                        
                        # buy put
                        self.Buy(put[0].Symbol, options_q)
                    
                    # monthly signal reset
                    self.vix_signal = 0
                    self.sma_signal_set = False
                    self.vix_signal_set = False 
                    self.macro_signal_set = False
                    self.targets = np.array([0.95, 1.05])
            else:
                pass
    invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    if len(invested) == 1:
        self.Liquidate(self.symbol)
# Source: https://fred.stlouisfed.org/series/T10Y3M
class FREDData(PythonData):
def GetSource(self, config:SubscriptionDataConfig, date:datetime, isLiveMode:bool) -> SubscriptionDataSource:
    return SubscriptionDataSource(f'data.quantpedia.com/backtesting_data/economic/{config.Symbol.Value}.csv', SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
_last_update_date:Dict[str, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[str, datetime.date]:
   return FREDData._last_update_date
def Reader(self, config:SubscriptionDataConfig, line:str, date:datetime, isLiveMode:bool) -> BaseData:
    data = FREDData()
    data.Symbol = config.Symbol
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    # Parse the CSV file's columns into the custom data class
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + relativedelta(months=1)
    if split[1] != '.':
        data.Value = float(split[1])
    # store last update date
    if config.Symbol.Value not in FREDData._last_update_date:
        FREDData._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > FREDData._last_update_date[config.Symbol.Value]:
        FREDData._last_update_date[config.Symbol.Value] = data.Time.date()
    
    return data
