# Original QuantConnect / library Python
# locale=en slug="momentum-and-trend-following-in-global-asset-allocation"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from collections import deque
from AlgorithmImports import *
class VolatilityWeightedShortTermReversal(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100000)
    self.t_bill = 'BIL'
    
    developed = [
        "EWJ", # iShares MSCI Japan Index ETF
        "EFNL", # iShares MSCI Finland Capped Investable Market Index ETF
        "IVV",  # iShares S&P 500 Index
        "EWQ",  # iShares MSCI France Index ETF
        "EWU",  # iShares MSCI United Kingdom ETF
        "EWI",  # iShares MSCI Italy Index ETF
        "ENZL", # iShares MSCI New Zealand Investable Market Index Fund
        "NORW"  # Global X FTSE Norway 30 ETF
        "EWY",  # iShares MSCI South Korea Index ETF
        "EWP",  # iShares MSCI Spain Index ETF
        "EWD",  # iShares MSCI Sweden Index ETF
        "EWG",  # iShares MSCI Germany Index ETF
        "EWL",  # iShares MSCI Switzerland Index ETF
        "EWC",  # iShares MSCI Canada Index ETF
        "EWO",  # iShares MSCI Austria Investable Mkt Index ETF
        "EWK",  # iShares MSCI Belgium Investable Market Index ETF
        "EWN",  # iShares MSCI Netherlands ETF
        "EWA",  # iShares MSCI-Australia ETF
    ]
    
    emerging = ['FXI', 'ARGT', 'EZA', 'AND', 'FXI', 'EWH', 'EWT', 'EIDO', 'EPHE', 'EWM', 'THD', 'EWS', 'TUR', 'EWZ', 'ARGT', 'ECH', 'EPOL', 'EWW', 'ERUS', 'EPI', 'EIDO', 'GAF']
    
    reits = ['IYR', 'REM', 'REZ', 'IFEU']
    bonds = ["CME_TY1",     # 10 Yr Note Futures, Continuous Contract #1
            "CME_FV1",      # 5 Yr Note Futures, Continuous Contract #1
            "CME_TU1",      # 2 Yr Note Futures, Continuous Contract #1
            "ASX_XT1",      # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1
            "ASX_YT1",      # 3 Year Commonwealth Treasury Bond Futures, Continuous Contract #1
            "EUREX_FGBL1",  # Euro-Bund (10Y) Futures, Continuous Contract #1
            "EUREX_FBTP1",  # Long-Term Euro-BTP Futures, Continuous Contract #1
            "EUREX_FGBM1",  # Euro-Bobl Futures, Continuous Contract #1
            "EUREX_FGBS1",  # Euro-Schatz Futures, Continuous Contract #1 
            "SGX_JB1",      # SGX 10-Year Mini Japanese Government Bond Futures
            "LIFFE_R1"      # Long Gilt Futures, Continuous Contract #1
            "MX_CGB1",      # Ten-Year Government of Canada Bond Futures, Continuous Contract #1
            ]
            
    commodities = [ "CME_S1",   # Soybean Futures, Continuous Contract
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
                    "CME_PA1",  # Palladium Futures, Continuous Contract 
                    "CME_RR1",  # Rough Rice Futures, Continuous Contract
                    "ICE_RS1",  # Canola Futures, Continuous Contract
                    "ICE_GO1",  # Gas Oil Futures, Continuous Contract
                    "CME_RB2",  # Gasoline Futures, Continuous Contract
                    "CME_KW2",  # Wheat Kansas, Continuous Contract
                    "ICE_WT1",  # WTI Crude Futures, Continuous Contract
                    
                    "ICE_CC1",  # Cocoa Futures, Continuous Contract 
                    "ICE_CT1",  # Cotton No. 2 Futures, Continuous Contract
                    "ICE_KC1",  # Coffee C Futures, Continuous Contract
                    "ICE_O1",   # Heating Oil Futures, Continuous Contract
                    "ICE_OJ1",  # Orange Juice Futures, Continuous Contract
                    "ICE_SB1"   # Sugar No. 11 Futures, Continuous Contract
                ]
    
    self.data = {}  # Monthly symbol closes.
    
    self.index_price = {} # Asset class index price.
    self.sma = {}   # Asset class SMA.
    self.period = 12
    
    self.custom_data: List[str] = bonds + commodities
    self.asset_classes = {}
    self.asset_classes['developed'] = developed
    self.asset_classes['emerging'] = emerging
    self.asset_classes['reits'] = reits
    self.asset_classes['bonds'] = bonds
    self.asset_classes['commodities'] = commodities
    for symbol in [self.t_bill] + developed + emerging + reits:
        self.AddEquity(symbol, Resolution.Daily)
        self.data[symbol] = deque(maxlen = self.period)
    
    for symbol in bonds + commodities:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        self.data[symbol] = deque(maxlen = self.period)
        data.SetFeeModel(CustomFeeModel())
        #data.SetLeverage(2)
    
    for asset_class in self.asset_classes:
        self.sma[asset_class] = SimpleMovingAverage(10)
        self.index_price[asset_class] = 0
        
    self.rebalance_flag: bool = False
    self.Schedule.On(self.DateRules.MonthStart(emerging[0]), self.TimeRules.AfterMarketOpen(emerging[0]), self.Rebalance)
    self.settings.daily_precise_end_time = False
def on_data(self, slice: Slice) -> None:
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    uptrend_classes = []
    downtrend_classes = []
    
    # Calculate index price.
    for asset_class in self.asset_classes:
        
        class_symbols = self.asset_classes[asset_class]
        class_symbols_count = len(class_symbols)
        class_total_price = 0
        
        # Store index price and symbol price.
        for symbol in class_symbols:
            if symbol in self.custom_data:
                if self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol]:
                    self.liquidate(symbol)
                    break
            if self.Securities.ContainsKey(symbol):
                price = self.Securities[symbol].Price
                if price != 0:
                    self.data[symbol].append(price)
                    class_total_price += price
        
        if class_total_price == 0:
            continue
        index_price = class_total_price / class_symbols_count
        self.index_price[asset_class] = index_price
        
        # Update index SMA.
        self.sma[asset_class].Update(self.Time, index_price)
        
        # Trend following filtering.
        if self.sma[asset_class].IsReady:
            index_price = self.index_price[asset_class]
            
            if index_price > self.sma[asset_class].Current.Value:
                uptrend_classes.append(asset_class)
            else:
                downtrend_classes.append(asset_class)
                
    # Trade execution
    self.Liquidate()
    class_count = len(self.asset_classes)
    
    targets: List[PortfolioTarget] = []
    for asset_class in uptrend_classes:
        # Performance calc.
        performance = {}
        for symbol in self.asset_classes[asset_class]:
            if len(self.data[symbol]) == self.data[symbol].maxlen:
                closes = np.array([x for x in self.data[symbol]])
                daily_retuns = closes[1:] / closes[:-1] - 1
                volatility = np.std(daily_retuns) * np.sqrt(252)
                ret = closes[-1] / closes[0] - 1
                performance[symbol] = ret / volatility
        
        if len(performance) == 0: continue
        
        # Performance sorting.
        perf_values = [x for x in performance.values()]
        long = [x[0] for x in performance.items() if x[1] >= np.percentile(perf_values, 50)]
        for symbol in long:
            if symbol in slice and slice[symbol]:
                self.SetHoldings(symbol, 1 / (class_count * len(long)))
    
    for asset_class in downtrend_classes:
        if symbol in slice and slice[symbol]:
            self.SetHoldings(self.t_bill, 1 / class_count)
def Rebalance(self):
    self.rebalance_flag = True
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
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
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
