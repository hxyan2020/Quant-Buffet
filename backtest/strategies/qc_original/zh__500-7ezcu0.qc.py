# Original QuantConnect / library Python
# locale=zh slug="标普500指数的短期自适应反转"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
from pandas.core.frame import DataFrame
from typing import List
import sys
# endregion
class ShorttermAdaptiveReversalinSP500Index(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(1999, 1, 1)
    self.SetCash(100000)
    # market subscription and consolidator
    self.market:Symbol = self.AddEquity("SPY", Resolution.Minute).Symbol
    self.consolidator = TradeBarConsolidator(timedelta(days=1))
    self.consolidator.DataConsolidated += self.consolidation_handler
    self.SubscriptionManager.AddConsolidator(self.market, self.consolidator)
    
    # history warmup
    min_day_period:int = 200
    history:DataFrame = self.History(self.market, start=self.Time.date() - relativedelta(years=1), end=self.Time.date(), resolution=Resolution.Daily)
    if len(history) >= min_day_period and 'close' in history.columns:
        self.history = history['close'].unstack(level=0).dropna()
    else:
        message:str = f'Need at least {min_day_period} days of market warmup data -> SPY data is available from 1998'
        self.Debug(message)
        self.Quit(message)
    
    # optimization setting
    self.optimize_long:bool = True
    self.optimize_short:bool = False
    self.opt_flags:List[bool] = [True, False] if (self.optimize_long and self.optimize_short) else [True] if (self.optimize_long and not self.optimize_short) else [False] if (not self.optimize_long and self.optimize_short) else []
    self.opt_buy_ema:float = None
    self.opt_sell_ema:float = None
    self.opt_buy_level:float = None
    self.opt_sell_level:float = None
    
    # optimization parameters
    self.optimize_flag:bool = False
    self.ema_param_range:List[int] = list(range(2, 21, 1))
    self.buy_level_param_range:List[float] = list(np.arange(-5, 0, 0.1))
    self.sell_level_param_range:List[float] = list(np.arange(0, 5, 0.1))
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Optimize)
def consolidation_handler(self, sender, consolidated) -> None:
    # store daily data
    self.history.loc[consolidated.EndTime, consolidated.Symbol] = consolidated.Close
    self.history = self.history.iloc[1:] 
def Optimize(self) -> None:
    if self.Time.month == 1:
        self.optimize_flag = True
def OnData(self, data: Slice) -> None:
    # one minute before close
    if self.Time.hour == 15 and self.Time.minute == 59:
        if self.market in data and data[self.market]:
            market_price_df:DataFrame = self.history
            signal:bool = False
            for buy_flag in self.opt_flags:
                opt_ema = self.opt_buy_ema if buy_flag else self.opt_sell_ema
                opt_level = self.opt_buy_level if buy_flag else self.opt_sell_level
                
                if opt_ema is not None and opt_level is not None:
                    # signal calculation
                    ema:float = market_price_df.ewm(span=opt_ema, adjust=False).mean().iloc[-1].values[0]
                    std:float = market_price_df.rolling(opt_ema).std().iloc[-1].values[0]
                    
                    z_score:float = (-ema + data[self.market].Value) / std
                    signal = opt_level > z_score if buy_flag else opt_level = ema_df['EMA_1'] # unnecessary
    z_score:np.ndarray = ((-ema_df.values).T + market_price_df[self.market].values) / std_df.values.T
    # optimization for long and short
    for buy_flag in self.opt_flags:
        opt_param_sharpe = sys.float_info.min
        opt_ema:int = 0
        opt_level:int = 0
        opt_found:bool = False
        for level in self.buy_level_param_range if buy_flag else self.sell_level_param_range:
            # calculate performance for each portfolio with particular buy level used
            signal:np.ndarray = (level > z_score).astype(float) if buy_flag else (level  opt_param_sharpe:
                    opt_param_sharpe:float = sharpe_ratio[index_of_max_sharpe]
                    opt_ema:int = self.ema_param_range[index_of_max_sharpe]
                    opt_level:int = level
                    opt_found = True
        # store optimal parameters for following year
        if opt_found:
            if buy_flag:
                self.opt_buy_ema = opt_ema
                self.opt_buy_level = opt_level
            else:
                self.opt_sell_ema = opt_ema
                self.opt_sell_level = opt_level
