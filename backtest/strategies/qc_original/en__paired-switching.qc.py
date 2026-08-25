# Original QuantConnect / library Python
# locale=en slug="paired-switching"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
from collections import deque
import numpy as np
import data_tools
#endregion
class ShortTermReversalwithFutures(XXX):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000) 
    symbols:Dict[str, str] = {
        'CME_S1': Futures.Grains.Soybeans,
        'CME_W1': Futures.Grains.Wheat,
        'CME_BO1': Futures.Grains.SoybeanOil,
        'CME_C1': Futures.Grains.Corn,
        'CME_LC1': Futures.Meats.LiveCattle,
        'CME_FC1': Futures.Meats.FeederCattle,
        'CME_KW2': Futures.Grains.Wheat,
        'ICE_CC1': Futures.Softs.Cocoa,
        'ICE_SB1': Futures.Softs.Sugar11CME,
        
        'CME_GC1': Futures.Metals.Gold,
        'CME_SI1': Futures.Metals.Silver,
        'CME_PL1': Futures.Metals.Platinum,
        'CME_RB1': Futures.Energies.Gasoline,
        'ICE_WT1': Futures.Energies.CrudeOilWTI,
        'ICE_O1': Futures.Energies.HeatingOil,
        'CME_BP1': Futures.Currencies.GBP,
        'CME_EC1': Futures.Currencies.EUR,
        'CME_JY1': Futures.Currencies.JPY,
        'CME_SF1': Futures.Currencies.CHF,
        'CME_ES1': Futures.Indices.SP500EMini,
        'CME_TY1': Futures.Financials.Y10TreasuryNote,
        'CME_FV1': Futures.Financials.Y5TreasuryNote,
    }
                    
    self.period:int = 14
    self.futures_info:Dict = {}
    min_expiration_days:int = 2
    max_expiration_days:int = 360
    # daily close, volume and open interest data
    self.data:Dict = {}
    self.quantile:int = 2
    for qp_symbol, qc_future in symbols.items():
        # QP futures
        data:Security = self.AddData(data_tools.QuantpediaFutures, qp_symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(5)
        self.data[data.Symbol] = deque(maxlen=self.period)
        
        # QC futures
        future:Future = self.AddFuture(qc_future, Resolution.Daily)
        future.SetFilter(timedelta(days=min_expiration_days), timedelta(days=max_expiration_days))
        self.futures_info[future.Symbol.Value] = data_tools.FuturesInfo(data.Symbol)
    self.recent_month:int = -1
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
def find_and_update_contracts(self, futures_chain, symbol) -> None:
    near_contract:FuturesContract = None
    if symbol in futures_chain:
        contracts:List = [contract for contract in futures_chain[symbol] if contract.Expiry.date() > self.Time.date()]
        if len(contracts) >= 2:
            contracts:List = sorted(contracts, key=lambda x: x.Expiry, reverse=False)
            near_contract = contracts[0]
    self.futures_info[symbol].update_contracts(near_contract)
def OnData(self, data: Slice) -> None:
    if data.FutureChains.Count > 0:
        for symbol, futures_info in self.futures_info.items():
            # check if near contract is expired or is not initialized
            if not futures_info.is_initialized() or \
                (futures_info.is_initialized() and futures_info.near_contract.Expiry.date()  self.quantile * 2:
            volume_sorted:List = sorted(ret_volume_oi_data.items(), key = lambda x: x[1][1], reverse = True)
            quantile:int = int(len(volume_sorted) / self.quantile)
            high_volume:List = [x for x in volume_sorted[:quantile]]
            
            open_interest_sorted:List = sorted(ret_volume_oi_data.items(), key = lambda x: x[1][2], reverse = True)
            quantile = int(len(open_interest_sorted) / self.quantile)
            low_oi:List = [x for x in open_interest_sorted[-quantile:]]
            
            filtered:List = [x for x in high_volume if x in low_oi]
            filtered_by_return:List = sorted(filtered, key = lambda x : x[0], reverse = True)
            quantile = int(len(filtered_by_return) / self.quantile)
            long:List[Symbol] = filtered_by_return[-quantile:]
            short:List[Symbol] = filtered_by_return[:quantile]
            if len(long + short) >= 2: 
                # return weighting
                diff:Dict[Symbol, float] = {}
                avg_ret:float = np.average([x[1][0] for x in long + short])
    
                for symbol, ret_volume_oi in long + short:
                    diff[symbol] = ret_volume_oi[0] - avg_ret
                
                total_diff:float = sum([abs(x[1]) for x in diff.items()])
                long_symbols:List[Symbol] = [x[0] for x in long]
    
                if total_diff != 0:
                    for symbol, data in long + short:
                        if symbol in long_symbols:
                            weight[symbol] = diff[symbol] / total_diff
                        else:
                            weight[symbol] = - diff[symbol] / total_diff
        # trade execution
        invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
        for symbol in invested:
            if symbol not in weight:
                self.Liquidate(symbol)
        for symbol, w in weight.items():
            self.SetHoldings(symbol, w)
