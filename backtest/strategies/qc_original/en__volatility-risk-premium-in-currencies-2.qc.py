# Original QuantConnect / library Python
# locale=en slug="volatility-risk-premium-in-currencies-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class VolatilityRiskPremiumInCurrencies2(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.min_expiry = 25
    self.max_expiry = 35
    
    self.period = 12 * 21 # need 12 months of daily prices
    
    self.prices = {}                # storing daily prices
    self.contracts = {}             # storing option contracts
    self.symbols_by_ticker = {}     # storing symbols under their tickers
    self.tickers_currencies = {}    # storing currencies symbols keyed by etf tickers
    self.vol_difference = {}        # storing volatility differences for each etf
    
    self.etf_currencies = {
        'FXA': "CME_AD1", # Australia
        'FXC': "CME_CD1", # Canada
        'FXE': "CME_EC1", # Euro
        'FXY': "CME_JY1", # Japan
        'BNZ': "CME_NE1", # New Zealand
        'FXF': "CME_SF1", # Switzerland
        'FXB': "CME_BP1", # Great Britain
    }
    for etf_ticker, currency_ticker in self.etf_currencies.items():
        # subscribe to etf
        security = self.AddEquity(etf_ticker, Resolution.Minute)
        
        # change normalization to raw to allow adding etf contracts
        security.SetDataNormalizationMode(DataNormalizationMode.Raw)
        
        # get etf symbol
        etf_symbol = security.Symbol
        
        # Subscribe to future
        security = self.AddData(QuantpediaFutures, currency_ticker, Resolution.Daily)
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(5)
        
        currency_symbol = security.Symbol
        
        # store etf symbol under etf ticker
        self.symbols_by_ticker[etf_ticker] = etf_symbol
        # create RollingWindow for daily prices
        self.prices[etf_symbol] = RollingWindow[float](self.period)
        # create pair etf ticker and currency symbol
        self.tickers_currencies[etf_ticker] = currency_symbol
        # create object from Contracts class for etf symbol
        self.contracts[etf_symbol] = Contracts(self.Time.date(), 0, [])
    
    self.day = -1
    self.selection_flag = False
    
def OnData(self, data):
    # not every IV comes at 9:30...
    if self.selection_flag and self.Time.hour == 9:
        for kvp in data.OptionChains:
            chain = kvp.Value
            ticker = chain.Underlying.Symbol.Value
            # get etf symbol
            symbol = self.symbols_by_ticker[ticker]
            # currency symbol 
            currency_symbol = self.tickers_currencies[ticker]
            # check if data is still coming
            if self.securities[currency_symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[currency_symbol]:
                self.liquidate()
                return
            # get contracts
            contracts = [x for x in chain]
            
            # check if there are enough contracts for option, daily prices are ready and volatility difference wasn't calculated
            if len(contracts)  Dict[Symbol, datetime.date]:
   return QuantpediaFutures._last_update_date
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['back_adjusted'] = float(split[1])
    data['spliced'] = float(split[2])
    data.Value = float(split[1])
    if config.Symbol not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol]:
        QuantpediaFutures._last_update_date[config.Symbol] = data.Time.date()
    return data

# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
