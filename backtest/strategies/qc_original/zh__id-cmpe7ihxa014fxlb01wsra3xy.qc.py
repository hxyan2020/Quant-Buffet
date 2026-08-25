# Original QuantConnect / library Python
# locale=zh slug="货币市场中的价差（基差）动量"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
#endregion
class SpreadBasisMomentumWithinCurrencies(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2009, 1, 1)
    self.SetCash(100000)
    
    self.tickers:Dict[str, str] = {
        'CME_AD1' : Futures.Currencies.AUD, # Australian Dollar Futures, Continuous Contract #1
        'CME_BP1' : Futures.Currencies.GBP, # British Pound Futures, Continuous Contract #1
        'CME_CD1' : Futures.Currencies.CAD, # Canadian Dollar Futures, Continuous Contract #1
        'CME_EC1' : Futures.Currencies.EUR, # Euro FX Futures, Continuous Contract #1
        'CME_JY1' : Futures.Currencies.JPY, # Japanese Yen Futures, Continuous Contract #1
        'CME_MP1' : Futures.Currencies.MXN, # Mexican Peso Futures, Continuous Contract #1
        'CME_NE1' : Futures.Currencies.NZD, # New Zealand Dollar Futures, Continuous Contract #1
        'CME_SF1' : Futures.Currencies.CHF, # Swiss Franc Futures, Continuous Contract #1
    }
    self.futures_data:Dict[str, data_tools.FutureData] = {}
    self.futures_count:int = 2
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

def OnData(self, data: Slice) -> None:
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
                    raw_price1:float = data[near_c.Symbol].Value * self.Securities[ticker].SymbolProperties.PriceMagnifier
                    raw_price2:float = data[dist_c.Symbol].Value * self.Securities[ticker].SymbolProperties.PriceMagnifier
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
