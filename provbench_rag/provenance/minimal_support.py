"""Greedy minimal support selection from ranked candidates."""

from __future__ import annotations

from collections.abc import Callable, Sequence


def greedy_minimal_cover(
    ranked_doc_ids: Sequence[str],
    coverage_fn: Callable[[set[str]], float],
    target_coverage: float = 1.0,
    max_pick: int | None = None,
) -> list[str]:
    """
    Greedily add documents from `ranked_doc_ids` (in order) until `coverage_fn(selected)` >= target.
    `coverage_fn` returns [0,1] sufficiency of current selected id set for the answer.
    """
    selected: list[str] = []
    selected_set: set[str] = set()
    for did in ranked_doc_ids:
        if max_pick is not None and len(selected) >= max_pick:
            break
        if did in selected_set:
            continue
        trial = set(selected_set)
        trial.add(did)
        if coverage_fn(trial) > coverage_fn(selected_set) + 1e-12:
            selected.append(did)
            selected_set = trial
            if coverage_fn(selected_set) >= target_coverage - 1e-12:
                break
    return selected
