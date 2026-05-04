from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class RawTransaction:
    tid: int
    quantities: Dict[str, float]


@dataclass(frozen=True)
class RevisedTransaction:
    tid: int
    items: Tuple[str, ...]
    utilities: Tuple[float, ...]
    transaction_utility: float


@dataclass(frozen=True)
class ProjectedTransaction:
    prefix_utility: float
    items: Tuple[str, ...]
    utilities: Tuple[float, ...]


@dataclass
class MiningStats:
    candidates: int = 0
    visited_transactions: int = 0
    upper_bound_calculations: int = 0


def merge_projected_transactions(
    projected: Sequence[ProjectedTransaction],
) -> List[ProjectedTransaction]:
    """Merge identical suffixes by summing per-position utilities."""
    merged: Dict[Tuple[str, ...], Tuple[float, List[float]]] = {}
    for tx in projected:
        key = tx.items
        if key not in merged:
            merged[key] = (tx.prefix_utility, list(tx.utilities))
            continue
        prefix_sum, util_list = merged[key]
        merged[key] = (
            prefix_sum + tx.prefix_utility,
            [u + v for u, v in zip(util_list, tx.utilities)],
        )

    out: List[ProjectedTransaction] = []
    for items, (prefix_sum, utilities_sum) in merged.items():
        out.append(
            ProjectedTransaction(
                prefix_utility=prefix_sum,
                items=items,
                utilities=tuple(utilities_sum),
            )
        )
    return out
