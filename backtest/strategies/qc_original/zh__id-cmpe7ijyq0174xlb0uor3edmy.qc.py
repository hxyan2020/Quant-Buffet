# Original QuantConnect / library Python
# locale=zh slug="用小盘股对抗β因子的择时策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
#endregion
class TimingBettingAgainstBetawithSmallStocks(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.countries = [
                    "AUS", "AUT", "BEL", "CAN", "DNK", "FIN", "FRA", "DEU",
                    "GRC", "HKG", "IRL", "ISR","ITA","JPN","NLD","NZL","NOR",
                    "PRT","SGP","ESP","SWE","CHE","GBR","USA"
                ]
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol        
    self.smb_history:dict = {}
    self.quantile:int = 5
    self.max_missing_days:int = 5
    
    self.period:int = 3 * 21 # performance period.
    self.SetWarmUp(self.period, Resolution.Daily)
    self.smb_symbol:Symbol = self.AddData(SMB, 'SMB_percentage', Resolution.Daily).Symbol
    for country in self.countries:
        # BAB and SMB data.
        data = self.AddData(BAB, country + '_BAB', Resolution.Daily)
        data.SetLeverage(10)
        data.SetFeeModel(CustomFeeModel())
        
        self.smb_history[country] = RollingWindow[float](self.period)
    self.recent_month:int = -1
def OnData(self, data:Slice) -> None:
    if self.smb_symbol in data and data[self.smb_symbol]:
        for country in self.countries:
            smb_value:float = data[self.smb_symbol].GetProperty(country)
            self.smb_history[country].Add(smb_value)
    # rebalance monthly
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    # SMB factor data is still comming in
    if self.Securities[self.smb_symbol].GetLastData() and (self.Time.date() - self.Securities[self.smb_symbol].GetLastData().Time.date()).days > self.max_missing_days:
        self.Liquidate()
        return
    # calculate average performance
    avg_perf:dict[str, float] = {}
    for country in self.countries:
        if self.smb_history[country].IsReady:
            # BAB factor data is still comming in
            if self.Securities[country + '_BAB'].GetLastData() and (self.Time.date() - self.Securities[country + '_BAB'].GetLastData().Time.date()).days > self.max_missing_days:
                continue
            avg_perf[country] = np.average([x for x in self.smb_history[country]])
    
    if len(avg_perf)  str:
    return symbol + '_BAB'
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
    
# SMB factor.
# NOTE: IMPORTANT: Data order must be ascending (datewise).
# Data source: https://www.aqr.com/Insights/Datasets/Betting-Against-Beta-Equity-Factors-Daily
class SMB(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/equity/smb_factor_percentage.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
# File example.
# DATE;AUS;AUT;BEL;CAN;CHE;DEU;DNK;ESP;FIN;FRA;GBR;GRC;HKG;IRL;ISR;ITA;JPN;NLD;NOR;NZL;PRT;SGP;SWE;USA
# 09/30/2020;1.40;1.19;0.72;-0.22;0.84;1.05;0.31;1.26;0.67;0.83;1.12;-0.16;-0.47;0.16;-0.20;1.21;-0.07;0.26;0.23;-0.37;0.68;-0.84;0.43;-0.61
def Reader(self, config, line, date, isLiveMode):
    data = SMB()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    # Prevent look-ahead bias.
    data.Time = datetime.strptime(split[0], "%m/%d/%Y") + timedelta(days=1)
    
    data['AUS'] = float(split[1])
    data['AUT'] = float(split[2])
    data['BEL'] = float(split[3])
    data['CAN'] = float(split[4])
    data['CHE'] = float(split[5])
    data['DEU'] = float(split[6])
    data['DNK'] = float(split[7])
    data['ESP'] = float(split[8])
    data['FIN'] = float(split[9])
    data['FRA'] = float(split[10])
    data['GBR'] = float(split[11])
    data['GRC'] = float(split[12])
    data['HKG'] = float(split[13])
    data['IRL'] = float(split[14])
    data['ISR'] = float(split[15])
    data['ITA'] = float(split[16])
    data['JPN'] = float(split[17])
    data['NLD'] = float(split[18])
    data['NOR'] = float(split[19])
    data['NZL'] = float(split[20])
    data['PRT'] = float(split[21])
    data['SGP'] = float(split[22])
    data['SWE'] = float(split[23])
    data['USA'] = float(split[24])
    
    data.Value = float(split[1])
    return data
    
# BAB factor.
# NOTE: IMPORTANT: Data order must be ascending (datewise).
# Data source: https://www.aqr.com/Insights/Datasets/Betting-Against-Beta-Equity-Factors-Daily
class BAB(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource(f"data.quantpedia.com/backtesting_data/equity/{config.Symbol.Value}.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
# File example.
# date;AUS
# 09/30/2020;24.05738634
def Reader(self, config, line, date, isLiveMode):
    data = BAB()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    # Prevent look-ahead bias.
    data.Time = datetime.strptime(split[0], "%m/%d/%Y") + timedelta(days=1)
    data.Value = float(split[1])
    return data
