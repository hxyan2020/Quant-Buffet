# Original QuantConnect / library Python
# locale=zh slug="商品中的隐含偏度策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class ImpliedSkewnessStrategyInCommodities(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    self.symbols = []           # storing commodities symbols
    self.managed_queue = []     # storing parts of portfolio with their current holding period
    self.contracts_expiry = {}  # storing contracts expiry date under symbols
    self.tickers_symbols = {}   # storing commodities symbols under their tickers
    
    self.futures = ['GLD', 'USO', 'UNG', 'SLV', 'CORN', 'WEAT', 'SOYB', 'CPER']
    self.quantile = 4
    for ticker in self.futures:
        # subscribe to commodity future
        security = self.AddEquity(ticker, Resolution.Minute)
        
        # change normalization to raw to allow adding futures contracts
        security.SetDataNormalizationMode(DataNormalizationMode.Raw)
        # set fee model and leverage
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(5)
        
        # get commodity symbol
        symbol = security.Symbol
        # store future symbol under future ticker
        self.tickers_symbols[ticker] = symbol
        # add commodity symbol to symbols, which can be traded in this strategy
        self.symbols.append(symbol)
        
    self.min_expiry = 25
    self.max_expiry = 35
    
    self.holding_period = 21 # holding each part of portfolio n days
    self.current_day = -1
def OnData(self, data):
    # rebalance daily
    if self.current_day == self.Time.day:
        return
    self.current_day = self.Time.day
    
    for symbol in self.symbols:
        # subscribe to new contracts, because current ones has expiried
        if symbol not in self.contracts_expiry or self.contracts_expiry[symbol]  0 and len(itm_calls) > 0 and len(otm_puts) > 0 and len(otm_calls) > 0:
        # sort by expiry
        itm_put, itm_call, otm_put, otm_call = self.SortByExpiry(itm_puts, itm_calls, otm_puts, otm_calls)
        
        # add contracts
        for contract in [itm_put, itm_call, otm_put, otm_call]:
            self.AddContract(contract)
        
        # store expiry date
        self.contracts_expiry[symbol] = itm_put.ID.Date.date()

def FilterContracts(self, contracts, option_right, strike):
    ''' filter contracts based on option_right and strike parameter from contracts parameter'''   
    
    # filter contracts based on option right and strike parameters
    filtered_contracts:list = [i for i in contracts if i.ID.OptionRight == option_right and 
                                             i.ID.StrikePrice == strike and 
                                             self.min_expiry = underlying_price:
            # found otm call
            otm_call_iv = c.ImpliedVolatility
        elif c.Right == OptionRight.Put and c.Strike
