"""Portfolio analysis module — diversification, sector analysis, index comparison."""

from backend.collector.stock_data import fetch_stock
from backend.collector.company_data import fetch_fundamentals
from backend.utils.stocks import STOCKS


# Broad sector groupings for diversification check
SECTOR_GROUPS = {
    "Energy": ["energy", "oil", "gas", "power", "wind", "solar", "renewable"],
    "Banking & Finance": ["bank", "finance", "insurance", "nbfc", "finserv", "capital"],
    "IT & Technology": ["technology", "software", "it services", "tech"],
    "Healthcare & Pharma": ["pharma", "health", "hospital", "diagnostic", "biotech"],
    "FMCG & Consumer": ["consumer", "fmcg", "food", "beverage", "personal"],
    "Auto": ["auto", "motor", "vehicle", "tyre"],
    "Metals & Mining": ["metal", "steel", "mining", "alumin", "copper", "zinc"],
    "Infrastructure & Real Estate": ["construct", "infra", "real estate", "cement", "housing"],
    "Telecom & Media": ["telecom", "media", "entertainment", "broadcast"],
    "Chemicals": ["chemical", "fertilizer", "agro"],
    "Defence & PSU": ["defence", "defense", "railway", "government", "psu"],
}


def _classify_sector(sector_name, industry_name):
    """Classify a stock into a broad sector group."""
    combined = f"{sector_name or ''} {industry_name or ''}".lower()
    for group, keywords in SECTOR_GROUPS.items():
        for kw in keywords:
            if kw in combined:
                return group
    return "Other"


def analyze_portfolio(holdings):
    """Analyze a portfolio of holdings.

    Args:
        holdings: list of dicts [{"name": str, "symbol": str, "quantity": int}, ...]

    Returns:
        dict with portfolio analysis including:
        - stocks: per-stock data (price, value, weight, sector, fundamentals)
        - total_value: total portfolio value
        - sector_allocation: sector → percentage
        - diversification_warnings: list of warning strings
        - suggestions: list of improvement suggestions
    """
    stock_data = []
    total_value = 0

    for holding in holdings:
        symbol = holding["symbol"]
        qty = holding["quantity"]
        name = holding["name"]

        try:
            fund = fetch_fundamentals(symbol)
            price = fund.get("current_price")
            if price is None:
                continue

            value = price * qty
            total_value += value

            sector = fund.get("sector", "Unknown")
            industry = fund.get("industry", "Unknown")
            broad_sector = _classify_sector(sector, industry)

            stock_data.append({
                "name": name,
                "symbol": symbol,
                "quantity": qty,
                "price": price,
                "value": value,
                "sector": sector,
                "industry": industry,
                "broad_sector": broad_sector,
                "pe_ratio": fund.get("pe_ratio"),
                "debt_to_equity": fund.get("debt_to_equity"),
                "dividend_yield": fund.get("dividend_yield"),
                "fifty_two_week_high": fund.get("fifty_two_week_high"),
                "fifty_two_week_low": fund.get("fifty_two_week_low"),
            })
        except Exception:
            stock_data.append({
                "name": name, "symbol": symbol, "quantity": qty,
                "price": None, "value": 0, "sector": "Unknown",
                "industry": "Unknown", "broad_sector": "Other",
                "pe_ratio": None, "debt_to_equity": None,
                "dividend_yield": None, "fifty_two_week_high": None,
                "fifty_two_week_low": None,
            })

    # Calculate weights
    for s in stock_data:
        s["weight"] = (s["value"] / total_value * 100) if total_value > 0 else 0

    # Sector allocation
    sector_alloc = {}
    for s in stock_data:
        grp = s["broad_sector"]
        sector_alloc[grp] = sector_alloc.get(grp, 0) + s["weight"]

    # ── Warnings & suggestions ────────────────────────────────────────────
    warnings = []
    suggestions = []

    # Over-concentration check (>30% in one stock)
    for s in stock_data:
        if s["weight"] > 30:
            warnings.append(
                f"{s['name']} accounts for {s['weight']:.1f}% of your portfolio — "
                f"consider reducing to below 20% for better risk management."
            )

    # Sector concentration (>50% in one sector)
    for sector, pct in sector_alloc.items():
        if pct > 50:
            warnings.append(
                f"Your portfolio is {pct:.1f}% concentrated in {sector}. "
                f"Diversifying across sectors can reduce risk."
            )

    # Too few sectors
    if len(sector_alloc) <= 1 and len(stock_data) > 1:
        suggestions.append(
            "All holdings are in a single sector. Consider adding stocks from "
            "different sectors like Banking, IT, FMCG, or Healthcare for better diversification."
        )
    elif len(sector_alloc) <= 2 and len(stock_data) > 2:
        suggestions.append(
            "Portfolio spans only 2 sectors. Consider adding exposure to "
            "uncorrelated sectors for improved risk-adjusted returns."
        )

    # High-risk concentration
    high_debt = [s for s in stock_data if s.get("debt_to_equity") and s["debt_to_equity"] > 150]
    if len(high_debt) > len(stock_data) / 2 and len(stock_data) > 1:
        names = ", ".join(s["name"] for s in high_debt)
        suggestions.append(
            f"Multiple holdings ({names}) have high debt-to-equity ratios. "
            f"Consider balancing with lower-leverage companies."
        )

    # Missing dividends
    div_stocks = [s for s in stock_data if s.get("dividend_yield") and s["dividend_yield"] > 0.01]
    if not div_stocks and len(stock_data) > 1:
        suggestions.append(
            "None of your holdings offer significant dividends. "
            "Consider adding dividend-paying stocks (e.g. ITC, Coal India, Power Grid) for income stability."
        )

    # General diversification suggestions
    missing_sectors = set(SECTOR_GROUPS.keys()) - set(sector_alloc.keys())
    if len(missing_sectors) > 5 and len(stock_data) > 2:
        top_missing = list(missing_sectors)[:3]
        suggestions.append(
            f"Consider exploring sectors like {', '.join(top_missing)} "
            f"for broader market exposure."
        )

    return {
        "stocks": stock_data,
        "total_value": total_value,
        "sector_allocation": sector_alloc,
        "warnings": warnings,
        "suggestions": suggestions,
    }
