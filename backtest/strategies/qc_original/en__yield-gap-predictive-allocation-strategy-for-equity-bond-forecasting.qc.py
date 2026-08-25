# Original QuantConnect / library Python
# locale=en slug="yield-gap-predictive-allocation-strategy-for-equity-bond-forecasting"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from collections import deque  # Import deque from collections for efficient queue operations
from AlgoLib import *  # Import all functions and classes from AlgoLib
import numpy as np  # Import numpy for numerical operations
from scipy import stats  # Import stats from scipy for statistical functions

class FED_Model(XXX):
'''
FED_Model is a quantitative trading model that makes investment decisions based on the
Federal Reserve Economic Data (FRED). It uses various economic indicators to predict market
movement and adjust portfolio holdings accordingly.
'''

def Initialize(self):
    '''
    Initialize the algorithm settings, symbols, and indicators used in the model.
    '''
    
    self.SetStartDate(2000, 1, 1)  # Set the start date of the algorithm
    self.SetCash(100000)  # Set the initial cash for the algorithm
    self.data = {}  # Initialize an empty dictionary to store data
    self.period = 12 * 21  # Set the period for warm-up in days (approx. 12 months)
    self.SetWarmUp(self.period)  # Set the warm-up period of the algorithm
    self.market = self.AddEquity('SPY', Resolution.Daily).Symbol  # Add S&P 500 ETF and get its symbol
    self.market_data = deque()  # Initialize a deque to store market data
    self.cash = self.AddEquity('SHY', Resolution.Daily).Symbol  # Add short-term treasury ETF and get its symbol
    self.risk_free_rate = self.AddData(QuandlValue, 'FRED/DGS3MO', Resolution.Daily).Symbol  # Add 3-month Treasury bill rate as risk-free rate
    self.bond_yield = self.AddData(QuantpediaBondYield, 'US10YT', Resolution.Daily).Symbol  # Add 10-year Treasury yield data
    self.sp_earnings_yield = self.AddData(QuandlValue, 'MULTPL/SP500_EARNINGS_YIELD_MONTH', Resolution.Daily).Symbol  # Add S&P 500 earnings yield data
    self.yield_gap = deque()  # Initialize a deque to store yield gap data
    self.recent_month = -1  # Initialize recent_month to track the month of the last rebalance

def OnData(self, data):
    '''
    Event handler for new data. This method decides whether to rebalance the portfolio based on
    new data and the model's indicators.
    '''
    
    rebalance_flag = False  # Initialize the rebalance flag to False
    if self.sp_earnings_yield in data and data[self.sp_earnings_yield]:
        
        # Check if there's new earnings yield data
        if self.Time.month != self.recent_month:
            
            # If it's a new month since last checked
            self.recent_month = self.Time.month  # Update the recent month
            rebalance_flag = True  # Set the rebalance flag to True
    
    if not rebalance_flag:
        
        # If not already set to rebalance
        if self.Securities[self.sp_earnings_yield].GetLastData():
            
            # If there's last data for earnings yield
            if (self.Time.date() - self.Securities[self.sp_earnings_yield].GetLastData().Time.date()).days > 31:
                
                # If it's been more than 31 days since the last data, liquidate the portfolio
                self.Liquidate()
        
        if self.market in data and self.risk_free_rate in data and self.bond_yield in data:
            
            # If there's new data for market, risk-free rate, and bond yield
            if data[self.market] and data[self.risk_free_rate] and data[self.bond_yield]:
                
                # Extract values for market price, risk-free rate, bond yield, and S&P earnings yield
                market_price = data[self.market].Value
                rf_rate = data[self.risk_free_rate].Value
                bond_yield = data[self.bond_yield].Value
                sp_ey = data[self.sp_earnings_yield].Value
                
                if market_price != 0 and rf_rate != 0 and bond_yield != 0 and sp_ey != 0:
                    
                    # If all values are non-zero, append to their respective deques
                    self.market_data.append((market_price, rf_rate))
                    yield_gap = np.log(sp_ey) - np.log(bond_yield)
                    self.yield_gap.append(yield_gap)
                    rebalance_flag = True  # Set the rebalance flag to True
    
    min_count = 6  # Set the minimum count for rebalancing
    
    if len(self.market_data) >= min_count:
        
        # If there's enough market data
        market_closes = np.array([x[0] for x in self.market_data])  # Get market close prices
        market_returns = (market_closes[1:] - market_closes[:-1]) / market_closes[:-1]  # Calculate market returns
        rf_rates = np.array([x[1] for x in self.market_data][1:])  # Get risk-free rates
        excess_returns = market_returns - rf_rates  # Calculate excess returns
        yield_gaps = [x for x in self.yield_gap]  # Get yield gaps
        
        # Perform linear regression between yield gaps and market returns
        beta, alpha, r_value, p_value, std_err = stats.linregress(yield_gaps[1:-1], market_returns[1:])
        
        X = yield_gaps[-1]  # Get the latest yield gap
        Y = alpha + (beta * X)  # Calculate the predicted return
        
        if Y > 0:
            
            # If predicted return is positive, invest in the market
            if self.Portfolio[self.cash].Invested:
                self.Liquidate(self.cash)  # Liquidate cash position
            self.SetHoldings(self.market, 1)  # Set holdings to market
        
        else:
            
            # If predicted return is negative, move to cash
            if self.Portfolio[self.market].Invested:
                self.Liquidate(self.market)  # Liquidate market position
            self.SetHoldings(self.cash, 1)  # Set holdings to cash
