# Original QuantConnect / library Python
# locale=zh slug="异常现象中的季节性效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
# https://quantpedia.com/strategies/seasonality-effect-in-anomalies/
#
# The investment universe consists of stocks listed at NYSE, AMEX, and NASDAQ, with monthly return data available at CRSP Database. Accounting data (such as firms’ book values) 
# are obtained from Compustat. The investor takes the long position on three best-performing and short on three worst-performing anomaly portfolios. According to the same-calendar
# month returns of the portfolios (their formation is outlined in the description of Table 4, page 43) over the period of the last 20 years. Stocks in the portfolios are 
# value-weighted, the portfolio is to be rebalanced monthly and held for one month.
#
# QC implementation:
#   - Seasonal performance is calculated over 10 year period.
#   - Investment universe consists of Quantpedia's equity long-short anomalies.
class SeasonalityEffectinAnomalies(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    # ids with backtest period end year
    self.backtest_to = {}
    
    # daily price data
    self.perf = {}
    self.period = 21
    self.SetWarmUp(self.period)
    # monthly returns
    self.monthly_returns = {}
    self.min_seasonal_period = 10
    
    csv_string_file = self.Download('data.quantpedia.com/backtesting_data/equity/quantpedia_strategies/backtest_end_year.csv')
    lines = csv_string_file.split('\r\n')
    last_id = None
    for line in lines[1:]:
        split = line.split(';')
        id = str(split[0])
        backtest_to = int(split[1])
        
        data = self.AddData(QuantpediaEquity, id, Resolution.Daily)
        data.SetLeverage(10)
        data.SetFeeModel(CustomFeeModel())
        
        self.backtest_to[id] = backtest_to
        self.perf[id] = self.ROC(id, self.period, Resolution.Daily)
        self.monthly_returns[id] = []
        
        if not last_id:
            last_id = id
    self.recent_month = -1

def OnData(self, data):
    if self.IsWarmingUp:
        return
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    
    seasonal_return = {}
    
    for id in self.perf:
        if self.perf[id].IsReady and id in data and data[id]:
            # store monthly returns
            perf = self.perf[id].Current.Value
            self.monthly_returns[id].append((perf, self.Time.month - 1))
            
            # calculate seasonal performance of those strategies, which were published last year and sooner
            if self.backtest_to[id] = self.min_seasonal_period:
                    seasonal_return[id] = sum(seasonal_monthly_returns[-self.min_seasonal_period:])
    long = []
    short = []
    
    # seasonal return sorting
    count_traded = 3
    if len(seasonal_return) >= count_traded*2:
        sorted_by_perf = sorted(seasonal_return.items(), key = lambda x: x[1], reverse = True)
        long = [x[0] for x in sorted_by_perf[:count_traded]]
        short = [x[0] for x in sorted_by_perf[-count_traded:]]
    # trade execution
    invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    
    long_count = len(long)                
    short_count = len(short)
    
    for symbol in long:
        self.SetHoldings(symbol, 1 / long_count)
    for symbol in short:
        self.SetHoldings(symbol, -1 / short_count)
        
# Quantpedia strategy equity curve data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaEquity(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/equity/quantpedia_strategies/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaEquity()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    data['close'] = float(split[1])
    data.Value = float(split[1])
    return data
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
