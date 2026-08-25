# Original QuantConnect / library Python
# locale=en slug="return-asymmetry-effect-in-commodity-futures-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class ReturnAsymmetryEffectInCommodityFutures(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.tickers = [
        "CME_S1",   # Soybean Futures, Continuous Contract
        "CME_W1",   # Wheat Futures, Continuous Contract
        "CME_SM1",  # Soybean Meal Futures, Continuous Contract
        "CME_BO1",  # Soybean Oil Futures, Continuous Contract
        "CME_C1",   # Corn Futures, Continuous Contract
        "CME_O1",   # Oats Futures, Continuous Contract
        "CME_LC1",  # Live Cattle Futures, Continuous Contract
        "CME_FC1",  # Feeder Cattle Futures, Continuous Contract
        "CME_LN1",  # Lean Hog Futures, Continuous Contract
        "CME_GC1",  # Gold Futures, Continuous Contract
        "CME_SI1",  # Silver Futures, Continuous Contract
        "CME_PL1",  # Platinum Futures, Continuous Contract
        "CME_CL1",  # Crude Oil Futures, Continuous Contract
        "CME_HG1",  # Copper Futures, Continuous Contract
        "CME_LB1",  # Random Length Lumber Futures, Continuous Contract
        # "CME_NG1",  # Natural Gas (Henry Hub) Physical Futures, Continuous Contract
        "CME_PA1",  # Palladium Futures, Continuous Contract 
        "CME_RR1",  # Rough Rice Futures, Continuous Contract
        "CME_RB2",  # Gasoline Futures, Continuous Contract
        "CME_KW2",  # Wheat Kansas, Continuous Contract
        "ICE_CC1",  # Cocoa Futures, Continuous Contract 
        "ICE_CT1",  # Cotton No. 2 Futures, Continuous Contract
        "ICE_KC1",  # Coffee C Futures, Continuous Contract
        "ICE_O1",   # Heating Oil Futures, Continuous Contract
        "ICE_OJ1",  # Orange Juice Futures, Continuous Contract
        "ICE_SB1"   # Sugar No. 11 Futures, Continuous Contract
        "ICE_RS1",  # Canola Futures, Continuous Contract
        "ICE_GO1",  # Gas Oil Futures, Continuous Contract
        "ICE_WT1",  # WTI Crude Futures, Continuous Contract
    ]
    self.data = {} # storing objects of SymbolData class keyed by comodity symbols
    self.period = 261 # need 261 daily prices, to calculate 260 daily returns
    self.buy_count = 7 # buy n comodities on each rebalance
    self.sell_count = 7 # sell n comodities on each rebalance
    self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    # subscribe to futures contracts
    for ticker in self.tickers:
        security = self.AddData(QuantpediaFutures, ticker, Resolution.Daily)
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(5)
        self.data[security.Symbol] = SymbolData(self.period)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.rebalance_flag = False   
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol, 0), self.Rebalance)
def OnData(self, data):
    # update daily closes
    for symbol in self.data:
        if self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol]:
            self.liquidate()
            return
        if symbol in data and data[symbol]:
            close = data[symbol].Value
            self.data[symbol].update_closes(close)
    # rebalance monthly        
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    IE = {}
    for symbol, symbol_obj in self.data.items():
        # check if comodity has ready prices
        if not symbol_obj.is_ready():
            continue
        # calculate IE
        IE_value = symbol_obj.calculate_IE()
        # store IE value under comodity symbol
        IE[symbol] = IE_value
    # make sure, there are enough comodities for rebalance
    if len(IE)  avg_plus_two_std:
            over_avg_plus_two_std += 1
        elif daily_return  Dict[Symbol, datetime.date]:
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
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
