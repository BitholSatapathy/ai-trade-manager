try:
    from backend.collector.stock_data import fetch_stock
    from backend.collector.news_data import fetch_news
    from backend.indicators.rsi import compute_rsi
    from backend.indicators.moving_avg import moving_average
    from backend.ai.sentiment import get_sentiment
    from backend.ai.reasoning import generate_reason
    from backend.advisor.decision import make_decision
except ModuleNotFoundError:
    # Fallback for running this file directly: python backend/main.py
    from collector.stock_data import fetch_stock
    from collector.news_data import fetch_news
    from indicators.rsi import compute_rsi
    from indicators.moving_avg import moving_average
    from ai.sentiment import get_sentiment
    from ai.reasoning import generate_reason
    from advisor.decision import make_decision


def run_pipeline(symbol):

    symbol = symbol.strip()
    if not symbol:
        raise ValueError("Please enter a stock symbol like RELIANCE.NS")

    data = fetch_stock(symbol)
    if data.empty:
        raise ValueError(
            f"No market data found for '{symbol}'. Use a Yahoo Finance ticker, e.g. RELIANCE.NS"
        )

    try:
        rsi = compute_rsi(data)
        ma = moving_average(data)

        try:
            news = fetch_news(symbol)
        except Exception:
            news = []
        sentiment = get_sentiment(news)

        decision, confidence = make_decision(rsi, sentiment)
        reason = generate_reason(rsi, sentiment, decision)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Analysis temporarily unavailable. Please try again in a minute.") from exc

    return {
        "symbol": symbol,
        "rsi": rsi,
        "moving_avg": ma,
        "sentiment": sentiment,
        "decision": decision,
        "confidence": confidence,
        "reason": reason,
        "data": data
    }


if __name__ == "__main__":
    result = run_pipeline("RELIANCE.NS")
    print(result)
