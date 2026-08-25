# Original QuantConnect / library Python
# locale=en slug="商品中的期限结构效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *  
import numpy as np 

class CommodityTermStructureStrategy(QCAlgorithm):
'''
This class implements a commodity term structure trading strategy using QuantConnect's
algorithm trading platform. It focuses on trading a selection of commodity futures based on
their roll returns, aiming to capitalize on the term structure of commodity markets.
'''

def Initialize(self):
    '''
    Initializes the algorithm settings, including the start date, initial cash, and the futures
    contracts to be traded. Also sets up the algorithm's parameters like warm-up period,
    quintile for position sizing, and expiration day filters for contracts.
    '''
    
    self.SetStartDate(2009, 1, 1)  # Set the algorithm start date
    self.SetCash(100000)  # Set the initial cash for the algorithm

    # Define a dictionary of commodity symbols to be traded
    self.commodity_symbols = {
        'CME_S1': Futures.Grains.Soybeans,
        'CME_W1': Futures.Grains.Wheat,
        'CME_SM1': Futures.Grains.SoybeanMeal,
        'CME_C1': Futures.Grains.Corn,
        'CME_O1': Futures.Grains.Oats,
        'CME_LC1': Futures.Meats.LiveCattle,
        'CME_FC1': Futures.Meats.FeederCattle,
        'CME_LN1': Futures.Meats.LeanHogs,
        'CME_GC1': Futures.Metals.Gold,
        'CME_SI1': Futures.Metals.Silver,
        'CME_PL1': Futures.Metals.Platinum,
        'CME_HG1': Futures.Metals.Copper,
        'CME_LB1': Futures.Forestry.RandomLengthLumber,
        'CME_NG1': Futures.Energies.NaturalGas,
        'CME_PA1': Futures.Metals.Palladium,
        'CME_DA1': Futures.Dairy.ClassIIIMilk,
        'CME_RB1': Futures.Energies.Gasoline,
        'ICE_WT1': Futures.Energies.CrudeOilWTI,
        'ICE_CC1': Futures.Softs.Cocoa,
        'ICE_O1': Futures.Energies.HeatingOil,
        'ICE_SB1': Futures.Softs.Sugar11
    }

    self.SetWarmUp(252, Resolution.Daily)  # Set the warm-up period for the algorithm
    self.contract_info = {}  # Initialize a dictionary to store information about contracts
    self.quintile = 5  # Define the quintile for sorting contracts based on roll returns
    self.min_expiration_days = 2  # Set the minimum expiration days for a contract to be considered
    self.max_expiration_days = 360  # Set the maximum expiration days for a contract to be considered

    # Add futures contracts to the algorithm with the specified resolution and filter
    for symbol_key, future_symbol in self.commodity_symbols.items():
        self.AddFuture(future_symbol, Resolution.Daily).SetFilter(timedelta(days=self.min_expiration_days), timedelta(days=self.max_expiration_days))
        self.contract_info[symbol_key] = None  # Initialize contract information to None

    self.previous_month = -1  # Initialize the variable to track the previous month

def OnData(self, data):
    '''
    Called on each new data point. Checks if the algorithm is warmed up, updates the current month,
    and triggers rebalancing if a new month has started.
    '''
    
    if self.IsWarmingUp:  # Check if the algorithm is still in the warm-up period
        return  # If yes, do nothing

    current_month = self.Time.month  # Get the current month
    if current_month != self.previous_month:  # Check if the month has changed
        self.previous_month = current_month  # Update the previous month
        self.Rebalance(data)  # Trigger the rebalancing process

def Rebalance(self, data):
    '''
    Calculates roll returns for each future contract and rebalances the portfolio
    by going long in the top quintile and short in the bottom quintile based on roll returns.
    '''
    
    roll_returns = self.CalculateRollReturns(data)  # Calculate roll returns for all contracts
    
    if not roll_returns:  # Check if there are no roll returns
        return  # If yes, do nothing

    # Sort the symbols based on their roll returns
    sorted_symbols = sorted(roll_returns, key=roll_returns.get)
    
    # Determine the contracts to go long and short based on quintile
    to_long = sorted_symbols[-len(sorted_symbols) // self.quintile:]
    to_short = sorted_symbols[:len(sorted_symbols) // self.quintile]

    # Liquidate positions not in the long or short list
    for symbol in self.Portfolio.Keys:
        if self.Portfolio[symbol].Invested and symbol not in to_long + to_short:
            self.Liquidate(symbol)

    # Calculate the investment quantity based on the number of positions
    invest_quantity = 1 / len(to_long + to_short)
    
    # Go long and short in the selected contracts
    for symbol in to_long:
        self.SetHoldings(symbol, invest_quantity)
    for symbol in to_short:
        self.SetHoldings(symbol, -invest_quantity)

def CalculateRollReturns(self, data):
    '''
    Calculates the roll returns for all active future contracts available in the algorithm.
    Roll returns are calculated as the logarithm of the price ratio of the far contract to the near contract.
    '''
    
    roll_returns = {}  # Initialize a dictionary to store roll returns
    for future_symbol in self.commodity_symbols.values():  # Iterate over each future symbol
        contracts = self.ActiveContracts(future_symbol)  # Get active contracts for the symbol
        if len(contracts) >= 2:  # Ensure there are at least two contracts for comparison
            
            # Sort contracts by expiry and pick the nearest two
            near, far = sorted(contracts, key=lambda x: x.Expiry)[:2]
            
            # Check if both contracts have price data
            if near.Symbol in data and far.Symbol in data:
                near_price = data[near.Symbol].Price  # Get the near contract price
                far_price = data[far.Symbol].Price  # Get the far contract price
                
                # Ensure both prices are greater than zero before calculating roll return
                if near_price > 0 and far_price > 0:
                    roll_return = np.log(far_price / near_price)  # Calculate roll return
                    roll_returns[future_symbol] = roll_return  # Store the roll return
    
    return roll_returns  # Return the calculated roll returns

def ActiveContracts(self, future_symbol):
    '''
    Retrieves a list of active contracts for a given future symbol that are valid based on the
    algorithm's minimum expiration days criterion.
    '''
    
    # Get the list of future contracts for the symbol at the current time
    chains = self.FutureChainProvider.GetFutureContractList(future_symbol, self.Time)
    
    # Filter contracts based on the minimum expiration days criterion
    valid_contracts = [contract for contract in chains if contract.Expiry > self.Time + timedelta(days=self.min_expiration_days)]
    
    return valid_contracts  # Return the list of valid contracts
