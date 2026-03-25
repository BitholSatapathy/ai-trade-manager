from pathlib import Path
import sys

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

try:
	import plotly.graph_objects as go
except Exception:
	go = None

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))

from backend.main import run_pipeline
from backend.utils.search import search_stock
from backend.utils.stocks import INDEX_FUNDS
from backend.collector.stock_data import fetch_index_quotes

# ── Page Config ───────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Trade Manager", page_icon="📈", layout="wide")


# ── Ticker Tape ───────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def get_index_data():
    return fetch_index_quotes(INDEX_FUNDS)


def render_ticker_tape():
    index_data = get_index_data()
    if not index_data:
        return

    items_html = ""
    for name, info in index_data.items():
        price = info["price"]
        change = info["change_pct"]

        if change > 0:
            arrow = "▲"
            css_class = "ticker-up"
            sign = "+"
        elif change < 0:
            arrow = "▼"
            css_class = "ticker-down"
            sign = ""
        else:
            arrow = "—"
            css_class = "ticker-flat"
            sign = ""

        items_html += f'''
        <span class="ticker-item">
            <span class="ticker-name">{name}</span>
            <span class="ticker-price">₹{price:,.2f}</span>
            <span class="{css_class}">{arrow} {sign}{change:.2f}%</span>
        </span>
        <span class="ticker-sep">│</span>
        '''

    # Self-contained HTML rendered in an iframe via st.components.v1.html
    ticker_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: transparent;
            overflow: hidden;
            font-family: 'Segoe UI', -apple-system, sans-serif;
        }}
        .ticker-wrap {{
            width: 100%;
            overflow: hidden;
            background: linear-gradient(90deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
            border-radius: 8px;
            padding: 12px 0;
            border: 1px solid #30363d;
        }}
        .ticker-content {{
            display: inline-flex;
            white-space: nowrap;
            animation: ticker-scroll 35s linear infinite;
        }}
        .ticker-content:hover {{
            animation-play-state: paused;
        }}
        @keyframes ticker-scroll {{
            0%   {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}
        .ticker-item {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 0 20px;
            font-size: 13px;
            color: #c9d1d9;
        }}
        .ticker-name {{
            font-weight: 700;
            color: #f0f6fc;
            letter-spacing: 0.3px;
        }}
        .ticker-price {{
            color: #c9d1d9;
        }}
        .ticker-up {{
            color: #3fb950;
            font-weight: 600;
        }}
        .ticker-down {{
            color: #f85149;
            font-weight: 600;
        }}
        .ticker-flat {{
            color: #8b949e;
            font-weight: 600;
        }}
        .ticker-sep {{
            color: #30363d;
            padding: 0 2px;
            font-size: 16px;
        }}
    </style>
    </head>
    <body>
        <div class="ticker-wrap">
            <div class="ticker-content">
                {items_html}
                {items_html}
            </div>
        </div>
    </body>
    </html>
    """
    components.html(ticker_html, height=50, scrolling=False)


render_ticker_tape()


# ── Header ────────────────────────────────────────────────────────────────
st.title("📈 AI Trade Manager")
st.caption("AI-powered stock analysis for the Indian market 🇮🇳  •  200+ NSE stocks with smart search")


# ── Analysis Cache ────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def analyze_stock(symbol):
	return run_pipeline(symbol)


def build_chart_data(raw_data):
	if not isinstance(raw_data, pd.DataFrame) or raw_data.empty:
		return pd.DataFrame(columns=["Close", "MA20"])

	df = raw_data.copy()

	# Handle yfinance variants where Close can resolve to a Series or a DataFrame.
	close_obj = None
	if "Close" in df.columns:
		close_obj = df["Close"]
	else:
		# Case-insensitive fallback for unexpected column casing.
		for col in df.columns:
			if str(col).lower() == "close":
				close_obj = df[col]
				break

	if close_obj is None:
		return pd.DataFrame(columns=["Close", "MA20"])

	if isinstance(close_obj, pd.DataFrame):
		close_series = None
		for idx in range(close_obj.shape[1]):
			candidate = pd.to_numeric(close_obj.iloc[:, idx], errors="coerce")
			if candidate.notna().any():
				close_series = candidate
				break
		if close_series is None:
			return pd.DataFrame(columns=["Close", "MA20"])
	else:
		close_series = pd.to_numeric(close_obj, errors="coerce")

	chart_df = pd.DataFrame({"Close": close_series})
	chart_df["MA20"] = chart_df["Close"].rolling(window=5, min_periods=1).mean()
	chart_df = chart_df.dropna(subset=["Close"]).reset_index(drop=True)

	return chart_df


# ── Search UI ─────────────────────────────────────────────────────────────
query = st.text_input(
	"🔍 Search by company name, ticker, or abbreviation",
	placeholder="e.g. TCS, Reliance, bajaj, INFY, zomato..."
)

if query:
	results = search_stock(query)

	if results:
		# Show a subtle "matched" hint if the top match differs noticeably from the query
		top_match = list(results.keys())[0]
		if query.lower().strip() != top_match.lower().strip():
			st.caption(f"✨ Best match: **{top_match}** ({results[top_match]})")

		selected = st.selectbox(
			"Select Company",
			list(results.keys())
		)

		symbol = results[selected]

		if st.button("🚀 Analyze", type="primary"):
			with st.spinner(f"Analyzing {selected}..."):
				try:
					result = analyze_stock(symbol)

					st.subheader(f"{selected} ({symbol})")

					col1, col2, col3 = st.columns(3)

					col1.metric("RSI", f"{result['rsi']:.2f}")
					col2.metric("Moving Avg", f"₹{result['moving_avg']:.2f}")
					col3.metric("Sentiment", result["sentiment"])

					decision = result["decision"]

					if decision == "BUY":
						st.success(f"📈 Decision: {decision}")
					elif decision == "SELL":
						st.error(f"📉 Decision: {decision}")
					else:
						st.warning(f"⚖️ Decision: {decision}")

					st.subheader("Confidence Level")

					confidence = result.get("confidence", 50)
					st.progress(confidence / 100)
					st.write(f"{confidence}% confidence")

					st.subheader("🧠 AI Insight")
					st.info(result["reason"])

					st.subheader("📊 Price Trend with Moving Average")
					chart_df = build_chart_data(result.get("data"))
					if chart_df.empty:
						st.error("No chart data available")
					else:
						if go is not None:
							fig = go.Figure()
							fig.add_trace(
								go.Scatter(
									y=chart_df["Close"],
									mode="lines",
									name="Close",
									line=dict(color="#58a6ff", width=2),
								)
							)
							fig.add_trace(
								go.Scatter(
									y=chart_df["MA20"],
									mode="lines",
									name="MA20",
									line=dict(color="#f0883e", width=2, dash="dot"),
								)
							)
							fig.update_layout(
								height=360,
								margin=dict(l=20, r=20, t=30, b=20),
								plot_bgcolor="#0d1117",
								paper_bgcolor="#0d1117",
								font_color="#c9d1d9",
								legend=dict(
									orientation="h",
									yanchor="bottom",
									y=1.02,
									xanchor="right",
									x=1,
								),
							)
							st.plotly_chart(fig, use_container_width=True)
						else:
							# Safe fallback that does not rely on plotting backends.
							st.line_chart(chart_df[["Close", "MA20"]])
				except ValueError as err:
					analyze_stock.clear()
					st.warning(str(err))
				except Exception as err:
					analyze_stock.clear()
					st.error("We could not analyze this stock right now. Please try again in a minute.")
					st.caption(f"Debug: {type(err).__name__}: {err}")
	else:
		st.warning("No matching stocks found. Try a different name, ticker symbol, or abbreviation.")
