"""Dense retrieval from a precomputed embedding matrix (NumPy .npz)."""

from __future__ import annotations

from pathlib import Path

import numpy as np


class DenseVectorStore:
    """
    Loads `vectors.npz` with arrays:
      embeddings: float32 [n_docs, dim]
      doc_ids: object array of str doc_ids (same row order as embeddings)
    Query embeddings are supplied by the caller (e.g., from an external encoder).
    """

    def __init__(self, npz_path: str | Path) -> None:
        path = Path(npz_path)
        data = np.load(path, allow_pickle=True)
        self.embeddings = np.asarray(data["embeddings"], dtype=np.float32)
        raw_ids = data["doc_ids"]
        self.doc_ids = [str(x) for x in raw_ids.tolist()]
        if len(self.doc_ids) != self.embeddings.shape[0]:
            raise ValueError("doc_ids length must match embeddings rows")

    @staticmethod
    def l2_normalize(x: np.ndarray) -> np.ndarray:
        denom = np.linalg.norm(x, axis=-1, keepdims=True)
        denom = np.maximum(denom, 1e-12)
        return x / denom

    def query(self, query_embedding: np.ndarray, top_k: int = 20) -> list[tuple[str, float]]:
        q = np.asarray(query_embedding, dtype=np.float32).reshape(1, -1)
        q = self.l2_normalize(q)
        d = self.l2_normalize(self.embeddings)
        sims = (d @ q.T).reshape(-1)
        k = min(top_k, sims.shape[0])
        idx = np.argpartition(-sims, kth=k - 1)[:k]
        idx = idx[np.argsort(-sims[idx])]
        return [(self.doc_ids[i], float(sims[i])) for i in idx]
