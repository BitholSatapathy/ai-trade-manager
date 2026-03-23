import streamlit as st
import pandas as pd
from backend.main import run_pipeline
from backend.utils.search import search_stock

st.title("📈 AI Trade Manager (Indian Market)")

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
			st.write(f"RSI: {result['rsi']:.2f}")
			st.write(f"Moving Avg: {result['moving_avg']:.2f}")
			st.write(f"Sentiment: {result['sentiment']}")
			st.write(f"Decision: {result['decision']}")
			st.write(f"Confidence: {result.get('confidence', 50)}%")
			st.subheader("🧠 AI Insight")
			st.write(result["reason"])

			if "data" in result and "Close" in result["data"]:
				df = result["data"].copy()
				df["MA20"] = df["Close"].rolling(20).mean()

				st.line_chart(df[["Close", "MA20"]])
			else:
				st.warning("Price chart data is unavailable in this run. Please click Analyze again.")
	else:
		st.warning("No matching stocks found")
