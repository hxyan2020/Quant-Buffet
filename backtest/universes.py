"""Named ETF universes for Quant Buffet full-catalog backtests."""

from __future__ import annotations

# Liquid proxies used when strategy text/code does not list tickers.
US_EQUITY = ["SPY", "QQQ", "IWM"]
US_SECTORS = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
US_SECTORS_FULL = US_SECTORS + ["XLC", "XLRE"]
GLOBAL_EQUITY = ["SPY", "EFA", "EEM", "VGK", "EWJ", "FXI"]
COUNTRY_DM = [
    "EWA", "EWC", "EWD", "EWG", "EWH", "EWI", "EWJ", "EWK", "EWL",
    "EWN", "EWP", "EWQ", "EWS", "EWU", "EWY",
]
COUNTRY_EM = [
    "EWZ", "FXI", "EWT", "EWY", "EIDO", "THD", "EPHE", "ECH", "EPOL",
    "EZA", "ARGT", "TUR", "ASHR",
]
BONDS = ["SHY", "IEF", "TLT", "LQD", "HYG", "TIP", "BND"]
CREDIT = ["LQD", "HYG", "AGG", "BIL"]
COMMODITIES = ["GLD", "SLV", "DBC", "GSG", "USO", "UNG", "DBA"]
REAL_ESTATE = ["VNQ", "IYR", "RWX"]
MULTI_ASSET = ["SPY", "EFA", "EEM", "VNQ", "DBC", "GLD", "TLT", "IEF", "HYG"]
RISK_ON_OFF = ["SPY", "QQQ", "TLT", "IEF", "GLD", "BIL"]
VOL_PROXY = ["SPY", "BIL", "VIXY", "SVXY"]
CRYPTO_PROXY = ["BTC-USD", "ETH-USD"]  # yfinance
FX_PROXY = ["UUP", "FXE", "FXY", "FXB"]  # may miss some — filtered at load
# Safer FX/dollar book using liquid ETFs already in whitelist path
FX_SAFE = ["SPY", "EFA", "EWJ", "GLD", "TLT"]  # dollar-sensitive mix

WHITELIST = set(
    US_EQUITY
    + US_SECTORS_FULL
    + GLOBAL_EQUITY
    + COUNTRY_DM
    + COUNTRY_EM
    + BONDS
    + CREDIT
    + COMMODITIES
    + REAL_ESTATE
    + MULTI_ASSET
    + RISK_ON_OFF
    + ["BIL", "SHV", "IEI", "MBB", "AGG", "ACWI", "ACWX", "URTH", "VEA", "VWO", "VTI", "VOO", "DIA", "MDY", "RSP", "OEF"]
    + VOL_PROXY
    + CRYPTO_PROXY
)

# Prefer these when keyword matching books
BOOKS = {
    "us_equity": US_EQUITY,
    "us_sectors": US_SECTORS_FULL,
    "global_equity": GLOBAL_EQUITY,
    "country_dm": COUNTRY_DM[:12],
    "country_em": COUNTRY_EM[:12],
    "bonds": BONDS,
    "credit": CREDIT,
    "commodities": COMMODITIES,
    "real_estate": REAL_ESTATE,
    "multi_asset": MULTI_ASSET,
    "risk_on_off": RISK_ON_OFF,
    "vol": ["SPY", "BIL"],  # avoid leveraged vol products by default
    "crypto": CRYPTO_PROXY,
    "fx": FX_SAFE,
    "spy_bil": ["SPY", "BIL"],
    "qqq_bil": ["QQQ", "BIL"],
}
