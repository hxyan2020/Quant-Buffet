# Original QuantConnect / library Python
# locale=en slug="条件性货币动量投资组合策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
import numpy as np
import pandas as pd
from AlgorithmImports import *
from pandas.core.frame import DataFrame
from typing import List, Dict
# endregion

class ConditionalCurrencyMomentumPortfolios(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.us_ir:Symbol = self.AddData(data_tools.InterestRate3M, 'IR3TIB01USM156N', Resolution.Daily).Symbol

    self.leverage:int = 5
    self.quantile:int = 4
    self.monthly_period:int = 36
    self.daily_period:int = 21

    self.data:Dict[Symbol, data_tools.SymbolData] = {}
    self.top_portfolio:List[Symbol] = []
    self.bottom_portfolio:List[Symbol] = []

    # Cash rate source: https://fred.stlouisfed.org/series/IR3TIB01USM156N
    self.symbols:Dict[str, str] = {
        "AUDUSD" : "IR3TIB01AUM156N",   # Australian Dollar Futures, Continuous Contract #1
        "GBPUSD" : "LIOR3MUKM",         # British Pound Futures, Continuous Contract #1
        "CADUSD" : "IR3TIB01CAM156N",   # Canadian Dollar Futures, Continuous Contract #1
        "EURUSD" : "IR3TIB01EZM156N",   # Euro FX Futures, Continuous Contract #1
        "JPYUSD" : "IR3TIB01JPM156N",   # Japanese Yen Futures, Continuous Contract #1
        "MXNUSD" : "IR3TIB01MXM156N",   # Mexican Peso Futures, Continuous Contract #1
        "NZDUSD" : "IR3TIB01NZM156N",   # New Zealand Dollar Futures, Continuous Contract #1
        "CHFUSD" : "IR3TIB01CHM156N"    # Swiss Franc Futures, Continuous Contract #1
    }
    
    # data subscription
    for symbol, rate_symbol in self.symbols.items():
        data:Security = self.AddForex(symbol, Resolution.Daily, Market.Oanda)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)

        ir_symbol:Symbol = self.AddData(data_tools.InterestRate3M, rate_symbol, Resolution.Daily).Symbol

        self.data[data.Symbol] = data_tools.SymbolData(self.daily_period, ir_symbol)

    self.return_dispersion:RollingWindow = RollingWindow[float](self.monthly_period)
    self.volatility:RollingWindow = RollingWindow[float](self.monthly_period)

    self.SetWarmup(self.monthly_period * self.daily_period, Resolution.Daily)
    
    self.recent_month:int = -1
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

def OnData(self, data: Slice) -> None:
    rebalance_flag:bool = False

    # store daily prices
    for symbol, symbol_data in self.data.items():
        if symbol in data and data[symbol]:
            symbol_data.update_price(data[symbol].Price)

            # monthly rebalance
            if self.recent_month != self.Time.month and not rebalance_flag:
                self.recent_month = self.Time.month
                rebalance_flag = True

    if not rebalance_flag:
        return

    ir_last_update_date:Dict[str, datetime.date] = data_tools.InterestRate3M.get_last_update_date()
    curr_us_ir_value:Union[float, None] = self.Securities[self.us_ir].Price if self.Securities[self.us_ir].GetLastData() and ir_last_update_date[self.us_ir.Value] > self.Time.date() else None
    
    if curr_us_ir_value is None:
        self.Liquidate()
        return

    fd_by_symbol:Dict[Symbol, float] = {}

    # save daily prices lists
    for symbol, symbol_data in self.data.items():
        if self.Securities[symbol_data._ir_symbol].GetLastData():
            if ir_last_update_date[symbol_data._ir_symbol.Value]  0 else 0
    ord_signal = 1 if self.return_dispersion[0] > np.percentile(np.array(list(self.return_dispersion)[1:]), 90) else 0
    vol_signal = 1 if self.volatility[0] > np.percentile(np.array(list(self.volatility)[1:]), 90) else 0

    signals:List[int] = [afd_signal, ord_signal, vol_signal]
    traded_direction:int = 1 if all(x==1 for x in signals) else -1

    # sort and divide to quantiles
    sorted_by_momentum:List[Symbol] = sorted([(symbol, self.data[symbol].get_monthly_return()) for symbol, value in fd_by_symbol.items()], key=lambda x: x[1])
    quantile:int = len(sorted_by_momentum) // self.quantile
    top_portfolio:List[Symbol] = [i[0] for i in sorted_by_momentum][-quantile:]
    bottom_portfolio:List[Symbol] = [i[0] for i in sorted_by_momentum][:quantile]

    # trade execution
    invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in top_portfolio + bottom_portfolio:
            self.Liquidate(symbol)

    for i, portfolio in enumerate([top_portfolio, bottom_portfolio]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, ((-1) ** i) * traded_direction / len(top_portfolio))
