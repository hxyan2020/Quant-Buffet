# Original QuantConnect / library Python
# locale=en slug="通过便利收益因子预测大宗商品期货收益策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
import numpy as np
from typing import List, Dict, Tuple
# endregion
class ConvenienceYieldRiskFactorPredictsCommodityFuturesReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2008, 1, 1)
    self.SetCash(100000)
    self.period:int = 12
    self.filter_period:int = 182
    self.tickers:dict[str, str] = {
        "CME_S1"  : Futures.Grains.Soybeans,
        "CME_W1"  : Futures.Grains.Wheat,
        "CME_SM1" : Futures.Grains.SoybeanMeal,
        "CME_BO1" : Futures.Grains.SoybeanOil,
        "CME_C1"  : Futures.Grains.Corn,
        "CME_O1"  : Futures.Grains.Oats,
        "CME_LC1" : Futures.Meats.LiveCattle,
        "CME_FC1" : Futures.Meats.FeederCattle,
        "CME_LN1" : Futures.Meats.LeanHogs,
        "CME_GC1" : Futures.Metals.Gold,
        "CME_SI1" : Futures.Metals.Silver,
        "CME_PL1" : Futures.Metals.Platinum,
        "CME_HG1" : Futures.Metals.Copper,
        "CME_LB1" : Futures.Forestry.RandomLengthLumber,
        "CME_NG1" : Futures.Energies.NaturalGas,
        "CME_PA1" : Futures.Metals.Palladium,
        "CME_CU1" : Futures.Energies.ChicagoEthanolPlatts,
        "CME_DA1" : Futures.Dairy.ClassIIIMilk,
        "ICE_CC1" : Futures.Softs.Cocoa,
        "ICE_CT1" : Futures.Softs.Cotton2,
        "ICE_KC1" : Futures.Softs.Coffee,
        "ICE_O1"  : Futures.Energies.HeatingOil,
        "ICE_OJ1" : Futures.Softs.OrangeJuice,
        "ICE_SB1" : Futures.Softs.Sugar11CME,
    }
    self.leverage:int = 2
    self.data:Dict[Symbol, Tuple[float, float]] = {}
    self.cyr_signal:Dict[Symbol, RollingWindow] = {}
    self.futures_data:dict[Symbol, data_tools.FuturesData] = {}
    for qp_ticker, qc_ticker in self.tickers.items():
        # subscribe Quantpedia data
        security:Security = self.AddData(data_tools.QuantpediaFutures, qp_ticker, Resolution.Daily)
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        qp_symbol:Symbol = security.Symbol
        # QC futures
        future:Future = self.AddFuture(qc_ticker, Resolution.Daily, dataNormalizationMode=DataNormalizationMode.Raw)
        future.SetFilter(0, self.filter_period)
        future_symbol:str = future.Symbol
        self.futures_data[future_symbol] = qp_symbol
    self.recent_month:int = -1

def OnData(self, data:Slice):
    qp_custom_data_last_update_date:Dict[Symbol, datetime.date] = data_tools.QuantpediaFutures._last_update_date
    if all([self.Securities[x].GetLastData() for x in list(self.futures_data.keys())]) and any([self.Time.date() >= qc_custom_data_last_update_date[x] for x in qc_custom_data_last_update_date]):
        self.Liquidate()
        return
    # save daily data 
    for contract_symbol, chain in data.FutureChains.items():
        if len([i for i in chain]) >= 3:
            sorted_by_date:List[Symbol] = sorted(chain, key=lambda x: x.Expiry)
            first_convenience_yield:float = (365 * (sorted_by_date[0].LastPrice - sorted_by_date[1].LastPrice)) / ((sorted_by_date[1].Expiry - self.Time).days - (sorted_by_date[0].Expiry - self.Time).days)
            second_convenience_yield:float = (365 * (sorted_by_date[1].LastPrice - sorted_by_date[2].LastPrice)) / ((sorted_by_date[2].Expiry - self.Time).days - (sorted_by_date[1].Expiry - self.Time).days)
            if contract_symbol not in self.data:
                self.data[contract_symbol] = []
            self.data[contract_symbol].append((first_convenience_yield, second_convenience_yield))
    # monthly rebalance
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    if len(self.data) == 0:
        self.Liquidate()
        return
    # save convenience yield risk values
    for contract_symbol, cyr_values in self.data.items():
        if len(cyr_values) != 0:
            first_std:float = np.std([i[0] for i in cyr_values])
            second_std:float = np.std([i[1] for i in cyr_values])
            if contract_symbol not in self.cyr_signal:
                self.cyr_signal[contract_symbol] = RollingWindow[float](self.period)
            
            self.cyr_signal[contract_symbol].Add(first_std - second_std)
    self.data.clear()
    if len(self.cyr_signal) == 0:
        self.Liquidate()
        return
    cyr_mean:Dict[Symbol, float] = {}
    # mean of 12 months convenience yield risk values
    for contract_symbol, cyr_signals in self.cyr_signal.items():
        if cyr_signals.IsReady:
            if contract_symbol not in cyr_mean:
                cyr_mean[contract_symbol] = np.mean(list(cyr_signals))
    # sort and divide
    if len(cyr_mean) != 0:
        sorted_cyr:List[Symbol] = sorted(cyr_mean.items(), key=lambda x:x[1])
        CYR_median:float = np.median([i[1] for i in sorted_cyr])
        high:List[Symbol] = [symbol for symbol, cyr_value in sorted_cyr if cyr_value > CYR_median]
        low:List[Symbol] = [symbol for symbol, cyr_value in sorted_cyr if cyr_value
