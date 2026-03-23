import yfinance as yf
import time


FALLBACK_HEADLINES = [
    "Market updates are temporarily unavailable.",
]


def fetch_news(symbol, retries=1, pause_seconds=1.0):

    for attempt in range(retries + 1):
        try:
            stock = yf.Ticker(symbol)
            news_items = stock.news or []

            headlines = []

            for item in news_items[:5]:
                title = item.get('title') or item.get('summary') or item.get('publisher')
                if title:
                    headlines.append(title)

            return headlines or FALLBACK_HEADLINES
        except Exception as exc:
            is_rate_limit = exc.__class__.__name__ == "YFRateLimitError"
            if is_rate_limit and attempt < retries:
                time.sleep(pause_seconds * (attempt + 1))
                continue

            if not is_rate_limit and attempt < retries:
                time.sleep(0.5 * (attempt + 1))
                continue

            return FALLBACK_HEADLINES
