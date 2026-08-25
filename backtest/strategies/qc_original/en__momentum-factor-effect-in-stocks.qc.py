# Original QuantConnect / library Python
# locale=en slug="momentum-factor-effect-in-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *  # Import QuantConnect library components
# Additional imports
from typing import Dict, List  # Import typing support for variable annotations
import pandas as pd  # Import pandas for data manipulation

class StockMomentumStrategy(QCAlgorithm):
'''
This class implements a stock momentum strategy using QuantConnect. It aims to select and trade stocks based on their momentum, considering various factors like market cap, trading volume, and fundamental data.
'''

def Initialize(self):
    '''
    Initializes the algorithm settings, including start date, initial cash, security resolution, and other parameters relevant to the strategy.
    '''
    
    self.SetStartDate(2000, 1, 1)  # Set start date of the algorithm
    self.SetCash(100000)  # Set initial cash for the algorithm
    self.AddEquity('SPY', Resolution.Daily).Symbol  # Add S&P 500 ETF as a security

    self.momentum_weights: Dict[Symbol, float] = {}  # Dictionary to hold the momentum weights of stocks
    self.price_history: Dict[Symbol, RollingWindow] = {}  # Dictionary to hold the price history of stocks
    self.analysis_period: int = 252  # Set the period for momentum analysis (approx. 12 months)
    self.tier_count: int = 5  # Number of tiers to divide stocks into based on momentum
    self.max_leverage: int = 5  # Set the maximum leverage
    self.market_codes: List[str] = ['NYSE', 'NASDAQ', 'AMEX']  # List of market codes to consider for stock selection

    self.max_stocks: int = 500  # Maximum number of stocks to consider for the universe
    self.sort_key = lambda x: x.Volume  # Key for sorting stocks based on volume

    self.previous_month: int = -1  # Variable to track the previous month
    self.is_selection_time: bool = False  # Flag to indicate if it's time to select stocks
    self.UniverseSettings.Resolution = Resolution.Daily  # Set the resolution for the universe selection
    self.AddUniverse(self.SelectStocks)  # Add universe selection method
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0  # Set minimum margin

def OnSecuritiesChanged(self, changes: SecurityChanges):
    '''
    This method is called whenever there are changes in the securities in the universe. It sets the fee model and leverage for added securities.
    '''
    
    for security in changes.AddedSecurities:
        security.SetFeeModel(StandardFeeModel())  # Set the fee model for the security
        security.SetLeverage(self.max_leverage)  # Set the leverage for the security

def SelectStocks(self, fundamental_data: List[Fundamental]) -> List[Symbol]:
    '''
    Selects stocks based on fundamental data and calculates their momentum scores. It creates a universe of stocks to be traded.
    '''
    
    if not self.is_selection_time:
        return Universe.Unchanged  # Return unchanged universe if it's not selection time

    # Filter stocks based on fundamental data and market cap
    eligible_stocks = [x for x in fundamental_data if x.HasFundamentalData and x.MarketCap > 0 and x.Exchange in self.market_codes]

    # Limit the number of stocks to the maximum allowed
    if len(eligible_stocks) > self.max_stocks:
        eligible_stocks = sorted(eligible_stocks, key=self.sort_key, reverse=True)[:self.max_stocks]

    # Calculate momentum scores for eligible stocks
    for stock in eligible_stocks:
        symbol = stock.Symbol
        if symbol not in self.price_history:
            self.price_history[symbol] = RollingWindow[float](self.analysis_period)
            history = self.History(symbol, self.analysis_period, Resolution.Daily)
            if history.empty:
                self.Log(f"Insufficient data for {symbol}")
                continue
            for close_price in history.loc[symbol].close:
                self.price_history[symbol].Add(close_price)

    momentum_scores = {s.Symbol: self.price_history[s.Symbol][0] / self.price_history[s.Symbol][-1] - 1 for s in eligible_stocks if self.price_history[s.Symbol].IsReady}

    # Select stocks for buying and selling based on momentum scores
    if len(momentum_scores) >= self.tier_count:
        sorted_symbols = sorted(momentum_scores, key=momentum_scores.get)
        tier_size = len(sorted_symbols) // self.tier_count
        to_buy = sorted_symbols[-tier_size:]
        to_sell = sorted_symbols[:tier_size]

        for portfolio, symbols in enumerate([to_buy, to_sell]):
            for symbol in symbols:
                self.momentum_weights[symbol] = ((-1) ** portfolio) / len(symbols)

    return list(self.momentum_weights.keys())

def OnData(self, data: Slice):
    '''
    This method is called with each new data slice. It checks if it's time to adjust the portfolio based on the selected stocks and their weights.
    '''
    
    if self.previous_month != self.Time.month:
        self.previous_month = self.Time.month
        self.is_selection_time = True
        return

    if not self.is_selection_time:
        return

    self.is_selection_time = False
    targets = [PortfolioTarget(symbol, weight) for symbol, weight in self.momentum_weights.items() if symbol in data]
    self.SetHoldings(targets, True)  # Adjust holdings based on momentum weights
    self.momentum_weights.clear()  # Clear the weights after adjustments

class StandardFeeModel(FeeModel):
'''
Custom fee model class that calculates the order fee based on the transaction size.
'''

def GetOrderFee(self, parameters: OrderFeeParameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.0001  # Calculate fee based on price and quantity
    return OrderFee(CashAmount(fee, "USD"))  # Return the calculated fee
