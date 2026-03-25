import yfinance as yf

def fetch_fundamentals(symbol):
    """Fetch key fundamentals from yfinance .info in a single call."""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info or {}
    except Exception:
        info = {}

    def _get(key, default=None):
        val = info.get(key, default)
        return val if val is not None else default

    current = _get("currentPrice") or _get("regularMarketPrice") or _get("previousClose")
    prev_close = _get("previousClose") or _get("regularMarketPreviousClose")

    return {
        "current_price": current,
        "previous_close": prev_close,
        "day_high": _get("dayHigh") or _get("regularMarketDayHigh"),
        "day_low": _get("dayLow") or _get("regularMarketDayLow"),
        "fifty_two_week_high": _get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": _get("fiftyTwoWeekLow"),
        "market_cap": _get("marketCap"),
        "pe_ratio": _get("trailingPE"),
        "forward_pe": _get("forwardPE"),
        "pb_ratio": _get("priceToBook"),
        "industry_pe": _get("industryPe") or _get("sectorPe"),
        "debt_to_equity": _get("debtToEquity"),
        "roe": _get("returnOnEquity"),
        "dividend_yield": _get("dividendYield"),
        "book_value": _get("bookValue"),
        "face_value": _get("faceValue"),
        "eps": _get("trailingEps"),
        "sector": _get("sector"),
        "industry": _get("industry"),
        "company_name": _get("longName") or _get("shortName"),
    }


def fetch_financials(symbol):
    """Fetch yearly financials (Revenue, Net Income, Total Equity / Net Worth)."""
    result = {"years": [], "revenue": [], "net_income": [], "net_worth": []}

    try:
        stock = yf.Ticker(symbol)

        # Income statement → Revenue + Net Income
        income = stock.financials
        if income is not None and not income.empty:
            years = []
            revenue = []
            net_income = []
            for col in income.columns:
                yr = col.year if hasattr(col, "year") else str(col)[:4]
                years.append(str(yr))

                # Revenue
                rev = None
                for key in ["Total Revenue", "Revenue", "Operating Revenue"]:
                    if key in income.index:
                        val = income.loc[key, col]
                        if val is not None and str(val) != "nan":
                            rev = float(val)
                            break
                revenue.append(rev)

                # Net Income
                ni = None
                for key in ["Net Income", "Net Income Common Stockholders",
                             "Net Income From Continuing Operations"]:
                    if key in income.index:
                        val = income.loc[key, col]
                        if val is not None and str(val) != "nan":
                            ni = float(val)
                            break
                net_income.append(ni)

            result["years"] = list(reversed(years))
            result["revenue"] = list(reversed(revenue))
            result["net_income"] = list(reversed(net_income))

        # Balance sheet → Net Worth (Total Stockholder Equity)
        balance = stock.balance_sheet
        if balance is not None and not balance.empty:
            net_worth = []
            b_years = []
            for col in balance.columns:
                yr = col.year if hasattr(col, "year") else str(col)[:4]
                b_years.append(str(yr))

                nw = None
                for key in ["Total Stockholder Equity", "Stockholders Equity",
                             "Common Stock Equity", "Total Equity Gross Minority Interest"]:
                    if key in balance.index:
                        val = balance.loc[key, col]
                        if val is not None and str(val) != "nan":
                            nw = float(val)
                            break
                net_worth.append(nw)

            result["net_worth"] = list(reversed(net_worth))
            if not result["years"]:
                result["years"] = list(reversed(b_years))

    except Exception:
        pass

    return result
