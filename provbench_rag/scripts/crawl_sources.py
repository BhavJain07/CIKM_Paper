"""Download URLs from a manifest (one URL per line) into a snapshot directory."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _safe_name(url: str) -> str:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return h


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("url_manifest", help="Text file with one URL per line")
    ap.add_argument("out_dir", help="Directory to write downloaded files")
    ap.add_argument("--user-agent", default="ProvBench-RAG/0.1 (+research snapshot)")
    args = ap.parse_args(argv)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ok = 0
    with Path(args.url_manifest).open(encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if not url or url.startswith("#"):
                continue
            target = out / f"{_safe_name(url)}.txt"
            req = Request(url, headers={"User-Agent": args.user_agent})
            try:
                with urlopen(req, timeout=60) as resp:  # noqa: S310
                    body = resp.read()
                target.write_bytes(body)
                ok += 1
            except (HTTPError, URLError, TimeoutError, OSError) as e:
                print(f"FAIL {url}: {e}")
    print(f"Downloaded {ok} files into {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
