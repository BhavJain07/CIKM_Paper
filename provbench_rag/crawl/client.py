"""Politeness-first HTTP client: robots.txt, delays, retries, size caps."""

from __future__ import annotations

import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser


def _default_user_agent() -> str:
    return (
        "ProvBench-RAG/0.1 (research corpus builder; academic use) "
        "Python-urllib/laboratory"
    )


@dataclass
class PoliteHttpClient:
    """
    Fetches URLs only when allowed by robots.txt for the host's /robots.txt User-agent: *.
    Uses random jitter on delay to avoid synchronized hits.
    """

    user_agent: str = field(default_factory=_default_user_agent)
    min_delay_s: float = 1.0
    max_delay_s: float = 2.5
    max_bytes: int = 5_000_000
    timeout_s: int = 45
    retries: int = 3
    _last_fetch_monotonic: dict[str, float] = field(default_factory=dict)
    _robots: dict[str, RobotFileParser | None] = field(default_factory=dict)

    def _robots_for(self, url: str) -> RobotFileParser | None:
        p = urlparse(url)
        host = f"{p.scheme}://{p.netloc}"
        if host in self._robots:
            return self._robots[host]
        robots_url = f"{host}/robots.txt"
        rp = RobotFileParser()
        try:
            rp.set_url(robots_url)
            rp.read()
        except (urllib.error.URLError, OSError):
            self._robots[host] = None
            return None
        self._robots[host] = rp
        return rp

    def allowed(self, url: str) -> bool:
        rp = self._robots_for(url)
        if rp is None:
            return True
        return rp.can_fetch(self.user_agent, url)

    def _sleep_polite(self, url: str) -> None:
        p = urlparse(url)
        host = p.netloc
        now = time.monotonic()
        last = self._last_fetch_monotonic.get(host, 0.0)
        wait = self.min_delay_s + random.random() * max(0.0, self.max_delay_s - self.min_delay_s)
        delta = wait - (now - last)
        if delta > 0:
            time.sleep(delta)
        self._last_fetch_monotonic[host] = time.monotonic()

    def get_bytes(self, url: str) -> tuple[bytes, str | None]:
        """Return (body, content_type or None). Raises on HTTP errors after retries."""
        if not self.allowed(url):
            raise PermissionError(f"robots.txt disallows fetch: {url}")
        last_err: Exception | None = None
        for attempt in range(self.retries):
            self._sleep_polite(url)
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,text/plain,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                },
                method="GET",
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:  # noqa: S310
                    ctype = resp.headers.get_content_type()
                    data = resp.read(self.max_bytes + 1)
                if len(data) > self.max_bytes:
                    raise ValueError(f"response exceeds max_bytes for {url}")
                return data, ctype
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as e:
                last_err = e
                time.sleep(1.0 * (attempt + 1))
        assert last_err is not None
        raise last_err

    def get_text(self, url: str) -> tuple[str, str]:
        """Best-effort decode as UTF-8 with replacement; returns (text, final_url not tracked)."""
        raw, _ctype = self.get_bytes(url)
        return raw.decode("utf-8", errors="replace"), url
