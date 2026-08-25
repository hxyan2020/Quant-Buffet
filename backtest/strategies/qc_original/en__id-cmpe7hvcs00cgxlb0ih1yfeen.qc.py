# Original QuantConnect / library Python
# locale=en slug="异常交易量持续效应策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from dateutil.relativedelta import relativedelta
import numpy as np
# endregion

class PersistenceofAbnormalTradingVolumeEffect(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.long_by_month:Dict[int, Symbol] = {}
    self.short_by_month:Dict[int, Symbol] = {}
    self.symbol_data:Dict[Symbol, SymbolData] = {}

    self.monthly_period:int = 18
    self.delete_treshold:int = 2
    self.quantile:int = 5
    self.leverage:int = 5

    self.fundamental_count:int = 1000
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetLeverage(self.leverage)
        security.SetFeeModel(CustomFeeModel())
    
    for security in changes.RemovedSecurities:
        if security.Symbol in self.symbol_data:
            self.symbol_data.pop(security.Symbol)

def FundamentalSelectionFunction(self, fundamental:List[Fundamental]) -> List[Symbol]:
    # store volume every day
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        if symbol in self.symbol_data:
            self.symbol_data[symbol].update_daily_volume(stock.Volume)

    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged


    selected:List[Symbol] = [x.Symbol
        for x in sorted([x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.AdjustedPrice >= 1 and x.MarketCap != 0 and \
        (x.SecurityReference.ExchangeId == 'NYS') or (x.SecurityReference.ExchangeId == 'NAS') or (x.SecurityReference.ExchangeId == 'ASE')
        ], 
        key = lambda x: x.DollarVolume, reverse = True)][:self.fundamental_count]

    # selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.AdjustedPrice >= 1 and x.MarketCap != 0 and \
    #     (x.SecurityReference.ExchangeId == 'NYS') or (x.SecurityReference.ExchangeId == 'NAS') or (x.SecurityReference.ExchangeId == 'ASE')
    # ]        
    # if len(selected) > self.fundamental_count:
    #     selected = [x.Symbol for x in sorted(selected, key=lambda x: x.MarketCap, reverse=True)[:self.fundamental_count]]
    # else:
    #     selected = list(map(lambda x: x.Symbol, selected))

    # store monthly data
    for symbol in self.symbol_data:
        self.symbol_data[symbol].update_monthly_data()

    ATV:Dict[Symbol, float] = {}
    for symbol in selected:
        if symbol not in self.symbol_data:
            self.symbol_data[symbol] = SymbolData(self.monthly_period)

        if self.symbol_data[symbol].is_ready():
            ATV[symbol] = self.symbol_data[symbol].ATV()

    # sort and divide to upper decile and lower decile
    if len(ATV) >= self.quantile:
        sorted_volume:List[Symbol] = sorted(ATV, key=ATV.get, reverse=True)
        quantile:int = len(sorted_volume) // self.quantile
        self.long_by_month[self.Time.month] = sorted_volume[:quantile]
        self.short_by_month[self.Time.month] = sorted_volume[-quantile:]

        self.long = symbol_quantile_check(self.Time, self.long_by_month)
        self.short = symbol_quantile_check(self.Time, self.short_by_month)

        if len(self.long_by_month) > self.delete_treshold:
            self.long_by_month.pop(list(self.long_by_month.keys())[0])
            self.short_by_month.pop(list(self.short_by_month.keys())[0])
        
    return self.long + self.short

def OnData(self, data: Slice) -> None:
    # monthly rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False

    # order execution
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    
    self.long.clear()
    self.short.clear()

def Selection(self) -> None:
    self.selection_flag = True

def symbol_quantile_check(time:datetime, symbols:Dict[int, List[Symbol]]) -> List[Symbol]:
t_1 = (time - relativedelta(months=1)).month
t_2 = (time - relativedelta(months=2)).month
if t_1 in symbols and t_2 in symbols:
    # fet the symbols for the months
    m_month = set(symbols[time.month])
    m_1_month = set(symbols[t_1])
    m_2_month = set(symbols[t_2])

    # symbols in m, m-1 but not in m-2
    missing_symbols = list(m_1_month.intersection(m_month).difference(m_2_month))
    return missing_symbols

return []

# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))

class SymbolData():
def __init__(self, monthly_period:int) -> None:
    self._monthly_period = monthly_period
    
    self._daily_volume_date:List[float] = []
    self._recent_monthly_volume_mean:float = None
    self._monthly_volume_sum:RollingWindow = RollingWindow[float](monthly_period)

def update_daily_volume(self, volume:float) -> None:
    self._daily_volume_date.append(volume)

def update_monthly_data(self) -> None:
    self._recent_monthly_volume_mean = np.mean(list(self._daily_volume_date))
    self._monthly_volume_sum.Add(sum(list(self._daily_volume_date)))
    self._daily_volume_date.clear()

def ATV(self) -> float:
    atv:float = np.log(self._recent_monthly_volume_mean / np.mean(list(self._monthly_volume_sum)[-12:]))
    return atv

def is_ready(self) -> bool:
    return self._monthly_volume_sum.IsReady and self._recent_monthly_volume_mean is not None
