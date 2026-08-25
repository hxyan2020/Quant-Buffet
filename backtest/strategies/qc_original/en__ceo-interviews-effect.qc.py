# Original QuantConnect / library Python
# locale=en slug="ceo-interviews-effect"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
import json
#endregion
class CEOInterviewsEffect(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1) # Interviews data starts in December 2006
    self.SetCash(100_000)
    self.UniverseSettings.Leverage = 10
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0
    self.settings.daily_precise_end_time = False

    self.holding_period: int = 10 # Days
    self.selection_flag: bool = False
    self.interviews_data: Dict[date, List[str]] = {}
    self.selected_securities: Dict[str, Symbol] = {}
    self.opened_short_positions_period: Dict[Symbol, int] = {}
    self.universe_tickers: Set(str) = set()
    
    url: str = 'data.quantpedia.com/backtesting_data/index/sp500_ceo_interviews.json'
    response: str = self.Download(url)
    ceo_interviews: List[Dict[str, str]] = json.loads(response)
    
    for interview_data in ceo_interviews:
        date: datetime.date = datetime.strptime(interview_data['date'], '%d.%m.%Y').date()
        self.interviews_data[date] = []
        for ticker in interview_data['tickers']:
            self.universe_tickers.add(ticker)
            self.interviews_data[date].append(ticker)
    self.market: Symbol = self.AddEquity('SPY', Resolution.Minute).Symbol
    self.Schedule.On(
        self.DateRules.MonthStart(self.market), 
        self.TimeRules.BeforeMarketClose(self.market), 
        self.Selection)
    self.Schedule.On(
        self.DateRules.EveryDay(self.market), 
        self.TimeRules.BeforeMarketClose(self.market, 1), 
        self.ManageTrade)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
      
    self.selected_securities = {
        f.Symbol.Value: f.Symbol for f in fundamental
        if f.Symbol.Value in self.universe_tickers
    }
    return list(self.selected_securities.values())
    
def ManageTrade(self) -> None:
    # Liquidate opened symbols
    symbols_to_remove: List[Symbol] = []
    rebalance_flag: bool = False
    
    for symbol in self.opened_short_positions_period:
        holding_period_remaining: int = self.opened_short_positions_period[symbol]
        if holding_period_remaining == 0:
            symbols_to_remove.append(symbol)
        else:
            self.opened_short_positions_period[symbol] -= 1
    
    for symbol in symbols_to_remove:
        rebalance_flag = True
        self.Liquidate(symbol)
        del self.opened_short_positions_period[symbol]
    # Storing symbol of stocks, which CEOs had interview today
    short_symbols: List[Symbol] = [] 
    curr_date: datetime.date = self.Time.date()
    
    if curr_date in self.interviews_data:
        tickers: List[str] = self.interviews_data[curr_date]
        for ticker in tickers:
            if ticker not in self.selected_securities:
                continue
            rebalance_flag = True
            symbol: Symbol = self.selected_securities[ticker]
            self.opened_short_positions_period[symbol] = self.holding_period
    
    if rebalance_flag:
        opened_shorts: int = len(self.opened_short_positions_period)
        if opened_shorts != 0:                
            # Rebalance whole trade selection alongside the hedge
            for symbol in self.opened_short_positions_period:
                price: float = self.Securities[symbol].Price
                if price != 0:
                    self.SetHoldings(symbol, -1 / opened_shorts)
            
            # Hedge with S&P500 future
            self.SetHoldings(self.market, 1)
        else:
            # Liquidate hedge
            self.Liquidate(self.market)
def Selection(self) -> None:
    self.selection_flag = True
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
