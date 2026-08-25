# Original QuantConnect / library Python
# locale=en slug="国家etf配对交易"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgoLib import *
import itertools as it

class PairsTradingwithCountryETFs(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
   
    self.symbols = [
                    "EWA",  # iShares MSCI Australia Index ETF
                    "EWO",  # iShares MSCI Austria Investable Mkt Index ETF
                    "EWK",  # iShares MSCI Belgium Investable Market Index ETF
                    "EWZ",  # iShares MSCI Brazil Index ETF
                    "EWC",  # iShares MSCI Canada Index ETF
                    "FXI",  # iShares China Large-Cap ETF
                    "EWQ",  # iShares MSCI France Index ETF
                    "EWG",  # iShares MSCI Germany ETF 
                    "EWH",  # iShares MSCI Hong Kong Index ETF
                    "EWI",  # iShares MSCI Italy Index ETF
                    "EWJ",  # iShares MSCI Japan Index ETF
                    "EWM",  # iShares MSCI Malaysia Index ETF
                    "EWW",  # iShares MSCI Mexico Inv. Mt. Idx
                    "EWN",  # iShares MSCI Netherlands Index ETF
                    "EWS",  # iShares MSCI Singapore Index ETF
                    "EZA",  # iShares MSCI South Africe Index ETF
                    "EWY",  # iShares MSCI South Korea ETF
                    "EWP",  # iShares MSCI Spain Index ETF
                    "EWD",  # iShares MSCI Sweden Index ETF
                    "EWL",  # iShares MSCI Switzerland Index ETF
                    "EWT",  # iShares MSCI Taiwan Index ETF
                    "THD",  # iShares MSCI Thailand Index ETF
                    "EWU",  # iShares MSCI United Kingdom Index ETF
                    "SPY",  # SPDR S&P 500 ETF
                    ]
    
    self.period = 120
    self.max_traded_pairs = 5 # The top 5 pairs with the smallest distance are used.
    
    self.history_price = {}
    self.traded_pairs = []
    self.traded_quantity = {}

    for symbol in self.symbols:
        data = self.AddEquity(symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(5)
        symbol_obj = data.Symbol
        
        if symbol not in self.history_price:
            self.history_price[symbol] = RollingWindow[float](self.period)
            
            history = self.History(self.Symbol(symbol), self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Note enough data for {symbol} yet")
            else:
                closes = history.loc[symbol].close[:-1]
                for time, close in closes.items():
                    self.history_price[symbol].Add(close)

    self.sorted_pairs = []
    self.symbol_pairs = list(it.combinations(self.symbols, 2))  
    self.days = 20

def OnData(self, data):
    # Update the price series everyday
    for symbol in self.history_price:
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data and data[symbol_obj]:
            price = data[symbol_obj].Value
            self.history_price[symbol].Add(price)
                    
    # Start of trading period.
    if self.days == 20:
        # minimize the sum of squared deviations
        distances = {}
        for pair in self.symbol_pairs:
            if self.history_price[pair[0]].IsReady and self.history_price[pair[1]].IsReady:
                if (self.Time.date() - self.Securities[pair[0]].GetLastData().Time.date()).days  mean + 0.5*std or actual_spread  b etf's price
                    if a_price_norm > b_price_norm:
                        long_q = traded_portfolio_value / b_price    # long b etf
                        short_q = -traded_portfolio_value / a_price  # short a etf
                        if self.Securities.ContainsKey(symbol_a) and self.Securities.ContainsKey(symbol_b) and \
                            self.Securities[symbol_a].Price != 0 and self.Securities[symbol_a].IsTradable and \
                            self.Securities[symbol_b].Price != 0 and self.Securities[symbol_b].IsTradable:
                            self.MarketOrder(symbol_a, short_q)
                            self.MarketOrder(symbol_b, long_q)
                            
                            self.traded_quantity[pair] = (short_q, long_q)
                            self.traded_pairs.append(pair)
                    # b etf's price > a etf's price
                    else:
                        long_q = traded_portfolio_value / a_price    # long a etf
                        short_q = -traded_portfolio_value / b_price  # short b etf
                        if self.Securities.ContainsKey(symbol_a) and self.Securities.ContainsKey(symbol_b) and \
                            self.Securities[symbol_a].Price != 0 and self.Securities[symbol_a].IsTradable and \
                            self.Securities[symbol_b].Price != 0 and self.Securities[symbol_b].IsTradable:
                            self.MarketOrder(symbol_a, long_q)
                            self.MarketOrder(symbol_b, short_q)
                            
                            self.traded_quantity[pair] = (long_q, short_q)
                            self.traded_pairs.append(pair)
        # The position is closed when prices revert back.
        else:
            if pair in self.traded_pairs and pair in self.traded_quantity:
                # make opposite order to opened position
                self.MarketOrder(pair[0], -self.traded_quantity[pair][0])
                self.MarketOrder(pair[1], -self.traded_quantity[pair][1])
                pairs_to_remove.append(pair)
        
    for pair in pairs_to_remove:
        self.traded_pairs.remove(pair)
        del self.traded_quantity[pair]

def Distance(self, price_a, price_b):
    # Calculate the sum of squared deviations between two normalized price series.
    norm_a = np.array(price_a) / price_a[-1]
    norm_b = np.array(price_b) / price_b[-1]
    return sum((norm_a - norm_b)**2)

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
