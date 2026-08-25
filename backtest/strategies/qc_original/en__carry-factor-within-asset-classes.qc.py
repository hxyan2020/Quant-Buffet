# Original QuantConnect / library Python
# locale=en slug="carry-factor-within-asset-classes"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class TermStructureCommodities(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    commodities:dict = {
        'CME_S1': Futures.Grains.Soybeans,
        'CME_W1' : Futures.Grains.Wheat,
        'CME_SM1' : Futures.Grains.SoybeanMeal,
        'CME_C1' : Futures.Grains.Corn,
        'CME_O1' : Futures.Grains.Oats,
        'CME_LC1' : Futures.Meats.LiveCattle,
        'CME_FC1' : Futures.Meats.FeederCattle,
        'CME_LN1' : Futures.Meats.LeanHogs,
        'CME_GC1' : Futures.Metals.Gold,
        'CME_SI1' : Futures.Metals.Silver,
        'CME_PL1' : Futures.Metals.Platinum,
        'CME_HG1' : Futures.Metals.Copper,
        'CME_LB1' : Futures.Forestry.RandomLengthLumber,
        'CME_NG1' : Futures.Energies.NaturalGas,
        'CME_PA1' : Futures.Metals.Palladium,
        'CME_DA1' : Futures.Dairy.ClassIIIMilk,
        
        'CME_RB1' : Futures.Energies.Gasoline,
        # 'ICE_WT1' : Futures.Energies.CrudeOilWTI,
        'ICE_CC1' : Futures.Softs.Cocoa,
        'ICE_O1' : Futures.Energies.HeatingOil,
        # 'ICE_SB1' : Futures.Softs.Sugar11CME,
    }
                    
    currencies:dict = {
        'CME_AD1' : Futures.Currencies.AUD,
        'CME_BP1' : Futures.Currencies.GBP,
        'CME_CD1' : Futures.Currencies.CAD,
        'CME_EC1' : Futures.Currencies.EUR,
        'CME_JY1' : Futures.Currencies.JPY,
        'CME_MP1' : Futures.Currencies.MXN,
        'CME_NE1' : Futures.Currencies.NZD,
        'CME_SF1' : Futures.Currencies.CHF,
    }
                    
    equities:dict = {
        'CME_NQ1' : Futures.Indices.NASDAQ100EMini,
        'CME_ES1' : Futures.Indices.SP500EMini,
        'LIFFE_Z1' : Futures.Indices.FTSEEmergingEmini,
        'SGX_NK1' : Futures.Indices.Nikkei225Dollar,
        # 'ICE_DX1' : Futures.Indices.,
        # 'EUREX_FDAX1' : Futures.Indices.,
        # 'EUREX_FSMI1' : Futures.Indices.,
        # 'EUREX_FSTX1' : Futures.Indices.,
        # 'LIFFE_FCE1' : Futures.Indices.,
    }
    bonds:dict = {
        'CME_TY1' : Futures.Financials.Y10TreasuryNote,      # 10 Yr Note Futures, Continuous Contract #1
        'CME_FV1' : Futures.Financials.Y5TreasuryNote,      # 5 Yr Note Futures, Continuous Contract #1
        'CME_TU1' : Futures.Financials.Y2TreasuryNote,      # 2 Yr Note Futures, Continuous Contract #1
        # 'ASX_XT' : Futures.Financials.,     # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1
        # 'ASX_YT' : Futures.Bonds.,     # 3 Year Commonwealth Treasury Bond Futures, Continuous Contract #1
        # 'MX_CGB' : Futures.Bonds.,     # Ten-Year Government of Canada Bond Futures, Continuous Contract #1
        # 'EUREX_FGBL' : Futures.Bonds.,  # Euro-Bund (10Y) Futures, Continuous Contract #1
        # 'EUREX_FBTP' : Futures.Bonds., # Long-Term Euro-BTP Futures, Continuous Contract #1
        # 'EUREX_FGBM' : Futures.Bonds.,  # Euro-Bobl Futures, Continuous Contract #1
        # 'EUREX_FGBS' : Futures.Bonds.,  # Euro-Schatz Futures, Continuous Contract #1 
        # 'SGX_JB' : Futures.Bonds.,      # SGX 10-Year Mini Japanese Government Bond Futures
        # 'LIFFE_R' : Futures.Bonds.      # Long Gilt Futures, Continuous Contract #1
        }
    self.asset_classes:dict[str, dict] = {}
    self.asset_classes['commodities'] = commodities
    self.asset_classes['currencies'] = currencies
    self.asset_classes['equities'] = equities
    self.asset_classes['bonds'] = bonds
    self.futures_info:dict = {}
    self.min_expiration_days:int = 2
    self.max_expiration_days:int = 360
    for asset_class_name, asset_class in self.asset_classes.items():
        for qp_symbol, qc_future in asset_class.items():
            # QP futures
            data:Security = self.AddData(QuantpediaFutures, qp_symbol, Resolution.Daily)
            data.SetFeeModel(CustomFeeModel())
            data.SetLeverage(5)
            
            # QC futures
            future:Future = self.AddFuture(qc_future, Resolution.Daily, dataNormalizationMode=DataNormalizationMode.Raw)
            future.SetFilter(timedelta(days=self.min_expiration_days), timedelta(days=self.max_expiration_days))
            self.futures_info[future.Symbol.Value] = FuturesInfo(data.Symbol)
    self.recent_month:int = -1
def find_and_update_contracts(self, futures_chain, symbol):
    near_contract:FuturesContract = None
    dist_contract:FuturesContract = None
    if symbol in futures_chain:
        contracts:list = [contract for contract in futures_chain[symbol] if contract.Expiry.date() > self.Time.date()]
        if len(contracts) >= 2:
            contracts:list = sorted(contracts, key=lambda x: x.Expiry, reverse=False)
            near_contract = contracts[0]
            dist_contract = contracts[1]
    self.futures_info[symbol].update_contracts(near_contract, dist_contract)
def OnData(self, data):
    if data.FutureChains.Count > 0:
        for symbol, futures_info in self.futures_info.items():
            if self.securities[futures_info.quantpedia_future].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[futures_info.quantpedia_future]:
                self.liquidate(futures_info.quantpedia_future)
                futures_info.near_contract = None
                futures_info.distant_contract = None
            # check if near contract is expired or is not initialized
            if not futures_info.is_initialized() or \
                (futures_info.is_initialized() and futures_info.near_contract.Expiry.date() == self.Time.date()):
                self.find_and_update_contracts(data.FutureChains, symbol)
    roll_return:dict[Symbol, float] = {}
    rebalance_flag:bool = False
    # roll return calculation
    for symbol, futures_info in self.futures_info.items():
        # futures data is present in the algorithm
        if futures_info.quantpedia_future in data and data[futures_info.quantpedia_future]:
            # new month rebalance
            if self.Time.month != self.recent_month:
                self.recent_month = self.Time.month
                rebalance_flag = True
            if rebalance_flag:
                if futures_info.is_initialized():
                    near_c = futures_info.near_contract
                    dist_c = futures_info.distant_contract
                    if self.Securities.ContainsKey(near_c.Symbol) and self.Securities.ContainsKey(dist_c.Symbol):
                        raw_price1:float = self.Securities[near_c.Symbol].Close * self.Securities[symbol].SymbolProperties.PriceMagnifier
                        raw_price2:float = self.Securities[dist_c.Symbol].Close * self.Securities[symbol].SymbolProperties.PriceMagnifier
                        if raw_price1 != 0 and raw_price2 != 0:
                            roll_return[futures_info.quantpedia_future] = raw_price1 / raw_price2 - 1
    if rebalance_flag:
        weight:dict[Symbol, float] = {}
        if len(roll_return) != 0:
            long:list[Symbol] = []
            short:list[Symbol] = []
            class_count:int = len(self.asset_classes)
            # sort by roll return
            sorted_by_roll:list = sorted(roll_return.items(), key = lambda x: x[1], reverse = True)
            positive_roll:list[Symbol] = [x for x in sorted_by_roll if x[1] > 0]
            negative_roll:list[Symbol] = [x for x in sorted_by_roll if x[1]  None:
    self.quantpedia_future:Symbol = quantpedia_future
    self.near_contract:FuturesContract = None
    self.distant_contract:FuturesContract = None

def update_contracts(self, near_contract:FuturesContract, distant_contract:FuturesContract) -> None:
    self.near_contract = near_contract
    self.distant_contract = distant_contract

def is_initialized(self) -> bool:
    return self.near_contract is not None and self.distant_contract is not None

# Custom fee model.
class CustomFeeModel():
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
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
    if config.Symbol not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol]:
        QuantpediaFutures._last_update_date[config.Symbol] = data.Time.date()
    return data
