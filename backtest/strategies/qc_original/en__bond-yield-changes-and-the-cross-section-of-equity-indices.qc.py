# Original QuantConnect / library Python
# locale=en slug="bond-yield-changes-and-the-cross-section-of-equity-indices"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class BondYieldChangesAndTheCrossSectionOfEquityIndices(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.futures = [
        ('ASX_YT1', 'AU10YT'),
        ('LIFFE_FCE1', 'CA10YT'),
        ('EUREX_FSMI1', 'CH10YT'),
        ('EUREX_FSTX1', 'DE10YT'),
        ('LIFFE_Z1', 'GB10YT'),
        ('SGX_NK1', 'JP10YT'),
    ]
    
    self.etfs = [
        ('EWA', 'AU10YT'),  # iShares MSCI Australia Index ETF
        ('EWO', 'AS10YT'), # iShares MSCI Austria Investable Mkt Index ETF
        ('EWK', 'BE10YT'), # iShares MSCI Belgium Investable Market Index ETF
        ('EWZ', 'BR10YT'), # iShares MSCI Brazil Index ETF
        ('EWC', 'CA10YT'), # iShares MSCI Canada Index ETF
        ('FXI', 'CN10YT'), # iShares China Large-Cap ETF
        ('EWQ', 'FR10YT'), # iShares MSCI France Index ETF
        ('EWG', 'DE10YT'), # iShares MSCI Germany ETF 
        ('EWH', 'HK10YT'), # iShares MSCI Hong Kong Index ETF
        ('EWI', 'IT10YT'), # iShares MSCI Italy Index ETF
        ('EWJ', 'JP10YT'), # iShares MSCI Japan Index ETF
        ('EWM', 'MY10YT'), # iShares MSCI Malaysia Index ETF
        ('EWW', 'MX10YT'), # iShares MSCI Mexico Inv. Mt. Idx
        ('EWN', 'NL10YT'), # iShares MSCI Netherlands Index ETF
        ('EWS', 'SG10YT'), # iShares MSCI Singapore Index ETF
        ('EZA', 'ZA10YT'), # iShares MSCI South Africe Index ETF
        ('EWY', 'KR10YT'), # iShares MSCI South Korea ETF
        ('EWP', 'ES10YT'), # iShares MSCI Spain Index ETF
        # ('EWD', 'SE10YT'), # iShares MSCI Sweden Index ETF # No data on investpy
        ('EWL', 'CH10YT'), # iShares MSCI Switzerland Index ETF
        ('EWT', 'TW10YT'), # iShares MSCI Taiwan Index ETF
        ('THD', 'TH10YT'), # iShares MSCI Thailand Index ETF
        ('EWU', 'GB10YT'), # iShares MSCI United Kingdom Index ETF
        ('SPY', 'US10YT') # SPDR S&P 500 ETF
    ]
    
    self.data = {}
    self.bond_yields = {}
    
    self.period = 12 * 21 # 12 months of bond yields
    
    self.futures_flag = False
    
    # Strategy works on equity futures
    if self.futures_flag:
        for equity_future, bond_yield_symbol in self.futures:
            # Equity future data.
            data = self.AddData(QuantpediaFutures, equity_future, Resolution.Daily)
            data.SetFeeModel(CustomFeeModel())
            data.SetLeverage(5)
            
            # Bond yield data.
            self.AddData(QuantpediaBondYield, bond_yield_symbol, Resolution.Daily)
            
            # Add Symboldata to bond yield with equity future symbol
            self.bond_yields[bond_yield_symbol] = SymbolData(self.period, data.Symbol)
    
    # Otherwise strategy works on ETFs   
    else:
        for etf_symbol, bond_yield_symbol in self.etfs:
            # ETF data
            data = self.AddEquity(etf_symbol, Resolution.Daily)
            data.SetFeeModel(CustomFeeModel())
            data.SetLeverage(5)
            
            # Bond yield data.
            self.AddData(QuantpediaBondYield, bond_yield_symbol, Resolution.Daily)
            
            # # Add Symboldata to bond yield with ETF symbol
            self.bond_yields[bond_yield_symbol] = SymbolData(self.period, data.Symbol)
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Rebalance)
def OnData(self, data):
    # Update bond yields
    for symbol, symbol_data in self.bond_yields.items():
        custom_data = [symbol, symbol_data.symbol] if self.futures_flag else [symbol]
        if any([self.securities[x].get_last_data() and self.time.date() > LastDateHandler.get_last_update_date()[x] for x in custom_data]):
            self.liquidate()
            return
        if symbol in data and data[symbol]:
            self.bond_yields[symbol].update(data[symbol].Value)
            
def Rebalance(self):
    bond_yield_changes = {}
    
    for _, symbol_data in self.bond_yields.items():
        symbol = symbol_data.symbol # Get corre
        
        # Check if bond yields data are ready and corresponding equity or future is Tradable
        if symbol_data.is_ready() and self.Securities[symbol].Price != 0 and self.Securities[symbol].IsTradable:
            # Construct the bond yield change as minus the difference in 10-year government bond yield to maturity over the past 12 months
            bond_yield_change = -symbol_data.difference()
            
            # Store bond yield change under it's equity or future symbol
            bond_yield_changes[symbol_data.symbol] = bond_yield_change
    
    # If there isn't enough data for quintile selection return from function
    if len(bond_yield_changes)  Dict[Symbol, datetime.date]:
   return LastDateHandler._last_update_date
# Quantpedia bond yield data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaBondYield(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/bond_yield/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaBondYield()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(',')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    data['yield'] = float(split[1])
    data.Value = float(split[1])
    if config.Symbol.Value not in LastDateHandler._last_update_date:
        LastDateHandler._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > LastDateHandler._last_update_date[config.Symbol.Value]:
        LastDateHandler._last_update_date[config.Symbol.Value] = data.Time.date()
    return data
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
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
    if config.Symbol not in LastDateHandler._last_update_date:
        LastDateHandler._last_update_date[config.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > LastDateHandler._last_update_date[config.Symbol]:
        LastDateHandler._last_update_date[config.Symbol] = data.Time.date()
    return data
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
