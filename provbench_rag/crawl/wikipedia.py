"""English Wikipedia via MediaWiki Action API (no key required for read requests)."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from provbench_rag.crawl.html_text import html_to_text

_API = "https://en.wikipedia.org/w/api.php"
_PARSE = "https://en.wikipedia.org/w/index.php"


def _wiki_delay():
    # Conservative default to reduce likelihood of 429s.
    time.sleep(0.5)


def _retry_sleep_seconds(err: HTTPError, attempt: int) -> float:
    """
    Backoff for transient MediaWiki throttling / upstream errors.

    Prefer `Retry-After` when provided; otherwise exponential backoff with a cap.
    """
    try:
        ra = err.headers.get("Retry-After")
        if ra:
            return float(ra)
    except Exception:
        pass
    return min(60.0, 1.5**attempt)


def _urlopen_with_retries(req: urllib.request.Request, timeout_s: float) -> bytes:
    last: Exception | None = None
    for attempt in range(1, 9):
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                return resp.read()
        except HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(_retry_sleep_seconds(e, attempt))
                continue
            raise
        except OSError as e:
            last = e
            time.sleep(min(10.0, 1.5**attempt))
            continue
    if last is None:
        raise OSError("urlopen failed without exception")
    raise last


@dataclass(frozen=True)
class RevisionMeta:
    rev_id: int
    timestamp: datetime
    size: int


def api_get(params: dict[str, str], user_agent: str) -> dict[str, Any]:
    """GET request to MediaWiki API with JSON response."""
    qs = urllib.parse.urlencode({**params, "format": "json"})
    url = f"{_API}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})  # noqa: S310
    _wiki_delay()
    raw = _urlopen_with_retries(req, timeout_s=60)
    return json.loads(raw.decode("utf-8"))


def parse_revision_html(rev_id: int, user_agent: str) -> str:
    """Render revision to HTML via index.php?oldid= and strip to text."""
    qs = urllib.parse.urlencode({"oldid": str(rev_id)})
    url = f"{_PARSE}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})  # noqa: S310
    _wiki_delay()
    raw = _urlopen_with_retries(req, timeout_s=60)
    html = raw.decode("utf-8", errors="replace")
    return html_to_text(html)


def list_revisions(title: str, limit: int, user_agent: str) -> tuple[int, list[RevisionMeta]]:
    """
    Return (page_id, revisions newest-first).
    """
    data = api_get(
        {
            "action": "query",
            "titles": title,
            "prop": "revisions",
            "rvprop": "ids|timestamp|size",
            "rvlimit": str(limit),
        },
        user_agent,
    )
    pages = data.get("query", {}).get("pages", {})
    if not pages:
        raise ValueError(f"No page for title={title!r}")
    page = next(iter(pages.values()))
    if page.get("missing") or int(page.get("pageid", -1)) < 0:
        raise ValueError(f"missing page for title={title!r}")
    pid = int(page["pageid"])
    revs_raw = page.get("revisions", [])
    out: list[RevisionMeta] = []
    for r in revs_raw:
        ts = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00"))
        out.append(RevisionMeta(rev_id=int(r["revid"]), timestamp=ts, size=int(r.get("size", 0))))
    return pid, out


def revision_validity_window(ts: datetime) -> tuple[date | None, date | None]:
    """Coarse validity: open-ended from revision date."""
    d = ts.date()
    return d, None
