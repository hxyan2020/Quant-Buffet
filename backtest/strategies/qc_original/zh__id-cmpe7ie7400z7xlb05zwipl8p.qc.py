# Original QuantConnect / library Python
# locale=zh slug="外汇动量的季节性效应策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class FXMomentumSeasonality(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = [
        'CME_AD1', # Australian Dollar Futures, Continuous Contract #1
        'CME_CD1', # Canadian Dollar Futures, Continuous Contract #1
        'CME_SF1', # Swiss Franc Futures, Continuous Contract #1
        'CME_EC1', # Euro FX Futures, Continuous Contract #1
        'CME_BP1', # British Pound Futures, Continuous Contract #1
        'CME_JY1', # Japanese Yen Futures, Continuous Contract #1
        'CME_NE1', # New Zealand Dollar Futures, Continuous Contract #1
        'CME_MP1' # Mexican Peso Futures, Continuous Contract #1
    ]
    
    self.current_prices = {}
    self.yesterday_prices = {}
    
    # Momentum strategy is traded only during the last 1/3 of each month (days 20-29).
    self.start_day = 20
    self.end_day = 29
    leverage: int = 5
    
    for currency_future in self.symbols:
        security = self.AddData(QuantpediaFutures, currency_future, Resolution.Daily)
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(leverage)
        
        self.current_prices[currency_future] = 0
        self.yesterday_prices[currency_future] = 0
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.settings.daily_precise_end_time = False
def OnData(self, data):
    custom_data_last_update_date: Dict[str, datetime.date] = QuantpediaFutures.get_last_update_date()
    # Storing daily data about future currencies
    for symbol in self.symbols:
        if self.securities[symbol].get_last_data() and self.time.date() > custom_data_last_update_date[symbol]:
            self.liquidate()
            return
        if symbol in data:
            if data[symbol]:
                price = data[symbol].Value
                if price != 0:
                    self.yesterday_prices[symbol] = self.current_prices[symbol]
                    self.current_prices[symbol] = price
        
    long = []
    short = []
    
    if self.start_day  self.yesterday_prices[symbol]:
                long.append(symbol)
            else:
                short.append(symbol)
    
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([long, short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
		
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
    
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
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
    if config.Symbol.Value not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol.Value]:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = data.Time.date()
    return data
