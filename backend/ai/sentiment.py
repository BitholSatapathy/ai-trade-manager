from textblob import TextBlob


def get_sentiment(news_list):
    if not news_list:
        return "Neutral"

    scores = []

    for news in news_list:
        score = TextBlob(news).sentiment.polarity
        scores.append(score)

    avg = sum(scores) / len(scores)

    if avg > 0:
        return "Positive"
    elif avg < 0:
        return "Negative"
    else:
        return "Neutral"
