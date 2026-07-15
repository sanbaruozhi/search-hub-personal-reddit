"""Minimal, read-only Reddit Data API client for personal search.

This file mirrors the only Reddit API access path used by the local search
system. It intentionally contains no write, messaging, moderation, or user
profiling functionality.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from dataclasses import asdict, dataclass

import httpx


TOKEN_ENDPOINT = "https://www.reddit.com/api/v1/access_token"
SEARCH_ENDPOINT = "https://oauth.reddit.com/search"
USER_AGENT = "macos:search-hub-personal-reddit:v0.1 (by /u/Competitive-Bag-3069)"
MAX_RESULTS = 20
MAX_EXCERPT_CHARS = 600


@dataclass(frozen=True)
class PublicPost:
    title: str
    url: str
    subreddit: str
    created_utc: float | None
    score: int | None
    comment_count: int | None
    excerpt: str


def _credentials() -> tuple[str, str]:
    client_id = os.environ.get("REDDIT_CLIENT_ID", "").strip()
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise RuntimeError("Reddit credentials are not configured")
    return client_id, client_secret


def _clean_excerpt(value: object) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= MAX_EXCERPT_CHARS:
        return text
    return text[: MAX_EXCERPT_CHARS - 1].rstrip() + "…"


async def search_public_posts(query: str, *, limit: int = 5) -> list[PublicPost]:
    """Search public Reddit posts using official OAuth endpoints only."""

    query = " ".join(query.split())
    if not query:
        raise ValueError("query must not be blank")
    limit = max(1, min(int(limit), MAX_RESULTS))
    client_id, client_secret = _credentials()

    async with httpx.AsyncClient(
        timeout=30,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        token_response = await client.post(
            TOKEN_ENDPOINT,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        token_response.raise_for_status()
        token = str(token_response.json().get("access_token") or "").strip()
        if not token:
            raise RuntimeError("Reddit returned an empty OAuth token")

        response = await client.get(
            SEARCH_ENDPOINT,
            params={
                "q": query,
                "type": "link",
                "sort": "relevance",
                "t": "all",
                "limit": limit,
                "raw_json": 1,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": USER_AGENT,
            },
        )
        response.raise_for_status()

    children = response.json().get("data", {}).get("children", [])
    posts: list[PublicPost] = []
    for child in children:
        item = child.get("data", {}) if isinstance(child, dict) else {}
        permalink = str(item.get("permalink") or "").strip()
        if not permalink:
            continue
        posts.append(
            PublicPost(
                title=str(item.get("title") or "").strip(),
                url=f"https://www.reddit.com{permalink}",
                subreddit=str(item.get("subreddit_name_prefixed") or "").strip(),
                created_utc=item.get("created_utc") if isinstance(item.get("created_utc"), (int, float)) else None,
                score=item.get("score") if isinstance(item.get("score"), int) else None,
                comment_count=item.get("num_comments") if isinstance(item.get("num_comments"), int) else None,
                excerpt=_clean_excerpt(item.get("selftext")),
            )
        )
        if len(posts) >= limit:
            break
    return posts


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only personal Reddit search")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    posts = asyncio.run(search_public_posts(args.query, limit=args.limit))
    print(json.dumps([asdict(post) for post in posts], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
