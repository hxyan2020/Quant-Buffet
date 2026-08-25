# Original QuantConnect / library Python
# locale=en slug="合成借贷利率预测后续市场回报"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion

class SyntheticLendingRatesPredictSubsequentMarketReturn(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2016, 1, 1)
    self.SetCash(100000)

    self.spy_symbol:Symbol = self.AddEquity('SPY', Resolution.Minute).Symbol  

    self.lending_data_symbol:Symbol = self.AddData(
        QuantpediaLendingRates,
        'lending_rate', 
        Resolution.Minute).Symbol

    self.last_lending_mean = None          

def OnData(self, data: Slice):
    curr_time:datetime.datetime = self.Time
    
    # liquidate at 15:58
    if curr_time.hour == 15 and curr_time.minute == 58:
        self.Liquidate(self.spy_symbol) 

    # lending rate data came in
    if self.lending_data_symbol in data and data[self.lending_data_symbol]:
        curr_lending_mean:float = data[self.lending_data_symbol].Value

        if self.last_lending_mean:
            # calculate daily change in lending rate
            diff:float = curr_lending_mean - self.last_lending_mean

            if diff > 0:
                self.SetHoldings(self.spy_symbol, 1)
            else:
                self.SetHoldings(self.spy_symbol, -1)

        self.last_lending_mean = curr_lending_mean    

# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaLendingRates(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/options/lending_rates_day_close_matur_45_days.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)

def Reader(self, config, line, date, isLiveMode):
    data:QuantpediaLendingRates = QuantpediaLendingRates()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None

    split:list = line.split(';')

    datetime_str:str = split[0] + ', 15:59'
    
    data.Time = datetime.strptime(datetime_str, "%Y-%m-%d, %H:%M")
    valid_values:list = list(filter(lambda value: value != '', split[1:]))
    valid_values:list = list(map(lambda str_value: float(str_value), valid_values))
    data.Value = np.mean(valid_values)

    return data
