# Original QuantConnect / library Python
# locale=en slug="the-u-s-dollar-and-variance-risk-premia-imbalances"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *

class TheUSDollarandVarianceRiskPremiaImbalances(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.min_expiry:int = 20
    self.max_expiry:int = 35
    
    self.period:int = 22
    self.prices:Dict[Symbol, RollingWindow] = {}
    self.contracts:Dict[str, tuple] = {} # storing option contracts
    self.next_expiry:datetime.datetime.date = None

    self.us:str = 'SPY'  # SPDR S&P 500 ETF

    self.euroarea_gdp:Dict[str, str] = {
        'EWQ' : 'FRA_GDPD',  # iShares MSCI France Index ETF
        'EWG' : 'DEU_GDPD',  # iShares MSCI Germany Index ETF
        'EWI' : 'ITA_GDPD',  # iShares MSCI Italy Index ETF
        'EWN' : 'NLD_GDPD',  # iShares MSCI Netherlands Index ETF
    }

    # subscribe GDP data
    for ticker, gdp_symbol in self.euroarea_gdp.items():
        self.AddData(GDPData, gdp_symbol, Resolution.Daily)

    self.rest_of_the_world:List[str] = [
        'EWA',  # iShares MSCI Australia Index ETF
        'EWC',  # iShares MSCI Canada Index ETF
        'EWJ',  # iShares MSCI Japan Index ETF
        'EWL',  # iShares MSCI Switzerland Index ETF
        'EWU',  # iShares MSCI United Kingdom Index ETF
    ]

    self.tickers:List[str] = [self.us] + list(self.euroarea_gdp.keys()) + self.rest_of_the_world

    for ticker in self.tickers:
        # subscribe to country
        security:Equity = self.AddEquity(ticker, Resolution.Daily)
        
        # change normalization to raw to allow adding option contracts
        security.SetDataNormalizationMode(DataNormalizationMode.Raw)

        # set fee model and leverage
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(5)
        
        # create RollingWindow for daily prices
        self.prices[ticker] = RollingWindow[float](self.period)
    
def OnData(self, data: Slice) -> None:
    # update RollingWindow with daily prices
    for ticker in self.tickers:
        if ticker in data and data[ticker]:
            self.prices[ticker].Add(data[ticker].Value)

    # check date of expiry
    if self.next_expiry and self.Time.date() >= self.next_expiry.date():
        self.Liquidate()

        for ticker in self.tickers:
            if ticker in self.contracts:
                # remove expired contracts
                self.RemoveSecurity(self.contracts[ticker][0])
                self.RemoveSecurity(self.contracts[ticker][1])
                
                # remove contracts from dictionary
                del self.contracts[ticker]
    
    gdp_last_update_date:Dict[str, datetime.date] = GDPData.get_last_update_date()

    # set selection flag when there're no active contracts or every active contract expired
    if len(self.contracts) == 0:
        for ticker in self.tickers:
            if ticker not in self.contracts:
                if ticker in self.euroarea_gdp and not (self.Securities.ContainsKey(self.euroarea_gdp[ticker]) and self.Securities[self.euroarea_gdp[ticker]].Price != 0):
                    # ticker is in euroarea, yet does not have GDP data subscribed
                    continue

                # get all contracts for current country
                contracts:List[Symbol] = list(self.OptionChainProvider.GetOptionContractList(ticker, self.Time))
                # get current price for country etf
                underlying_price:float = self.Securities[ticker].Price
                
                # get strikes from country contracts
                strikes:List[float] = [i.ID.StrikePrice for i in contracts]
                if len(strikes) > 0:
                    # get at the money strike
                    atm_strike:float = min(strikes, key=lambda x: abs(x-underlying_price))
    
                    atm_calls:List[Symbol] = [i for i in contracts if i.ID.OptionRight == OptionRight.Call and 
                                                             i.ID.StrikePrice == atm_strike and 
                                                             self.min_expiry  1 and self.us in VP:
                # we construct a Euro VP as the GDP weighted average of the VPs available for the Eurozone countries
                euroarea_vp_tickers:List[str] = [x for x in VP if x in self.euroarea_gdp]
                rest_of_the_world_tickers:List[str] = [x for x in VP if x in self.rest_of_the_world]

                # latest known GDP data is used
                total_euroarea_gdp:float = sum([self.Securities[self.euroarea_gdp[x]].Price for x in euroarea_vp_tickers])
                euroarea_vp:float = sum([VP[x] * (self.Securities[self.euroarea_gdp[x]].Price / total_euroarea_gdp) for x in euroarea_vp_tickers])

                vp_mean:float = np.mean([vp for ticker, vp in VP.items() if ticker in rest_of_the_world_tickers] + [euroarea_vp])
                VPI:float = VP[self.us] - vp_mean
                
                # the timing strategy is long (short) in the Dollar factor, and short (long) the USD, whenever VPI is positive (negative)
                traded_tickers:List[str] = euroarea_vp_tickers + rest_of_the_world_tickers
                traded_len:int = len(traded_tickers)

                if VPI > 0:
                    for ticker in traded_tickers:
                        self.SetHoldings(ticker, 1 / traded_len)
                else:
                    for ticker in traded_tickers:
                        self.SetHoldings(ticker, -1 / traded_len)

# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))

# source: https://data.oecd.org/gdp/gross-domestic-product-gdp.htm
class GDPData(PythonData):
_last_update_date:Dict[str, datetime.date] = {}

@staticmethod
def get_last_update_date() -> Dict[str, datetime.date]:
   return GDPData._last_update_date

def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource(f'data.quantpedia.com/backtesting_data/economic/gdp/{config.Symbol.Value}.csv', SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)

def Reader(self, config, line, date, isLiveMode):
    data = GDPData()
    data.Symbol = config.Symbol
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    # Parse the CSV file's columns into the custom data class
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + relativedelta(months=2)
    data.Value = float(split[1])

    # store last update date
    if config.Symbol.Value not in GDPData._last_update_date:
        GDPData._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()

    if data.Time.date() > GDPData._last_update_date[config.Symbol.Value]:
        GDPData._last_update_date[config.Symbol.Value] = data.Time.date()
    
    return data
