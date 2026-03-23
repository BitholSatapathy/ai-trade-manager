import yfinance as yf
import time


def fetch_stock(symbol, period="3mo", retries=2, pause_seconds=1.5):
    stock = yf.Ticker(symbol)

    for attempt in range(retries + 1):
        try:
            return stock.history(period=period)
        except Exception as exc:
            is_rate_limit = exc.__class__.__name__ == "YFRateLimitError"
            if is_rate_limit and attempt < retries:
                time.sleep(pause_seconds * (attempt + 1))
                continue

            if is_rate_limit:
                raise ValueError(
                    "Yahoo Finance rate limit reached. Please wait a minute and try again."
                ) from exc

            raise ValueError(
                "Unable to fetch market data right now. Please try again shortly."
            ) from exc
