# Original QuantConnect / library Python
# locale=zh slug="商品期权隐含波动率策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
# https://quantpedia.com/strategies/commodity-option-implied-volatility-strategy/
#
# The investment universe consists of 25 commodities.
# Commodities are sorted into four groups based on the 30-days implied volatility de-trended by the previous 12 months mean of implied volatility (see page 8 for exact formula).
# The “Low” (“High”) group contains the top 25% of all commodities with the lowest (highest) volatilities.
# The portfolio is long-short and buys commodities from the group “Low” and sells commodities from the group “High”.
# The portfolio is equally-weighted and is rebalanced on a monthly basis.
#
# QC Implementation:
import numpy as np
class CommodityOptionImpliedVolatilityStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.min_expiry = 25
    self.max_expiry = 35
    
    self.period = 12 # need n of implied volatilities
    
    self.iv = {} # storing implied volatilies in RollingWindow
    self.contracts = {} # storing option contracts
    self.tickers_symbols = {} # storing commodities symbols under their tickers
    
    self.tickers = ['GLD', 'USO', 'UNG', 'SLV', 'DBA', 'DBB', 'PPLT', 'PALL']
    self.next_expiry = None
    for ticker in self.tickers:
        # subscribe to commodity
        security = self.AddEquity(ticker, Resolution.Minute)
        
        # change normalization to raw to allow adding contracts
        security.SetDataNormalizationMode(DataNormalizationMode.Raw)
        # set fee model and leverage
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(5)
        
        # get commodity symbol
        symbol = security.Symbol
        # store symbol under ticker
        self.tickers_symbols[ticker] = symbol
        # create RollingWindow for implied volatilities
        self.iv[symbol] = RollingWindow[float](self.period)
    
    self.day = -1
    
def OnData(self, data):
    # rebalance daily
    if self.day == self.Time.day:
        return
    self.day = self.Time.day
    
    if self.next_expiry and self.Time.date() >= self.next_expiry.date():
        self.Liquidate()
    
        for symbol in self.tickers_symbols:
            if symbol in self.contracts:
                # remove expired contracts
                for contract in self.contracts[symbol]:
                    self.RemoveSecurity(contract)
                # remove contracts from dictionary
                del self.contracts[symbol]
                
    if not self.Portfolio.Invested:
        for symbol in self.tickers_symbols:
            if symbol not in self.contracts:
                # get all contracts for current commodity
                contracts = self.OptionChainProvider.GetOptionContractList(symbol, self.Time)
                # get current price for commodity
                underlying_price = self.Securities[symbol].Price
                
                # get strikes from commodity contracts
                strikes = [i.ID.StrikePrice for i in contracts]
                if len(strikes) > 0:
                    # get at the money strike
                    atm_strike:float = min(strikes, key=lambda x: abs(x-underlying_price))
    
                    atm_calls:list = [i for i in contracts if i.ID.OptionRight == OptionRight.Call and 
                                                             i.ID.StrikePrice == atm_strike and 
                                                             self.min_expiry
