from rapidfuzz import fuzz, process

from .stocks import STOCKS, ALIASES


def search_stock(query, limit=10):
    """Search Indian stocks by name, ticker, or abbreviation with fuzzy matching.

    Returns a dict of {display_name: yahoo_ticker} sorted by relevance.
    """
    if not query or not query.strip():
        return {}

    query = query.strip()
    q_lower = query.lower()

    results = {}          # name → (symbol, score)

    # ── 1. Exact alias hit ────────────────────────────────────────────────
    if q_lower in ALIASES:
        canonical = ALIASES[q_lower]
        if canonical in STOCKS:
            results[canonical] = (STOCKS[canonical], 100)

    # ── 2. Substring match on name or ticker ──────────────────────────────
    for name, symbol in STOCKS.items():
        if q_lower in name.lower() or q_lower in symbol.lower():
            if name not in results:
                results[name] = (symbol, 95)

    # ── 3. Fuzzy match on company names ───────────────────────────────────
    if len(results) < limit:
        name_list = list(STOCKS.keys())
        matches = process.extract(
            query,
            name_list,
            scorer=fuzz.WRatio,
            limit=limit * 2,
            score_cutoff=55,
        )
        for match_name, score, _idx in matches:
            if match_name not in results:
                results[match_name] = (STOCKS[match_name], score)

    # ── 4. Fuzzy match on ticker symbols ──────────────────────────────────
    if len(results) < limit:
        ticker_to_name = {sym: nm for nm, sym in STOCKS.items()}
        ticker_list = list(ticker_to_name.keys())
        ticker_matches = process.extract(
            query.upper(),
            ticker_list,
            scorer=fuzz.WRatio,
            limit=limit,
            score_cutoff=60,
        )
        for match_ticker, score, _idx in ticker_matches:
            name = ticker_to_name[match_ticker]
            if name not in results:
                results[name] = (STOCKS[name], score)

    # ── 5. Fuzzy match on aliases ─────────────────────────────────────────
    if len(results) < limit:
        alias_keys = list(ALIASES.keys())
        alias_matches = process.extract(
            q_lower,
            alias_keys,
            scorer=fuzz.WRatio,
            limit=limit,
            score_cutoff=65,
        )
        for match_alias, score, _idx in alias_matches:
            canonical = ALIASES[match_alias]
            if canonical in STOCKS and canonical not in results:
                results[canonical] = (STOCKS[canonical], score)

    # Sort by score descending, return top `limit`
    sorted_results = sorted(results.items(), key=lambda x: x[1][1], reverse=True)
    return {name: symbol for name, (symbol, _score) in sorted_results[:limit]}
