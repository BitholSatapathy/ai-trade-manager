from pathlib import Path
import sys

import streamlit as st
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))

from backend.main import run_pipeline
from backend.utils.search import search_stock

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
			result = run_pipeline(symbol)

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

			st.progress(result["confidence"] / 100)
			st.write(f"{result['confidence']}% confidence")

			st.subheader("🧠 AI Insight")
			st.info(result["reason"])

			if "data" in result and "Close" in result["data"]:
				df = result["data"].copy()
				df["MA20"] = df["Close"].rolling(20).mean()

				st.subheader("📊 Price Trend with Moving Average")
				st.line_chart(df[["Close", "MA20"]])
			else:
				st.warning("Price chart data is unavailable in this run. Please click Analyze again.")
	else:
		st.warning("No matching stocks found")
