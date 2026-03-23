def generate_reason(rsi, sentiment, decision):

    if decision == "BUY":
        return f"""
The stock indicates a bullish opportunity. 
RSI suggests it may be undervalued or gaining momentum, 
and the overall news sentiment is {sentiment.lower()}, 
which supports potential upward movement. 
Investors may consider accumulating positions.
"""

    elif decision == "SELL":
        return f"""
The stock shows signs of bearish pressure. 
RSI indicates overbought conditions or weakening momentum, 
combined with {sentiment.lower()} sentiment in news. 
This could signal a potential decline, suggesting caution or exit.
"""

    else:
        return f"""
The stock is currently in a neutral zone. 
RSI is balanced and sentiment is {sentiment.lower()}, 
indicating no strong directional bias. 
Holding existing positions may be a reasonable approach.
"""
