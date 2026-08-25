# Original QuantConnect / library Python
# locale=zh slug="商品期货中的价差（基差）动量"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
#endregion
class SpreadMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2009, 1, 1)
    self.SetCash(100000)
    self.tickers = {
        "CME_S1": Futures.Grains.Soybeans, # Soybean Futures, Continuous Contract
        "CME_W1": Futures.Grains.Wheat,   # Wheat Futures, Continuous Contract
        "CME_SM1": Futures.Grains.SoybeanMeal,  # Soybean Meal Futures, Continuous Contract
        "CME_BO1": Futures.Grains.SoybeanOil,  # Soybean Oil Futures, Continuous Contract
        "CME_C1": Futures.Grains.Corn,   # Corn Futures, Continuous Contract
        "CME_O1": Futures.Grains.Oats,   # Oats Futures, Continuous Contract
        "CME_LC1": Futures.Meats.LiveCattle,  # Live Cattle Futures, Continuous Contract
        "CME_FC1": Futures.Meats.FeederCattle,  # Feeder Cattle Futures, Continuous Contract
        "CME_LN1": Futures.Meats.LeanHogs,  # Lean Hog Futures, Continuous Contract
        "CME_GC1": Futures.Metals.Gold,  # Gold Futures, Continuous Contract
        "CME_SI1": Futures.Metals.Silver,  # Silver Futures, Continuous Contract
        "CME_PL1": Futures.Metals.Platinum,  # Platinum Futures, Continuous Contract
        "CME_HG1": Futures.Metals.Copper,  # Copper Futures, Continuous Contract
        "CME_LB1": Futures.Forestry.RandomLengthLumber,  # Random Length Lumber Futures, Continuous Contract
        "CME_PA1": Futures.Metals.Palladium,  # Palladium Futures, Continuous Contract
        "CME_RB2": Futures.Energies.Gasoline,  # Gasoline Futures, Continuous Contract
        "ICE_CC1": Futures.Softs.Cocoa,  # Cocoa Futures, Continuous Contract 
        "ICE_O1": Futures.Energies.HeatingOil,   # Heating Oil Futures, Continuous Contract
        "ICE_SB1": Futures.Softs.Sugar11CME,   # Sugar No. 11 Futures, Continuous Contract
        "ICE_WT1": Futures.Energies.CrudeOilWTI,  # WTI Crude Futures, Continuous Contract
    }
    self.futures_data:Dict[str, data_tools.FutureData] = {}
    self.max_missing_days:int = 5
    self.futures_num:int = 4
    self.lookup_period:int = 12 * 21
    min_expiration_days:int = 2
    max_expiration_days:int = 360
    
    # subscribe data
    for qp_ticker, qc_ticker in self.tickers.items():
        security = self.AddData(data_tools.QuantpediaFutures, qp_ticker, Resolution.Daily)
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(5)
        qp_symbol:Symbol = security.Symbol
        # QC futures
        future:Future = self.AddFuture(qc_ticker, Resolution.Daily)
        future.SetFilter(timedelta(days=min_expiration_days), timedelta(days=max_expiration_days))
        self.futures_data[future.Symbol.Value] = data_tools.FuturesData(qp_symbol, self.lookup_period)
    self.recent_month:int = -1
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
def FindAndUpdateContracts(self, futures_chain, ticker) -> None:
    near_contract:FuturesContract = None
    dist_contract:FuturesContract = None
    if ticker in futures_chain:
        contracts:List[:FuturesContract] = [contract for contract in futures_chain[ticker] if contract.Expiry.date() > self.Time.date()]
        if len(contracts) >= 2:
            contracts:List[:FuturesContract] = sorted(contracts, key=lambda x: x.Expiry, reverse=False)
            near_contract = contracts[0]
            dist_contract = contracts[1]
    self.futures_data[ticker].update_contracts(near_contract, dist_contract)

def OnData(self, data):
    curr_time:datetime.datetime = self.Time
    curr_date:datetime.date = curr_time.date()
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
                    raw_price1:float = data[near_c.Symbol].Value
                    raw_price2:float = data[dist_c.Symbol].Value
                    if raw_price1 != 0 and raw_price2 != 0:
                        future_obj.update_rate_of_change(raw_price1, raw_price2, curr_time)
    # update, when qp data still coming
    for _, future_obj in self.futures_data.items():
        qp_symbol:Symbol = future_obj.quantpedia_future
        if qp_symbol in data and data[qp_symbol]:
            future_obj.update_quantpedia_last_update(curr_date)
    # rebalance monthly
    if self.recent_month != curr_time.month:
        self.recent_month = curr_time.month
        self.Rebalance(curr_date)
                
def Rebalance(self, curr_date:datetime.date) -> None:
    if self.IsWarmingUp: return
    diff:Dict[Symbol, float] = {}
    last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()
    # filter ready futures and reset futures, which do not recieve new data
    for _, future_obj in self.futures_data.items():
        data_ready_flag:bool = future_obj.is_ready()
        # make sure data are ready and up to date
        if data_ready_flag and self.Securities[future_obj.quantpedia_future].GetLastData() and \
            future_obj.quantpedia_future.Value in last_update_date and self.Time.date()
