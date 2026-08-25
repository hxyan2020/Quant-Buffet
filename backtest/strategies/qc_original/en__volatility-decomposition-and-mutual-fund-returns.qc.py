# Original QuantConnect / library Python
# locale=en slug="volatility-decomposition-and-mutual-fund-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
from itertools import combinations
#endregion

class VolatilityDecompositionandMutualFundReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.period:int = 3 * 21
    self.quantile:int = 5
    self.leverage:int = 5
    self.price_data:dict[Symbol, RollingWindow] = {}
    
    self.holdings_by_fund:dict[str, FundHoldings] = {}
    self.ticker_universe:set = set()  # every ticker stored in hedge fund holdings data
    self.weight:dict[Symbol, float] = {}

    hedge_fund_file_content:str = self.Download('data.quantpedia.com/backtesting_data/equity/hedge_fund_holdings/hedge_funds_holdings.json')
    hedge_funds_data:dict = json.loads(hedge_fund_file_content)

    for index, hedge_fund_data in enumerate(hedge_funds_data):
        hedge_fund_names:list[str] = list(hedge_fund_data.keys())
        hedge_fund_names.remove('date')
        date:datetime.date = datetime.strptime(hedge_fund_data['date'], '%d.%m.%Y').date()

        for hedge_fund_name in hedge_fund_names:
            if hedge_fund_name not in self.holdings_by_fund:
                self.holdings_by_fund[hedge_fund_name] = FundHoldings(hedge_fund_name)

            holding_list:list[StockHolding] = []
            holdings:list[dict] = hedge_fund_data[hedge_fund_name]['stocks']
            for holding in holdings:
                ticker:str = holding['ticker']
                number_of_shares:int = int(holding['#_of_shares'])
                weight:float = float(holding['weight'])

                self.ticker_universe.add(ticker)

                holding_list.append(StockHolding(ticker, number_of_shares, weight))
            
            self.holdings_by_fund[hedge_fund_name].update_holdings_by_date(date, holding_list)

    self.selection_flag:bool = False
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.BeforeMarketClose(self.market), self.Selection)

def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse):
    # store daily prices
    for stock in coarse:
        symbol:Symbol = stock.Symbol
        ticker:str = symbol.Value

        if ticker in self.ticker_universe:
            if symbol in self.price_data:
                self.price_data[symbol].Add(stock.AdjustedPrice)
        
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:list[Symbol] = [x.Symbol for x in coarse if x.Symbol.Value in self.ticker_universe]

    # warmup price rolling windows
    for symbol in selected:
        if symbol in self.price_data:
            continue
        
        self.price_data[symbol] = RollingWindow[float](self.period)
       
        history:pd.DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            continue

        closes = history.loc[symbol].close
        for time, close in closes.iteritems():
            self.price_data[symbol].Add(close)

    return [x for x in selected if self.price_data[x].IsReady]

def FineSelectionFunction(self, fine):
    symbol_by_ticker:dict[str, Symbol] = {x.Symbol.Value : x.Symbol for x in fine}

    # get previous month's holdings
    prev_month:datetime = self.Time.date() - timedelta(days=self.Time.day) - relativedelta(months=2)

    portfolio_volatility:dict[str, float] = {}
    covariance_average:dict[str, float] = {}

    for fund in self.holdings_by_fund:
        if prev_month in self.holdings_by_fund[fund].holdings_by_date:
            # previous month's holdings for fund performance calculation
            prev_months_holdings = self.holdings_by_fund[fund].holdings_by_date[prev_month]
            
            # calculate portfolio volatility and weighted average of constituent holdings’ covariances
            p_vol:float = 0.
            cov_avg:float = 0.

            n = len(prev_months_holdings)
            if n > 2:
                for i_holding in prev_months_holdings:
                    i_ticker:str = i_holding.ticker
                    i_weight:float = i_holding.weight / 100
                    
                    for j_holding in prev_months_holdings:
                        j_ticker:str = j_holding.ticker
                        j_weight:float = j_holding.weight / 100

                        # both price series are ready
                        if i_ticker in symbol_by_ticker and j_ticker in symbol_by_ticker:
                            x:np.ndarray = np.array([[x for x in self.price_data[symbol_by_ticker[i_ticker]]], [x for x in self.price_data[symbol_by_ticker[j_ticker]]]])
                            cov:float = np.cov(x)[0][1]

                            # covariance average
                            if i_holding != j_holding:
                                cov_avg += (i_weight * j_weight * cov)
                            
                            # portfolio volatility
                            p_vol += (i_weight * j_weight * cov)
            
            if p_vol != 0 and cov_avg != 0:
                portfolio_volatility[fund] = p_vol
                covariance_average[fund] = cov_avg

    if len(portfolio_volatility) >= self.quantile:
        # pick bottom funds
        quantile:int = int(len(portfolio_volatility) / self.quantile)

        sorted_by_volatility = sorted(portfolio_volatility.items(), key = lambda x: x[1], reverse=True)
        bottom_by_volatility:list = [x[0] for x in sorted_by_volatility][-quantile:]
        
        sorted_by_covariance = sorted(covariance_average.items(), key = lambda x: x[1], reverse=True)
        bottom_by_covariance:list = [x[0] for x in sorted_by_covariance][-quantile:]

        # hold fund constituents instead of fund etfs
        fund_c:int = len(bottom_by_volatility + bottom_by_covariance)
        for fund in bottom_by_volatility + bottom_by_covariance:
            holdings = self.holdings_by_fund[fund].holdings_by_date[prev_month]
            for holding in prev_months_holdings:
                ticker:str = holding.ticker
                weight:float = holding.weight / 100
                if ticker in symbol_by_ticker:
                    self.weight[symbol_by_ticker[ticker]] = (1 / fund_c) * weight
    
    return list(self.weight.keys())

def OnData(self, data):
    if not self.selection_flag:
        return
    self.selection_flag = False

    invested:list[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.weight:
            self.Liquidate(symbol)
    
    for symbol, w in self.weight.items():
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, w)

    self.weight.clear()

def Selection(self):
    # rabalance once a quarter
    if self.Time.month % 3 == 0:
        self.selection_flag = True

class StockHolding():
def __init__(self, ticker:str, n_of_shares:int, weight:float):
    self.ticker:str = ticker
    self.n_of_shares:int = n_of_shares
    self.weight:float = weight

class FundHoldings():
def __init__(self, fund_name:str):
    self.fund_name:str = fund_name
    self.holdings_by_date:dict[datetime, list[StockHolding]] = {}

def update_holdings_by_date(self, date:datetime.date, holdings:list):
    self.holdings_by_date[date] = holdings

# Custom fee model
class CustomFeeModel():
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
