# Original QuantConnect / library Python
# locale=en slug="betting-against-uncertainty-beta-in-australia"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from scipy import stats
import numpy as np
#endregion
class BettingAgainstUncertaintyBetainAustralia(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    
    market: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.data: Dict[Symbol, RollingWindow] = {}    # daily stock prices
    self.period: int = 13
    self.leverage: int = 5
    self.quantile: int = 5
    self.min_share_price: float = 5.
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']
    
    # US National Business Confidence Index data
    # Data source: https://www.policyuncertainty.com/us_monthly.html
    self.nbci_data_symbol: Symbol = self.AddData(data_tools.BusinessConfidence, 'BusinessConfidence', Resolution.Daily).Symbol
    self.previous_nbci = None
    self.delta_nbci: List = []
    self.minimum_delta_nbci_period: int = 12   # minimum period for assessing sentiment period
    
    # US Economic policy uncertainty data
    # Data source: https://stats.oecd.org/index.aspx?queryid=299#
    self.epu_data_symbol: Symbol = self.AddData(data_tools.PolicyUncertainty, 'PolicyUncertainty', Resolution.Daily).Symbol
    self.monthly_epu: RollingWindow = RollingWindow[float](self.period-1)

    self.weight: Dict[Symbol, float] = {}    # traded weight for current month

    # universe properties
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    last_update_date: Dict[Symbol, datetime.date] = {
        data_tools.BusinessConfidence.get_last_update_date(),
        data_tools.PolicyUncertainty.get_last_update_date()
    }
    if not self.Securities[self.nbci_data_symbol].GetLastData() and self.Time.date()  self.min_share_price
        and f.MarketCap != 0
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # wait until year of monthly EPU data is ready
    if not self.monthly_epu.IsReady:
        return Universe.Unchanged
    epu_beta: Dict[Fundamental, float] = {}
    # warmup price rolling windows
    for stock in selected:
        symbol: Symbol = stock.Symbol
        
        if symbol not in self.data:
            self.data[symbol] = RollingWindow[float](self.period)
            history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes: Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].Add(close)
        
        if self.data[symbol].IsReady:
            # estimate monthly EPU beta
            monthly_prices: np.ndarray = np.array([x for x in self.data[symbol]])
            monthly_returns: np.ndarray = monthly_prices[:-1] / monthly_prices[1:] - 1
            slope,_,_,_,_ = stats.linregress(monthly_returns, [x for x in self.monthly_epu])
            epu_beta[stock] = slope
    
    if len(epu_beta) >= self.quantile:
        # sorting by EPU beta
        sorted_by_beta: List[Fundamental] = sorted(epu_beta, key = epu_beta.get, reverse=True)
        quantile: int = int(len(sorted_by_beta) / self.quantile)
        long: List[Fundamental] = sorted_by_beta[-quantile:]
        short: List[Fundamental] = sorted_by_beta[:quantile]
        
        # market cap weighting
        for i, portfolio in enumerate([long, short]):
            mc_sum: float = sum(map(lambda x: x.MarketCap, portfolio))
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum
    return list(self.weight.keys())
    
def OnData(self, slice: Slice) -> None:
    new_data_arrived: bool = False
    low_sentiment_flag: bool = False
    
    # store monthly nbci data and delta nbci
    if self.nbci_data_symbol in slice and slice[self.nbci_data_symbol]:
        new_data_arrived = True # new data arrived
        
        current_nbci: float = slice[self.nbci_data_symbol].Value
        if self.previous_nbci:
            d_nbci: float = current_nbci / self.previous_nbci - 1
            self.delta_nbci.append(d_nbci)
            
            # at least one year of data is ready for median calculation
            if len(self.delta_nbci) >= self.minimum_delta_nbci_period:
                delta_nbci_median: float = np.median(self.delta_nbci)
                # sentiment
                if d_nbci
