import yfinance as yf
import time
from datetime import datetime, timedelta

try:
    from pandas_datareader import data as web
except Exception:
    web = None


def _fetch_from_stooq(symbol):
    if web is None:
        return None

    end = datetime.utcnow()
    start = end - timedelta(days=180)

    # Stooq may use .IN for NSE symbols instead of .NS.
    stooq_symbols = [symbol]
    if symbol.upper().endswith(".NS"):
        stooq_symbols.append(symbol[:-3] + ".IN")

    for stooq_symbol in stooq_symbols:
        try:
            df = web.DataReader(stooq_symbol, "stooq", start, end)
            if df is None or df.empty:
                continue

            # Stooq commonly returns descending dates; normalize for indicators/chart.
            df = df.sort_index()
            return df
        except Exception:
            continue

    return None


def fetch_stock(symbol, period="3mo", retries=2, pause_seconds=1.5):
    stock = yf.Ticker(symbol)

    for attempt in range(retries + 1):
        try:
            df = stock.history(period=period)
            if not df.empty:
                return df

            # Secondary fetch path reduces failures for some symbols/environments.
            df = yf.download(symbol, period=period, progress=False, threads=False)
            if not df.empty:
                return df

            # Free fallback source to reduce complete outages on shared cloud IPs.
            stooq_df = _fetch_from_stooq(symbol)
            if stooq_df is not None and not stooq_df.empty:
                return stooq_df

            raise ValueError("No market data returned")
        except Exception as exc:
            is_rate_limit = exc.__class__.__name__ == "YFRateLimitError"
            if is_rate_limit and attempt < retries:
                time.sleep(pause_seconds * (attempt + 1))
                continue

            if not is_rate_limit and attempt < retries:
                time.sleep(0.75 * (attempt + 1))
                continue

            if is_rate_limit:
                stooq_df = _fetch_from_stooq(symbol)
                if stooq_df is not None and not stooq_df.empty:
                    return stooq_df

                raise ValueError(
                    "Yahoo Finance rate limit reached, and fallback source is unavailable. Please wait a minute and try again."
                ) from exc

            raise ValueError(
                "Unable to fetch market data right now. Please try again shortly."
            ) from exc
