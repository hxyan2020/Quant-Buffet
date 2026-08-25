# Original QuantConnect / library Python
# locale=en slug="hedging-portfolio"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from collections import deque
from AlgorithmImports import *
import numpy as np
import pandas as pd
class HedgingPortfolio(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(1000000)
    
    self.min_expiry = 240
    self.max_expiry = 260
    
    self.data = {}
    self.daily_period = 252
    self.sma_period = self.daily_period
    self.SetWarmUp(self.daily_period)
    
    market = self.AddEquity('SPY', Resolution.Daily)
    market.SetDataNormalizationMode(DataNormalizationMode.Raw)
    self.market = market.Symbol
    self.tf_positions = {}  # opened trend following positions (symbol->quantity)
    
    self.trend_following_symbols = [
        "CME_ES1",  # E-mini S&P 500 Futures, Continuous Contract #1
        "CME_SF1",  # Swiss Franc Futures, Continuous Contract #1
        "CME_JY1",  # Japanese Yen Futures, Continuous Contract #1
        "CME_GC1",  # Gold Futures, Continuous Contract
        "CME_US1",  # U.S. Treasury Bond Futures, Continuous Contract #1
        "CME_W1",   # Wheat Futures, Continuous Contract
        "CME_S1",   # Soybean Futures, Continuous Contract
        "ICE_SB1",  # Sugar No. 11 Futures, Continuous Contract
    ]
    
    self.factor_symbols = self.trend_following_symbols[:4]
    self.price_df = pd.DataFrame()
    
    for symbol in self.trend_following_symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetLeverage(10)
        data.SetFeeModel(CustomFeeModel())
    
    self.settings.daily_precise_end_time = False
    self.rebalance_flag = False
    
def OnData(self, data):
    # store daily closes for every symbol
    tracked_symbols = self.trend_following_symbols + [self.market]
    price_dict = {}
    if all(x in data and data[x] for x in tracked_symbols):
        for symbol in tracked_symbols:
            price_dict[symbol] = data[symbol].value
            
    # NOTE: datetime might not be needed, it is used for debugging purposes though
    price_dict['datetime'] = self.Time
    
    # price for every needed symbols is available, plus datetime
    if len(price_dict) == len(tracked_symbols) + 1:
        # As of pandas 2.0, append (previously deprecated) was removed.
        # self.price_df = self.price_df.append(price_dict, ignore_index=True)
        self.price_df = pd.concat([self.price_df, pd.DataFrame.from_records([price_dict])], ignore_index=True)
    
    # at least two years of price data is available
    if len(self.price_df) >= self.daily_period*2:
        market_daily_changes = self.price_df[self.market].pct_change().dropna()
        equity = (market_daily_changes + 1).cumprod() * 1
        equity = pd.concat([pd.Series([1]), equity])
        market_dd = equity / np.maximum.accumulate(equity) - 1
    
        # liquidate at the end of drawdown period
        if market_dd.iloc[-1] >= -0.15 and self.Portfolio.Invested:
            self.Liquidate()
            self.tf_positions.clear()
            
        # change trade direction for trend following positions if needed
        if len(self.tf_positions) != 0:
            for symbol, q in self.tf_positions.items():
                recent_price = self.price_df[f'{symbol}'].iloc[-1]
                recent_ma = self.price_df[f'{symbol}_ma'].iloc[-1]
                
                # long should be held
                if recent_price > recent_ma:
                    if q  0:   # long is opened
                        # reverse position
                        new_q = -2*abs(q)
                        self.MarketOrder(symbol, new_q)
                        self.tf_positions[symbol] = new_q
        # beggining of drawdown period
        if market_dd.iloc[-1]  QuantpediaFutures.get_last_update_date()[symbol]:
                    self.liquidate()
                    return
                self.price_df[f'{symbol}_perf'] = self.price_df[symbol].pct_change()
                self.price_df[f'{symbol}_ma'] = self.price_df[symbol].rolling(self.sma_period).mean()
                self.price_df[f'{symbol}_over_ma'] = np.where(self.price_df[symbol] > self.price_df[f'{symbol}_ma'], 1, -1)
                self.price_df[f'{symbol}_over_ma'] = self.price_df[f'{symbol}_over_ma'].shift(1)
            
            self.price_df['market_dd'] = market_dd
            self.price_df = self.price_df.dropna()
            
            dd_periods = self.price_df[self.price_df['market_dd']  2:
                
                # lists of tuples with symbol and vol
                factor_vol_arr = []
                tf_vol_arr = []
                
                # basic factor volatility
                for symbol in self.factor_symbols:
                    factor_perf_values = dd_periods[f'{symbol}_perf']
                    factor_vol = factor_perf_values.std() * np.sqrt(252)
                    factor_vol_arr.append((symbol, factor_vol))
                
                # trend following factor volatility
                for symbol in self.trend_following_symbols:
                    tf_perf_values = dd_periods[f'{symbol}_perf'] * dd_periods[f'{symbol}_over_ma']
                    tf_vol = tf_perf_values.std() * np.sqrt(252)
                    tf_vol_arr.append((symbol, tf_vol))
                
                # inverse volatility weighting
                total_vol = sum([1 / x[1] for x in factor_vol_arr + tf_vol_arr])
                factor_weight_arr = []
                tf_weight_arr = []
                
                # assign weight to simple factors
                for symbol, vol in factor_vol_arr:
                    factor_weight_arr.append((symbol, (1/vol) / total_vol))
                # assign weight to trend following strategies
                for symbol, vol in tf_vol_arr:
                    recent_price = self.price_df[f'{symbol}'].iloc[-1]
                    recent_ma = self.price_df[f'{symbol}_ma'].iloc[-1]
                    
                    # check ma versus price to pick long or short trade
                    if recent_price > recent_ma:
                        tf_weight_arr.append((symbol, (1/vol) / total_vol))
                    else:
                        tf_weight_arr.append((symbol, -(1/vol) / total_vol))
                
                # trade simple factors as well as trend following strategies
                for symbol, weight in factor_weight_arr + tf_weight_arr:
                    q = (self.Portfolio.TotalPortfolioValue * weight) / dd_periods[f'{symbol}'].iloc[-1]
                    self.MarketOrder(symbol, q)
                    
                    # store trend following postions for rebalance during the time trade is open
                    if symbol in tf_weight_arr:
                        self.tf_positions[symbol] = q
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
_last_update_date: Dict[str, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[str, datetime.date]:
   return QuantpediaFutures._last_update_date
def GetSource(self, config:SubscriptionDataConfig, date:datetime, isLiveMode:bool) -> SubscriptionDataSource:
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config:SubscriptionDataConfig, line:str, date:datetime, isLiveMode:bool) -> BaseData:
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['back_adjusted'] = float(split[1])
    data['spliced'] = float(split[2])
    data.Value = float(split[1])
    # store last update date
    if config.Symbol.Value not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol.Value]:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = data.Time.date()
    return data
