# Original QuantConnect / library Python
# locale=zh slug="优化子投资组合动量策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from itertools import combinations
from pandas.core.frame import DataFrame
from dateutil.relativedelta import relativedelta
from scipy.optimize import minimize
import sys
# endregion
class OptimalizedSubportfolioMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)
    industry_tickers: List[str] = [
        'XLB', 'XLY', 'XLF', 'XLP', 'XLV', 'XLU', 'XLC', 'XLE', 'XLI', 'XLK'
    ]
    self.universe_assets: List[Symbol] = [
        self.AddEquity(ticker, Resolution.Daily).Symbol for ticker in industry_tickers
    ]
    self.cash: Symbol = self.AddEquity('BIL', Resolution.Daily).Symbol
    self.max_lookback_period: int = 18
    self.period: int = 60
    self.percentage_traded: float = .9
    self.universe_returns: Dict[Symbol, RollingWindow] = {
        symbol : RollingWindow[float](self.period) for symbol in self.universe_assets
    }
    
    self.recent_month: int = -1
    self.settings.daily_precise_end_time = False
def OnData(self, slice: Slice) -> None:
    # rebalance once a month
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    # price history
    etf_history: DataFrame = self.History(self.universe_assets + [self.cash], start=self.Time.date() - relativedelta(months=self.period + self.max_lookback_period), end=self.Time.date())['close'].unstack(level=0)
    etf_history = etf_history.groupby(pd.Grouper(freq='MS')).last()
    etf_history = etf_history.pct_change()
    etf_history = etf_history.iloc[1:]
    # data is ready
    if any(np.isnan(x) for x in etf_history.iloc[0]) or len(etf_history)  cash, 1 -> sub-portfolio
        signal[etf_cols_from_range] = np.where(ema_df[etf_cols_from_range].values > ema_df[cash_cols].values, 1, 0)
    
    # all the possible combination of sub-portfolios
    best_comb: Series = pd.Series()
    best_comb_sharpe: float = sys.float_info.min
    for period in range(1, self.max_lookback_period + 1):
        relevant_portfolios: List[str] = [x for x in etf_cols if x[-len(f'_{period}'):] == f'_{period}']
        for cnt in range(1, len(relevant_portfolios) + 1):
            for combination in list(combinations(relevant_portfolios, cnt)):
                comb_etfs: List[str] = [x.split('_')[0] for x in combination]
                comb_arr: List[str] = list(combination)
                # replace 0 with cash
                comb_df: DataFrame = etf_history[comb_etfs].values * signal[comb_arr].shift(1)
                for col in comb_arr:
                    comb_df[col] = np.where(comb_df[col] == 0, etf_history[self.cash], comb_df[col])
                # calculate sharpe ratio
                comb_df_perf: DataFrame = comb_df.mean(axis=1)
                comb_df_perf = comb_df_perf.iloc[1:]
                sr:float = comb_df_perf.mean() / comb_df_perf.std()  * (12 ** 0.5)
                if sr > best_comb_sharpe:
                    best_comb_sharpe = sr
                    best_comb = signal[comb_arr].iloc[-1]
    # traded weight calculation
    traded_weight:Dict[Symbol, float] = {}
    for item in best_comb.index:
        etf: Symbol = self.Symbol(item.split('_')[0])
        signal: int = best_comb[item]
        if signal == 1:
            traded_weight[etf] = self.percentage_traded / best_comb.shape[0]
        else:
            if self.cash not in traded_weight:
                traded_weight[self.cash] = 0
            traded_weight[self.cash] += self.percentage_traded / best_comb.shape[0]
    # trade execution
    invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in traded_weight:
            self.Liquidate(symbol)
    for symbol, w in traded_weight.items():
        self.SetHoldings(symbol, w)
