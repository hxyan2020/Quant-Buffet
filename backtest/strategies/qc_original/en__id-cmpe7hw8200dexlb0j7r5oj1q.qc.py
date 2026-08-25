# Original QuantConnect / library Python
# locale=en slug="行业调整后的反转效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Dict, Set
from dateutil.relativedelta import relativedelta
from numpy import isnan
# endregion

class IndustryAdjustedReversal(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.exchange_codes:List[str] = ['NYS', 'AMEX', 'NAS']    

    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.leverage:int = 5
    self.quantile:int = 10
    self.monthly_period:int = 2

    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}

    self.current_month:int = -1
    self.rebalance_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if self.Time.month == self.current_month:
        return Universe.Unchanged
    self.current_month = self.Time.month

     # store monthly prices
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        if symbol in self.data:
            self.data[symbol].update_monthly_price(stock.AdjustedPrice)

    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' \
                    and x.MarketCap != 0 and not np.isnan(x.AssetClassification.MorningstarIndustryGroupCode) and x.AssetClassification.MorningstarIndustryGroupCode != 0 \
                    and x.SecurityReference.ExchangeId in self.exchange_codes]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # store stocks by industry code
    industries:Set[MorningstarIndustryGroupCode] = set([x.AssetClassification.MorningstarIndustryGroupCode for x in selected])
    grouped_industries:Dict[MorningstarIndustryGroupCode, List[Symbol]] = { industry : [stock.Symbol for stock in selected if stock.AssetClassification.MorningstarIndustryGroupCode == industry] for industry in industries }

    # sort stocks by industry numbers and price warmup
    ISR:Dict[Symbol, float] = {}
    for stock in selected:
        symbol:Symbol = stock.Symbol

        if symbol not in self.data:               
            self.data[symbol] = data_tools.SymbolData(self.monthly_period)

            history:DataFrame = self.History(symbol, start=self.Time.date() - relativedelta(months=1), end=self.Time.date()).unstack(level=0)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            history = history.close.groupby(pd.Grouper(freq='MS')).first()
            for time, close in history.iterrows():
                self.data[symbol].update_monthly_price(float(close.values))

        if self.data[symbol].is_ready():
            industry_return:float = np.mean([self.data[x].get_monthly_return() for x in grouped_industries[stock.AssetClassification.MorningstarIndustryGroupCode] if x in self.data and self.data[x].is_ready()])
            stock_return:float = self.data[symbol].get_monthly_return()
            ISR[stock] = stock_return - industry_return

    if len(ISR) >= self.quantile:
        sorted_symbols:List[Symbol] = sorted(ISR, key=ISR.get)
        quantile:int = len(ISR) // self.quantile
        long:List[Symbol] = sorted_symbols[:quantile]
        short:List[Symbol] = sorted_symbols[-quantile:]

        for i, portfolio in enumerate([long, short]):
            mc_sum:float = sum(list(map(lambda stock: stock.MarketCap, portfolio)))
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1)**i) / len(portfolio)
        
        self.rebalance_flag = True

    return list(self.weight.keys())

def OnData(self, data: Slice) -> None:
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False

    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
