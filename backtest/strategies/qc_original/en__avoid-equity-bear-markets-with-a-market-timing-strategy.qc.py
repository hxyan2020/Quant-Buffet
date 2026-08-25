# Original QuantConnect / library Python
# locale=en slug="avoid-equity-bear-markets-with-a-market-timing-strategy"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List
from pandas.core.frame import DataFrame
import data_tools
# endregion

class AvoidEquityBearMarketswithaMarketTimingStrategy(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2001, 1, 1)
    self.SetCash(100000)

    self.period:int = 365
    self.moving_average_period:int = 200
    self.leverage:int = 5

    # custom data subscription
    self.market_sec:Security = self.AddData(data_tools.MarketEQ, 'MKT', Resolution.Daily)
    self.t10y3m:Symbol = self.AddData(data_tools.TreasureBill, 'T10Y3M', Resolution.Daily).Symbol
    self.rrsfs:Symbol = self.AddData(data_tools.RRSFS, 'RRSFS_YOY', Resolution.Daily).Symbol
    self.indpro:Symbol = self.AddData(data_tools.IndustrialProduction, 'INDPRO_YOY', Resolution.Daily).Symbol
    self.house_started:Symbol = self.AddData(data_tools.HouseStarted, 'HOUST_YOY', Resolution.Daily).Symbol

    self.signal_market:Symbol = self.market_sec.Symbol
    self.traded_market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.bill:Symbol = self.AddEquity("SHY", Resolution.Daily).Symbol

    for symbol in [self.traded_market, self.bill]:
        self.Securities[symbol].SetLeverage(self.leverage)

    self.rebalance:bool = False

    self.Schedule.On(self.DateRules.MonthEnd(self.bill), self.TimeRules.BeforeMarketClose(self.bill), self.Selection)

def OnData(self, data: Slice) -> None:
    if not self.rebalance:
        return
    self.rebalance = False

    market_last_update_date:datetime.date = data_tools.MarketEQ._last_update_date
    t10y3m_last_update_date:datetime.date = data_tools.TreasureBill._last_update_date
    rrsfs_last_update_date:datetime.date = data_tools.RRSFS._last_update_date
    indpro_last_update_date:datetime.date = data_tools.IndustrialProduction._last_update_date
    house_started_last_update_date:datetime.date = data_tools.HouseStarted._last_update_date

    # call history on assets
    symbols:List[Symbol] = [self.t10y3m, self.rrsfs, self.indpro, self.house_started]
    history:DataFrame = self.History(symbols, self.period, Resolution.Daily)['value'].unstack(level=0)
    
    history_market:DataFrame = self.History([self.signal_market], self.period, Resolution.Daily)['value']
    
    if len(history.dropna().iloc[-3:]) != 3 or history.dropna().iloc[-3:].isnull().values.any() or not all(x in list(history.columns) for x in symbols): 
        return

    if len(history) >= self.moving_average_period:
        history.reset_index(inplace=True)
        history.set_index('time', inplace=True)
        market_returns:DataFrame = history_market.iloc[-self.moving_average_period:].pct_change()
        
        rr:float = self.rachev_ratio(market_returns.iloc[1:], 0.5)

        trend_signal:bool = False
        macro_signal:bool = False

        # trend signal evaluation
        if history_market.iloc[-1] > history_market.iloc[-self.moving_average_period:].mean() and rr >= 1. \
            and history[self.t10y3m].iloc[-1] > 0:
            trend_signal = True

        if (self.Securities[self.signal_market].GetLastData() and self.Time.date() >= market_last_update_date) or \
            (self.Securities[self.t10y3m].GetLastData() and self.Time.date() >= t10y3m_last_update_date) or \
            (self.Securities[self.rrsfs].GetLastData() and self.Time.date() >= rrsfs_last_update_date) or \
            (self.Securities[self.indpro].GetLastData() and self.Time.date() >= indpro_last_update_date) or \
            (self.Securities[self.house_started].GetLastData() and self.Time.date() >= house_started_last_update_date):
            
            self.Liquidate()
            return

        # macro signal evaluation
        if history[self.rrsfs].dropna().iloc[-2] > 0 and history[self.indpro].dropna().iloc[-2] > 0 and history[self.house_started].dropna().iloc[-2] > history[self.house_started].dropna().iloc[-3]:
            macro_signal = True

        if self.traded_market in data and data[self.traded_market] and self.bill in data and data[self.bill]:
            traded_asset:Symbol = self.traded_market

            if not self.Portfolio.Invested:
                if trend_signal:
                    traded_asset:Symbol = self.traded_market
                else:
                    traded_asset = self.bill

            elif self.Portfolio[self.bill].Invested and trend_signal:
                traded_asset = self.traded_market
            elif self.Portfolio[self.traded_market].Invested and not trend_signal and not macro_signal:
                traded_asset = self.bill
            
            if not self.Portfolio[traded_asset].Invested:
                self.Liquidate()
                self.SetHoldings(traded_asset, 1)

def Selection(self) -> None:
    self.rebalance = True

def rachev_ratio(self, df:DataFrame, alpha=0.5) -> float:
    # calculate VaR for left and right tails
    left_var:float = df.quantile(alpha)
    right_var:float = df.quantile(1 - alpha)
    
    # calculate Expected Shortfall for left and right tails
    left_es:float = df[df  right_var].mean()
    
    # calculate the Rachev Ratio
    rr:float = right_es / -left_es
    
    return rr
