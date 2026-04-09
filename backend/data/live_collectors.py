"""
Live API collectors for election social and sentiment data.

This module is optional and safe-by-default:
- If API keys are missing or API calls fail, callers can fallback to mock generators.
- Output schema matches create_dataset.py expectations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd
import requests

from config import SENTIMENT_KEYWORDS
from .sentiment_extractor import SentimentExtractor


PARTIES = ["LDF", "UDF", "NDA", "OTHERS"]


@dataclass
class ApiContext:
    x_bearer_token: str = ""
    youtube_api_key: str = ""
    news_api_key: str = ""


def load_env_file(path: Path) -> None:
    """Load KEY=VALUE entries from an env file into process env if unset."""
    import os

    if not path.exists():
        return

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_api_context() -> ApiContext:
    import os

    return ApiContext(
        x_bearer_token=os.getenv("X_BEARER_TOKEN", "").strip(),
        youtube_api_key=os.getenv("YOUTUBE_API_KEY", "").strip(),
        news_api_key=os.getenv("NEWS_API_KEY", "").strip(),
    )


def _party_queries() -> Dict[str, str]:
    queries: Dict[str, str] = {}
    for party in ["LDF", "UDF", "NDA"]:
        keywords = SENTIMENT_KEYWORDS.get(party, [])[:5]
        quoted = [f'"{kw}"' for kw in keywords if kw]
        queries[party] = " OR ".join(quoted) if quoted else party
    return queries


def _score_text(sentiment_extractor: SentimentExtractor, text: str) -> float:
    if not text:
        return 0.0
    return float(sentiment_extractor.analyze_text(text))


def _safe_get(url: str, *, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, str]] = None, timeout: int = 30) -> Optional[dict]:
    try:
        res = requests.get(url, headers=headers, params=params, timeout=timeout)
        if res.status_code != 200:
            return None
        return res.json()
    except Exception:
        return None


def fetch_news_records(
    news_api_key: str,
    sentiment_extractor: SentimentExtractor,
    *,
    from_date: str,
    to_date: Optional[str] = None,
    page_size: int = 50,
) -> List[dict]:
    if not news_api_key:
        return []

    records: List[dict] = []
    endpoint = "https://newsapi.org/v2/everything"
    today = datetime.utcnow().date().isoformat()
    queries = _party_queries()

    for party, query in queries.items():
        payload = _safe_get(
            endpoint,
            params={
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "from": from_date,
                "to": to_date or today,
                "pageSize": page_size,
                "apiKey": news_api_key,
            },
        )
        if not payload:
            continue

        for article in payload.get("articles", []):
            title = article.get("title") or ""
            desc = article.get("description") or ""
            text = f"{title}. {desc}".strip()
            published = article.get("publishedAt", "")[:10]
            date_month = published[:7] if len(published) >= 7 else today[:7]
            source_name = (article.get("source") or {}).get("name") or "News"
            records.append(
                {
                    "date_month": date_month,
                    "platform": "News",
                    "party": party,
                    "identifier": source_name,
                    "engagement_volume": 1,
                    "sentiment_score": _score_text(sentiment_extractor, text),
                }
            )

    return records


def fetch_youtube_records(
    youtube_api_key: str,
    sentiment_extractor: SentimentExtractor,
    *,
    max_results: int = 30,
) -> List[dict]:
    if not youtube_api_key:
        return []

    records: List[dict] = []
    search_url = "https://www.googleapis.com/youtube/v3/search"
    videos_url = "https://www.googleapis.com/youtube/v3/videos"
    queries = _party_queries()

    for party, query in queries.items():
        search_payload = _safe_get(
            search_url,
            params={
                "key": youtube_api_key,
                "part": "snippet",
                "q": f"Kerala election {query}",
                "type": "video",
                "maxResults": max_results,
                "order": "date",
            },
        )
        if not search_payload:
            continue

        ids = [
            ((item.get("id") or {}).get("videoId"))
            for item in search_payload.get("items", [])
        ]
        ids = [video_id for video_id in ids if video_id]
        if not ids:
            continue

        stats_payload = _safe_get(
            videos_url,
            params={
                "key": youtube_api_key,
                "part": "statistics,snippet",
                "id": ",".join(ids),
            },
        )
        if not stats_payload:
            continue

        for item in stats_payload.get("items", []):
            snippet = item.get("snippet") or {}
            stats = item.get("statistics") or {}
            title = snippet.get("title") or ""
            published = (snippet.get("publishedAt") or "")[:10]
            date_month = published[:7] if len(published) >= 7 else datetime.utcnow().date().isoformat()[:7]
            views = int(stats.get("viewCount", 0) or 0)
            likes = int(stats.get("likeCount", 0) or 0)
            comments = int(stats.get("commentCount", 0) or 0)
            engagement = views + likes * 3 + comments * 5

            records.append(
                {
                    "date_month": date_month,
                    "platform": "YouTube",
                    "party": party,
                    "identifier": snippet.get("channelTitle") or "YouTube",
                    "engagement_volume": int(engagement),
                    "sentiment_score": _score_text(sentiment_extractor, title),
                }
            )

    return records


def fetch_x_records(
    x_bearer_token: str,
    sentiment_extractor: SentimentExtractor,
    *,
    max_results: int = 100,
) -> List[dict]:
    """
    Fetch recent tweets from X API v2.
    Note: standard recent endpoint only covers recent days.
    """
    if not x_bearer_token:
        return []

    records: List[dict] = []
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {x_bearer_token}"}
    queries = _party_queries()

    for party, query in queries.items():
        payload = _safe_get(
            url,
            headers=headers,
            params={
                "query": f"({query}) lang:en -is:retweet",
                "max_results": min(max_results, 100),
                "tweet.fields": "created_at,public_metrics,text",
            },
        )
        if not payload:
            continue

        for tweet in payload.get("data", []):
            metrics = tweet.get("public_metrics") or {}
            likes = int(metrics.get("like_count", 0) or 0)
            replies = int(metrics.get("reply_count", 0) or 0)
            reposts = int(metrics.get("retweet_count", 0) or 0)
            quotes = int(metrics.get("quote_count", 0) or 0)
            engagement = likes + replies * 3 + reposts * 4 + quotes * 2

            created = (tweet.get("created_at") or "")[:10]
            date_month = created[:7] if len(created) >= 7 else datetime.utcnow().date().isoformat()[:7]
            text = tweet.get("text") or ""

            records.append(
                {
                    "date_month": date_month,
                    "platform": "Twitter/X",
                    "party": party,
                    "identifier": "X search",
                    "engagement_volume": int(engagement),
                    "sentiment_score": _score_text(sentiment_extractor, text),
                }
            )

    return records


def create_social_media_details_live(
    sentiment_extractor: SentimentExtractor,
    *,
    from_date: str = "2024-01-01",
    to_date: Optional[str] = None,
) -> pd.DataFrame:
    """Build live social-media detail rows with create_dataset-compatible schema."""
    ctx = get_api_context()

    rows: List[dict] = []
    rows.extend(fetch_x_records(ctx.x_bearer_token, sentiment_extractor))
    rows.extend(fetch_youtube_records(ctx.youtube_api_key, sentiment_extractor))
    rows.extend(fetch_news_records(ctx.news_api_key, sentiment_extractor, from_date=from_date, to_date=to_date))

    if not rows:
        return pd.DataFrame(columns=[
            "date_month",
            "platform",
            "party",
            "identifier",
            "engagement_volume",
            "sentiment_score",
        ])

    df = pd.DataFrame(rows)
    df["engagement_volume"] = df["engagement_volume"].astype(int)
    df["sentiment_score"] = df["sentiment_score"].astype(float)
    return df


def _percentage_split(scores: Iterable[float]) -> tuple[int, int, int]:
    scores_list = list(scores)
    if not scores_list:
        return 0, 0, 100
    total = len(scores_list)
    pos = sum(1 for s in scores_list if s > 0.1)
    neg = sum(1 for s in scores_list if s < -0.1)
    neu = total - pos - neg
    return int(round((pos / total) * 100)), int(round((neg / total) * 100)), int(round((neu / total) * 100))


def create_sentiment_data_live(social_df: pd.DataFrame) -> pd.DataFrame:
    """Create party summary schema compatible with create_sentiment_data()."""
    base_defaults: Dict[str, Dict[str, float]] = {
        "LDF": {
            "governance_score": 0.58,
            "change_sentiment": 0.20,
            "development_score": 0.60,
            "welfare_score": 0.65,
            "sabarimala_gold_impact": -0.15,
            "healthcare_crisis_impact": -0.12,
            "unemployment_impact": -0.10,
            "fcra_controversy_impact": 0.02,
            "ls2024_momentum": -0.20,
            "lb2025_momentum": -0.12,
            "anti_incumbency_score": -0.18,
            "ai_campaign_score": 0.30,
            "ground_campaign_score": 0.70,
            "celebrity_endorsement": 0.15,
            "poll_seats_low": 57,
            "poll_seats_mid": 65,
            "poll_seats_high": 78,
            "poll_vote_share": 36.5,
        },
        "UDF": {
            "governance_score": 0.42,
            "change_sentiment": 0.75,
            "development_score": 0.45,
            "welfare_score": 0.50,
            "sabarimala_gold_impact": 0.10,
            "healthcare_crisis_impact": 0.08,
            "unemployment_impact": 0.05,
            "fcra_controversy_impact": 0.05,
            "ls2024_momentum": 0.35,
            "lb2025_momentum": 0.25,
            "anti_incumbency_score": 0.20,
            "ai_campaign_score": 0.20,
            "ground_campaign_score": 0.65,
            "celebrity_endorsement": 0.25,
            "poll_seats_low": 49,
            "poll_seats_mid": 68,
            "poll_seats_high": 81,
            "poll_vote_share": 38.5,
        },
        "NDA": {
            "governance_score": 0.30,
            "change_sentiment": 0.50,
            "development_score": 0.40,
            "welfare_score": 0.30,
            "sabarimala_gold_impact": 0.08,
            "healthcare_crisis_impact": 0.03,
            "unemployment_impact": 0.04,
            "fcra_controversy_impact": -0.08,
            "ls2024_momentum": 0.15,
            "lb2025_momentum": 0.10,
            "anti_incumbency_score": 0.08,
            "ai_campaign_score": 0.35,
            "ground_campaign_score": 0.45,
            "celebrity_endorsement": 0.30,
            "poll_seats_low": 1,
            "poll_seats_mid": 7,
            "poll_seats_high": 17,
            "poll_vote_share": 20.2,
        },
        "OTHERS": {
            "governance_score": 0.15,
            "change_sentiment": 0.25,
            "development_score": 0.10,
            "welfare_score": 0.10,
            "sabarimala_gold_impact": 0.0,
            "healthcare_crisis_impact": 0.0,
            "unemployment_impact": 0.0,
            "fcra_controversy_impact": 0.0,
            "ls2024_momentum": -0.05,
            "lb2025_momentum": -0.03,
            "anti_incumbency_score": 0.0,
            "ai_campaign_score": 0.0,
            "ground_campaign_score": 0.15,
            "celebrity_endorsement": 0.05,
            "poll_seats_low": 0,
            "poll_seats_mid": 0,
            "poll_seats_high": 0,
            "poll_vote_share": 4.8,
        },
    }

    rows: List[dict] = []
    for party in PARTIES:
        part_df = social_df[social_df["party"] == party] if not social_df.empty else pd.DataFrame()

        news_df = part_df[part_df["platform"] == "News"] if not part_df.empty else pd.DataFrame()
        x_df = part_df[part_df["platform"] == "Twitter/X"] if not part_df.empty else pd.DataFrame()
        yt_df = part_df[part_df["platform"] == "YouTube"] if not part_df.empty else pd.DataFrame()

        sentiment_values = part_df["sentiment_score"].tolist() if not part_df.empty else []
        pos_pct, neg_pct, neu_pct = _percentage_split(sentiment_values)

        defaults = base_defaults[party]

        row = {
            "party": party,
            "news_sentiment": float(news_df["sentiment_score"].mean()) if not news_df.empty else 0.0,
            "twitter_mentions": int(len(x_df)),
            "facebook_engagement": 0,
            "instagram_posts": 0,
            "linkedin_articles": int(len(news_df)),
            "youtube_views": int(yt_df["engagement_volume"].sum()) if not yt_df.empty else 0,
            "positive_mentions_pct": pos_pct,
            "negative_mentions_pct": neg_pct,
            "neutral_mentions_pct": neu_pct,
            "final_sentiment_score": float(part_df["sentiment_score"].mean()) if not part_df.empty else 0.0,
            **defaults,
        }

        rows.append(row)

    return pd.DataFrame(rows)
