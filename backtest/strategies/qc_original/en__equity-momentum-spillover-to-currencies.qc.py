# Original QuantConnect / library Python
# locale=en slug="equity-momentum-spillover-to-currencies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class EquityMomentumSpillovertoCurrencies(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2007, 1, 1)
    self.SetCash(100000)
    
    # Country symbol and currency future symbol.
    self.symbols = {
                    "CME_CD1" : "LIFFE_FCE1",   # Canadian Dollar Futures, Continuous Contract #1
                    "CME_SF1" : "EUREX_FSMI1",  # Swiss Franc Futures, Continuous Contract #1
                    "CME_EC1" : "EUREX_FSTX1",  # Euro FX Futures, Continuous Contract #1
                    "CME_BP1" : "LIFFE_Z1",     # British Pound Futures, Continuous Contract #1
                    "CME_JY1" : "SGX_NK1",      # Japanese Yen Futures, Continuous Contract #1
                    }
    self.period = 12 * 21
    self.pairs = []
    self.data = {}  # momentum data
    self.max_missing_days = 5
    
    for i, curr_symbol1 in enumerate(self.symbols):
        # Equity index futures data.
        index_symbol = self.symbols[curr_symbol1]
        self.AddData(QuantpediaFutures, index_symbol, Resolution.Daily)
        self.data[index_symbol] = RollingWindow[float](self.period)
        
        # Currency futures data.
        if curr_symbol1 != "":  # except US dollar
            data = self.AddData(QuantpediaFutures, curr_symbol1, Resolution.Daily)
            data.SetLeverage(20)
            data.SetFeeModel(CustomFeeModel())
        else:
            continue
        for j, curr_symbol2 in enumerate(self.symbols):
            if j  eq_momentum2:
                curr_position[pair[0]] += 1
                curr_position[pair[1]] -= 1
            # add short pair position
            else:
                curr_position[pair[0]] -= 1
                curr_position[pair[1]] += 1
    if len(curr_position) != 0:
        futures_invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
        for currency_future in futures_invested:
            if currency_future not in curr_position:
                self.Liquidate(currency_future)
        
        total_position = sum([abs(x[1]) for x in curr_position.items()])
        for currency_future, country_signal in curr_position.items():
            self.SetHoldings(currency_future, country_signal)
    else:
        self.Liquidate()
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
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
    return data
