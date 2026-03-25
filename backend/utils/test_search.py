"""Unit tests for the fuzzy stock search engine."""
import sys
from pathlib import Path

# Ensure project root is on the path so relative imports work.
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.utils.search import search_stock


# ── Alias matches ─────────────────────────────────────────────────────────
def test_alias_tcs():
    results = search_stock("tcs")
    assert "Tata Consultancy Services" in results
    assert results["Tata Consultancy Services"] == "TCS.NS"


def test_alias_sbi():
    results = search_stock("sbi")
    assert "State Bank of India" in results


def test_alias_ril():
    results = search_stock("ril")
    assert "Reliance Industries" in results


# ── Fuzzy / misspelled ────────────────────────────────────────────────────
def test_fuzzy_misspelled():
    results = search_stock("tata consultsncy")
    assert "Tata Consultancy Services" in results


def test_fuzzy_partial_bajaj():
    results = search_stock("bajaj")
    names = list(results.keys())
    bajaj_hits = [n for n in names if "bajaj" in n.lower()]
    assert len(bajaj_hits) >= 1


# ── Ticker symbol search ─────────────────────────────────────────────────
def test_ticker_infy():
    results = search_stock("INFY")
    assert "Infosys" in results


def test_ticker_reliance():
    results = search_stock("RELIANCE")
    assert "Reliance Industries" in results


# ── Case insensitivity ────────────────────────────────────────────────────
def test_case_insensitive():
    r1 = search_stock("TCS")
    r2 = search_stock("tcs")
    r3 = search_stock("Tcs")
    assert "Tata Consultancy Services" in r1
    assert "Tata Consultancy Services" in r2
    assert "Tata Consultancy Services" in r3


# ── Empty / nonsense ──────────────────────────────────────────────────────
def test_empty_query():
    assert search_stock("") == {}
    assert search_stock("   ") == {}


def test_nonsense_query():
    results = search_stock("xyzzyfoobarbaz")
    # Should return empty or very low-confidence results
    assert len(results) <= 2


# ── New-age stocks ────────────────────────────────────────────────────────
def test_zomato():
    results = search_stock("zomato")
    assert "Zomato" in results


def test_paytm():
    results = search_stock("paytm")
    assert any("Paytm" in name for name in results)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
