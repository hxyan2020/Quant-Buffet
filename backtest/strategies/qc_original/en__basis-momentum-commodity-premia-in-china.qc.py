# Original QuantConnect / library Python
# locale=en slug="basis-momentum-commodity-premia-in-china"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class BasisMomentumCommodityPremiainChina(QCAlgorithm):
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
    
    self.period:int = 12*21
    self.SetWarmup(self.period, Resolution.Daily)
    self.price_data:dict = {}
    self.contract_range:list[int] = [3, 4]  # 3rd and 4th futures contract
    self.latest_update_date:dict = {}   # latest price data arrival time
    for symbol in self.symbols:
        # futures data
        for i in self.contract_range:
            sym = symbol + str(i)
            data = self.AddData(QuantpediaChineseFutures, sym, Resolution.Daily)
            data.SetLeverage(5)
            data.SetFeeModel(CustomFeeModel())
            self.price_data[sym] = RollingWindow[float](self.period)
        self.latest_update_date[symbol] = None
            
    self.recent_month = -1

def OnData(self, data):
    rebalance_flag:bool = False
    basis_momentum_signal:dict[Symbol, float] = {}
    # store daily prices
    for symbol in self.symbols:
        # both contracts data points are available
        if all(symbol+str(i) in data and data[symbol+str(i)] and data[symbol+str(i)].Value != 0 for i in self.contract_range):
            near_c_symbol:str = symbol + str(self.contract_range[0])  # 3rd contract
            dist_c_symbol:str = symbol + str(self.contract_range[1])  # 4th contract
            self.price_data[near_c_symbol].Add(data[near_c_symbol].Value)  # 3rd contract price
            self.price_data[dist_c_symbol].Add(data[dist_c_symbol].Value)  # 4th contract price
            self.latest_update_date[symbol] = self.Time.date()
            if self.IsWarmingUp: continue
            # rebalance date
            if self.Time.month != self.recent_month:
                rebalance_flag = True
                # check data arrival time
                if (self.Time.date() - self.latest_update_date[symbol]).days > 5:
                    continue
                # price data for both contracts are ready
                if self.price_data[near_c_symbol].IsReady and self.price_data[dist_c_symbol].IsReady:
                    # calculate momentum from forward ratio rolled contracts
                    near_momentum:float = self.price_data[near_c_symbol][0] / self.price_data[near_c_symbol][self.period-1] - 1
                    dist_momentum:float = self.price_data[dist_c_symbol][0] / self.price_data[dist_c_symbol][self.period-1] - 1
                    basis_momentum_signal[near_c_symbol] = near_momentum - dist_momentum
    # monthly rebalance
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    # buying the commodity futures with positive signal and selling commodity futures with a negative signal
    long:list[Symbol] = [x[0] for x in basis_momentum_signal.items() if x[1] > 0.]
    short:list[Symbol] = [x[0] for x in basis_momentum_signal.items() if x[1]
