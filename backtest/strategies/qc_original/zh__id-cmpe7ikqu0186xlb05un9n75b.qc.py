# Original QuantConnect / library Python
# locale=zh slug="地理国家动量"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
#endregion
class GeographicalCountryMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.symbols = {
                    "Australia"      : "EWA",  # iShares MSCI Australia Index ETF
                    "Austria"        : "EWO",  # iShares MSCI Austria Investable Mkt Index ETF
                    "Belgium"        : "EWK",  # iShares MSCI Belgium Investable Market Index ETF
                    "Brazil"         : "EWZ",  # iShares MSCI Brazil Index ETF
                    "Canada"         : "EWC",  # iShares MSCI Canada Index ETF
                    "China"          : "FXI",  # iShares China Large-Cap ETF
                    "France"         : "EWQ",  # iShares MSCI France Index ETF
                    "Germany"        : "EWG",  # iShares MSCI Germany ETF 
                    "Hong Kong"      : "EWH",  # iShares MSCI Hong Kong Index ETF
                    "Italy"          : "EWI",  # iShares MSCI Italy Index ETF
                    "Japan"          : "EWJ",  # iShares MSCI Japan Index ETF
                    "Malaysia"       : "EWM",  # iShares MSCI Malaysia Index ETF
                    "Mexico"         : "EWW",  # iShares MSCI Mexico Inv. Mt. Idx
                    "Netherlands"    : "EWN",  # iShares MSCI Netherlands Index ETF
                    "Singapore"      : "EWS",  # iShares MSCI Singapore Index ETF
                    "South Africa"   : "EZA",  # iShares MSCI South Africa Index ETF
                    "South Korea"    : "EWY",  # iShares MSCI South Korea ETF
                    "Spain"          : "EWP",  # iShares MSCI Spain Index ETF
                    "Sweden"         : "EWD",  # iShares MSCI Sweden Index ETF
                    "Switzerland"    : "EWL",  # iShares MSCI Switzerland Index ETF
                    "Taiwan"         : "EWT",  # iShares MSCI Taiwan Index ETF
                    "Thailand"       : "THD",  # iShares MSCI Thailand Index ETF
                    "United Kingdom" : "EWU",  # iShares MSCI United Kingdom Index ETF
                    "United States"  : "SPY",  # SPDR S&P 500 ETF
                    }
    
    self.country_data = {}
    self.period = 21 # performance period
    self.SetWarmUp(self.period, Resolution.Daily)
    self.quantile = 5
    self.max_missing_days = 365
    csv_string_file = self.Download('data.quantpedia.com/backtesting_data/economic/city_distance_420.csv')
    lines = csv_string_file.split('\r\n')
    # header and line example: 
    # country;country_population;biggest_city;city_population;GDP_symbol;sydney_d;vienna_d;brussel_d;sao_paulo_d;toronto_d;shanghai_d;paris_d;berlin+_d;hong_kong_d;rome_d;tokyo_d;kota_bharu_d;mexico_city_d;amsterdam_d;singapore_d;cape_town_d;seoul_d;madrid_d;stockholm_d;zurich_d;taipei_d;bangkok_d;london_d;new_york_d
    # Australia;24990000;Sydney;4627345;ODA/AUS_PPPGDP;0;15996;16734;13349;15558;7876;16950;16084;7371;16311;7819;6794;12965;16632;6302;11005;8324;17674;15586;16557;7255;7532;16983;15979
    # skip header.
    for line in lines[1:]:
        split_line = line.split(';')
        country = split_line[0]
        country_pop = float(split_line[1])
        agglomeration = split_line[2]
        agglomeration_pop = float(split_line[3])
        gdp_symbol = split_line[4]
        
        self.country_data[country] = CountryData(self.period, country, country_pop, agglomeration, agglomeration_pop, gdp_symbol)
        
        line_index = 5
        for symbol_index, symbol in enumerate(self.symbols):
            self.country_data[country].AgglomerationDistance[symbol] = float(split_line[line_index + symbol_index])
        
        # etf data.
        data = self.AddEquity(self.symbols[country], Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(5)
        
        # gdp quandl data.
        self.AddData(QuandlValue, gdp_symbol, Resolution.Daily)
    
    # aggregate distance calc.
    for country_i in self.country_data:
        for country_d in self.country_data[country_i].AgglomerationDistance:
            country_i_ratio = self.country_data[country_i].AgglomerationPopulation / self.country_data[country_i].CountryPopulation
            country_d_ratio = self.country_data[country_d].AgglomerationPopulation / self.country_data[country_d].CountryPopulation
            distance_ratio = country_i_ratio * country_d_ratio * self.country_data[country_i].AgglomerationDistance[country_d]
            self.country_data[country_i].AgglomerationDistance[country_d] = distance_ratio
    
    self.recent_month = -1

def OnData(self, data):
    for country in self.country_data:
        etf_obj = self.Symbol(self.symbols[country])
        if etf_obj in data.Bars and data[etf_obj]:
            price = data.Bars[etf_obj].Value
            self.country_data[country].update(price)
    
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    # size zscore calc.
    size = { x : np.log(self.Securities[self.country_data[x].GDPSymbol].Price)  \
            for x in self.country_data if self.Securities.ContainsKey(self.country_data[x].GDPSymbol) and self.Securities[self.country_data[x].GDPSymbol].GetLastData() and (self.Time.date() - self.Securities[self.country_data[x].GDPSymbol].GetLastData().Time.date()).days  bool:
    return self.Price.IsReady

def performance(self, values_to_skip = 0) -> float:
    closes = [x for x in self.Price][values_to_skip:]
    return (closes[0] / closes[-1] - 1)                
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
    
# Quandl "value" data
class QuandlValue(NasdaqDataLink):
def __init__(self):
    self.ValueColumnName = 'Value'
