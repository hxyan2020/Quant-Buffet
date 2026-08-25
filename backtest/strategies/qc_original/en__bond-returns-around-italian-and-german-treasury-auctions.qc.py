# Original QuantConnect / library Python
# locale=en slug="bond-returns-around-italian-and-german-treasury-auctions"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class BondReturnsAroundItalianAndGermanTreasuryAuctions(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2011, 1, 1)
    self.SetCash(100_000)
    
    leverage: int = 5
    self.symbols_by_country: Dict[str, Symbol] = {}
    
    tickers_by_country: Dict[str, str] = {
        'italy': 'EUREX_FGBL1',
        'germany': 'EUREX_FBTP1'
    }
    
    for country, ticker in tickers_by_country.items():
        data: Security = self.AddData(data_tools.QuantpediaFutures, ticker, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(leverage)
        self.symbols_by_country[country] = data.Symbol
    
    self.bond_auction_symbol: Symbol = self.AddData(data_tools.QuantpediaBondsAuction, 'IT_GE_bond_auction', Resolution.Daily).Symbol
def OnData(self, data: Slice) -> None:
    if self.Portfolio.Invested:
        self.Liquidate()
    
    long: List[Symbol] = []
    
    # check if at least one bond has auction
    if self.bond_auction_symbol in data and data[self.bond_auction_symbol]:
        for country, symbol in self.symbols_by_country.items():
            if any([self.securities[x].get_last_data() and self.time.date() > data_tools.LastDateHandler.get_last_update_date()[x] for x in [symbol, self.bond_auction_symbol]]):
                self.liquidate()
                return
            if symbol in data and data[symbol]:
                # store bonds with auction day
                if data[self.bond_auction_symbol].GetProperty(country) == 1:
                    long.append(symbol)
    # buy bonds with auction day
    for symbol in long:
        if data.contains_key(symbol) and data[symbol]:
            self.SetHoldings(symbol, 1 / len(long))
