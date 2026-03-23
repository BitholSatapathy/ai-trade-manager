from pathlib import Path
import sys

import streamlit as st
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))

from backend.main import run_pipeline
from backend.utils.search import search_stock


@st.cache_data(ttl=300, show_spinner=False)
def analyze_stock(symbol):
	return run_pipeline(symbol)

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

				if "data" in result and "Close" in result["data"]:
					try:
						df = result["data"].copy()

						close_data = df["Close"]
						if isinstance(close_data, pd.DataFrame):
							# yfinance may return duplicate/multi-level Close columns; use the first valid series.
							close_data = close_data.iloc[:, 0]

						chart_df = pd.DataFrame()
						chart_df["Close"] = pd.to_numeric(close_data, errors="coerce")
						chart_df["MA20"] = chart_df["Close"].rolling(20, min_periods=1).mean()
						chart_df = chart_df.dropna(subset=["Close"]).reset_index(drop=True)

						st.subheader("📊 Price Trend with Moving Average")
						if chart_df.empty:
							st.warning("Price chart data is unavailable right now.")
						else:
							st.line_chart(chart_df[["Close", "MA20"]])
					except Exception as chart_err:
						st.warning("Could not render chart for this stock right now.")
						st.caption(f"Chart Debug: {type(chart_err).__name__}")
				else:
					st.warning("Price chart data is unavailable in this run. Please click Analyze again.")
			except ValueError as err:
				analyze_stock.clear()
				st.warning(str(err))
			except Exception as err:
				analyze_stock.clear()
				st.error("We could not analyze this stock right now. Please try again in a minute.")
				st.caption(f"Debug: {type(err).__name__}: {err}")
	else:
		st.warning("No matching stocks found")
