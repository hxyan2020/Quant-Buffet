# Original QuantConnect / library Python
# locale=en slug="波动率风险溢价效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class ExploitVolatilityRiskPremium(XXX):
'''
A strategy that exploits the volatility risk premium in the SPY ETF. It involves selling at-the-money straddles,
buying out-of-the-money puts for protection, and investing in the SPY ETF with remaining funds.
'''

def Initialize(self):
    '''
    Initializes the algorithm settings, including start date, initial cash, equity, and options.
    Sets leverage for the equity and filters for the option chain.
    '''
    
    self.SetStartDate(2012, 1, 1)  # Set the backtest start date
    self.SetCash(100000)  # Set the initial cash for the backtest
    
    equity = self.AddEquity("SPY", Resolution.Minute)  # Add SPY ETF as an equity with minute resolution
    equity.SetLeverage(5)  # Set leverage for the equity
    self.spy_symbol = equity.Symbol  # Save the SPY symbol for later use
    
    option_contract = self.AddOption("SPY", Resolution.Minute)  # Add SPY option with minute resolution
    option_contract.SetFilter(-20, 20, 30, 60)  # Set a filter for strike price range and expiration days
    
    self.prev_day = -1  # Initialize a variable to track the previous day processed
    
def OnData(self, data):
    '''
    Executes the trading logic once per day when new data is received.
    Sells at-the-money straddles, buys out-of-the-money puts for protection,
    and allocates remaining funds to SPY ETF.
    '''
    
    # Execute logic once per day
    if self.Time.day == self.prev_day:
        return  # Skip if already processed this day
    self.prev_day = self.Time.day  # Update the previous day processed
        
    for option_chain in data.OptionChains:  # Iterate through each option chain in the data
        chains = option_chain.Value  # Get the actual option chain

        if not self.Portfolio.Invested:  # Check if the portfolio is not yet invested
            calls = [opt for opt in chains if opt.Right == OptionRight.Call]  # Filter for call options
            puts = [opt for opt in chains if opt.Right == OptionRight.Put]  # Filter for put options
            
            if not calls or not puts:
                return  # Skip if no calls or puts available
        
            market_price = self.Securities[self.spy_symbol].Price  # Get the current market price of SPY
            expiry_dates = [opt.Expiry for opt in puts]  # Get expiry dates for puts
            
            # Choose the expiry close to one month away
            chosen_expiry = min(expiry_dates, key=lambda x: abs((x - self.Time).days - 30))
            strike_prices = [opt.Strike for opt in puts]  # Get strike prices for puts
            
            # Select the at-the-money (ATM) strike
            atm_strike = min(strike_prices, key=lambda x: abs(x - market_price))
            
            # Select the 15% out-of-the-money (OTM) put strike
            otm_put_strike = min(strike_prices, key=lambda x: abs(x - 0.85 * market_price))
    
            atm_calls = [opt for opt in calls if opt.Expiry == chosen_expiry and opt.Strike == atm_strike]  # Filter for ATM calls
            atm_puts = [opt for opt in puts if opt.Expiry == chosen_expiry and opt.Strike == atm_strike]  # Filter for ATM puts
            otm_puts = [opt for opt in puts if opt.Expiry == chosen_expiry and opt.Strike == otm_put_strike]  # Filter for OTM puts
    
            if atm_calls and atm_puts and otm_puts:
                qty = int(self.Portfolio.MarginRemaining / (market_price * 100))  # Calculate quantity to trade

                # Sell ATM straddle (both call and put)
                self.Sell(atm_calls[0].Symbol, qty)
                self.Sell(atm_puts[0].Symbol, qty)
                
                # Buy OTM put as a protective measure
                self.Buy(otm_puts[0].Symbol, qty)
                
                # Allocate remaining funds to SPY ETF
                self.SetHoldings(self.spy_symbol, 1)
    
        # Liquidate SPY holding if it's the only position left
        if len([x.Key for x in self.Portfolio if x.Value.Invested]) == 1:
            self.Liquidate(self.spy_symbol)
