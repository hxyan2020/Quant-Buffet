# Original QuantConnect / library Python
# locale=en slug="technology-momentum"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
import data_tools
from typing import List, Dict
# endregion
class TechnologyMomentum(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)
    self.international_data: bool = False
    self.tickers: List[str] = [
        'ABAX', 'ARAY', 'ACTU', 'ADBE', 'ADVS', 'AFFX', 'A', 'ALGN', 'AOSL', 'ALIN-A', 'AMZN', 'AMD', 'AAPL', 'AMAT',
        'AMCC', 'ARBA', 'ARUN', 'T', 'ATML', 'AXTI', 'BRCD', 'CDNS', 'CALD', 'CAVM', 'CPHD', 'CSCO', 'C', 'CDXS', 'COHR',
        'CPTS', 'CY', 'DEPO', 'DLGC', 'DIS', 'DLB', 'DWA', 'DSPG', 'EBAY', 'ELON', 'EA', 'EFII', 'EPOC', 'EQIX', 'EXAR',
        'EXEL', 'EXTR', 'FB', 'FCS', 'FNSR', 'F', 'FORM', 'FTNT', 'GE', 'GM', 'GDHX', 'GILD', 'GOOGL', 'GSIT', 'HLIT',
        'HPQ', 'HMC', 'IBM', 'IGTE', 'IKAN', 'IPXL', 'INFN', 'INFA', 'IDIT', 'ISSI', 'INTC', 'ISIL', 'IVAC', 'INTU',
        'ISRG', 'INVN', 'IPA', 'IXYS', 'JDSU', 'JNPR', 'KEYN', 'KLAC', 'LRCX', 'LF', 'LLTC', 'LSI', 'LLC', 'MTSN',
        'MXIM', 'MERU', 'MCRL', 'MSFT', 'MPWR', 'ONTO', 'NTUS', 'NPTN', 'NTAP', 'NFLX', 'NTGR', 'N', 'NSANY', 'NVLS',
        'NVDA', 'OCLR', 'OCZ', 'OMCL', 'OVTI', 'ONXX', 'OPEN_old', 'OPWV', 'OPLK', 'OPXT', 'ORCL', 'P', 'PSEM', 'PLXT',
        'PMCS', 'PLCM', 'POWI', 'QMCO', 'QNST', 'RMBS', 'MKTG', 'RVBD', 'ROVI', 'SABA', 'CRM', 'SNDK', 'SANM', 'SCLN',
        'SREV', 'SHOR', 'SFLY', 'SIGM', 'SGI', 'SIMG', 'SLTM', 'CODE', 'SPWR', 'SMCI', 'NLOK', 'SYMM', 'SYNA', 'SNX',
        'SNPS', 'TNAV', 'TSLA', 'XPER', 'THOR', 'TIBX', 'TIVO', 'TYO', 'TRID', 'TRMB', 'TWTR', 'UI', 'UCTT', 'ULTRACEMCO',
        'VAR', 'PAY', 'VMW', 'VLTR', 'WMT', 'XLNX', 'YAHOO', 'DZSI', 'ZNGA'
    ]
    self.years_period: int = 5
    self.min_prices: int = 15
    self.quantile: int = 10
    self.leverage: int = 5
    self.weights: Dict[Symbol, float] = {}
    self.count_by_class_by_date: Dict[datetime.date, Dict[str, int]] = {}
    self.data: Dict[str, data_tools.SymbolData] = {}
    self.classification_symbol_by_ticker: Dict[str, Symbol] = {}
    for ticker in self.tickers:
        classification_symbol: Symbol = self.AddData(data_tools.QuantpediaPatentClassification, ticker, Resolution.Daily).Symbol
        self.classification_symbol_by_ticker[ticker] = classification_symbol
        self.data[ticker] = data_tools.SymbolData()
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # daily update prices required in stock's monthly return calculation
    for equity in fundamental:
        ticker: str = equity.Symbol.Value
        if ticker in self.data:
            self.data[ticker].update_prices(equity.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    start_boundry_date: datetime.date = self.Time.date() - relativedelta(years=self.years_period)
    for _, symbol_obj in self.data.items():
        # reset of prices and update of monthly return, which is required for each stock on monthly basis, to keep valid data
        if symbol_obj.prices_ready(self.min_prices):
            symbol_obj.update_monthly_return()
        else:
            symbol_obj.reset_monthly_return()
        symbol_obj.reset_prices()
        
        # remove stock's patents classifications, which won't be needed anymore
        symbol_obj.remove_needless_classifications(start_boundry_date)
    selected: List[Fundamental] = [
        x for x in fundamental
        if x.Symbol.Value in self.data
        and x.MarketCap != 0
        and self.data[x.Symbol.Value].monthly_return_ready() 
        and self.data[x.Symbol.Value].classifications_ready()]
    if len(selected) == 0:
        return Universe.Unchanged    
    dates_to_remove: datetime.date = []
    companies_patents_classes: List[str] = []
    start_boundry_date: datetime.date = self.Time.date() - relativedelta(years=self.years_period)
    for date, count_by_class in self.count_by_class_by_date.items():
        if date  None:
    curr_date: datetime.date = self.Time.date()
    custom_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.QuantpediaPatentClassification.get_last_update_date()
    latest_update_date: datetime.date = max(date for date in custom_data_last_update_date.values())
    stock_to_delete: List[str] = []
    # if self.time.date() > latest_update_date:
    #     self.liquidate()
    #     return
    for stock_ticker, classification_symbol in self.classification_symbol_by_ticker.items():
        if self.Securities[stock_ticker].GetLastData() and self.Time.date() > custom_data_last_update_date[stock_ticker]:
            self.Liquidate(stock_ticker)
            stock_to_delete.append(stock_ticker)
            continue
        
        if data.contains_key(classification_symbol) and data[classification_symbol]:
            if curr_date not in self.count_by_class_by_date:
                self.count_by_class_by_date[curr_date] = {}
            symbol_obj: SymbolData = self.data[stock_ticker]
            wanted_property: str = 'international' if self.international_data else 'u.s.'
            patent_classes: List[str] = list(data[classification_symbol].GetProperty(wanted_property))
            for patent_class in patent_classes:
                if patent_class not in self.count_by_class_by_date[curr_date]:
                    self.count_by_class_by_date[curr_date][patent_class] = 0
                self.count_by_class_by_date[curr_date][patent_class] += 1
                symbol_obj.update_patents(curr_date, patent_class)
    for ticker in stock_to_delete:
        self.classification_symbol_by_ticker.pop(ticker)
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weights.items() if data.contains_key(symbol) and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weights.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
