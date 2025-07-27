from app.services.news_service import BengaluruNewsFetcher


def run_bengaluru_news() -> list:
    """
    Fetch and return filtered Bengaluru news articles.
    """
    news_fetcher = BengaluruNewsFetcher()
    articles = news_fetcher.fetch_news()

    if articles is None:
        return []

    return articles