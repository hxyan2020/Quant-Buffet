# Original QuantConnect / library Python
# locale=zh slug="储蓄率贝塔与股票表现"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from collections import deque
from typing import List, Dict
from pandas.core.frame import DataFrame
from scipy import stats
import data_tools
class SavingsRateBetaandPerformanceofStocks(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.selected_stocks:List[Fundamental] = []
    
    # Daily price data.
    self.data:Dict[Symbol, float] = {}
    self.period:int = 21
    self.quantile:int = 5
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.regression_period:int = 36
    self.regression_data:Dict[Symbol, deque] = {}
    
    # Saving rate data.
    self.saving_rate:Symbol = self.AddData(data_tools.SavingRate, 'PSAVERT', Resolution.Daily).Symbol  # Monthly resolution.
    # Uncertainity index data.
    self.uncertainity_index:Symbol = self.AddData(data_tools.UncertainityIndex, 'USEPUINDXD', Resolution.Daily).Symbol # Daily resolution.
    self.uncertainity_index_max_period:int = 20 * 12 * 30
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)            
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.RemovedSecurities:
        symbol:Symbol = security.Symbol
        if symbol in self.regression_data:
            del self.regression_data[symbol]
    
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].append(stock.AdjustedPrice)    
    
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.Market == 'usa' and x.MarketCap != 0
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        if symbol not in self.regression_data:
            self.regression_data[symbol] = deque(maxlen = self.regression_period)
        
        # Warmup data queue.
        if symbol not in self.data:
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if 'close' in history:
                closes:pd.Series = [x for x in history.close]
                self.data[symbol] = deque(closes, maxlen = self.period)
            else:
                self.data[symbol] = deque(maxlen = self.period)
    
    self.selected_stocks = selected
    return list(map(lambda x: x.Symbol, selected))
    
def OnData(self, data: Slice) -> None:
    saving_rate_last_update_date:DateTime.Date = data_tools.SavingRate.get_last_update_date()
    uncertainity_index_last_update_date:DateTime.Date = data_tools.UncertainityIndex.get_last_update_date()
    # data is still comming in
    if self.Securities[self.saving_rate].GetLastData() and self.Securities[self.uncertainity_index]:
        if self.saving_rate in saving_rate_last_update_date and self.Time.date() >= saving_rate_last_update_date[self.saving_rate] or \
            self.uncertainity_index in uncertainity_index_last_update_date and self.Time.date() >= uncertainity_index_last_update_date[self.uncertainity_index]: 
            self.Liquidate()
            return
    # store data
    if self.uncertainity_index in data:
        if data[self.uncertainity_index]:
            if self.uncertainity_index not in self.data:
                hist:DataFrame = self.History(self.uncertainity_index, self.uncertainity_index_max_period, Resolution.Daily)
                uncertainity_index_hist:DataFrame = hist[~hist.index.duplicated(keep='first')]
                if len(uncertainity_index_hist) != 0:
                    # Prevent from adding the same value in the next step - OnData function.
                    self.data[self.uncertainity_index] = deque(uncertainity_index_hist['value'][:-1])
            self.data[self.uncertainity_index].append(data[self.uncertainity_index].Value)
    
    # store savings rate
    if self.saving_rate in data:
        if data[self.saving_rate]:
            self.data[self.saving_rate] = data[self.saving_rate].Value
    
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Beta and market cap tuple.
    beta:Dict[Fundamental, float] = {}
    
    for stock in self.selected_stocks:
        symbol:Symbol = stock.Symbol
        # Saving rate data is ready.
        if self.saving_rate in self.data and len(self.data[symbol]) == self.data[symbol].maxlen:
            symbol_return:float = self.Return(self.data[symbol])
            saving_rate:float = self.data[self.saving_rate]
                
            self.regression_data[symbol].append((symbol_return, saving_rate))
                
            if len(self.regression_data[symbol]) == self.regression_data[symbol].maxlen:
                symbol_returns:List[float] = [x[0] for x in self.regression_data[symbol]]
                saving_rates:List[float] = [x[1] for x in self.regression_data[symbol]]
                    
                slope, intercept, r_value, p_value, std_err = stats.linregress(saving_rates, symbol_returns)
                beta[stock] = slope
    
    weight:Dict[Symbol, float] = {}
    if len(beta) >= self.quantile:
        # Beta sorting.
        sorted_by_beta:List[Fundamental] = sorted(beta, key = beta.get, reverse = True)
        quantile:int = int(len(sorted_by_beta) / self.quantile)
        long:List[Fundamental] = sorted_by_beta[-quantile:]
        short:List[Fundamental] = sorted_by_beta[:quantile]
        
        uncertainity_index_median:float = np.median(self.data[self.uncertainity_index])
        
        # Market cap weighting.
        # NOTE: The higher the macroeconomic uncertainty index, higher uncertainty levels.
        if self.data[self.uncertainity_index][-1] > uncertainity_index_median:
            for i, portfolio in enumerate([long, short]):
                mc_sum:float = sum(map(lambda x: x.MarketCap, portfolio))
                for stock in portfolio:
                    weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum
    
    # Trade execution.
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

def Selection(self) -> None:
    self.selection_flag = True
    
def Return(self, values) -> float:
    return (values[-1] - values[0]) / values[0]
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
