def make_decision(rsi, sentiment, fundamentals=None):
    """Score-based decision engine that considers technicals AND fundamentals.

    Scoring bands:
      Technical (RSI + Sentiment):  -2 to +2
      Fundamental adjustments:      -3 to +3
      Total range:                  -5 to +5
    """
    score = 0

    # ── Technical signals ─────────────────────────────────────────────────
    if rsi < 30:
        score += 1        # Oversold → bullish
    elif rsi > 70:
        score -= 1        # Overbought → bearish

    if sentiment == "Positive":
        score += 1
    elif sentiment == "Negative":
        score -= 1

    # ── Fundamental signals ───────────────────────────────────────────────
    fund_notes = []
    if fundamentals and isinstance(fundamentals, dict):
        pe = fundamentals.get("pe_ratio")
        pb = fundamentals.get("pb_ratio")
        dte = fundamentals.get("debt_to_equity")
        roe = fundamentals.get("roe")
        div_yield = fundamentals.get("dividend_yield")

        # PE Ratio — value vs overvalued
        if pe is not None:
            if pe < 15:
                score += 1
                fund_notes.append("Low PE (value)")
            elif pe > 40:
                score -= 1
                fund_notes.append("High PE (overvalued risk)")

        # PB Ratio
        if pb is not None:
            if pb < 1.5:
                score += 0.5
                fund_notes.append("Low PB (undervalued)")
            elif pb > 5:
                score -= 0.5
                fund_notes.append("High PB")

        # Debt to Equity
        if dte is not None:
            if dte > 150:
                score -= 1
                fund_notes.append("High debt")
            elif dte < 50:
                score += 0.5
                fund_notes.append("Low debt")

        # ROE
        if roe is not None:
            if roe > 0.20:
                score += 0.5
                fund_notes.append("Strong ROE")
            elif roe < 0.05:
                score -= 0.5
                fund_notes.append("Weak ROE")

        # Dividend Yield
        if div_yield is not None:
            if div_yield > 0.03:
                score += 0.5
                fund_notes.append("Good dividend")

    # ── Decision mapping ──────────────────────────────────────────────────
    if score >= 3:
        decision, confidence = "BUY", 90
    elif score >= 2:
        decision, confidence = "BUY", 80
    elif score >= 1:
        decision, confidence = "BUY", 65
    elif score <= -3:
        decision, confidence = "SELL", 90
    elif score <= -2:
        decision, confidence = "SELL", 80
    elif score <= -1:
        decision, confidence = "SELL", 65
    else:
        decision, confidence = "HOLD", 50

    return decision, confidence, score, fund_notes
