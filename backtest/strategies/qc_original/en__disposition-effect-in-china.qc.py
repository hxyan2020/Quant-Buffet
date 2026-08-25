# Original QuantConnect / library Python
# locale=en slug="disposition-effect-in-china"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import SymbolData, CustomFeeModel, ChineseStocks, MultipleLinearRegression
import numpy as np
# endregion

class DispositionEffectinChina(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    # chinese stock universe
    self.top_size_symbol_count:int = 300
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/chinese_stocks/large_cap_500.csv')
    self.tickers:List[str] = ticker_file_str.split('\r\n')[:self.top_size_symbol_count]

    self.period = 365                       # daily period
    self.data:dict[str, SymbolData] = {}    # symbol data
    self.max_missing_days:int = 5           # max missing n of price data entries in a row for custom data
    self.value_weighted:bool = True         # True - value weighted; False - equally weighted
    self.min_symbols:int = 2
    self.leverage:int = 5
    self.rebalance_month:int = 5            # May rebalance

    self.SetWarmUp(self.period, Resolution.Daily)

    for t in self.tickers:
        data = self.AddData(ChineseStocks, t, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)

        self.data[data.Symbol] = SymbolData(self.period)
    
    self.recent_month:int = -1

def OnData(self, data: Slice):
    total_trading_volume:float = 0
    included_symbols:List[Symbol] = []
    disposition:dict[Symbol, bool] = {}

    # store daily data
    for symbol, symbol_data in self.data.items():
        if data.ContainsKey(symbol):
            price_data:dict[str, str] = data[symbol].GetProperty('price_data')
            # valid price data
            if data[symbol].Value != 0. and price_data:
                # update price and market cap
                close:float = float(data[symbol].Value)
                volume:float = float(price_data['turnoverVol'])
                
                included_symbols.append(symbol)
                total_trading_volume += volume
                
                symbol_data.update_price(close)
                symbol_data.update_volume(volume)

                mc:float = float(price_data['marketValue'])
                symbol_data.update_market_cap(mc)

                # update second regression variable
                if symbol_data.is_ready():
                    symbol_data.update_disposition_regression_x()

                    if self.recent_month != self.Time.month and self.Time.month == self.rebalance_month and not self.IsWarmingUp:
                        if symbol_data.cumulative_raw_volume_is_ready():
                            # first regression - abnormal trading volume
                            regr_data:np.ndarray = symbol_data.get_abnormal_trading_volume_regression_data()
                            ATV_regression_model = MultipleLinearRegression(regr_data[0], regr_data[1])
                            abnormal_trading_volume:np.ndarray = ATV_regression_model.resid

                            # second regression - disposition
                            regr_data:np.ndarray = symbol_data.get_disposition_regression_data()
                            disposition_regression_model = MultipleLinearRegression(regr_data, abnormal_trading_volume.T)

                            # negative beta_1 or positive beta_2 indicates a disposition effect
                            if disposition_regression_model.params[1]  0:
                                disposition[symbol] = True
                            else:
                                disposition[symbol] = False

    # update total market volume for included stocks in todays data structure
    for symbol in included_symbols:
        self.data[symbol].update_total_market_volume(total_trading_volume)

    # rebalance yearly
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    if self.Time.month != self.rebalance_month:
        return

    if self.IsWarmingUp:
        return

    long:List[str] = []
    short:List[str] = []

    if len(disposition) >= self.min_symbols:
        # according to the paper, long the no disposition small and big size portfolios and short the disposition small and big size portfolios
        long = [symbol for symbol, disp in disposition.items() if disp == False]
        short = [symbol for symbol, disp in disposition.items() if disp == True]
    
    # weight calculation
    weights_to_trade = {}

    if self.value_weighted:
        total_market_cap_long:float = sum([self.data[x].recent_market_cap() for x in long])
        total_market_cap_short:float = sum([self.data[x].recent_market_cap() for x in short])

        for symbol in long:
            if symbol in data and data[symbol]:
                weights_to_trade[symbol] = self.data[symbol].recent_market_cap() / total_market_cap_long
        for symbol in short:
            if symbol in data and data[symbol]:
                weights_to_trade[symbol] = -self.data[symbol].recent_market_cap() / total_market_cap_short
    else:
        long_c:int = len(long)
        short_c:int = len(short)

        for symbol in long:
            if symbol in data and data[symbol]:
                weights_to_trade[symbol] = 1 / long_c
        for symbol in short:
            if symbol in data and data[symbol]:
                weights_to_trade[symbol] = -1 / short_c
    
    # trade execution
    invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in weights_to_trade:
            self.Liquidate(symbol)
    
    for symbol, w in weights_to_trade.items():
        self.SetHoldings(symbol, w)
