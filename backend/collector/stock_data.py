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

    stooq_symbols = [symbol]
    if symbol.upper().endswith(".NS"):
        stooq_symbols.append(symbol[:-3] + ".IN")

    for stooq_symbol in stooq_symbols:
        try:
            df = web.DataReader(stooq_symbol, "stooq", start, end)
            if df is None or df.empty:
                continue
            df = df.sort_index()
            return df
        except Exception:
            continue

    return None


def fetch_stock(symbol, period="1mo", retries=1, pause_seconds=1.0):
    """Fetch stock data with fast defaults (1-month window, 1 retry)."""
    stock = yf.Ticker(symbol)

    for attempt in range(retries + 1):
        try:
            df = stock.history(period=period)
            if not df.empty:
                return df

            df = yf.download(symbol, period=period, progress=False, threads=False)
            if not df.empty:
                return df

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
                time.sleep(0.5 * (attempt + 1))
                continue

            if is_rate_limit:
                stooq_df = _fetch_from_stooq(symbol)
                if stooq_df is not None and not stooq_df.empty:
                    return stooq_df

                raise ValueError(
                    "Yahoo Finance rate limit reached. Please wait a minute and try again."
                ) from exc

            raise ValueError(
                "Unable to fetch market data right now. Please try again shortly."
            ) from exc





def fetch_index_quotes(index_map):
    """Fetch latest price + daily change for multiple indices in one batch call."""
    if not index_map:
        return {}

    tickers_str = " ".join(index_map.values())
    try:
        df = yf.download(
            tickers_str,
            period="2d",
            progress=False,
            threads=True,
            group_by="ticker",
        )
    except Exception:
        return {}

    results = {}
    for display_name, ticker in index_map.items():
        try:
            if len(index_map) == 1:
                close_col = df["Close"]
            else:
                close_col = df[(ticker, "Close")]

            close_col = close_col.dropna()
            if len(close_col) < 1:
                continue

            latest = float(close_col.iloc[-1])
            if len(close_col) >= 2:
                prev = float(close_col.iloc[-2])
                change_pct = ((latest - prev) / prev) * 100 if prev else 0.0
            else:
                change_pct = 0.0

            results[display_name] = {"price": latest, "change_pct": round(change_pct, 2)}
        except Exception:
            continue

    return results
