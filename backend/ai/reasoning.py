def _fmt(val, suffix="", prefix=""):
    """Format a numeric value for display, or return 'N/A'."""
    if val is None:
        return "N/A"
    if isinstance(val, float):
        return f"{prefix}{val:,.2f}{suffix}"
    return f"{prefix}{val}{suffix}"


def generate_reason(rsi, sentiment, decision, fundamentals=None,
                    financials=None, score=None, fund_notes=None):
    """Generate a detailed AI insight incorporating technicals + fundamentals."""

    parts = []

    # ── Decision headline ─────────────────────────────────────────────────
    if decision == "BUY":
        parts.append("The analysis indicates a bullish opportunity for this stock.")
    elif decision == "SELL":
        parts.append("The analysis shows bearish signals for this stock.")
    else:
        parts.append("The stock is currently in a neutral zone with no strong directional bias.")

    # ── Technical summary ─────────────────────────────────────────────────
    if rsi < 30:
        parts.append(f"RSI at {rsi:.1f} suggests the stock is oversold, indicating potential upside.")
    elif rsi > 70:
        parts.append(f"RSI at {rsi:.1f} suggests overbought conditions, signalling caution.")
    else:
        parts.append(f"RSI at {rsi:.1f} is in the neutral range.")

    parts.append(f"News sentiment is {sentiment.lower()}.")

    # ── Fundamental analysis ──────────────────────────────────────────────
    if fundamentals and isinstance(fundamentals, dict):
        fund_parts = []

        pe = fundamentals.get("pe_ratio")
        if pe is not None:
            if pe < 15:
                fund_parts.append(f"PE ratio of {pe:.1f} indicates the stock may be undervalued relative to earnings.")
            elif pe > 40:
                fund_parts.append(f"PE ratio of {pe:.1f} is elevated, suggesting the stock is priced for high growth expectations.")
            else:
                fund_parts.append(f"PE ratio of {pe:.1f} is in a moderate range.")

        dte = fundamentals.get("debt_to_equity")
        if dte is not None:
            if dte > 150:
                fund_parts.append(f"Debt-to-equity of {dte:.0f}% is high, which adds financial risk.")
            elif dte < 50:
                fund_parts.append(f"Debt-to-equity of {dte:.0f}% is conservative, indicating a strong balance sheet.")

        roe = fundamentals.get("roe")
        if roe is not None:
            roe_pct = roe * 100
            if roe > 0.20:
                fund_parts.append(f"ROE of {roe_pct:.1f}% demonstrates strong profitability.")
            elif roe < 0.05:
                fund_parts.append(f"ROE of {roe_pct:.1f}% is below average, suggesting weak returns on equity.")

        div_yield = fundamentals.get("dividend_yield")
        if div_yield is not None and div_yield > 0.01:
            fund_parts.append(f"Dividend yield of {div_yield*100:.2f}% provides income potential.")

        if fund_parts:
            parts.append("Fundamental Analysis: " + " ".join(fund_parts))

    # ── Financial growth ──────────────────────────────────────────────────
    if financials and isinstance(financials, dict):
        revenue = financials.get("revenue", [])
        net_income = financials.get("net_income", [])

        rev_vals = [r for r in revenue if r is not None]
        ni_vals = [n for n in net_income if n is not None]

        if len(rev_vals) >= 2:
            rev_growth = ((rev_vals[-1] - rev_vals[-2]) / abs(rev_vals[-2])) * 100 if rev_vals[-2] != 0 else 0
            if rev_growth > 10:
                parts.append(f"Revenue grew {rev_growth:.1f}% year-over-year, showing strong business momentum.")
            elif rev_growth < -5:
                parts.append(f"Revenue declined {rev_growth:.1f}% year-over-year, which is a concern.")

        if len(ni_vals) >= 2:
            if ni_vals[-1] > 0 and ni_vals[-2] > 0:
                profit_growth = ((ni_vals[-1] - ni_vals[-2]) / abs(ni_vals[-2])) * 100
                if profit_growth > 15:
                    parts.append(f"Net profit grew {profit_growth:.1f}% YoY, reflecting improving profitability.")
                elif profit_growth < -10:
                    parts.append(f"Net profit fell {profit_growth:.1f}% YoY, signalling earnings pressure.")
            elif ni_vals[-1] < 0:
                parts.append("The company reported a net loss in the latest year.")

    # ── Score & notes ─────────────────────────────────────────────────────
    if fund_notes:
        parts.append("Key factors: " + ", ".join(fund_notes) + ".")

    if score is not None:
        parts.append(f"Overall composite score: {score:+.1f}.")

    return " ".join(parts)
