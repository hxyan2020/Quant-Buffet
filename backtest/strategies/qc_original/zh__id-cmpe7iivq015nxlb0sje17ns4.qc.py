# Original QuantConnect / library Python
# locale=zh slug="智能货币多重策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
from AlgorithmImports import *
class InteligentCurrencyMultistrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.period = 9 * 21
    self.three_months_period = 3 * 21
    
    self.trade_futures = 3                  # trading n futures for each portfolio part (long and short)
    self.future_weights = [0.5, 0.33, 0.17] # top long future has 0.5 weight in portfolio part and so on...
    
    self.data = {}
    
    # Currency future symbol, PPP yearly quandl symbol, quandl future contract 1., quandl future contract 2.
    # PPP source: https://www.quandl.com/data/ODA-IMF-Cross-Country-Macroeconomic-Statistics?keyword=%20United%20States%20Implied%20PPP%20Conversion%20Rate
    self.tickers_ppps = [
        ("CME_AD1", "ODA/AUS_PPPEX", "CHRIS/CME_AD1", "CHRIS/CME_AD2"), # Australian Dollar Futures
        ("CME_BP1", "ODA/GBR_PPPEX", "CHRIS/CME_BP1", "CHRIS/CME_BP2"), # British Pound Futures
        # ("CME_CD1", "ODA/CAD_PPPEX", "CHRIS/CME_CD1", "CHRIS/CME_CD2"), # Canadian Dollar Futures
        ("CME_EC1", "ODA/DEU_PPPEX", "CHRIS/CME_EC1", "CHRIS/CME_EC2"), # Euro FX Futures
        ("CME_JY1", "ODA/JPN_PPPEX", "CHRIS/CME_JY1", "CHRIS/CME_JY2"), # Japanese Yen Futures
        ("CME_NE1", "ODA/NZL_PPPEX", "CHRIS/CME_NE1", "CHRIS/CME_NE2"), # New Zealand Dollar Futures
        ("CME_SF1", "ODA/CHE_PPPEX", "CHRIS/CME_SF1", "CHRIS/CME_SF2")  # Swiss Franc Futures
    ]
    
    self.g4_currencies = ["CME_BP1", "CME_EC1", "CME_JY1"]
    
    for ticker, ppp_ticker, quandl1, quandl2 in self.tickers_ppps:
        # quantpedia data
        data = self.AddData(data_tools.QuantpediaFutures, ticker, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(5)
        
        future_symbol = data.Symbol
        
        # PPP quandl data.
        data = self.AddData(data_tools.QuandlValue, ppp_ticker, Resolution.Daily)
        ppp_symbol = data.Symbol
        
        # contract 1. quandl data
        data = self.AddData(data_tools.QuandlFutures, quandl1, Resolution.Daily)
        quandl1_symbol = data.Symbol
        
        # contract 2. quandl data
        data = self.AddData(data_tools.QuandlFutures, quandl2, Resolution.Daily)
        quandl2_symbol = data.Symbol
        
        self.data[future_symbol] = data_tools.SymbolData(
            self.period, ppp_symbol, quandl1_symbol, quandl2_symbol
        )
    
    self.CMRI_symbol = self.AddData(data_tools.QuantpediaCMRI, 'CMRI', Resolution.Daily).Symbol
    self.CMRI_value = None
    self.recent_month = -1
    
def OnData(self, data):
    # update MCRI risk value
    if self.CMRI_symbol in data and data[self.CMRI_symbol]:
        value = data[self.CMRI_symbol].Value
        self.CMRI_value = value
    
    # update daily prices and ppp values
    for symbol, symbol_data in self.data.items():
        ppp_symbol = symbol_data.ppp_symbol
        quandl1_symbol = symbol_data.quandl1_symbol
        quandl2_symbol = symbol_data.quandl2_symbol
        
        # update daily price, when it is ready
        if symbol in data and data[symbol]:
            price = data[symbol].Value
            symbol_data.update(price)
        
        # update ppp value, when it is ready
        if ppp_symbol in data and data[ppp_symbol]:
            ppp_value = data[ppp_symbol].Value
            symbol_data.update_ppp(ppp_value)
            
        # make sure both quandl contracts have prices
        if quandl1_symbol in data and data[quandl1_symbol] and quandl2_symbol in data and data[quandl2_symbol]:
            quandl1_price = data[quandl1_symbol].Value
            quandl2_price = data[quandl2_symbol].Value
            
            symbol_data.carry_signal(quandl1_price, quandl2_price)
    
    # rebalance monthly
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    
    self.Liquidate()
    
    value = {} # storing value signal keyed by symbol
    carry = {} # sotring carry signal keyed by symbol
    momentum = {} # storing momentum signal keyed by symbol
    
    for symbol, symbol_data in self.data.items():
        ticker = symbol.Value
        symbol_last_data = self.Securities[symbol].GetLastData()
        
        # make sure there are still new future data
        if symbol_last_data is not None and (self.Time.date() - symbol_last_data.Time.date()).days = (self.trade_futures * 2):
        value_long, value_short = self.SelectLongAndShort(value)
        
        self.Trade(value_long, basic_weight, True)
        self.Trade(value_short, basic_weight, False)
     
    # make sure there are enough futures for trade   
    if len(carry) >= (self.trade_futures * 2):
        carry_long, carry_short = self.SelectLongAndShort(carry)
        
        self.Trade(carry_long, basic_weight, True)
        self.Trade(carry_short, basic_weight, False)
        
    for symbol, weight in momentum.items():
        symbol_weight = weight / portfolio_parts_num
        symbol_weight = basic_weight * symbol_weight
        symbol_weight = np.floor(symbol_weight / self.data[symbol].last_price)
        symbol_weight = symbol_weight / 2 if self.CMRI_value > 0.5 else symbol_weight
        
        self.MarketOrder(symbol, symbol_weight)
        
    # make sure, that there is always new CMRI value for each rebalance
    self.CMRI_value = None
    
def FindOutPortfolioPartsNum(self, value, carry, momentum):
    portfolio_parts_num = 0
    
    if len(value) >= (self.trade_futures * 2):
        portfolio_parts_num += 1
        
    if len(carry) >= (self.trade_futures * 2):
        portfolio_parts_num += 1
        
    if len(momentum) > 0:
        portfolio_parts_num += 1
        
    return portfolio_parts_num
        
def SelectLongAndShort(self, signal_dict):
    sorted_by_signal = [x[0] for x in sorted(signal_dict.items(), key=lambda item: item[1])]
        
    long = sorted_by_signal[-self.trade_futures:]
    short = sorted_by_signal[:self.trade_futures]
    
    # reverse long portfolio to apply same function for trade
    long.reverse()
    
    return long, short
        
def Trade(self, futures_list, basic_weight, long_flag):
    for symbol, weight in zip(futures_list, self.future_weights):
        # calculate symbol weight, then place order
        symbol_weight = basic_weight * weight if long_flag else basic_weight * -weight
        symbol_weight = np.floor(symbol_weight / self.data[symbol].last_price)
        
        symbol_weight = symbol_weight / 2 if self.CMRI_value > 0.5 else symbol_weight 
        
        self.MarketOrder(symbol, symbol_weight)
