"""Pydantic models aligned with documents.jsonl, queries.jsonl, clusters.jsonl."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ParagraphSpan(BaseModel):
    """Character offsets into `text` for a paragraph-level slice."""

    start: int = Field(ge=0)
    end: int = Field(ge=0)

    @model_validator(mode="after")
    def end_after_start(self) -> "ParagraphSpan":
        if self.end < self.start:
            raise ValueError("end must be >= start")
        return self


class DocumentRecord(BaseModel):
    doc_id: str
    cluster_id: str
    source_url: str
    source_type: str
    authority_level: int = Field(ge=1, le=5, description="1=low, 5=official/canonical")
    publication_date: date | None = None
    validity_start: date | None = None
    validity_end: date | None = None
    jurisdiction: str | None = None
    original_or_copy_label: Literal["original", "copy", "mirror", "summary", "unknown"]
    text: str
    paragraph_spans: list[ParagraphSpan] = Field(default_factory=list)


class QueryRecord(BaseModel):
    query_id: str
    query_text: str
    domain: str
    query_time: date | datetime | None = None
    query_jurisdiction: str | None = None
    gold_answer: str
    acceptable_answers: list[str] = Field(default_factory=list)
    gold_evidence_ids: list[str]
    minimal_evidence_ids: list[str]
    preferred_source_ids: list[str]
    abstain_required: bool = False


class ClusterRecord(BaseModel):
    cluster_id: str
    relation_type: Literal[
        "original_vs_copy",
        "fresh_vs_stale",
        "authority_split",
        "jurisdiction_mismatch",
        "conflict",
    ]
    document_ids: list[str]
    canonical_source_id: str | None = None
