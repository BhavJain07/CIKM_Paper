"""JSONL helpers."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def iter_jsonl(path: str | Path, model: type[T]) -> Iterator[T]:
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield model.model_validate_json(line)


def write_jsonl(path: str | Path, records: list[BaseModel]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(r.model_dump_json() + "\n")


def map_jsonl(path: str | Path, fn: Callable[[dict], dict | None], out_path: str | Path) -> int:
    """Transform JSONL dict lines; skip when fn returns None."""
    n = 0
    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open(encoding="utf-8") as inp, outp.open("w", encoding="utf-8") as out:
        for line in inp:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            mapped = fn(obj)
            if mapped is None:
                continue
            out.write(json.dumps(mapped, ensure_ascii=False) + "\n")
            n += 1
    return n
