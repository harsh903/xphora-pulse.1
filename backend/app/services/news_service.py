#!/usr/bin/env python3
# Mediastack Bengaluru News Fetcher (Class-Based, JSON Filtered)

import requests
from datetime import datetime, timedelta
from config import NEWS_API_KEY

class BengaluruNewsFetcher():
    BASE_URL = 'http://api.mediastack.com/v1/news'

    def __init__(self):
        self.api_key = NEWS_API_KEY

    def fetch_news(self):
        """
        Fetch and return filtered Bengaluru news (last 3 days): title, description, url, published_at
        """
        try:
            params = {
                'access_key': self.api_key,
                'countries': 'in',
                'keywords': 'Bengaluru',
                'sort': 'published_desc',
                'limit': 100
            }

            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()

            data = response.json()

            if 'error' in data:
                print(f"API error: {data['error']['info']}")
                return None

            articles = data.get('data', [])
            fifteen_days_ago = datetime.utcnow() - timedelta(days=15)
            filtered_articles = []

            for article in articles:
                published_at = article.get('published_at')
                if published_at:
                    try:
                        pub_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
                        if pub_date >= fifteen_days_ago:
                            filtered_articles.append({
                                'title': article.get('title'),
                                'description': article.get('description'),
                                'url': article.get('url'),
                                'published_at': published_at
                            })
                    except ValueError:
                        # Skip article if date format is wrong
                        continue

            return filtered_articles

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"Error fetching news: {e}")
            return None
