"""Live market snapshot via Yahoo Finance (yfinance, no API key).

Deliberately failure-tolerant: market data is a nice-to-have side panel, so
any network or upstream hiccup degrades to "no data" instead of breaking the
app. Quotes are cached for 5 minutes.
"""

import re

import streamlit as st
import yfinance as yf


def ticker_for(report: str) -> str:
    """Collection names are TICKER_AR<year>, so the ticker is the first token."""
    return re.split(r"[_\W]", report)[0].upper()


@st.cache_data(ttl=300, show_spinner=False)
def quotes(tickers: list[str]) -> list[dict]:
    out = []
    for ticker in dict.fromkeys(t for t in tickers if t):
        try:
            info = yf.Ticker(ticker).fast_info
            price = info["last_price"]
            prev = info.get("previous_close")
            out.append({
                "ticker": ticker,
                "price": price,
                "change_pct": (price - prev) / prev * 100 if prev else None,
                "low_52w": info.get("year_low"),
                "high_52w": info.get("year_high"),
            })
        except Exception:
            continue  # one bad ticker (or offline) must not break the panel
    return out
