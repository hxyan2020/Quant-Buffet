# Original QuantConnect / library Python
# locale=zh slug="etf-动量策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class ETFMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2008, 1, 1)
    self.SetCash(100000)
    self.market = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # Daily ROC data with market cap.
    self.data = {}
    self.period = 36 * 21
    self.SetWarmUp(self.period)
    
    # Data source: https://etfdb.com/screener/#page=4&tab=overview&sort_by=assets&sort_direction=desc&asset_class=equity&regions=U.S.&inception_on_start=2005-01-01&inception_on_end=2020-09-01
    csv_string_file = self.Download('data.quantpedia.com/backtesting_data/economic/us_equities.csv')
    
    # header: symbol;etf_name;total_assets_mm;previous_closing_price
    lines = csv_string_file.split('\r\n')
    for line in lines[1:]:
        line_split = line.split(';')
        
        etf_symbols = line_split[0]
        market_cap = float(line_split[2])  # $MM
        last_price = float(line_split[3])
        
        if market_cap > 20 and last_price > 1:
            data = self.AddEquity(etf_symbols, Resolution.Daily)
            data.SetLeverage(5)
            
            self.data[etf_symbols] = (self.ROC(etf_symbols, self.period, Resolution.Daily), market_cap)
            
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Rebalance)
    
def Rebalance(self):
    performance = {x : self.data[x][0].Current.Value for x in self.data if self.data[x][0].IsReady}
    sorted_by_performance = sorted(performance.items(), key = lambda x: x[1], reverse = True)
    decile = int(len(sorted_by_performance) / 10)
    
    # Symbol, market cap tuples.
    long = [(x[0], self.data[x[0]][1]) for x in sorted_by_performance[:decile]]
    short = [(x[0], self.data[x[0]][1]) for x in sorted_by_performance[-decile:]]
    
    # Market cap weighting.
    weight = {}
    total_market_cap_long = sum([x[1] for x in long])
    for symbol, market_cap in long:
        weight[symbol] = market_cap / total_market_cap_long
    
    total_market_cap_short = sum([x[1] for x in short])
    for symbol, market_cap in short:
        weight[symbol] = -market_cap / total_market_cap_short   
    
    # Trade execution.
    invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in weight:
            self.Liquidate(symbol)
    
    for symbol, w in weight.items():
        if self.Securities[symbol].Price != 0 and self.Securities[symbol].IsTradable:
            self.SetHoldings(symbol, w)
