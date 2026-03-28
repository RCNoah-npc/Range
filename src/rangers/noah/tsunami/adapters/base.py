"""Abstract base class for financial data adapters."""

from abc import ABC, abstractmethod

import pandas as pd


class DataAdapter(ABC):
    """Interface for financial data sources.

    All adapters must implement these methods.  The Tsunami pipeline
    calls them generically so that switching from yfinance to a paid
    provider (FMP, Polygon, etc.) requires only a new adapter class.
    """

    @abstractmethod
    def get_financials(self, ticker: str) -> dict:
        """Return fundamental metrics for vulnerability scoring.

        Expected keys:
            sga_pct        -- SG&A as % of revenue
            gross_margin_pct -- Gross margin percentage (0-1 scale)
            debt_to_equity -- Debt-to-equity ratio
            fcf_yield_pct  -- Free cash flow yield (0-1 scale)
            roic_pct       -- Return on invested capital (0-1 scale)
        """

    @abstractmethod
    def get_price(self, ticker: str) -> float:
        """Return the current spot price."""

    @abstractmethod
    def get_valuation(self, ticker: str) -> dict:
        """Return valuation metrics.

        Expected keys:
            eps -- Trailing EPS
            pe  -- Trailing P/E ratio
        """

    @abstractmethod
    def get_historical_prices(self, ticker: str, period: str) -> pd.DataFrame:
        """Return OHLCV DataFrame for volatility calculations.

        Must include a 'Close' column at minimum.
        ``period`` follows yfinance convention: '1y', '2y', etc.
        """

    @abstractmethod
    def get_options_chain(self, ticker: str, min_dte: int) -> pd.DataFrame:
        """Return puts options chain filtered to >= min_dte days out.

        Required columns:
            strike, bid, ask, volume, openInterest,
            impliedVolatility, expiry (str YYYY-MM-DD)
        """
