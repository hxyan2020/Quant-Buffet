# Original QuantConnect / library Python
# locale=en slug="momentum-commodity-premia-in-china"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class MomentumCommodityPremiainChina(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2017, 1, 1)
    self.SetCash(100000)
    
    # NOTE: QC max cap of 100 custom symbols added => 50 commodities x2 contracts
    self.symbols:list[str] = [
        # 'ER','ME','RO','S','TC','WS','WT',    # empty
        
        'CU', 'A', 'AG', 'AL', 'AP', 'AU',
        'B', 'BB', 'BU', 'C', 'CF', 'CS',
        'CY', 'FB', 'FG', 'FU', 'HC', 'I',
        'IC', 'IF', 'IH', 'J', 'JD', 'JM', 
        'JR', 'L', 'LR', 'M', 'MA', 'NI',
        'OI', 'P', 'PB', 'PM', 'PP', 'RB',
        'RI', 'RM', 'RS', 'RU',  'SF', 'SM',
        'SN', 'SR', 'T', 'TF', 'V',
        'WR', 'ZN', 'Y'
        #  'ZC', 'TA', 'WH'
    ]
    
    self.period:int = 12 * 21
    self.SetWarmup(self.period, Resolution.Daily)
    self.price_data:dict = {}
    self.latest_update_date:dict = {}   # latest price data arrival time
    self.quantile:int = 2
    for symbol in self.symbols:
        # futures data
        sym:str = symbol + '3'  # erd contract
        data = self.AddData(QuantpediaChineseFutures, sym, Resolution.Daily)
        data.SetLeverage(5)
        data.SetFeeModel(CustomFeeModel())
        self.price_data[sym] = RollingWindow[float](self.period)
        self.latest_update_date[sym] = None
            
    self.recent_month = -1

def OnData(self, data):
    momentum:dict[Symbol, float] = {}
    # store daily prices
    for near_c_symbol, _ in self.price_data.items():
        # store price data
        if near_c_symbol in data and data[near_c_symbol] and data[near_c_symbol].Value != 0:
            self.price_data[near_c_symbol].Add(data[near_c_symbol].Value)  # 3rd contract price
            self.latest_update_date[near_c_symbol] = self.Time.date()
            if self.IsWarmingUp: continue
            # rebalance date
            if self.Time.month != self.recent_month:
                # check data arrival time
                if (self.Time.date() - self.latest_update_date[near_c_symbol]).days > 5:
                    continue
                # price data for both contracts are ready
                if self.price_data[near_c_symbol].IsReady:
                    # calculate momentum from forward ratio rolled contracts
                    near_momentum:float = self.price_data[near_c_symbol][0] / self.price_data[near_c_symbol][self.period-1] - 1
                    momentum[near_c_symbol] = near_momentum
    # monthly rebalance
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    long:list[Symbol] = []
    short:list[Symbol] = []
    if len(momentum) >= self.quantile:
        # sort by momentum
        sorted_by_momentum = sorted(momentum.items(), key=lambda x: x[1], reverse=True)
        quantile:int = int(len(momentum) / self.quantile)
        # buying (selling) the half with the highest (lowest) return
        long = [x[0] for x in sorted_by_momentum][:quantile]
        short = [x[0] for x in sorted_by_momentum][-quantile:]
    # trade execution
    invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    for symbol in long:
        self.SetHoldings(symbol, 1 / len(long))
    
    for symbol in short:
        self.SetHoldings(symbol, -1 / len(short))
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaChineseFutures(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/china/forward_ratio_rolled/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaChineseFutures()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): 
        return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    data['close'] = float(split[1]) if split[1] != '' else 0 # unadjusted close
    data['adj_close'] = float(split[2]) if split[2] != '' else 0
    data['last_trade_month'] = int(split[3])
    data.Value = float(split[2]) if split[2] != '' else 0
    return data
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
