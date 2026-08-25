# Original QuantConnect / library Python
# locale=en slug="international-volatility-arbitrage"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import calendar
import datetime
#endregion
class InternationalVolatilityArbitrage(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(1000000)
    
    self.min_expiry = 20
    self.max_expiry = 90
    
    self.percentage_traded = 0.2    # traded percentage of the portfolio
    
    self.period = 12 * 21           # need 12 months of daily prices
    
    self.prices = {}                # storing daily prices
    self.contracts = {}             # storing option contracts
    self.tickers_symbols = {}       # storing symbols under their tickers
    
    self.tickers = [
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
    for ticker in self.tickers:
        # subscribe to etf
        security = self.AddEquity(ticker, Resolution.Minute)
        
        # change normalization to raw to allow adding etf contracts
        security.SetDataNormalizationMode(DataNormalizationMode.Raw)
        # set fee model and leverage
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(5)
        
        # get etf symbol
        symbol = security.Symbol
        # store etf symbol under etf ticker
        self.tickers_symbols[ticker] = symbol
        # create RollingWindow for daily prices
        self.prices[symbol] = RollingWindow[float](self.period)
    
    self.fourth_friday = self.FindFourthFriday(self.Time.year, self.Time.month)
    
    self.day = -1
    self.selection_flag = False
    
def OnData(self, data):
    # execute once a day
    if self.day == self.Time.day:
        return
    self.day = self.Time.day
    
    # update RollingWindow with daily prices
    for _, symbol in self.tickers_symbols.items():
        # update RollingWindow with daily prices
        if symbol in data and data[symbol]:
            self.prices[symbol].Add(data[symbol].Value)
            
    if data.OptionChains.Count >= 3 and self.selection_flag:
        # stop rebalance
        self.selection_flag = False
        self.Liquidate()
        
        vol_metric = {} # storing volatility differences for each etf
        
        for kvp in data.OptionChains:
            chain = kvp.Value
            # get etf symbol
            symbol = self.tickers_symbols[chain.Underlying.Symbol.Value]
            # get contracts
            contracts = [x for x in chain]
            
            # check if there are enough contracts for option and daily prices are ready
            if len(contracts)  3:
            # perform selection
            tercile = int(len(vol_metric) / 3)
            sorted_by_vol_metric = [x[0] for x in sorted(vol_metric.items(), key=lambda item: item[1])]
            
            # short expensive (high) tercile
            short = sorted_by_vol_metric[-tercile:]
            # long cheap (low) tercile
            long = sorted_by_vol_metric[:tercile]
            
            # trade execution
            self.Liquidate()
            
            # trade long
            self.TradeOptions(long, True)
            # trade short
            self.TradeOptions(short, False)
            
    # rebalance on fourth friday
    if self.fourth_friday  3 else fridays[-1]
    return fourth_friday
    
def FilterContracts(self, strikes, contracts, underlying_price):
    ''' filter call and put contracts from contracts parameter '''
    ''' return call and put contracts '''
    
    # Straddle
    call_strike:float = min(strikes, key=lambda x: abs(x-underlying_price))
    put_strike = call_strike
    
    calls = [] # storing call contracts
    puts = [] # storing put contracts
    
    for contract in contracts:
        # check if contract has one month expiry
        if self.min_expiry
