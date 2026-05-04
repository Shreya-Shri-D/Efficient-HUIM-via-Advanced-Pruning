from __future__ import annotations

from src.bounds import (
    compute_local_upper_bounds,
    compute_strict_local_upper_bounds,
    compute_strict_subtree_upper_bounds,
)
from src.model import ProjectedTransaction


def _exact_utility(alpha_db, z: str) -> float:
    s = 0.0
    for tx in alpha_db:
        if z in tx.items:
            p = tx.items.index(z)
            s += tx.prefix_utility + tx.utilities[p]
    return s


def test_upper_bounds_are_not_below_exact_utility() -> None:
    alpha_db = [
        ProjectedTransaction(10.0, ("B", "D", "E"), (21.0, 14.0, 6.0)),
        ProjectedTransaction(16.0, ("D", "E"), (28.0, 20.0)),
    ]
    candidates = ["B", "D", "E"]
    following = set(candidates)

    loc = compute_local_upper_bounds(alpha_db, candidates)
    sloc = compute_strict_local_upper_bounds(
        alpha_db,
        candidates,
        following_items=following,
        use_strict_remaining=True,
        use_transaction_skip=False,
    )
    ssub = compute_strict_subtree_upper_bounds(
        alpha_db,
        candidates,
        following_items=following,
        use_strict_remaining=True,
    )

    for z in candidates:
        exact = _exact_utility(alpha_db, z)
        assert loc[z] >= exact
        assert sloc[z] >= exact
        assert ssub[z] >= exact
