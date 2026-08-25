# Original QuantConnect / library Python
# locale=zh slug="均值方差套利交易策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import pandas as pd
from collections import deque
import data_tools
class MeanVarianceCarryTradeStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2009, 1, 1)
    self.SetCash(100000)
    
    self.tickers:dict[str, str] = {
        'CME_AD1' : Futures.Currencies.AUD, # Australian Dollar Futures, Continuous Contract #1
        'CME_BP1' : Futures.Currencies.GBP, # British Pound Futures, Continuous Contract #1
        'CME_CD1' : Futures.Currencies.CAD, # Canadian Dollar Futures, Continuous Contract #1
        'CME_EC1' : Futures.Currencies.EUR, # Euro FX Futures, Continuous Contract #1
        'CME_JY1' : Futures.Currencies.JPY, # Japanese Yen Futures, Continuous Contract #1
        'CME_MP1' : Futures.Currencies.MXN, # Mexican Peso Futures, Continuous Contract #1
        'CME_NE1' : Futures.Currencies.NZD, # New Zealand Dollar Futures, Continuous Contract #1
        'CME_SF1' : Futures.Currencies.CHF, # Swiss Franc Futures, Continuous Contract #1
    }
    self.period:int = 250
    self.max_missing_days:int = 5
    self.min_expiration_days:int = 0
    self.max_expiration_days:int = 360
    
    self.futures_data:dict[str, FuturesData] = {}
    for qp_ticker, qc_ticker in self.tickers.items():
        # quantpedia #1 Contract
        data = self.AddData(data_tools.QuantpediaFutures, qp_ticker, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(5)
        quantpedia_future_symbol:Symbol = data.Symbol
        # QC futures
        future:Future = self.AddFuture(qc_ticker, Resolution.Daily, dataNormalizationMode=DataNormalizationMode.Raw)
        future.SetFilter(timedelta(days=self.min_expiration_days), timedelta(days=self.max_expiration_days))
        self.futures_data[future.Symbol.Value] = data_tools.FuturesData(quantpedia_future_symbol, self.period)
    
    self.recent_month:int = -1
def FindAndUpdateContracts(self, futures_chain, ticker) -> None:
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
    # daily update QC futures data 
    if data.FutureChains.Count > 0:
        for ticker, future_obj in self.futures_data.items():
            # check if near contract is expired or is not initialized
            if not future_obj.is_initialized() or \
                (future_obj.is_initialized() and future_obj.near_contract.Expiry.date() == self.Time.date()):
                self.FindAndUpdateContracts(data.FutureChains, ticker)
            # update QC futures rolling return
            if future_obj.is_initialized():
                near_c:FuturesContract = future_obj.near_contract
                dist_c:FuturesContract = future_obj.distant_contract
                if near_c.Symbol in data and data[near_c.Symbol] and dist_c.Symbol in data and data[dist_c.Symbol]:
                    raw_price1:float = data[near_c.Symbol].Value * self.Securities[ticker].SymbolProperties.PriceMagnifier
                    raw_price2:float = data[dist_c.Symbol].Value * self.Securities[ticker].SymbolProperties.PriceMagnifier
                    if raw_price1 != 0 and raw_price2 != 0:
                        daily_return:float = raw_price1 / raw_price2 - 1 
                        future_obj.update_roll_return(daily_return)
    # check if quantpedia data still coming
    for _, future_obj in self.futures_data.items():
        quantpedia_future:Symbol = future_obj.quantpedia_future
        # if quantpedia_future in data and data[quantpedia_future]:
        #     future_obj.update_quantpedia_last_update(self.Time.date())
    # rebalance monthly
    if self.recent_month != self.Time.month:
        self.recent_month = self.Time.month
        self.Rebalance()
def Rebalance(self):
    custom_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()
    self.Liquidate()
    ready_futures:dict[Symbol, list] = {}
    
    # filter ready futures and reset futures, which do not recieve new data
    for _, future_obj in self.futures_data.items():
        data_ready_flag = future_obj.is_ready()
        if self.securities[future_obj.quantpedia_future].get_last_data() and self.time.date() > custom_data_last_update_date[future_obj.quantpedia_future]:
            self.liquidate()
            return
        if data_ready_flag:
            ready_futures[future_obj.quantpedia_future] = future_obj.reverse_roll_return()
        elif data_ready_flag:
            future_obj.reset_data()
    
    ready_futures_length:int = len(ready_futures)
    if ready_futures_length == 0: return
    df:pd.DataFrame = pd.DataFrame(ready_futures, columns=ready_futures.keys())
    optimization:data_tools.PortfolioOptimization = data_tools.PortfolioOptimization(df, 0, ready_futures_length)
    opt_weight:list[float] = optimization.opt_portfolio()
    if sum(opt_weight) == 0: return
    for index in range(ready_futures_length):
        weight:float = opt_weight[index]
        if weight >= 0.001:
            self.SetHoldings(df.columns[index], weight)
