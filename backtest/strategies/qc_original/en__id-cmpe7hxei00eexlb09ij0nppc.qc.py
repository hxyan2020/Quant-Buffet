# Original QuantConnect / library Python
# locale=en slug="离差交易"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
from numpy import floor
#endregion

class DispersionTrading(XXX):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(1000000)
    
    self.min_expiry:int = 20
    self.max_expiry:int = 60

    self.leverage:int = 5
    self.min_share_price:int = 5
    self.buying_power_model:int = 2
    
    self.index_symbol:Symbol = self.AddIndex('SPX').Symbol
    self.percentage_traded:float = 1.0
    
    self.selected_symbols:List[Symbol] = []
    self.subscribed_contracts = {}
    
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 100
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # rebalance on SPX contract expiration (should be on monthly basis)
    if len(self.selected_symbols) != 0:
        return Universe.Unchanged
    
    # select top n stocks by dollar volume
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.AdjustedPrice > self.min_share_price]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    self.selected_symbols = [x.Symbol for x in selected]

    return self.selected_symbols

def OnData(self, data: Slice) -> None:
    # liquidate portfolio, when SPX contract is about to expire in 2 days
    if self.index_symbol in self.subscribed_contracts and self.subscribed_contracts[self.index_symbol].ID.Date.date() - timedelta(2)  0:
                # sort by expiry
                atm_put:List[Symbol] = sorted(atm_puts, key = lambda item: item.ID.Date, reverse=True)[0]
                
                # add contract
                option = self.AddOptionContract(atm_put, Resolution.Minute)
                option.PriceModel = OptionPriceModels.CrankNicolsonFD()
                option.SetDataNormalizationMode(DataNormalizationMode.Raw)

                # store subscribed atm put contract
                self.subscribed_contracts[symbol] = atm_put
    
    # perform trade, when spx and stocks contracts are selected            
    if not self.Portfolio.Invested and len(self.subscribed_contracts) != 0 and self.index_symbol in self.subscribed_contracts:
        index_option_contract = self.subscribed_contracts[self.index_symbol]
        # make sure subscribed SPX contract has data
        if self.Securities.ContainsKey(index_option_contract):
            if self.Securities[index_option_contract].Price != 0 and self.Securities[index_option_contract].IsTradable:
                # sell SPX ATM put contract
                self.Securities[index_option_contract].MarginModel = BuyingPowerModel(self.buying_power_model)
                price:float = self.Securities[self.index_symbol].Price
                if price != 0:
                    q:int = floor((self.Portfolio.TotalPortfolioValue * self.percentage_traded) / (price*100))
                    self.Sell(index_option_contract, q)

                # buy stock's ATM put contracts            
                long_count:int = len(self.subscribed_contracts) - 1     # minus index symbol
                for stock_symbol, stock_option_contract in self.subscribed_contracts.items():
                    if stock_symbol == self.index_symbol:
                        continue
                    
                    if stock_option_contract in data and data[stock_option_contract]:
                        if self.Securities[stock_option_contract].Price != 0 and self.Securities[stock_option_contract].IsTradable:
                            # buy contract
                            self.Securities[stock_option_contract].MarginModel = BuyingPowerModel(self.buying_power_model)
                            if self.Securities.ContainsKey(stock_option_contract):
                                price:float = self.Securities[stock_symbol].Price
                                if price != 0:
                                    q:int = floor(((self.Portfolio.TotalPortfolioValue / long_count) * self.percentage_traded) / (price*100))
                                    self.Buy(stock_option_contract, q)

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
