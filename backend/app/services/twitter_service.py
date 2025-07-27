# twitter_agent.py
import os
import time
import json
import requests
import pandas as pd
from collections import Counter
from datetime import datetime, timedelta, timezone

from config import TWITTER_API_KEY

class TwitterCivicAgent:
    def __init__(self):
        self.TWITTER_API_KEY = TWITTER_API_KEY
        self.BASE_URL = "https://api.twitterapi.io/twitter/tweet/advanced_search"
        self.RESULTS_DIR = "bengaluru_civic_tweets"

        self.HASHTAGS = [
            "bengalururains", "bangalorefloods", "bescom",
            "bengalurupowercuts", "bbmp", "bwssb"
        ]

        self.AREAS = [
            "whitefield", "electronic city", "koramangala", "indiranagar", "jayanagar",
            "hsr layout", "marathahalli", "jp nagar", "bannerghatta", "hebbal",
            "bellandur", "sarjapur", "mahadevapura", "yelahanka", "btm layout",
            "malleshwaram", "rr nagar", "basavanagudi", "kengeri", "banashankari"
        ]

        if not os.path.exists(self.RESULTS_DIR):
            os.makedirs(self.RESULTS_DIR)

    def make_api_request(self, query, cursor=None, limit=100):
        headers = {"X-API-Key": self.TWITTER_API_KEY}
        params = {
            "query": query,
            "limit": min(20, limit)
        }
        if cursor:
            params["cursor"] = cursor

        try:
            response = requests.get(self.BASE_URL, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            return None

    def extract_tweets(self, query, max_tweets=100):
        all_tweets = []
        cursor = None

        while len(all_tweets) < max_tweets:
            remaining = max_tweets - len(all_tweets)
            data = self.make_api_request(query, cursor, remaining)

            if not data or "tweets" not in data or not data["tweets"]:
                break

            all_tweets.extend(data["tweets"])
            if "nextCursor" in data and data["nextCursor"]:
                cursor = data["nextCursor"]
                time.sleep(1)
            else:
                break

        return all_tweets[:max_tweets]

    def process_tweets(self, tweets):
        rows = []
        for tweet in tweets:
            row = {
                "id": tweet.get("id", ""),
                "text": tweet.get("text", ""),
                "created_at": tweet.get("createdAt", ""),
                "retweet_count": tweet.get("retweetCount", 0),
                "reply_count": tweet.get("replyCount", 0),
                "like_count": tweet.get("likeCount", 0),
                "view_count": tweet.get("viewCount", 0),
                "url": tweet.get("url", ""),
                "language": tweet.get("lang", ""),
            }

            if "author" in tweet and tweet["author"]:
                author = tweet["author"]
                row.update({
                    "author_id": author.get("id", ""),
                    "author_username": author.get("userName", ""),
                    "author_name": author.get("name", ""),
                    "author_location": author.get("location", ""),
                    "author_followers": author.get("followers", 0),
                })

            rows.append(row)

        df = pd.DataFrame(rows)
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"])
        return df

    def analyze_sentiment(self, df):
        positive = ["fixed", "resolved", "thank", "good", "working", "restored", "solved"]
        negative = ["problem", "issue", "outage", "down", "broken", "fail", "terrible", "pathetic"]

        def get_sentiment(text):
            if not isinstance(text, str):
                return "neutral"
            text = text.lower()
            pos = sum(word in text for word in positive)
            neg = sum(word in text for word in negative)
            return "positive" if pos > neg else "negative" if neg > pos else "neutral"

        df["sentiment"] = df["text"].apply(get_sentiment)
        return df

    def extract_locations(self, df):
        def find_area(text):
            if not isinstance(text, str):
                return None
            text = text.lower()
            matches = [area for area in self.AREAS if area in text]
            return ", ".join(matches) if matches else None

        df["mentioned_areas"] = df["text"].apply(find_area)
        return df

    def fetch_and_process(self, query: str, issue_type: str = "general", save=False):
        hashtags = " OR ".join([f"#{h}" for h in self.HASHTAGS])
        final_query = f"({query}) AND (Bengaluru OR Bangalore) AND ({hashtags})"

        tweets = self.extract_tweets(final_query, max_tweets=100)
        if not tweets:
            return None

        df = self.process_tweets(tweets)
        df = self.analyze_sentiment(df)
        df = self.extract_locations(df)
        df["issue_type"] = issue_type

        # ✅ Filter for last 15 days only
        now = datetime.now(timezone.utc)

        past_15_days = now - timedelta(days=15)
        df = df[df["created_at"] >= past_15_days]

        if df.empty:
            print("ℹ️ No tweets in the last 15 days for this query.")
            return None

        if save:
            df.to_csv(f"{self.RESULTS_DIR}/{issue_type}_tweets.csv", index=False)
        print(df)
        return df

