import yfinance as yf


def fetch_news(symbol):

    stock = yf.Ticker(symbol)
    news_items = stock.news

    headlines = []

    for item in news_items[:5]:
        title = item.get('title') or item.get('summary') or item.get('publisher')
        if title:
            headlines.append(title)

    return headlines
