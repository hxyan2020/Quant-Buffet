# Original QuantConnect / library Python
# locale=en slug="style-integrated-portfolios-of-commodity-futures"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
#endregion
class StyleIntegratedPortfoliosofCommodityFutures(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
   
    self.tickers:dict[str, str] = {
        "CME_S1" : Futures.Grains.Soybeans, # Soybean Futures, Continuous Contract
        "CME_W1" : Futures.Grains.Wheat,   # Wheat Futures, Continuous Contract
        "CME_SM1" : Futures.Grains.SoybeanMeal,  # Soybean Meal Futures, Continuous Contract
        "CME_BO1" : Futures.Grains.SoybeanOil,  # Soybean Oil Futures, Continuous Contract
        "CME_C1" : Futures.Grains.Corn,   # Corn Futures, Continuous Contract
        "CME_O1" : Futures.Grains.Oats,   # Oats Futures, Continuous Contract
        "CME_LC1" : Futures.Meats.LiveCattle,  # Live Cattle Futures, Continuous Contract
        "CME_FC1" : Futures.Meats.FeederCattle,  # Feeder Cattle Futures, Continuous Contract
        "CME_LN1" : Futures.Meats.LeanHogs,  # Lean Hog Futures, Continuous Contract
        "CME_GC1" : Futures.Metals.Gold,  # Gold Futures, Continuous Contract
        "CME_SI1" : Futures.Metals.Silver,  # Silver Futures, Continuous Contract
        "CME_PL1" : Futures.Metals.Platinum,  # Platinum Futures, Continuous Contract
        "CME_HG1" : Futures.Metals.Copper,  # Copper Futures, Continuous Contract
        "CME_LB1" : Futures.Forestry.RandomLengthLumber,  # Random Length Lumber Futures, Continuous Contract
        # "CME_NG1",  # Natural Gas (Henry Hub) Physical Futures, Continuous Contract #1
        "CME_PA1" : Futures.Metals.Palladium,  # Palladium Futures, Continuous Contract
        # "CME_RR1",  # Rough Rice Futures, Continuous Contract #1
        # "CME_CU1",  # Chicago Ethanol (Platts) Futures
        "CME_DA1" : Futures.Dairy.ClassIIIMilk,  # Class III Milk Futures
        
        "ICE_CC1" : Futures.Softs.Cocoa,  # Cocoa Futures, Continuous Contract 
        "ICE_CT1" : Futures.Softs.Cotton2,  # Cotton No. 2 Futures, Continuous Contract #1
        "ICE_KC1": Futures.Softs.Coffee, # Coffee C Futures, Continuous Contract #1
        "ICE_O1" : Futures.Energies.HeatingOil,   # Heating Oil Futures, Continuous Contract
        "ICE_OJ1": Futures.Softs.OrangeJuice,  # Orange Juice Futures, Continuous Contract #1
        "ICE_SB1" : Futures.Softs.Sugar11CME,   # Sugar No. 11 Futures, Continuous Contract
    }
    self.k:int = 5                              # k signals
    self.min_expiration_days:int = 0
    self.max_expiration_days:int = 360
    
    self.leverage:int = 5
    self.COT_data_period:int = 52               # n weeks
    self.momentum_period:int = 12 * 21          # m days
    self.value_period:int    = 5.5 * 12 * 21    # l days
    self.data:dict[Symbol, data_tools.SymbolData] = {}
    self.futures_data:dict[str, data_tools.FuturesData] = {}
    for qp_ticker, qc_ticker in self.tickers.items():
        # subscribe Quantpedia data
        security:Security = self.AddData(data_tools.QuantpediaFutures, qp_ticker, Resolution.Daily)
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        qp_symbol:Symbol = security.Symbol
        # subscribe COT data
        COT_ticker:str = 'Q' + qp_ticker.split('_')[1][:-1]
        COT_symbol:Symbol = self.AddData(data_tools.CommitmentsOfTraders, COT_ticker, Resolution.Daily).Symbol
        # QC futures
        future:Future = self.AddFuture(qc_ticker, Resolution.Daily, dataNormalizationMode=DataNormalizationMode.Raw)
        future.SetFilter(timedelta(days=self.min_expiration_days), timedelta(days=self.max_expiration_days))
        future_ticker:str = future.Symbol.Value
        self.futures_data[future_ticker] = data_tools.FuturesData()
        self.data[qp_symbol] = data_tools.SymbolData(COT_symbol, future_ticker,
            self.COT_data_period, self.value_period)
    
    self.recent_month:int = -1
    self.selection_flag:bool = False
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
def FindAndUpdateContracts(self, futures_chain, ticker:str) -> None:
    near_contract:FuturesContract = None
    dist_contract:FuturesContract = None
    if ticker in futures_chain:
        contracts:list[:FuturesContract] = [contract for contract in futures_chain[ticker] if contract.Expiry.date() > self.Time.date()]
        if len(contracts) >= 2:
            contracts:list[:FuturesContract] = sorted(contracts, key=lambda x: x.Expiry, reverse=False)
            near_contract = contracts[0]
            dist_contract = contracts[1]
    self.futures_data[ticker].update_contracts(near_contract, dist_contract)

def OnData(self, data):
    curr_date:datetime.date = self.Time.date()
    # rebalance monthly
    if self.recent_month != curr_date.month:
        self.selection_flag = True
        self.recent_month = curr_date.month
    momentum:dict[Symbol, float] = {}
    value:dict[Symbol, float] = {}
    skewness:dict[Symbol, float] = {}
    roll_yield:dict[Symbol, float] = {}
    speculative_pressure:dict[Symbol, float] = {}
    # daily update qc future data
    if data.FutureChains.Count > 0:
        for ticker, future_obj in self.futures_data.items():
            # check if near contract is expired or is not initialized
            if not future_obj.is_initialized() or \
                (future_obj.is_initialized() and future_obj.near_contract.Expiry.date() == curr_date):
                self.FindAndUpdateContracts(data.FutureChains, ticker)
            # update QC futures rolling return
            if future_obj.is_initialized():
                near_c:FuturesContract = future_obj.near_contract
                dist_c:FuturesContract = future_obj.distant_contract
                if near_c.Symbol in data and data[near_c.Symbol] and dist_c.Symbol in data and data[dist_c.Symbol]:
                    near_price:float = data[near_c.Symbol].Value * self.Securities[ticker].SymbolProperties.PriceMagnifier
                    dist_price:float = data[dist_c.Symbol].Value * self.Securities[ticker].SymbolProperties.PriceMagnifier
                    if near_price != 0 and dist_price != 0:
                        roll_yield:float = np.log(near_price) - np.log(dist_price)
                        future_obj.set_roll_yield(roll_yield)
    for qp_symbol, symbol_obj in self.data.items():
        # update Quantpedia prices
        if qp_symbol in data and data[qp_symbol]:
            # firstly make sure Quantpedia data still comming
            if self.securities[qp_symbol].get_last_data() and self.time.date() > data_tools.LastDateHandler.get_last_update_date()[qp_symbol]:
                symbol_obj_reset_prices()
            price:float = data[qp_symbol].Value
            symbol_obj.update_prices(price)
        # retreive COT data (weekly)
        COT_symbol:Symbol = symbol_obj.COT_symbol
        if self.securities[COT_symbol].get_last_data() and self.time.date() > data_tools.LastDateHandler.get_last_update_date()[COT_symbol]:
            symbol_obj.reset_speculative_net()
        if COT_symbol in data and data[COT_symbol]:
            speculator_long_count:float = data[COT_symbol].Large_Speculator_Long
            speculator_short_count:float = data[COT_symbol].Large_Speculator_Short
            # calculate net position of large speculators relative to their total position over previous week
            speculative_net:float = 0 if speculator_long_count == 0 or speculator_short_count == 0 else \
                 self.SpeculativeNetCal(speculator_long_count, speculator_short_count)
            symbol_obj.update_speculative_net(speculative_net)
            future_ticker:str = symbol_obj.future_ticker 
            # prices for momentum and value and skewness calulation is ready and data for average speculative net position is ready
            if self.selection_flag and symbol_obj.prices_ready() and symbol_obj.speculative_net_ready() and self.futures_data[future_ticker].is_ready():
                speculative_pressure[qp_symbol] = symbol_obj.get_speculative_pressure()
                momentum[qp_symbol] = symbol_obj.get_momentum(self.momentum_period)
                value[qp_symbol] = symbol_obj.get_value(self.momentum_period)
                skewness[qp_symbol] = symbol_obj.get_skewness(self.momentum_period)
                roll_yield[qp_symbol] = self.futures_data[future_ticker].get_roll_yield()
    # COT weekly data arrived and monthly selection should be made
    if self.selection_flag and len(momentum) != 0:
        self.selection_flag = False
        # normalize every signal
        speculative_pressure_values = list(self.NormalizeSignalDict(speculative_pressure).values())
        momentum_values = list(self.NormalizeSignalDict(momentum).values())
        value_values = list(self.NormalizeSignalDict(value).values())
        skewness_values = list(self.NormalizeSignalDict(skewness).values())
        roll_yield_values = list(self.NormalizeSignalDict(roll_yield).values())
        
        # calculate the integrated portfolio allocation
        signal_matrix:np.ndarray = np.array([speculative_pressure_values, momentum_values, value_values, skewness_values, roll_yield_values]).T
        weight_matrix:np.ndarray = np.array([[1 / self.k] * self.k]).T
        
        # matrix multiplication
        allocation = np.dot(signal_matrix, weight_matrix).T[0]
        
        # normalized allocation
        alloc_sum = sum([np.abs(x) for x in allocation])
        allocation_normalized = [x/alloc_sum for x in allocation]
        
        # pair symbols with its portfolio allocation
        alloc_with_symbol = { symbol : allocation_normalized[i] for i,symbol in enumerate(momentum.keys()) }
        
        # trade execution
        portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in alloc_with_symbol.items() if data.contains_key(symbol) and data[symbol]]
        self.SetHoldings(portfolio, True)
def SpeculativeNetCal(self, speculator_long_count:float, speculator_short_count:float) -> float:
    return (speculator_long_count - speculator_short_count) / (speculator_long_count + speculator_short_count)

def NormalizeSignalDict(self, signal_dict:dict) -> dict:
    signal_values:list = list(signal_dict.values())
    signal_mean:float = np.mean(signal_values)
    signal_std:float = np.std(signal_values)
    
    # new adjusted signal dict
    result:dict[Symbol, float] = { symbol : (signal-signal_mean)/signal_std for symbol, signal in signal_dict.items() }
    
    return result
