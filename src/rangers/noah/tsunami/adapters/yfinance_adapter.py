"""YFinance implementation of the DataAdapter interface."""

from __future__ import annotations

import warnings
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

from .base import DataAdapter


class YFinanceAdapter(DataAdapter):
    """Free-tier data adapter using the yfinance library."""

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _safe_get(info: dict, key: str, default: Any = None) -> Any:
        """Return info[key] if present and not None/NaN, else default."""
        val = info.get(key, default)
        if val is None:
            return default
        if isinstance(val, float) and np.isnan(val):
            return default
        return val

    @staticmethod
    def _first_valid(series: pd.Series) -> float | None:
        """Return the first non-NaN value from a pandas Series."""
        for val in series:
            if pd.notna(val):
                return float(val)
        return None

    # ------------------------------------------------------------------ #
    #  Interface methods
    # ------------------------------------------------------------------ #

    def get_financials(self, ticker: str) -> dict:
        """Pull fundamental metrics and derive SGA%, FCF yield, ROIC."""
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        income = tk.income_stmt
        balance = tk.balance_sheet
        cashflow = tk.cashflow

        # --- SGA % of revenue ---
        sga_pct = None
        if income is not None and not income.empty:
            sga_row = None
            for label in [
                "SellingGeneralAndAdministration",
                "Selling General And Administration",
                "SellingGeneralAndAdministrative",
            ]:
                if label in income.index:
                    sga_row = income.loc[label]
                    break
            rev_row = None
            for label in ["TotalRevenue", "Total Revenue"]:
                if label in income.index:
                    rev_row = income.loc[label]
                    break
            if sga_row is not None and rev_row is not None:
                sga_val = self._first_valid(sga_row)
                rev_val = self._first_valid(rev_row)
                if sga_val and rev_val and rev_val != 0:
                    sga_pct = sga_val / rev_val

        # --- Gross margin ---
        gross_margin_pct = self._safe_get(info, "grossMargins")

        # --- Debt to equity ---
        debt_to_equity_raw = self._safe_get(info, "debtToEquity")
        debt_to_equity = (
            debt_to_equity_raw / 100.0
            if debt_to_equity_raw is not None and debt_to_equity_raw > 10
            else debt_to_equity_raw
        )

        # --- FCF yield ---
        fcf_yield_pct = None
        if cashflow is not None and not cashflow.empty:
            fcf_row = None
            for label in ["FreeCashFlow", "Free Cash Flow"]:
                if label in cashflow.index:
                    fcf_row = cashflow.loc[label]
                    break
            fcf_val = self._first_valid(fcf_row) if fcf_row is not None else None
            shares = self._safe_get(info, "sharesOutstanding")
            price = self._safe_get(info, "currentPrice") or self._safe_get(
                info, "regularMarketPrice"
            )
            if fcf_val is not None and shares and price and (shares * price) != 0:
                fcf_yield_pct = fcf_val / (shares * price)

        # --- ROIC ---
        roic_pct = None
        if (
            income is not None
            and not income.empty
            and balance is not None
            and not balance.empty
        ):
            ni_row = None
            for label in ["NetIncome", "Net Income"]:
                if label in income.index:
                    ni_row = income.loc[label]
                    break
            ta_row = None
            for label in ["TotalAssets", "Total Assets"]:
                if label in balance.index:
                    ta_row = balance.loc[label]
                    break
            cl_row = None
            for label in ["CurrentLiabilities", "Current Liabilities"]:
                if label in balance.index:
                    cl_row = balance.loc[label]
                    break
            ni_val = self._first_valid(ni_row) if ni_row is not None else None
            ta_val = self._first_valid(ta_row) if ta_row is not None else None
            cl_val = self._first_valid(cl_row) if cl_row is not None else None
            if ni_val is not None and ta_val is not None and cl_val is not None:
                invested_capital = ta_val - cl_val
                if invested_capital != 0:
                    nopat = ni_val * (1 - 0.21)
                    roic_pct = nopat / invested_capital

        return {
            "sga_pct": sga_pct,
            "gross_margin_pct": gross_margin_pct,
            "debt_to_equity": debt_to_equity,
            "fcf_yield_pct": fcf_yield_pct,
            "roic_pct": roic_pct,
        }

    def get_price(self, ticker: str) -> float:
        """Return current spot price."""
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        price = self._safe_get(info, "currentPrice") or self._safe_get(
            info, "regularMarketPrice"
        )
        if price is None:
            raise ValueError(f"Cannot retrieve price for {ticker}")
        return float(price)

    def get_valuation(self, ticker: str) -> dict:
        """Return EPS and P/E ratio."""
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        eps = self._safe_get(info, "trailingEps", 0.0)
        pe = self._safe_get(info, "trailingPE", 0.0)
        return {"eps": float(eps), "pe": float(pe)}

    def get_historical_prices(self, ticker: str, period: str = "2y") -> pd.DataFrame:
        """Return OHLCV data for HV calculation."""
        tk = yf.Ticker(ticker)
        df = tk.history(period=period, auto_adjust=True)
        if df is None or df.empty:
            raise ValueError(f"No historical price data for {ticker}")
        return df

    def get_options_chain(self, ticker: str, min_dte: int = 180) -> pd.DataFrame:
        """Return puts chain with DTE >= min_dte.

        Iterates available expiration dates from yfinance and collects
        put options for those expiries that are at least ``min_dte`` days
        out.  Returns a single DataFrame with an added ``expiry`` column.
        """
        tk = yf.Ticker(ticker)
        expirations = tk.options
        if not expirations:
            warnings.warn(f"No options chain available for {ticker}")
            return pd.DataFrame()

        cutoff = datetime.utcnow() + timedelta(days=min_dte)
        frames: list[pd.DataFrame] = []

        for exp_str in expirations:
            exp_dt = datetime.strptime(exp_str, "%Y-%m-%d")
            if exp_dt < cutoff:
                continue
            chain = tk.option_chain(exp_str)
            puts = chain.puts.copy()
            puts["expiry"] = exp_str
            frames.append(puts)

        if not frames:
            warnings.warn(
                f"No options with DTE >= {min_dte} for {ticker}"
            )
            return pd.DataFrame()

        result = pd.concat(frames, ignore_index=True)
        rename_map = {
            "impliedVolatility": "impliedVolatility",
            "openInterest": "openInterest",
        }
        result.rename(columns=rename_map, inplace=True)
        return result
