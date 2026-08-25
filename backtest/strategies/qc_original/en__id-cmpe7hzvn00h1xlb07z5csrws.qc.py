# Original QuantConnect / library Python
# locale=en slug="动量崩盘的对冲策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Dict
from pandas.core.frame import DataFrame
# endregion

class HedgingMomentumCrashes(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.treasury:Symbol = self.AddEquity('BIL', Resolution.Daily).Symbol
    
    self.weight:Dict[Symbol, float] = {}
    self.data:Dict[Symbol, SymbolData] = {}
    self.volatilities:List[float] = []
    self.short:List[Fundamental] = []

    self.volatility_period:int = 126
    self.min_period:int = 12
    self.annual_period:int = self.min_period * 21
    self.quantile:int = 10
    self.leverage:int = 5
    
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x:x.DollarVolume

    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.treasury), self.TimeRules.AfterMarketOpen(self.treasury), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
    
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # store daily stock prices
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        if symbol in self.data:
            self.data[symbol].update_daily_return(stock.AdjustedPrice)
            
            if self.selection_flag:
                self.data[symbol].update_monthly_data(stock.AdjustedPrice)

    if self.selection_flag:
        short_count:int = len(self.short)
        if short_count != 0:
            short_portfolio_returns:np.ndarray = [self.data[stock.Symbol].get_daily_returns(self.volatility_period) for stock in self.short]
            weights:np.ndarray = np.ones(short_count) / short_count
            self.volatilities.append(self.annual_port_vol(weights, short_portfolio_returns))

    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged

    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.MarketCap != 0 and x.Market == 'usa' and \
                                    ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE"))]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    perf:Dict[Symbol, float] = {}

    # price warmup
    for stock in selected:
        symbol:Symbol = stock.Symbol

        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(self.annual_period, self.min_period)
            history:DataFrame = self.History(symbol, self.annual_period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            data:pd.DataFrame = history.loc[symbol]
            monthly_data = data.groupby(pd.Grouper(freq='MS')).last()
            for time, row in data.iterrows():
                self.data[symbol].update_daily_return(row.close)
            for time, row in monthly_data.iterrows():
                self.data[symbol].update_monthly_data(row.close)
        
        # calculate momentum
        if self.data[symbol].is_ready():
            if self.data[symbol].get_momentum() == 0:
                continue
            perf[stock] = self.data[symbol].get_momentum()

    if len(perf) >= self.quantile:
        sorted_by_perf:List = sorted(perf.items(), key = lambda x:x[1], reverse=True)
        quantile:int = int(len(sorted_by_perf) / self.quantile)
        long:List[Fundamental] = [x[0] for x in sorted_by_perf[:quantile]]
        self.short:List[Fundamental] = [x[0] for x in sorted_by_perf[-quantile:]]

        if len(self.volatilities) >= self.min_period:
            trade_direction:bool = True if self.volatilities[-1]  None:
    if not self.selection_flag:
        return
    self.selection_flag = False

    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True

def annual_port_vol(self, weights: np.ndarray, daily_returns: np.ndarray) -> float:
    # calculate the annual volatility of portfolio
    returns_array:np.ndarray = np.column_stack(daily_returns)
    covariance_matrix:np.ndarray = np.cov(returns_array, rowvar=False) * 252
    result:float = np.sqrt(np.dot(weights.T, np.dot(covariance_matrix, weights)))
    return result
