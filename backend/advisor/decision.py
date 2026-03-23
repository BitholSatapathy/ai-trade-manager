def make_decision(rsi, sentiment):

    score = 0

    if rsi < 30:
        score += 1
    elif rsi > 70:
        score -= 1

    if sentiment == "Positive":
        score += 1
    elif sentiment == "Negative":
        score -= 1

    if score >= 2:
        return "BUY", 85
    elif score <= -2:
        return "SELL", 85
    elif score == 1:
        return "BUY", 65
    elif score == -1:
        return "SELL", 65
    else:
        return "HOLD", 50
