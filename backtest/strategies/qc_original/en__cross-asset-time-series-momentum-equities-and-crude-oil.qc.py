# Original QuantConnect / library Python
# locale=en slug="cross-asset-time-series-momentum-equities-and-crude-oil"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class CrossAssetTimeSeriesMomentumEquitiesAndCrudeOil(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)
    
    leverage: int = 5
    self.min_expiry: int = 25
    self.max_expiry: int = 35
    
    self.tickers: List[str] = ['ASX_YAP1', 'LIFFE_FCE1', 'EUREX_FSMI1', 'EUREX_FSTX1', 'LIFFE_Z1', 'SGX_NK1']
    
    self.prices: Dict[Symbol, SymbolData] = {} # storing objects of Prices class under symbols
    self.contracts: Dict[Symbol, Contracts] = {} # storing objects of Contracts class under symbols
    self.tickers_symbols: Dict[str, Symbol] = {} # storing symbols under tickers
    
    # subscribe to USO etf
    security: Security = self.AddEquity('USO', Resolution.Minute)
    # change normalization to raw to allow adding etf contracts
    security.SetDataNormalizationMode(DataNormalizationMode.Raw)
    # set fee model and leverage
    security.SetFeeModel(CustomFeeModel())
    security.SetLeverage(leverage)
    
    # get security symbol
    self.uso_symbol: Symbol = security.Symbol
    # create object from Prices class for symbol
    self.prices[self.uso_symbol] = SymbolData()
    
    # subscribe to US treasury bills
    security: Security = self.AddEquity("SHY", Resolution.Minute)
    security.SetFeeModel(CustomFeeModel())
    security.SetLeverage(leverage)
    # store US treasury bills symbol
    self.us_treasury_bills_symbol: Symbol = security.Symbol
    
    for ticker in self.tickers:
        # subscribe to Quantpedia equity future
        security: security = self.AddData(QuantpediaFutures, ticker, Resolution.Daily)
        
        # set fee model and leverage
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(leverage)
        
        symbol: Symbol = security.Symbol
        # create object from Prices class for symbol
        self.prices[symbol] = SymbolData()
        # store security symbol under ticker
        self.tickers_symbols[ticker] = symbol
        
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
def OnData(self, data: Slice) -> None:
    # store market daily prices
    for _, symbol in self.tickers_symbols.items():
        # Check if custom data is still coming
        if self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol]:
            self.liquidate(symbol)
            self.prices[symbol].clear_old_prices()
            continue
        # store daily prices only if USO contracts were selected
        if self.uso_symbol in self.contracts and symbol in data and data[symbol]:
            # retrieve market price from data object
            market_price = data[symbol].Value
            self.prices[symbol].update_market_prices(market_price)
            
    # execute once a day
    if not (self.Time.hour == 16 and self.Time.minute == 00):
        return
    
    if self.uso_symbol in self.contracts:
        # check expiration of USO option contracts
        if self.contracts[self.uso_symbol].expiry_date  0:
            # filter calls and puts contracts with one month expiry
            calls, puts = self.FilterContracts(strikes, contracts, underlying_price)
            
            # make sure, there is at least one call and put contract
            if len(calls) and len(puts):
                # sort by expiry
                call: Contract = sorted(calls, key = lambda x: x.ID.Date)[0]
                put: Contract = sorted(puts, key = lambda x: x.ID.Date)[0]
                
                # add call contract
                self.AddContract(call)
                # add put contract
                self.AddContract(put)
                
                # retrieve expiry date for contracts
                expiry_date: datetime.date = call.ID.Date.date()
                # store contracts with expiry date under uso etf symbol
                self.contracts[self.uso_symbol] = Contracts(expiry_date, [call, put])
    
    # rebalance after expiration of every active option contract
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # not enough daily prices for USO monthly straddle return
    if len(self.prices[self.uso_symbol].call_prices) == 0:
        return
    
    long: List[Symbol] = []
    short: List[Symbol] = []
    
    # calculate USO monthly straddle return for next comparisons
    uso_monthly_straddle_ret: float = self.prices[self.uso_symbol].monthly_straddle_return()
    # clear old USO prices
    self.prices[self.uso_symbol].clear_old_prices()
    
    # select etfs for trading
    for _, symbol in self.tickers_symbols.items():
        # make sure there are enough data for market return
        if len(self.prices[symbol].market_prices) != 0:
            # get local market return
            market_return: float = self.prices[symbol].market_return()
            
            if market_return > 0 and uso_monthly_straddle_ret  0:
                short.append(symbol)
        
        # clear prices for last month
        self.prices[symbol].clear_old_prices()
        
    # trade execution
    targets: List[PortfolioTarget] = []
    
    if len(long) == 0 and len(short) == 0:
        # trade US treasury bills etf, because any country etf wasn't selected
        targets.append(PortfolioTarget(self.us_treasury_bills_symbol, 1))
    else:
        # equally weighted trade of long and short part of country etfs
        for i, portfolio in enumerate([long, short]):
            for symbol in portfolio:
                # if symbol in data and data[symbol]:
                    targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
        
    self.SetHoldings(targets, True)
    
def FilterContracts(self, strikes: List[float], contracts: List, underlying_price: float):
    ''' filter call and put contracts from contracts parameter '''
    ''' return call and put contracts '''
    
    # get min of strike based on etf underlying price
    
    # Strangle
    # call_strike:float = min([x for x in strikes if x > underlying_price], key=lambda x: abs(x-underlying_price))
    # put_strike:float = min([x for x in strikes if x  None:
    ''' subscribe option contract, set price mondel and normalization mode '''
    option = self.AddOptionContract(contract, Resolution.Minute)
    option.PriceModel = OptionPriceModels.BlackScholes()
    option.SetDataNormalizationMode(DataNormalizationMode.Raw)

class SymbolData():
def __init__(self) -> None:
    self.market_prices: List[float] = []
    self.call_prices: List[float] = []
    self.put_prices: List[float] = []
    
def update_straddle_prices(self, call_price: float, put_price: float) -> None:
    self.call_prices.append(call_price)
    self.put_prices.append(put_price)
def update_market_prices(self, market_price: float) -> None:
    self.market_prices.append(market_price)
    
def clear_old_prices(self) -> None:
    self.market_prices.clear()
    self.call_prices.clear()
    self.put_prices.clear()
    
def monthly_straddle_return(self) -> float:
    call_prices = np.array(self.call_prices)
    put_prices = np.array(self.put_prices)
    
    # get monthly return based on daily returns of each contract
    monthly_call_return: float = sum((call_prices[1:] - call_prices[:-1]) / call_prices[:-1])
    monthly_put_return: float = sum((put_prices[1:] - put_prices[:-1]) / put_prices[:-1])
    
    # return monthly stradle return
    return monthly_call_return + monthly_put_return
    
def market_return(self) -> float:
    return (self.market_prices[-1] - self.market_prices[0]) / self.market_prices[0]
class Contracts():
def __init__(self, expiry_date: datetime.date, contracts: List) -> None:
    self.expiry_date = expiry_date
    self.contracts = contracts
    
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
_last_update_date: Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return QuantpediaFutures._last_update_date
def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
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

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
