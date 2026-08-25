# Original QuantConnect / library Python
# locale=en slug="用期权gamma预测股票回报策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
# endregion

class OptionGammaPredictsStockReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100_000)
    
    self.leverage: int = 5
    self.quantile: int = 10

    self.min_contracts: int = 3
    self.one_stock_contracts: int = 6 * self.min_contracts

    self.min_expiry: int = 35
    self.max_expiry: int = 360

    self.exchanges: List[str] = ['NYS', 'NAS', 'ASE']

    self.market_cap: Dict[Symbol, float] = {}
    self.subscribed_options: List[OptionContract] = []
    self.symbols_by_tickers: Dict[str, Symbol] = {}

    self.market_symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.fundamental_count: int = 300
    self.fundamental_sorting_key = lambda x: x.MarketCap

    self.selection_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw

    self.Schedule.On(self.DateRules.MonthStart(self.market_symbol), self.TimeRules.BeforeMarketClose(self.market_symbol, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged

    selected: List[Fundamental] = [
        f for f in fundamental if f.HasFundamentalData and \
        f.MarketCap != 0 and \
        f.SecurityReference.ExchangeId in self.exchanges
    ]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    self.subscribed_options.clear()
    self.market_cap = { stock.Symbol: stock.MarketCap for stock in selected }

    return list(self.market_cap.keys()) 

def OnData(self, data: Slice) -> None:
    if self.selection_flag:
        self.selection_flag = False
        self.Liquidate()

        for symbol in self.market_cap:
            # subscribe to contract
            contracts: List[Symbol] = self.OptionChainProvider.GetOptionContractList(symbol, self.Time)
            underlying_price: float = self.Securities[symbol].Price
            
            strikes: List[float] = [i.ID.StrikePrice for i in contracts]
            
            if len(strikes) = self.min_contracts for x in [atm_calls, atm_puts, itm_calls, itm_puts, otm_calls, otm_puts]):
                continue
            
            # store stock's symbol under it's ticker, because it is the only possibility how to access it from option contract
            self.symbols_by_tickers[symbol.Value] = symbol

            # sort by expiry and subscribe n nearest contracts
            for selected_contracts in [atm_calls, atm_puts, itm_calls, itm_puts, otm_calls, otm_puts]:
                nearest_contracts: List[Symbol] = sorted(selected_contracts, key=lambda item: item.ID.Date)[:self.min_contracts]

                for contract in nearest_contracts:
                    option: OptionContract = self.AddOptionContract(contract, Resolution.Daily)
                    option.PriceModel = OptionPriceModels.CrankNicolsonFD()

                    # after trade execution subscribed options will be unsubscribed,
                    # to stop receiving unncessary data, which slows down strategy
                    self.subscribed_options.append(option)

    if len(self.symbols_by_tickers) != 0 and data.OptionChains.Count != 0:
        gamma_weighted_sum: Dict[Symbol, float] = {}
        
        for kvp in data.OptionChains:
            chain: OptionChain = kvp.Value
            ticker: str = chain.Underlying.Symbol.Value
            if ticker not in self.symbols_by_tickers:
                continue

            symbol: Symbol = self.symbols_by_tickers[ticker]
            contracts: List[OptionContract] = [x for x in chain]
            
            # check if there are enough contracts for option
            if len(contracts)  List[Symbol]:
    return [i for i in contracts if i.ID.OptionRight == option_right \
        and i.ID.StrikePrice == strike and self.min_expiry  None:
    self.selection_flag = True

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
