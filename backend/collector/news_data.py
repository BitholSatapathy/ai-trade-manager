import yfinance as yf
import time


FALLBACK_HEADLINES = [
    {"title": "Market updates are temporarily unavailable.", "link": None,
     "publisher": None, "date": None},
]


def fetch_news(symbol, retries=1, pause_seconds=1.0):
    """Fetch news articles for a stock with title, link, publisher, and date.

    Returns a list of dicts with keys: title, link, publisher, date.
    """
    for attempt in range(retries + 1):
        try:
            stock = yf.Ticker(symbol)
            news_items = stock.news or []

            articles = []
            for item in news_items[:10]:
                title = item.get("title") or item.get("summary")
                if not title:
                    continue

                link = item.get("link") or item.get("url")
                publisher = item.get("publisher")

                # Parse date from providerPublishTime (unix timestamp)
                pub_time = item.get("providerPublishTime")
                date_str = None
                if pub_time:
                    try:
                        from datetime import datetime
                        date_str = datetime.utcfromtimestamp(int(pub_time)).strftime("%d %b %Y")
                    except Exception:
                        pass

                articles.append({
                    "title": title,
                    "link": link,
                    "publisher": publisher,
                    "date": date_str,
                })

            return articles if articles else FALLBACK_HEADLINES

        except Exception as exc:
            is_rate_limit = exc.__class__.__name__ == "YFRateLimitError"
            if is_rate_limit and attempt < retries:
                time.sleep(pause_seconds * (attempt + 1))
                continue

            if not is_rate_limit and attempt < retries:
                time.sleep(0.5 * (attempt + 1))
                continue

            return FALLBACK_HEADLINES


def get_headlines(news_list):
    """Extract headline strings from enriched news list (for sentiment)."""
    return [item["title"] for item in news_list if item.get("title")]
