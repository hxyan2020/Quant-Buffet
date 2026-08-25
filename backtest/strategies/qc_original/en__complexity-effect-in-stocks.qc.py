# Original QuantConnect / library Python
# locale=en slug="complexity-effect-in-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
from pandas.core.series import Series
from collections import deque
from typing import List, Dict, Tuple
import json
# endregion
class ComplexityEffectInStocks(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100_000)  
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']	
    universe: List[str] = [
        'HON', 'MMM', 'VMI', 'MDU', 'SEB', 'GFF', 'VRTV', 'CODI', 'BBU', 'MATW', 'SPLP', 'CRESY', 'TRC', 'FIP', 'TUSK', 'RCMT', 'ALPP', 'NNBR', 'EFSH'
    ]
    
    market: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.period: int = 21
    self.quantile: int = 10
    self.leverage: int = 10
    self.selection_month: int = 6
    self.current_year: int = -1
    self.data: Dict[Symbol, deque[Tuple[datetime.date, float]]] = {}
    self.weight: Dict[Symbol, float] = {}
    self.long: List[str] = []
    self.short: List[str] = []
    self.selection_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    for ticker in universe:
        data: Equity = self.AddEquity(ticker, Resolution.Daily)
        data.SetLeverage(self.leverage)
    # load conglomerate segments percentages
    # DataSource: annual report from company's website or SEC website
    content: str = self.Download("data.quantpedia.com/backtesting_data/economic/conglomerate_revenue_segments.json")
    self.custom_data: Dict[str, dict] = json.loads(content)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the price every day
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            self.data[symbol].append((self.Time, stock.AdjustedPrice))

    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Symbol] = [
        x for x in fundamental
        if x.HasFundamentalData 
        and x.Market == 'usa'
        and x.SecurityReference.ExchangeId in self.exchange_codes
        and x.AssetClassification.MorningstarIndustryGroupCode != 0 
        and x.MarketCap != 0
    ]
    # warmup price rolling windows
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol in self.data:
            continue
        
        self.data[symbol] = deque(maxlen=self.period)
        history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet")
            continue
        data: Series = history.loc[symbol]
        for time, row in data.iterrows():
            if 'close' in row:
                self.data[symbol].append((time, row['close']))
    if self.current_year != self.Time.year and self.Time.month == self.selection_month:
        self.current_year = self.Time.year
    if len(selected) != 0:
        # create dataframe from saved prices
        industry_stocks: Dict[Symbol, List[float]] = {symbol: [i[1] for i in value] for symbol, value in self.data.items() if symbol in list(map(lambda x: x.Symbol, selected)) if len(self.data[symbol]) == self.data[symbol].maxlen}
        df_stocks: DataFrame = pd.DataFrame(industry_stocks, index=[i[0] for i in list(self.data.values())[0]])
        df_stocks = (df_stocks.iloc[-1] - df_stocks.iloc[0]) / df_stocks.iloc[0]
    # sort stocks on industry numbers
    symbols_by_industry: Dict[str, List[Symbol]] = {}
    for stock in selected:
        symbol: Symbol = stock.Symbol
        industry_group_code: MorningstarIndustryGroupCode = str(stock.AssetClassification.MorningstarIndustryGroupCode)
        if not industry_group_code in symbols_by_industry:
            symbols_by_industry[industry_group_code] = []
        symbols_by_industry[industry_group_code].append(symbol)
    # create pseudo conglomerates
    pseudo_conglomerates: Dict[str, float] = {}
    if not df_stocks.empty:
        for conglomerate, lst in self.custom_data.items():
            for year in lst:
                if year['year'] == str(self.current_year - 1):
                    for segment_data in year['codes']:
                        industry_code:str = segment_data.get('code')
                        if industry_code and not isinstance(industry_code, list):
                            if industry_code in symbols_by_industry and segment_data.get('percentage') is not None:
                                industry_stocks:List[Symbol] = symbols_by_industry[industry_code]
                                industry_stocks_perf:float = df_stocks[list([x for x in industry_stocks if x in df_stocks])].mean() * (segment_data['percentage'] / 100)
                                if not conglomerate in pseudo_conglomerates:
                                    pseudo_conglomerates[conglomerate] = 0
                                pseudo_conglomerates[conglomerate] += industry_stocks_perf
                        elif industry_code and isinstance(industry_code, list):
                            for ind_code in industry_code:
                                if ind_code in symbols_by_industry and segment_data.get('percentage') is not None:
                                    industry_stocks = symbols_by_industry[ind_code]
                                    industry_stocks_perf = df_stocks[list([x for x in industry_stocks if x in df_stocks])].mean() * ((segment_data['percentage'] / 2) / 100)
                                    if not conglomerate in pseudo_conglomerates:
                                        pseudo_conglomerates[conglomerate] = 0
                                    pseudo_conglomerates[conglomerate] += industry_stocks_perf
                
    # sort by conglomerate and divide to upper decile and lower decile
    if len(pseudo_conglomerates) >= self.quantile:
        sorted_by_conglomerates: List[str] = sorted(pseudo_conglomerates, key=pseudo_conglomerates.get, reverse=True)
        quantile: int = int(len(sorted_by_conglomerates) / self.quantile)
        self.long = sorted_by_conglomerates[:quantile]
        self.short = sorted_by_conglomerates[-quantile:]
    return list(map(lambda x: self.Symbol(x), self.long + self.short))

def OnData(self, data: Slice) -> None:
    # monthly rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()
def Selection(self) -> None:
    self.selection_flag = True
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
