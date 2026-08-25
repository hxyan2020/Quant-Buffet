# Original QuantConnect / library Python
# locale=en slug="turn-of-the-month-effect-in-futures-momentum-strategy"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from collections import deque
from pandas.tseries.offsets import BDay
from pandas.tseries.offsets import BMonthEnd
class TOMEffectFuturesMomentumStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(1991, 1, 1)
    self.SetCash(100000)
    self.symbols = [
        "CME_S1",       # Soybean Futures, Continuous Contract 
        "CME_W1",       # Wheat Futures, Continuous Contract 
        "CME_BO1",      # Soybean Oil Futures, Continuous Contract
        "CME_C1",       # Corn Futures, Continuous Contract
        "CME_O1",       # Oats Futures, Continuous Contract
        "CME_LC1",      # Live Cattle Futures, Continuous Contract
        "CME_FC1",      # Feeder Cattle Futures, Continuous Contract
        "CME_GC1",      # Gold Futures, Continuous Contract
        "CME_SI1",      # Silver Futures, Continuous Contract
        "CME_PL1",      # Platinum Futures, Continuous Contract
        "CME_CL1",      # Crude Oil Futures, Continuous Contract
        "CME_HG1",      # Copper Futures, Continuous Contract
        "CME_PA1",      # Palladium Futures, Continuous Contract 
        "CME_RR1",      # Rough Rice Futures, Continuous Contract
        "ICE_CC1",      # Cocoa Futures, Continuous Contract 
        "ICE_KC1",      # Coffee C Futures, Continuous Contract
        "ICE_OJ1",      # Orange Juice Futures, Continuous Contract
        "ICE_SB1",      # Sugar No. 11 Futures, Continuous Contract
        "ICE_RS1",      # Canola Futures, Continuous Contract
        "ICE_GO1",      # Gas Oil Futures, Continuous Contract
        "CME_RB2",      # Gasoline Futures, Continuous Contract
        "CME_KW2",      # Wheat Kansas, Continuous Contract
        "ICE_WT1",      # WTI Crude Futures, Continuous Contract
        "CME_AD1",      # Australian Dollar Futures, Continuous Contract #1
        "CME_BP1",      # British Pound Futures, Continuous Contract #1
        "CME_CD1",      # Canadian Dollar Futures, Continuous Contract #1
        "CME_EC1",      # Euro FX Futures, Continuous Contract #1
        "CME_JY1",      # Japanese Yen Futures, Continuous Contract #1
        "CME_SF1",      # Swiss Franc Futures, Continuous Contract #1
                    
        "CME_NQ1",      # E-mini NASDAQ 100 Futures, Continuous Contract #1
        "CME_ES1",      # E-mini S&P 500 Futures, Continuous Contract #1
        "EUREX_FSMI1",  # SMI Futures, Continuous Contract #1
        "EUREX_FSTX1",  # STOXX Europe 50 Index Futures, Continuous Contract #1
        "LIFFE_FCE1",   # CAC40 Index Futures, Continuous Contract #1
        "LIFFE_Z1",     # FTSE 100 Index Futures, Continuous Contract #1
                
        "CME_TY1",      # 10 Yr Note Futures, Continuous Contract #1 -5000
        "CME_FV1",      # 5 Yr Note Futures, Continuous Contract #1-8000
        "CME_TU1",      # 2 Yr Note Futures, Continuous Contract #1 -10000
        "ASX_XT1",      # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1   # 'Settlement price' instead of 'settle' on quandl. 
        "ASX_YT1",      # 3 Year Commonwealth Treasury Bond Futures, Continuous Contract #1    # 'Settlement price' instead of 'settle' on quandl.
        "EUREX_FGBL1",  # Euro-Bund (10Y) Futures, Continuous Contract #1
        "EUREX_FGBM1",  # Euro-Bobl Futures, Continuous Contract #1
        "EUREX_FGBS1",  # Euro-Schatz Futures, Continuous Contract #1 
        "SGX_JB1",      # SGX 10-Year Mini Japanese Government Bond Futures
        "LIFFE_R1"      # Long Gilt Futures, Continuous Contract #1
        "MX_CGB1",      # Ten-Year Government of Canada Bond Futures, Continuous Contract #1    # 'Settlement price' instead of 'settle' on quandl.
    ]
    
    ma_period = 100
    vol_period = 60
    
    self.SetWarmUp(vol_period)
    self.data = {}
    self.sma = {}
    
    self.days = 0
    
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetLeverage(5)
        data.SetFeeModel(CustomFeeModel())
        
        self.data[symbol] = deque(maxlen=vol_period)
        self.sma[symbol] = self.SMA(symbol, ma_period, Resolution.Daily)
        
def OnData(self, data):
    for symbol in self.symbols:
        # data is still coming
        if self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol]:
            self.liquidate(symbol)
            self.data[symbol].clear()
            continue
        if symbol in data and data[symbol]:
            price = data[symbol].Value
            self.data[symbol].append(price)        
    
    if self.IsWarmingUp: return
    
    if self.Portfolio.Invested:
        self.days += 1
        if self.days == 3:
            self.Liquidate()
            self.days = 0
    offset = BMonthEnd()
    last_day = offset.rollforward(self.Time)
    # day before EOM
    if self.Time.date() == last_day.date():
        # Volatility calculation
        volatility = {}
        for symbol in self.symbols:
            if len(self.data[symbol]) == self.data[symbol].maxlen:
                volatility[symbol] = self.Volatility(self.data[symbol])
        
        if len(volatility) == 0: return

        # MA sorting
        long = [x[0] for x in volatility.items() if self.data[x[0]][-1] > self.sma[x[0]].Current.Value]
        short = [x[0] for x in volatility.items() if self.data[x[0]][-1]  Dict[Symbol, datetime.date]:
   return QuantpediaFutures._last_update_date
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("http://data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    try:
        if not line[0].isdigit(): return None
        split = line.split(';')
        
        data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
        data['settle'] = float(split[1])
        data.Value = float(split[1])
        if config.Symbol.Value not in QuantpediaFutures._last_update_date:
            QuantpediaFutures._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
        if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol.Value]:
            QuantpediaFutures._last_update_date[config.Symbol.Value] = data.Time.date()
    except:
        return None
        
    return data
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
