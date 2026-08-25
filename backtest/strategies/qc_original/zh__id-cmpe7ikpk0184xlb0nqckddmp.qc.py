# Original QuantConnect / library Python
# locale=zh slug="时间序列动量与套利收益"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import math
import numpy as np
from typing import List, Dict
#endregion
class TimeSeriesMomentumandCarry(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.tickers:Dict[str, str] = { 
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
        "CME_PA1" : Futures.Metals.Palladium,  # Palladium Futures, Continuous Contract
        "CME_RB2" : Futures.Energies.Gasoline,  # Gasoline Futures, Continuous Contract
        "ICE_CC1" : Futures.Softs.Cocoa,  # Cocoa Futures, Continuous Contract 
        "ICE_O1" : Futures.Energies.HeatingOil,   # Heating Oil Futures, Continuous Contract
        "ICE_SB1" : Futures.Softs.Sugar11CME,   # Sugar No. 11 Futures, Continuous Contract
        "ICE_WT1" : Futures.Energies.CrudeOilWTI,  # WTI Crude Futures, Continuous Contract
        
        "CME_NQ1" : Futures.Indices.NASDAQ100EMini, # E-mini NASDAQ 100 Futures, Continuous Contract #1
        "CME_ES1" : Futures.Indices.SP500EMini, # E-mini S&P 500 Futures, Continuous Contract #1
        "SGX_NK1" : Futures.Indices.Nikkei225Dollar, # SGX Nikkei 225 Index Futures, Continuous Contract #1
        
        "CME_TY1" : Futures.Financials.Y10TreasuryNote, # 10 Yr Note Futures, Continuous Contract #1
        "CME_FV1" : Futures.Financials.Y5TreasuryNote, # 5 Yr Note Futures, Continuous Contract #1
        "CME_TU1" : Futures.Financials.Y2TreasuryNote, # 2 Yr Note Futures, Continuous Contract #1
        "CME_AD1" : Futures.Currencies.AUD, # Australian Dollar Futures, Continuous Contract #1
        "CME_BP1" : Futures.Currencies.GBP, # British Pound Futures, Continuous Contract #1
        "CME_CD1" : Futures.Currencies.CAD, # Canadian Dollar Futures, Continuous Contract #1
        "CME_EC1" : Futures.Currencies.EUR, # Euro FX Futures, Continuous Contract #1
        "CME_JY1" : Futures.Currencies.JPY, # Japanese Yen Futures, Continuous Contract #1
        "CME_MP1" : Futures.Currencies.MXN, # Mexican Peso Futures, Continuous Contract #1
        "CME_NE1" : Futures.Currencies.NZD, # New Zealand Dollar Futures, Continuous Contract #1
        "CME_SF1" : Futures.Currencies.CHF, # Swiss Franc Futures, Continuous Contract #1
    }
                
    self.period:int = 12 * 21
    self.min_expiration_days:int = 2
    self.max_expiration_days:int = 360
    leverage: int = 5
    
    self.futures_data:dict[Symbol, RollingWindow] = {}
    # subscribe data
    for qp_ticker, qc_ticker in self.tickers.items():
        security = self.AddData(QuantpediaFutures, qp_ticker, Resolution.Daily)
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(leverage)
        qp_symbol:Symbol = security.Symbol
        # QC futures
        future:Future = self.AddFuture(qc_ticker, Resolution.Daily, dataNormalizationMode=DataNormalizationMode.Raw)
        future.SetFilter(timedelta(days=self.min_expiration_days), timedelta(days=self.max_expiration_days))
        self.futures_data[future.Symbol.Value] = FuturesData(qp_symbol, self.period)
    
    self.recent_month:int = -1
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
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
    curr_date:datetime.date = self.Time.date()
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
                    raw_price1:float = data[near_c.Symbol].Value * self.Securities[ticker].SymbolProperties.PriceMagnifier
                    raw_price2:float = data[dist_c.Symbol].Value * self.Securities[ticker].SymbolProperties.PriceMagnifier
                    if raw_price1 != 0 and raw_price2 != 0:
                        future_obj.update_prices(raw_price1, raw_price2)
    # Rebalance monthly
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    self.Liquidate()
    
    basis:dict[Symbol, float] = {}
    momentum:dict[Symbol, float] = {}
    volatility:dict[Symbol, float] = {}
    for _, future_obj in self.futures_data.items():
        data_ready_flag:bool = future_obj.is_ready()
        if self.securities[future_obj.quantpedia_future].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[future_obj.quantpedia_future]:
            self.liquidate()
            return
        # make sure data are ready
        if data_ready_flag:
            qp_symbol:Symbol = future_obj.quantpedia_future
            
            basis_value, momentum_value, volatility_value = future_obj.get_metrics()
            basis[qp_symbol] = basis_value
            momentum[qp_symbol] = momentum_value
            volatility[qp_symbol] = volatility_value
        # reset future's data
        elif data_ready_flag:
            future_obj.reset_data()
    # make sure there are enough futures for selection
    if len(volatility) == 0:
        return
    
    # inverse volatility weighting
    long_part:List[Symbol] = [x[0] for x in momentum.items() if x[1] > 0 and x[0] in basis and basis[x[0]] > 0]
    short_part:List[Symbol] = [x[0] for x in momentum.items() if x[1]  None:
    self.quantpedia_future:Symbol = quantpedia_future
    self.near_contract:FuturesContract = None
    self.distant_contract:FuturesContract = None
    self.first_contract_prices:RollingWindow = RollingWindow[float](period)
    self.second_contract_price:float = None
def update_prices(self, first_contract_price:float, second_contract_price:float) -> None:
    self.first_contract_prices.Add(first_contract_price)
    self.second_contract_price = second_contract_price
def update_contracts(self, near_contract:FuturesContract, distant_contract:FuturesContract) -> None:
    self.near_contract = near_contract
    self.distant_contract = distant_contract
def get_metrics(self) -> tuple:
    prices:np.array = np.array([x for x in self.first_contract_prices])
    momentum_value:float = prices[0] / prices[-1] - 1
    
    returns:np.array = (prices[:-1] - prices[1:]) / prices[1:]
    volatility_value:float = np.std(returns)
    basis_value:float = np.log(prices[0] - self.second_contract_price)
    return basis_value, momentum_value, volatility_value
def reset_data(self) -> None:
    self.first_contract_prices.Reset()
    self.second_contract_price = None
def is_initialized(self) -> bool:
    return self.near_contract is not None and self.distant_contract is not None
def is_ready(self) -> bool:
    return self.first_contract_prices.IsReady and self.second_contract_price != None
# Custom fee model
class CustomFeeModel(FeeModel):
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
