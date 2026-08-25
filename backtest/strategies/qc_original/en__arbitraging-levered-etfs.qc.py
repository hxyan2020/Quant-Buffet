# Original QuantConnect / library Python
# locale=en slug="arbitraging-levered-etfs"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List, Set
from data_tools import CustomFeeModel, TradePair, SymbolData
# endregion

class ArbitragingLeveredETFs(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.corr_threshold:float = 0.5

    self.period:int = 12 * 21
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.trades:List[List[Symbol, float]] = []

    self.l_etfs:Dict[str, float] = {}

    l_etf_tickers_csv:str = self.Download('data.quantpedia.com/backtesting_data/equity/leveraged_etf_tickers.csv')
    lines:List[str] = l_etf_tickers_csv.split('\r\n')

    for line in lines[1:]:
        if line == '':
            continue

        line_split:List[str] = line.split(';')
        ticker:str = line_split[0]
        leverage:float = float(line_split[-1])

        self.l_etfs[ticker] = leverage
    
    etf_tickers_csv:str = self.Download('data.quantpedia.com/backtesting_data/equity/not_leveraged_etf_tickers.csv')
    lines:List[str] = etf_tickers_csv.split('\r\n')
    self.etfs:List[str] = { ticker: 1 for ticker in lines[1:] if ticker != '' }

    self.market_symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    
    self.Schedule.On(self.DateRules.MonthStart(self.market_symbol), self.TimeRules.BeforeMarketClose(self.market_symbol, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        if symbol in self.data:
            self.data[symbol].update_prices(stock.AdjustedPrice)
    
    if not self.selection_flag:
        return Universe.Unchanged

    selected_leveraged_symbols:List[Symbol] = []
    selected_symbols:List[Symbol] = []

    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        ticker:str = symbol.Value

        if ticker in self.etfs:
            selected_symbols.append(symbol)

        elif ticker in self.l_etfs:
            selected_leveraged_symbols.append(symbol)

        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history:pd.DataFrame = self.History(symbol, self.period, Resolution.Daily)

            if history.empty:
                continue

            closes:pd.Series = history.loc[symbol].close

            for _, close in closes.items():
                self.data[symbol].update_prices(close)

    trade_pairs:List[TradePair] = []
    symbols_to_trade:Set[Symbol] = set()
    abs_corr_by_symbol:Dict[Symbol, Tuple] = {}

    # pair each LETF to the ETF and calculate their correlation based on daily returns in one year
    for l_symbol in selected_leveraged_symbols:
        if not self.data[l_symbol].is_ready():
            continue

        leveraged_daily_returns:np.array = self.data[l_symbol].get_daily_returns()

        for symbol in selected_symbols:
            if not self.data[symbol].is_ready():
                continue

            daily_returns:np.array = self.data[symbol].get_daily_returns()

            correlation:float = np.corrcoef(leveraged_daily_returns, daily_returns)[0][-1]

            # make sure correlation is greater than threshold
            abs_corr:float = abs(correlation)
            if abs_corr >= self.corr_threshold:
                if (l_symbol not in abs_corr_by_symbol) or \
                    (l_symbol in abs_corr_by_symbol and abs_corr > abs_corr_by_symbol[l_symbol][1]):
                    # go short (long) on ETF, when correlation is negative (positive)
                    short_signal:bool = True if correlation  None:
    if not self.selection_flag:
        return
    self.selection_flag = False

    self.Liquidate()

    for symbol, quantity in self.trades:
        self.MarketOrder(symbol, quantity)

    self.trades.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
