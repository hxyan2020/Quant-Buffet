# Original QuantConnect / library Python
# locale=en slug="cross-asset-skewness-effect"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from scipy.stats import skew
from AlgorithmImports import *
class CrossAssetSkewnessEffect(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.leverage = 2
    
    commodities = ["CME_S1",   # Soybean Futures, Continuous Contract
                    "CME_W1",   # Wheat Futures, Continuous Contract
                    "CME_SM1",  # Soybean Meal Futures, Continuous Contract
                    "CME_BO1",  # Soybean Oil Futures, Continuous Contract
                    "CME_C1",   # Corn Futures, Continuous Contract
                    "CME_O1",   # Oats Futures, Continuous Contract
                    "CME_LC1",  # Live Cattle Futures, Continuous Contract
                    "CME_FC1",  # Feeder Cattle Futures, Continuous Contract
                    "CME_LN1",  # Lean Hog Futures, Continuous Contract
                    "CME_GC1",  # Gold Futures, Continuous Contract
                    "CME_SI1",  # Silver Futures, Continuous Contract
                    "CME_PL1",  # Platinum Futures, Continuous Contract
                    "CME_CL1",  # Crude Oil Futures, Continuous Contract
                    "CME_HG1",  # Copper Futures, Continuous Contract
                    "CME_LB1",  # Random Length Lumber Futures, Continuous Contract
                    # "CME_NG1",  # Natural Gas (Henry Hub) Physical Futures, Continuous Contract
                    "CME_PA1",  # Palladium Futures, Continuous Contract 
                    "CME_RR1",  # Rough Rice Futures, Continuous Contract
                    
                    "ICE_CC1",  # Cocoa Futures, Continuous Contract 
                    "ICE_CT1",  # Cotton No. 2 Futures, Continuous Contract
                    "ICE_KC1",  # Coffee C Futures, Continuous Contract
                    "ICE_O1",   # Heating Oil Futures, Continuous Contract
                    "ICE_OJ1",  # Orange Juice Futures, Continuous Contract
                    "ICE_SB1",  # Sugar No. 11 Futures, Continuous Contract
                    ]
                    
    currencies = ["CME_AD1", # Australian Dollar Futures, Continuous Contract #1
                "CME_BP1", # British Pound Futures, Continuous Contract #1
                "CME_CD1", # Canadian Dollar Futures, Continuous Contract #1
                "CME_EC1", # Euro FX Futures, Continuous Contract #1
                "CME_JY1", # Japanese Yen Futures, Continuous Contract #1
                "CME_MP1", # Mexican Peso Futures, Continuous Contract #1
                "CME_NE1",# New Zealand Dollar Futures, Continuous Contract #1
                "CME_SF1", # Swiss Franc Futures, Continuous Contract #1
                ]
                    
    equities = ["ICE_DX1",      # US Dollar Index Futures, Continuous Contract #1
                "CME_NQ1",      # E-mini NASDAQ 100 Futures, Continuous Contract #1
                "EUREX_FDAX1",  # DAX Futures, Continuous Contract #1
                "CME_ES1",      # E-mini S&P 500 Futures, Continuous Contract #1
                "EUREX_FSMI1",  # SMI Futures, Continuous Contract #1
                "EUREX_FSTX1",  # STOXX Europe 50 Index Futures, Continuous Contract #1
                "LIFFE_FCE1",   # CAC40 Index Futures, Continuous Contract #1
                "LIFFE_Z1",     # FTSE 100 Index Futures, Continuous Contract #1
                "SGX_NK1",      # SGX Nikkei 225 Index Futures, Continuous Contract #1
                ]
                
    bonds = ["CME_TY1",      # 10 Yr Note Futures, Continuous Contract #1
            "CME_FV1",      # 5 Yr Note Futures, Continuous Contract #1
            "CME_TU1",      # 2 Yr Note Futures, Continuous Contract #1
            "ASX_XT1",     # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1
            "ASX_YT1",     # 3 Year Commonwealth Treasury Bond Futures, Continuous Contract #1
            "EUREX_FGBL1",  # Euro-Bund (10Y) Futures, Continuous Contract #1
            "EUREX_FBTP1", # Long-Term Euro-BTP Futures, Continuous Contract #1
            "EUREX_FGBM1",  # Euro-Bobl Futures, Continuous Contract #1
            "EUREX_FGBS1",  # Euro-Schatz Futures, Continuous Contract #1 
            "SGX_JB1",      # SGX 10-Year Mini Japanese Government Bond Futures
            "LIFFE_R1"      # Long Gilt Futures, Continuous Contract #1
            "MX_CGB1",     # Ten-Year Government of Canada Bond Futures, Continuous Contract #1
            ]
    self.asset_classes = {}
    self.asset_classes['commodities'] = commodities
    self.asset_classes['currencies'] = currencies
    self.asset_classes['equities'] = equities
    self.asset_classes['bonds'] = bonds
    
    self.data = {}
    self.period = 12 * 21
    
    for symbol in commodities + currencies + equities + bonds:
        # Quantpedia #1 Contract.
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        self.data[symbol] = RollingWindow[float](self.period)
        
    self.rebalance_flag: bool = False
    self.Schedule.On(self.DateRules.MonthStart(commodities[0]), self.TimeRules.At(0, 0), self.Rebalance)
    self.settings.minimum_order_margin_portfolio_percentage = 0.

def OnData(self, data):
    # store daily prices
    for asset_class in self.asset_classes:
        for symbol in self.asset_classes[asset_class]:
            if symbol in data and data[symbol]:
                price = data[symbol].Value
                self.data[symbol].Add(price)
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    class_count = len(self.asset_classes)
    weight = {}
    
    for asset_class in self.asset_classes:
        
        class_symbols = self.asset_classes[asset_class]
        class_symbols_count = len(class_symbols)
        
        skewness_data = {}
        for symbol in class_symbols:
            if self.data[symbol].IsReady:
                if self.Securities[symbol].GetLastData() and self.Time.date()  0]
        negative_skewness = [x for x in sorted_by_skewness if x[1]  Dict[Symbol, datetime.date]:
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
