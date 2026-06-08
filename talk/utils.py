from .model import articles


def filter_articles(words):
    return [word for word in words if word.lower() not in articles]
