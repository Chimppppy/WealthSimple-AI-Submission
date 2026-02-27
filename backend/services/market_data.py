import time
import logging
from datetime import datetime, timezone
from typing import Optional

import yfinance as yf
import pandas as pd

from backend.models.market_data import Holding, PortfolioPoint, MarketContext

logger = logging.getLogger(__name__)

EQUITY_HOLDINGS = [
    {"ticker": "VFV.TO", "name": "Vanguard S&P 500 Index ETF", "weight": 0.40},
    {"ticker": "QQQ",    "name": "Invesco QQQ (Nasdaq 100)",   "weight": 0.30},
    {"ticker": "XEQT.TO","name": "iShares Core Equity ETF",    "weight": 0.30},
]

BOND_HOLDINGS = [
    {"ticker": "ZAG.TO", "name": "BMO Aggregate Bond ETF",     "weight": 0.60},
    {"ticker": "XBB.TO", "name": "iShares Canadian Bond ETF",  "weight": 0.40},
]

FALLBACK_EQUITY_RETURN = 0.06
FALLBACK_BOND_RETURN = 0.03
FALLBACK_CASH_RETURN = 0.01
CACHE_TTL_SECONDS = 3600

_cache: dict[str, tuple[float, MarketContext]] = {}


def get_market_context(
    equity_pct: float, bond_pct: float
) -> MarketContext:
    """Fetch real market data and compute blended returns.

    Results are cached in-memory for CACHE_TTL_SECONDS.
    Falls back to hardcoded assumptions if Yahoo Finance is unreachable.
    """
    cache_key = f"{equity_pct:.2f}_{bond_pct:.2f}"
    now = time.time()

    if cache_key in _cache:
        cached_at, ctx = _cache[cache_key]
        if now - cached_at < CACHE_TTL_SECONDS:
            return ctx

    try:
        ctx = _fetch_and_compute(equity_pct, bond_pct)
        _cache[cache_key] = (now, ctx)
        return ctx
    except Exception:
        logger.exception("Yahoo Finance fetch failed — using fallback returns")
        return _build_fallback(equity_pct, bond_pct)


def _fetch_and_compute(equity_pct: float, bond_pct: float) -> MarketContext:
    """Batch-download price history from Yahoo Finance and compute returns."""
    all_tickers = [h["ticker"] for h in EQUITY_HOLDINGS + BOND_HOLDINGS]
    data = yf.download(all_tickers, period="5y", auto_adjust=True, progress=False)

    if isinstance(data.columns, pd.MultiIndex):
        close = data["Close"]
    else:
        close = data

    holdings: list[Holding] = []
    equity_returns: list[float] = []
    equity_weights: list[float] = []
    bond_returns: list[float] = []
    bond_weights: list[float] = []

    for h in EQUITY_HOLDINGS:
        info = _compute_holding(h, close, "equity")
        holdings.append(info)
        best = _best_return(info)
        if best is not None:
            equity_returns.append(best)
            equity_weights.append(h["weight"])

    for h in BOND_HOLDINGS:
        info = _compute_holding(h, close, "bonds")
        holdings.append(info)
        best = _best_return(info)
        if best is not None:
            bond_returns.append(best)
            bond_weights.append(h["weight"])

    equity_return = _weighted_avg(equity_returns, equity_weights, FALLBACK_EQUITY_RETURN)
    bond_return = _weighted_avg(bond_returns, bond_weights, FALLBACK_BOND_RETURN)

    portfolio_history = _build_portfolio_history(
        close, equity_pct, bond_pct, EQUITY_HOLDINGS, BOND_HOLDINGS
    )

    return MarketContext(
        holdings=holdings,
        equity_return=round(equity_return, 4),
        bond_return=round(bond_return, 4),
        cash_return=FALLBACK_CASH_RETURN,
        portfolio_history=portfolio_history,
        data_source="Yahoo Finance",
        data_as_of=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


def _compute_holding(
    h: dict, close: pd.DataFrame, bucket: str
) -> Holding:
    """Compute price and annualized returns for a single holding."""
    ticker = h["ticker"]

    if ticker not in close.columns:
        return Holding(
            ticker=ticker, name=h["name"], bucket=bucket, weight=h["weight"]
        )

    series = close[ticker].dropna()
    if series.empty:
        return Holding(
            ticker=ticker, name=h["name"], bucket=bucket, weight=h["weight"]
        )

    price = round(float(series.iloc[-1]), 2)
    return_1y = _annualized_return(series, 1)
    return_3y = _annualized_return(series, 3)
    return_5y = _annualized_return(series, 5)

    return Holding(
        ticker=ticker,
        name=h["name"],
        bucket=bucket,
        weight=h["weight"],
        price=price,
        return_1y=return_1y,
        return_3y=return_3y,
        return_5y=return_5y,
    )


def _best_return(holding: Holding) -> Optional[float]:
    """Pick the longest-horizon return available: 5Y > 3Y > 1Y."""
    if holding.return_5y is not None:
        return holding.return_5y
    if holding.return_3y is not None:
        return holding.return_3y
    return holding.return_1y


def _annualized_return(
    series: pd.Series, target_years: int
) -> Optional[float]:
    """Compute annualized return over approximately the last N years.

    Uses a 10% tolerance on trading-day count and computes actual
    elapsed years from the date index for accuracy.
    """
    expected_days = target_years * 252
    min_required = int(expected_days * 0.90)

    if len(series) < min_required:
        return None

    lookback = min(expected_days, len(series))
    start_val = float(series.iloc[-lookback])
    end_val = float(series.iloc[-1])
    if start_val <= 0:
        return None

    start_date = series.index[-lookback]
    end_date = series.index[-1]
    elapsed_years = (end_date - start_date).days / 365.25
    if elapsed_years <= 0:
        return None

    return round((end_val / start_val) ** (1.0 / elapsed_years) - 1, 4)


def _weighted_avg(
    returns: list[float], weights: list[float], fallback: float
) -> float:
    """Compute weighted average return, falling back if no data."""
    if not returns:
        return fallback
    total_w = sum(weights)
    if total_w == 0:
        return fallback
    return sum(r * w for r, w in zip(returns, weights)) / total_w


def _build_portfolio_history(
    close: pd.DataFrame,
    equity_pct: float,
    bond_pct: float,
    equity_holdings: list[dict],
    bond_holdings: list[dict],
) -> list[PortfolioPoint]:
    """Build a 1-year normalized portfolio value series for charting.

    Starts at $10,000 and tracks the blended daily return.
    """
    one_year_ago = close.index[-1] - pd.DateOffset(years=1)
    recent = close[close.index >= one_year_ago].copy()

    if recent.empty:
        return []

    cash_pct = max(1.0 - equity_pct - bond_pct, 0.0)
    combined = pd.Series(0.0, index=recent.index, dtype=float)

    for h in equity_holdings:
        if h["ticker"] in recent.columns:
            normed = recent[h["ticker"]] / recent[h["ticker"]].iloc[0]
            combined += normed * h["weight"] * equity_pct

    for h in bond_holdings:
        if h["ticker"] in recent.columns:
            normed = recent[h["ticker"]] / recent[h["ticker"]].iloc[0]
            combined += normed * h["weight"] * bond_pct

    combined += cash_pct

    if combined.sum() == 0:
        return []

    base_value = 10_000
    combined = combined * base_value

    sampled = combined.resample("W").last().dropna()

    return [
        PortfolioPoint(date=d.strftime("%Y-%m-%d"), value=round(float(v), 2))
        for d, v in sampled.items()
    ]


def _build_fallback(equity_pct: float, bond_pct: float) -> MarketContext:
    """Return hardcoded assumptions when Yahoo Finance is unavailable."""
    holdings = [
        Holding(ticker=h["ticker"], name=h["name"], bucket="equity", weight=h["weight"])
        for h in EQUITY_HOLDINGS
    ] + [
        Holding(ticker=h["ticker"], name=h["name"], bucket="bonds", weight=h["weight"])
        for h in BOND_HOLDINGS
    ]

    return MarketContext(
        holdings=holdings,
        equity_return=FALLBACK_EQUITY_RETURN,
        bond_return=FALLBACK_BOND_RETURN,
        cash_return=FALLBACK_CASH_RETURN,
        portfolio_history=[],
        data_source="Hardcoded estimates (market data unavailable)",
        data_as_of=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )
