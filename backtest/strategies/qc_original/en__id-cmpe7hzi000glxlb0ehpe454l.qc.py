# Original QuantConnect / library Python
# locale=en slug="中国股市中的价值与盈利能力相关策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
# endregion

class ValueAndProfitabilityInChineseEquities(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    # https://www.tradingview.com/markets/stocks-hong-kong/market-movers-large-cap/
    self.tickers:list[str] = [
        '0700', '3690', '1299', '9618', '9633', '0388', '2388', '1024', '1810', '0016', 
        '0011', '0066', '1876', '0688', '1109', '0267', '2020', '2269', '0960', '0001',
        '1113', '0002', '0981', '0669', '0027', '2057', '2015', '2328', '0003', '0788',
        '2319', '0020', '0012',
        '0001', '0004', '0006', '0017', '0019', '0083', '0101', '0135', '0144', '0151', 
        '0175', '0241', '0268', '0270', '0288', '0291', '0316', '0322', '0384', '0489',
        '0586', '0656', '0762', '0836', '0868', '0881', '0883', '0916', '0968', '0992', 
        '1038', '1044', '1093', '1099', '1177', '1179', '1193', '1209', '1299', '1308', 
        '1359', '1378', '1821', '1913', '1928', '1929', '1972', '1997', '2007', '2066', 
        '2313', '2331', '2382', '2618', '2638', '2688', '3311', '3323', '3692', '3799', 
        '3800', '6098', '6186', '6618', '6823', '6862', '6969', '9889', '9961',
    ]

    self.quantile:int = 3
    self.leverage:int = 5
    self.max_missing_statement_days:int = 3*30

    # fundamental symbols
    self.income_statement_symbols:dict[Symbol] = {}
    self.balance_statement_symbols:dict[Symbol] = {}
    
    for ticker in self.tickers:
        # price data
        data = self.AddData(data_tools.HongKongStocks, ticker, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)

        # fundamental symbols
        self.income_statement_symbols[data.Symbol] = self.AddData(data_tools.HongKongIncomeStatement, ticker, Resolution.Daily).Symbol
        self.balance_statement_symbols[data.Symbol] = self.AddData(data_tools.HongKongBalanceSheetStatement, ticker, Resolution.Daily).Symbol

    self.recent_month:int = -1

def OnData(self, data: Slice) -> None:
    measure_dict:dict[str, list] = {} # dict of lists with measure values
    market_cap:dict[str, float] = {}
    rebalance_flag:bool = False

    for symbol in self.income_statement_symbols:
        income_symbol:Symbol = self.income_statement_symbols[symbol]
        balance_symbol:Symbol = self.balance_statement_symbols[symbol]

        if self.Time.month == self.recent_month:
            break

        if data.ContainsKey(symbol):
            if self.Securities[income_symbol].GetLastData() and (self.Time.date() - self.Securities[income_symbol].GetLastData().Time.date()).days = self.quantile:
        measurement_count:int = 6
        avg_rank:dict[str, int] = {}

        # rank stocks by every measure
        for i in range(measurement_count):
            i_measures:dict = { symbol : x[1] for symbol, x in measure_dict.items() }
            sorted_by_measure:list = [x[0] for x in sorted(i_measures.items(), key=lambda x: x[1], reverse=False)]
            for i, symbol in enumerate(sorted_by_measure):
                # add current rank to total rank first
                if symbol not in avg_rank:
                    avg_rank[symbol] = 0
                avg_rank[symbol] += i+1

        # calculate average rank
        avg_rank = { symbol : x / measurement_count for symbol, x in avg_rank.items() }

        # sort by average rank
        sorted_by_avg_rank:list = sorted(avg_rank.items(), key=lambda x:x[1], reverse=True)
        quantile:int = int(len(sorted_by_avg_rank) / self.quantile)
        long:list[str] = [x[0] for x in sorted_by_avg_rank[:quantile]]
        short:list[str] = [x[0] for x in sorted_by_avg_rank[-quantile:]]

        # market cap weighting
        total_mc_long:float = sum([market_cap[x] for x in long])
        total_mc_short:float = sum([market_cap[x] for x in short])
        
        for symbol in long:
            weights[symbol] = market_cap[symbol] / total_mc_long
        for symbol in short:
            weights[symbol] = -market_cap[symbol] / total_mc_short

    # trade execution
    invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in weights:
            self.Liquidate(symbol)
            
    for symbol, w in weights.items():
        self.SetHoldings(symbol, w)
