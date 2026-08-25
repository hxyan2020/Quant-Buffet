# Original QuantConnect / library Python
# locale=zh slug="外汇交易中的动量策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict, Union
from itertools import combinations
from pandas.core.frame import DataFrame
from enum import Enum
import numpy as np
# endregion
class TradingRule(Enum):
FILTER = 1
MOVING_AVERAGE = 2
CHANNEL = 3
MOMENTUM = 4
class TradedModel():
def __init__(self, symbol:str, trading_rule:TradingRule, param:Union[float, List[float]]) -> None:
    self._symbol:str = symbol
    self._rule:TradingRule = trading_rule
    self._param:Union[float, List[float]] = param
    self._sharpe_ratio:float = 0.

def get_symbol(self) -> str:
    return self._symbol

def get_param(self) -> Union[float, List[float]]:
    return self._param

def get_trading_rule(self) -> TradingRule:
    return self._rule
def get_sharpe_ratio(self) -> float:
    return self._sharpe_ratio

def set_sharpe_ratio(self, sharpe_ratio:float) -> None:
    self._sharpe_ratio = sharpe_ratio
class MomentumInFOREXTradingStrategies(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.reversed_fx_pairs:List[str] = [
        'USDCAD', 'USDJPY', 'USDSEK', 'USDHKD', 'USDZAR', 'USDCHF', 'USDTHB', 'USDSGD', 'USDCZK' #'USDKRW', 'USDRUB'
    ]
    self.fx_pairs:List[str] = [
        'GBPUSD', 'AUDUSD', 'EURUSD', 
    ]
    self.fx_pairs += self.reversed_fx_pairs
    for pair in self.fx_pairs:
        data = self.AddForex(pair, Resolution.Daily, Market.Oanda)
        
    self.filter_sizes:List[float] = [0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.1]
    self.ma_periods:List[Tuple[float]] = [(1., 5.), (5., 20.), (1., 200.)]
    self.momentum_periods:List[float] = [5., 20., 60.]
    self.channel_periods:List[float] = [5., 10., 20.]
    self.evaluation_period:int = 500
    self.x:float = 0.001
    self.top_model_cnt:int = 10
    self.active_models:List[TradedModel] = list()
    self.SetWarmUp(self.evaluation_period, Resolution.Daily)
    
    self.recent_month:int = -1
def OnData(self, data: Slice) -> None:
    if self.IsWarmingUp: return
    history:DataFrame = self.History(self.fx_pairs, self.evaluation_period, Resolution.Daily)
    closes:DataFrame = history['close'].unstack(level=0)
    
    # monthly model evaluation
    if self.recent_month != self.Time.month:
        self.recent_month = self.Time.month
    
        if len(closes) == self.evaluation_period + 1 and len(closes.columns) == len(self.fx_pairs):
            models:List[TradedModel] = []
            for symbol in self.fx_pairs:
                # symbol prices
                symbol_closes:DataFrame = closes[symbol]
                
                reverse_signal:bool = bool(symbol in self.reversed_fx_pairs)
                symbol_models:List[TradedModel] = self.create_models(symbol, symbol_closes, TradingRule.FILTER, self.filter_sizes, reverse_signal) \
                                        + self.create_models(symbol, symbol_closes, TradingRule.MOVING_AVERAGE, self.ma_periods, reverse_signal)   \
                                        + self.create_models(symbol, symbol_closes, TradingRule.MOMENTUM, self.momentum_periods, reverse_signal)   \
                                        + self.create_models(symbol, symbol_closes, TradingRule.CHANNEL, self.channel_periods, reverse_signal)     \
                
                models.extend(symbol_models)
            
            sorted_models:List = sorted(models, key=lambda item: item.get_sharpe_ratio(), reverse=True)
            self.active_models = sorted_models[:self.top_model_cnt]
    # rebalance daily
    model_cnt:int = len(self.active_models)
    weight_by_symbol:Dict[str, float] = { model.get_symbol() : 0. for model in self.active_models}
    
    if model_cnt != 0:
        model_weight:float = 1. / float(model_cnt)
        for model in self.active_models:
            symbol = model.get_symbol()
            symbol_closes:DataFrame = closes[symbol]
            signal:int = self.get_model_performance(symbol_closes, model, reverse_signal=symbol in self.reversed_fx_pairs, return_recent_signal=True)
            weight_by_symbol[symbol] += model_weight * signal
    invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in weight_by_symbol:
            self.Liquidate(symbol)
    
    for symbol, w in weight_by_symbol.items():
        self.SetHoldings(symbol, w)

def create_models(self, 
                symbol:str, 
                symbol_closes:DataFrame, 
                trading_rule:TradingRule, 
                params:Union[float, List[float]], 
                reverse_signal:bool=False) -> List[TradedModel]:
    models:List[TradedModel] = []
    for param in params:
        model:TradedModel = TradedModel(symbol, trading_rule, param)
        model_perf:np.ndarray = self.get_model_performance(symbol_closes, model, reverse_signal=reverse_signal)
        sharpe_ratio:float = self.get_sharpe_ratio(model_perf)
        if not np.isnan(sharpe_ratio):
            model.set_sharpe_ratio(sharpe_ratio)
            models.append(model)
    
    return models
def get_model_performance(self, 
                        symbol_closes:DataFrame, 
                        trade_model:TradedModel, 
                        reverse_signal:bool=False, 
                        return_recent_signal:bool = False) -> Union[np.ndarray, int]:
    symbol_returns:DataFrame = symbol_closes.pct_change()
    symbol_returns = symbol_returns.dropna()
    if trade_model.get_trading_rule() == TradingRule.FILTER:
        rolling_max:DataFrame = symbol_closes.cummax()
        rolling_min:DataFrame = symbol_closes.cummin()
        
        filter_size:float = float(trade_model.get_param())
        def filter_value_f(close, rolling_min, rolling_max, filter_size):
            if close >= rolling_min * (1 + filter_size):
                return 1
            elif close  long_term_ma[-1])
            recent_signal = (recent_signal * -1) if reverse_signal else recent_signal
            return recent_signal
        # shift to count in next days performance
        short_term_ma = short_term_ma.shift(1)
        long_term_ma = long_term_ma.shift(1)
        
        signal:np.ndarray = np.where(short_term_ma > long_term_ma, 1, -1)
        signal = (signal * -1) if reverse_signal else signal
        model_perf:np.ndarray = np.multiply(symbol_returns.iloc[long_term_period:].values, signal[1:][long_term_period:])
        
        return model_perf
    elif trade_model.get_trading_rule() == TradingRule.MOMENTUM:
        momentum_period:int = int(trade_model.get_param())
        rolling_momentum = symbol_closes.pct_change(periods=momentum_period)
        if return_recent_signal:
            recent_signal:int = int(rolling_momentum[-1] > 0.)
            recent_signal = (recent_signal * -1) if reverse_signal else recent_signal
            return recent_signal
        # shift to count in next days performance
        rolling_momentum = rolling_momentum.shift(1)
        rolling_momentum = rolling_momentum.dropna()
        signal:np.ndarray = np.where(rolling_momentum > 0., 1, -1)
        signal = (signal * -1) if reverse_signal else signal
        model_perf:np.ndarray = np.multiply(symbol_returns.iloc[-signal.shape[0]:].values, signal)
        return model_perf
    elif trade_model.get_trading_rule() == TradingRule.CHANNEL:
        channel_period:int = int(trade_model.get_param())
        rolling_min:DataFrame = symbol_closes.rolling(channel_period).min()
        rolling_max:DataFrame = symbol_closes.rolling(channel_period).max()
        
        def filter_value_f(close, rolling_min, rolling_max):
            if close >= rolling_min * (1 + self.x):
                return 1
            elif close  float:
    model_eq:np.ndarray = (model_perf + 1).cumprod(axis=0)
    volatility:float = np.std(model_perf) * np.sqrt(len(model_perf))
    years:float = len(model_perf) / 252.
    
    perf:float = (model_eq[-1] / model_eq[0] - 1)
    ann_perf = (1 if perf >= -1 else -1) * (pow(abs(1 + perf / 1), 1 / years) -1)
    sharpe_ratio:float = ann_perf / volatility
    return sharpe_ratio
