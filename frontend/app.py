from pathlib import Path
import sys

import streamlit as st
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

st.title("📈 AI Trade Manager (Indian Market)")
st.caption("AI-powered stock analysis system for Indian markets 🇮🇳")

query = st.text_input("Search Company (e.g. Reliance, TCS)")

if query:
	results = search_stock(query)

	if results:
		selected = st.selectbox(
			"Select Company",
			list(results.keys())
		)

		symbol = results[selected]

		if st.button("Analyze"):
			try:
				result = analyze_stock(symbol)

				st.subheader(f"{selected} ({symbol})")

				col1, col2, col3 = st.columns(3)

				col1.metric("RSI", f"{result['rsi']:.2f}")
				col2.metric("Moving Avg", f"{result['moving_avg']:.2f}")
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
							)
						)
						fig.add_trace(
							go.Scatter(
								y=chart_df["MA20"],
								mode="lines",
								name="MA20",
							)
						)
						fig.update_layout(height=360, margin=dict(l=20, r=20, t=30, b=20))
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
		st.warning("No matching stocks found")
