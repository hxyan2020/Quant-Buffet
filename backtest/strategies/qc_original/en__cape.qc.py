# Original QuantConnect / library Python
# locale=en slug="价值因子-各国中的cape效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
#endregion

class ValueFactorCAPEEffectwithinCountries(XXX):

def Initialize(self):
    self.SetStartDate(2008, 1, 1)  
    self.SetCash(100000)

    self.symbols = {
        "Australia"     : "EWA",  # iShares MSCI Australia Index ETF
        "Brazil"        : "EWZ",  # iShares MSCI Brazil Index ETF
        "Canada"        : "EWC",  # iShares MSCI Canada Index ETF
        "Switzerland"   : "EWL",  # iShares MSCI Switzerland Index ETF
        "China"         : "FXI",  # iShares China Large-Cap ETF
        "France"        : "EWQ",  # iShares MSCI France Index ETF
        "Germany"       : "EWG",  # iShares MSCI Germany ETF 
        "Hong Kong"     : "EWH",  # iShares MSCI Hong Kong Index ETF
        "Italy"         : "EWI",  # iShares MSCI Italy Index ETF
        "Japan"         : "EWJ",  # iShares MSCI Japan Index ETF
        "Korea"         : "EWY",  # iShares MSCI South Korea ETF
        "Mexico"        : "EWW",  # iShares MSCI Mexico Inv. Mt. Idx
        "Netherlands"   : "EWN",  # iShares MSCI Netherlands Index ETF
        "South Africa"  : "EZA",  # iShares MSCI South Africe Index ETF
        "Singapore"     : "EWS",  # iShares MSCI Singapore Index ETF
        "Spain"         : "EWP",  # iShares MSCI Spain Index ETF
        "Sweden"        : "EWD",  # iShares MSCI Sweden Index ETF
        "Taiwan"        : "EWT",  # iShares MSCI Taiwan Index ETF
        "UK"            : "EWU",  # iShares MSCI United Kingdom Index ETF
        "USA"           : "SPY",  # SPDR S&P 500 ETF
        
        "Russia"        : "ERUS",  # iShares MSCI Russia ETF
        "Israel"        : "EIS",   # iShares MSCI Israel ETF
        "India"         : "INDA",  # iShares MSCI India ETF
        "Poland"        : "EPOL",  # iShares MSCI Poland ETF
        "Turkey"        : "TUR"    # iShares MSCI Turkey ETF
    }

    self.quantile:int = 3
    self.max_missing_days:int = 31
    self.leverage:int = 2

    for country, etf_symbol in self.symbols.items():
        data = self.AddEquity(etf_symbol, Resolution.Daily)
        data.SetLeverage(self.leverage)
        data.SetFeeModel(CustomFeeModel())
    
    # CAPE data import.
    self.cape_data = self.AddData(CAPE, 'CAPE',  Resolution.Daily).Symbol
        
    self.recent_month:int = -1

def OnData(self, data:Slice) -> None:
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month

    if self.recent_month != 12:
        return
    
    price = {}
    for country, etf_symbol in self.symbols.items():
        if etf_symbol in data and data[etf_symbol]:
            # cape data is still comming in
            if self.Securities[self.cape_data].GetLastData() and (self.Time.date() - self.Securities[self.cape_data].GetLastData().Time.date()).days = self.quantile:
        sorted_by_price = sorted(price.items(), key = lambda x: x[1], reverse = True)
        tercile = int(len(sorted_by_price) / self.quantile)
        long = [x[0] for x in sorted_by_price[-tercile:]]
    
    # Trade execution.
    invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long:
            self.Liquidate(symbol)
    
    for symbol in long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, 1 / len(long))

# NOTE: IMPORTANT: Data order must be ascending (datewise)
# Data source: https://indices.barclays/IM/21/en/indices/static/historic-cape.app
class CAPE(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/economic/cape_by_country.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)

_header_columns:List[str] = []

def Reader(self, config, line, date, isLiveMode):
    data = CAPE()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit():
        CAPE._header_columns = line.split(',')[1:]
        return None

    split = line.split(',')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    for i, col in enumerate(CAPE._header_columns):
        if split[i+1] != '':
            data[col] = float(split[i+1])
        else:
            data[col] = 0.
    
    data.Value = float(split[1])

    return data

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
