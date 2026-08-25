# Original QuantConnect / library Python
# locale=zh slug="全球失衡货币因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
#endregion
class GlobalImbalanceCurrencyFactor(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.quantpedia_futures:bool = False
    
    self.countries:Dict[str, List[str]] = {
        'Australia': ['AUDUSD', 'AUS_GDP'],
        'United Kingdom': ['GBPUSD', 'GBR_GDP'],
        'New Zealand': ['NZDUSD', 'NZL_GDP'],
        'Canada': ['USDCAD', 'CAN_GDP'],
        'Switzerland': ['USDCHF', 'CHE_GDP'],
        'China': ['USDCNH', 'CHN_GDP'],
        'Czech Republic': ['USDCZK', 'CZE_GDP'],
        'Denmark': ['USDDKK', 'DNK_GDP'],
        'Hungary': ['USDHUF', 'HUN_GDP'],
        'India': ['USDINR', 'IND_GDP'],
        'Japan': ['USDJPY' ,'JPN_GDP'],
        'Norway': ['USDNOK', 'NOR_GDP'],
        'Poland': ['USDPLN', 'POL_GDP'],
        'Saudi Arabia': ['USDSAR', 'SAU_GDP'],
        'Sweden': ['USDSEK', 'SWE_GDP'],
        'Thailand': ['USDTHB', 'THA_GDP'],
        'Turkey': ['USDTRY', 'TUR_GDP']
    }
    
    if self.quantpedia_futures:
        self.countries:Dict[str, List[str]] = {
            'Australia': ['CME_AD1', 'AUS_GDP'],
            'United Kingdom': ['CME_BP1', 'GBR_GDP'],
            'New Zealand': ['CME_NE1', 'NZL_GDP'],
            'Canada': ['CME_CD1', 'CAN_GDP'],
            'Switzerland': ['CME_SF1', 'CHE_GDP'],
            'Japan': ['CME_JY1' ,'JPN_GDP']
        }
    
    self.quantile:int = 2
    self.leverage:int = 5
    
    self.net_foreign_assets:Symbol = self.AddData(data_tools.QuantpediaNetForeignAssets, 'NET_FOREIGN_ASSETS', Resolution.Daily).Symbol
    self.debt_all_currencies:Symbol = self.AddData(data_tools.QuantpediaCurrenciesDebt ,'DEBT_ALL_CURRENCIES', Resolution.Daily).Symbol
    self.debt_foreign_currencies:Symbol = self.AddData(data_tools.QuantpediaCurrenciesDebt ,'DEBT_FOREIGN_CURRENCIES', Resolution.Daily).Symbol
    
    # store SymbolData object under country 
    self.data:Dict[str, SymbolData] = { x : SymbolData() for x in self.countries }
    
    for country in self.countries:
        ticker:str = self.countries[country][0]
        gdp:str = self.countries[country][1]
        
        if self.quantpedia_futures:
            data = self.AddData(data_tools.QuantpediaFutures, ticker, Resolution.Daily)
        else:
            # subscribe to currency
            data = self.AddForex(ticker, Resolution.Daily, Market.Oanda)
        
        data.SetLeverage(self.leverage)
        
        # subscribe to quandl gdp
        self.AddData(data_tools.GDPData, gdp, Resolution.Daily)
    
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_flag:bool = False
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
def OnData(self, data: Slice) -> None:
    if self.debt_all_currencies in data and data[self.debt_all_currencies]:
        for country in self.countries:
            # get country debt based on index from data object
            debt = data[self.debt_all_currencies].GetProperty(country)
            # store debt in SymbolData object under country name in dictionary
            self.data[country].all_currencies_debt_value = float(debt)
    
    if self.net_foreign_assets in data and data[self.net_foreign_assets]:
        for country in self.countries:
            # get country net foreign asset based on index from data object
            asset = data[self.net_foreign_assets].GetProperty(country)
            # store net foreign asset in SymbolData object under country name in dictionary
            self.data[country].nfa_value = float(asset)
    
    if self.debt_foreign_currencies in data and data[self.debt_foreign_currencies]:
        for country in self.countries:
            # get country debt based on index from data object
            debt = data[self.debt_foreign_currencies].GetProperty(country)
            # store debt in SymbolData object under country name in dictionary
            self.data[country].foreign_currencies_debt_value = float(debt)
    debt_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaCurrenciesDebt.get_last_update_date()
    nfa_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaNetForeignAssets.get_last_update_date()
    gdp_last_update_date:Dict[str, datetime.date] = data_tools.GDPData.get_last_update_date()
    if self.quantpedia_futures:
        futures_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()
    # custom data is still comming in
    if not all(self.Securities[x].GetLastData() and self.Time.date()  futures_last_update_date[self.countries[country][0]]:
                continue
        else:
            if not self.Securities[self.countries[country][0]].GetLastData():
                continue
        if self.Securities[self.countries[country][1]].GetLastData() and self.Time.date() > gdp_last_update_date[self.countries[country][1]]:
            continue
                    
        if not symbol_data.is_ready():
            continue
        
        # store value under country
        nfa[country] = symbol_data.nfa_value / symbol_data.gdp_value
        
        # get country debts
        foreign_debt:float = symbol_data.foreign_currencies_debt_value
        all_debt:float = symbol_data.all_currencies_debt_value
        
        # can't perform division by zero
        if all_debt == 0:
            share_of_debt[country] = 0
            continue
        
        # store share of debt under country
        share_of_debt[country] = foreign_debt / all_debt
        
    # performing one month lag
    for _, symbol_data in self.data.items():
        symbol_data.gdp_ready = True
        
    if len(nfa) = self.quantile and len(high_nfa_by_share_of_debt) >= self.quantile:
        quantile = int(len(low_nfa_by_share_of_debt) / self.quantile)    
        long = [self.countries[x][0] for x in low_nfa_by_share_of_debt[-quantile:]]
        short = [self.countries[x][0] for x in high_nfa_by_share_of_debt[:quantile]]
    
    # trade execution
    long_length:int = len(long)
    short_length:int = len(short)
    
    invested:List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for ticker in invested:
        if ticker not in long + short:
            self.Liquidate(ticker)
    
    for ticker in long:
        weight = 1 / long_length
        
        if ticker[:3] == 'USD':
            weight = weight * -1
        
        self.SetHoldings(ticker, weight)
        
    for ticker in short:
        weight = -1 / short_length
        
        if ticker[:3] == 'USD':
            weight = weight * -1
        
        self.SetHoldings(ticker, weight)
            
def Selection(self) -> None:
    self.selection_flag = True
    
class SymbolData():
def __init__(self):
    self.nfa_value = -1
    self.all_currencies_debt_value = -1
    self.foreign_currencies_debt_value = -1
    self.gdp_value = -1
    self.gdp_ready = False
    
def is_ready(self):
    return self.gdp_ready and self.nfa_value != -1 and \
            self.all_currencies_debt_value != -1 and self.foreign_currencies_debt_value != -1
