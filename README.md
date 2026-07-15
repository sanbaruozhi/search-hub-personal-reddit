# search-hub-personal-reddit

This repository contains the Reddit Data API component of a local, private,
non-commercial personal search tool. It is published so Reddit can review the
exact code path that accesses its API.

## Purpose

The component helps one Reddit account holder discover relevant public posts
and communities. It performs low-volume, read-only keyword searches only when
the owner explicitly asks a question. Results retain Reddit attribution and
link directly to the original Reddit pages.

This component does **not**:

- post, comment, vote, moderate, or send private messages;
- scrape Reddit web pages or circumvent API limits;
- bulk export or redistribute Reddit content;
- train machine-learning or AI models with Reddit data;
- profile Redditors or infer sensitive characteristics;
- sell, license, or commercialize Reddit data.

## Why Devvit does not fit

Devvit is intended for apps that run inside Reddit and serve subreddit
experiences. This use case is an external, local-only research client that
performs read-only cross-community discovery and combines source links for one
user. It has no on-Reddit UI and performs no subreddit installation or write
actions.

## Data flow

1. The owner enters a search query locally.
2. The client requests an application-only OAuth token from Reddit.
3. The client calls the official `oauth.reddit.com/search` endpoint with a
   maximum of 20 results.
4. It returns a minimal set of public fields: title, permalink, subreddit,
   creation time, score, comment count, and a shortened text excerpt.
5. The standalone review client prints the response locally and does not store
   it.

The larger private search system may keep a short-lived local cache solely to
support the owner's immediate search workflow. It does not expose a public API
or provide Reddit data to other users.

## Credentials

Credentials are never committed. For local review, provide them through the
`REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` environment variables. The
production installation stores its credential bundle in the macOS Keychain.

## Local review

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export REDDIT_CLIENT_ID='...'
export REDDIT_CLIENT_SECRET='...'
python reddit_readonly_client.py "OpenAI" --limit 5
```

API access is attempted only after Reddit approval is granted.
