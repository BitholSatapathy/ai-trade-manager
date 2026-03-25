from backend.collector.stock_data import fetch_stock
from backend.collector.company_data import fetch_fundamentals, fetch_financials
from backend.collector.news_data import fetch_news, get_headlines
from backend.indicators.rsi import compute_rsi
from backend.indicators.moving_avg import moving_average
from backend.ai.sentiment import get_sentiment
from backend.ai.reasoning import generate_reason
from backend.advisor.decision import make_decision


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

        # Fundamentals & financials (non-blocking — failures return empty dicts)
        try:
            fundamentals = fetch_fundamentals(symbol)
        except Exception:
            fundamentals = {}

        try:
            financials = fetch_financials(symbol)
        except Exception:
            financials = {"years": [], "revenue": [], "net_income": [], "net_worth": []}

        # News (enriched format)
        try:
            news = fetch_news(symbol)
        except Exception:
            news = []
        headlines = get_headlines(news) if news else []
        sentiment = get_sentiment(headlines)

        # AI decision with fundamentals awareness
        decision, confidence, score, fund_notes = make_decision(rsi, sentiment, fundamentals)
        reason = generate_reason(
            rsi, sentiment, decision,
            fundamentals=fundamentals,
            financials=financials,
            score=score,
            fund_notes=fund_notes,
        )
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
        "score": score,
        "fund_notes": fund_notes,
        "reason": reason,
        "data": data,
        "fundamentals": fundamentals,
        "financials": financials,
        "news": news,
    }


if __name__ == "__main__":
    result = run_pipeline("RELIANCE.NS")
    print(result)
