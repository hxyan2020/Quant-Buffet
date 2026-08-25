# Original QuantConnect / library Python
# locale=en slug="us-equity-tail-risk-and-currency-risk-premia"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from collections import deque
import numpy as np
class USEquityTailRiskandCurrencyRiskPremia(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = {
                    "CME_AD1",   # Australian Dollar Futures, Continuous Contract #1
                    "CME_CD1",   # Canadian Dollar Futures, Continuous Contract #1
                    "CME_EC1",   # Euro FX Futures, Continuous Contract #1
                    "CME_JY1",   # Japanese Yen Futures, Continuous Contract #1
                    "CME_NE1",   # New Zealand Dollar Futures, Continuous Contract #1
                    "CME_SF1",    # Swiss Franc Futures, Continuous Contract #1
                    "CME_BP1"   # British Pound Futures, Continuous Contract #1
    }
    
    # Daily ROC data.
    self.data = {}
    self.period = 21
    self.SetWarmUp(self.period)
    # Regression data rolling window.
    self.regression_period = 60
    self.regression_data = {}
    self.pput_index = self.AddData(PPUT, 'PPUT', Resolution.Daily).Symbol
    self.data[self.pput_index] = self.ROC(self.pput_index, self.period, Resolution.Daily)
    
    self.market = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.data[self.market] = self.ROC(self.market, self.period, Resolution.Daily)
    
    for symbol in self.symbols:
        data = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(5)
        
        self.data[symbol] = self.ROC(symbol, self.period, Resolution.Daily)
        
        self.regression_data[symbol] = deque(maxlen = self.regression_period)
    
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Rebalance)
def Rebalance(self):
    # Regression data.
    # Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3399980
    dol_factor_return = None
    mkt_factor_return = None
    tail_factor_return = None
    
    if self.data[self.market].IsReady and self.data[self.pput_index].IsReady:
        # To measure the US tail risk, construct a zero-investment strategy that longs the CBOE PPut index and shorts the S&P 500 index.
        tail_factor_return = (self.data[self.pput_index].Current.Value - self.data[self.market].Current.Value) / 2
        mkt_factor_return = self.data[self.market].Current.Value
    
    currency_returns = {x : self.data[x].Current.Value for x in self.symbols if self.data[x].IsReady}
    if len(currency_returns) != 0:
        dol_factor_return = np.average([x[1] for x in currency_returns.items()])
    
    # Factors for regression are ready.
    if dol_factor_return and mkt_factor_return and tail_factor_return:
        
        tail_beta = {}
        
        for symbol, symbol_return in currency_returns.items():
            reg_data = (symbol_return, dol_factor_return, mkt_factor_return, tail_factor_return)
            self.regression_data[symbol].append(reg_data)
            
            if len(self.regression_data[symbol]) == self.regression_data[symbol].maxlen:
                symbol_returns = [x[0] for x in self.regression_data[symbol]]
                dols = [x[1] for x in self.regression_data[symbol]]
                mkts = [x[2] for x in self.regression_data[symbol]]
                tails = [x[3] for x in self.regression_data[symbol]]
                
                # Regression.
                x = [dols[:-1], mkts[:-1], tails[:-1]]
                regression_model = data_tools.MultipleLinearRegression(x, symbol_returns[1:])
                tail_beta[symbol] = regression_model.params[3]
                
        sorted_by_beta = sorted(tail_beta.items(), key = lambda x:x[1], reverse = True)
        quintile = int(len(sorted_by_beta) / 5)
        long = [x[0] for x in sorted_by_beta[-quintile:]]
        short = [x[0] for x in sorted_by_beta[:quintile]]
    
        # Trade execution.
        long_count = len(long)
        short_count = len(short)
        
        invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
        for symbol in invested:
            if symbol not in long + short:
                self.Liquidate(symbol)
        
        for symbol in long:
            self.SetHoldings(symbol, 1 / long_count)
        for symbol in short:
            self.SetHoldings(symbol, -1 / short_count)
            
# PPUT index.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
# Data source: http://www.cboe.com/products/strategy-benchmark-indexes/put-protection-index
class PPUT(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/index/pput.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = PPUT()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%m/%d/%Y") + timedelta(days=1)
    data['close'] = float(split[1])
    data.Value = float(split[1])
    return data
