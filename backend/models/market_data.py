from pydantic import BaseModel
from typing import Optional


class Holding(BaseModel):
    """A single ETF/stock in the preset portfolio."""

    ticker: str
    name: str
    bucket: str
    weight: float
    price: Optional[float] = None
    return_1y: Optional[float] = None
    return_3y: Optional[float] = None
    return_5y: Optional[float] = None


class PortfolioPoint(BaseModel):
    """Single data point in the portfolio history time series."""

    date: str
    value: float


class MarketContext(BaseModel):
    """Real market data powering the projection engine."""

    holdings: list[Holding]
    equity_return: float
    bond_return: float
    cash_return: float
    portfolio_history: list[PortfolioPoint]
    data_source: str
    data_as_of: str
