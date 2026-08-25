# Original QuantConnect / library Python
# locale=en slug="rank-effect-for-commodities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class RankEffectForCommodities(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.SetMaximumOrders(100000)
    self.quantile: int = 5
    
    self.symbols = [
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
        "CME_DA1",  # Class III Milk Futures
        "ICE_RS1",  # Canola Futures, Continuous Contract
        "ICE_GO1",  # Gas Oil Futures, Continuous Contract
        "CME_RB2",  # Gasoline Futures, Continuous Contract
        "CME_KW2",  # Wheat Kansas, Continuous Contract
        "ICE_WT1",  # WTI Crude Futures, Continuous Contract
        "ICE_RS1",  # Canola Futures, Continuous Contract
        "ICE_GO1",  # Gas Oil Futures, Continuous Contract
        "CME_RB2",  # Gasoline Futures, Continuous Contract
        "CME_KW2",  # Wheat Kansas, Continuous Contract
        "ICE_WT1",  # WTI Crude Futures, Continuous Contract
        "ICE_CC1",  # Cocoa Futures, Continuous Contract 
        "ICE_CT1",  # Cotton No. 2 Futures, Continuous Contract
        "ICE_KC1",  # Coffee C Futures, Continuous Contract
        "ICE_O1",   # Heating Oil Futures, Continuous Contract
        "ICE_OJ1",  # Orange Juice Futures, Continuous Contract
        "ICE_SB1",  # Sugar No. 11 Futures, Continuous Contract
    ]
    
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(10)
    
    self.base_price = {}
    self.settings.daily_precise_end_time = False
def OnData(self, data):
    # base
    if self.Time.year == 2010 and self.Time.month == 1 and self.Time.day == 5:
        for symbol in self.symbols:
            if symbol in data and data[symbol]:
                self.base_price[symbol] = data[symbol].Value
    
    performance = {}
    
    for symbol in self.symbols:
        # Check if data is still coming.
        if self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol]:
            self.liquidate(symbol)
            continue
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data and data[symbol_obj]:
            price = data[symbol_obj].Value
            if price != 0 and symbol in self.base_price:
                base_price = self.base_price[symbol]
                ret = (price / base_price) - 1
                performance[symbol] = ret
    if len(performance)  Dict[Symbol, datetime.date]:
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
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
