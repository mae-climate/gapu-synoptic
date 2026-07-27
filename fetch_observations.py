"""
Pull your own logged observations (flooded / dry / other note) from
GitHub issues tagged with OBSERVATION_LABEL, so the "recent outlook log"
panel can show verdict-vs-actual over time.

Uses the public issues API -- no auth needed for a public repo, GitHub's
own rate limit (60 req/hr unauthenticated) is plenty for a scheduled job
that runs a handful of times a day.
"""

from __future__ import annotations

import requests

from config import GITHUB_REPO, OBSERVATION_LABEL, HEADERS

API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/issues"


def fetch_observations(limit: int = 10) -> list[dict]:
    params = {"labels": OBSERVATION_LABEL, "state": "all", "per_page": limit}
    resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    out = []
    for issue in resp.json():
        out.append({
            "date": issue["created_at"][:10],
            "title": issue["title"],
            "body": (issue.get("body") or "").strip(),
            "url": issue["html_url"],
        })
    return out


def observation_submit_url(prefill_date: str = "") -> str:
    """Build the 'log an observation' link shown on the page -- opens a
    pre-filled GitHub issue, no API key or backend needed to accept it."""
    title = f"Observation {prefill_date}".strip()
    body = "Flooded / dry / other -- describe what actually happened:\n\n"
    from urllib.parse import quote
    return (
        f"https://github.com/{GITHUB_REPO}/issues/new"
        f"?title={quote(title)}&body={quote(body)}&labels={OBSERVATION_LABEL}"
    )


if __name__ == "__main__":
    import json

    print(json.dumps(fetch_observations(), indent=2))
    print(observation_submit_url())
