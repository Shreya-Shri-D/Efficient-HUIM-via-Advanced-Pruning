from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from .bounds import (
    compute_local_upper_bounds,
    compute_strict_local_upper_bounds,
    compute_strict_subtree_upper_bounds,
    compute_subtree_utility_root,
)
from .model import (
    MiningStats,
    ProjectedTransaction,
    RawTransaction,
    RevisedTransaction,
    merge_projected_transactions,
)
from .parallel import accumulate_local_utility_parallel


@dataclass(frozen=True)
class MinerConfig:
    minutil_ratio: float
    mode: str = "hui-pr"  # hui-pr or hui-pr-star
    use_transaction_merge: bool = True
    n_threads: int = 1


def mine_hui_pr(
    transactions: Sequence[RawTransaction],
    profits: Dict[str, float],
    config: MinerConfig,
) -> Tuple[Set[Tuple[str, ...]], MiningStats, float]:
    stats = MiningStats()
    revised, total_utility = _build_revised_transactions(transactions, profits)
    minutil = total_utility * config.minutil_ratio

    # locU(∅, i) == TWU(i)
    root_projected = [
        ProjectedTransaction(
            prefix_utility=0.0,
            items=t.items,
            utilities=t.utilities,
        )
        for t in revised
    ]
    if config.n_threads > 1:
        loc_u = accumulate_local_utility_parallel(revised, config.n_threads)
    else:
        loc_u = _local_utility_root(revised)
    fi_root = {i for i, v in loc_u.items() if v >= minutil}
    order = sorted(fi_root, key=lambda i: (loc_u[i], i))
    rank = {i: idx for idx, i in enumerate(order)}

    # Remove unpromising and sort by total order.
    filtered = _filter_and_order_root(root_projected, fi_root, rank)
    if config.use_transaction_merge:
        filtered = merge_projected_transactions(filtered)

    sub_u = compute_subtree_utility_root(filtered, order)
    ni_root = [i for i in order if sub_u.get(i, 0.0) >= minutil]
    fi_root_ordered = [i for i in order if i in fi_root]

    results: Set[Tuple[str, ...]] = set()
    _recursive_search(
        alpha=tuple(),
        alpha_db=filtered,
        ni=ni_root,
        fi=fi_root_ordered,
        minutil=minutil,
        config=config,
        results=results,
        stats=stats,
    )
    return results, stats, minutil


def _build_revised_transactions(
    transactions: Sequence[RawTransaction],
    profits: Dict[str, float],
) -> Tuple[List[RevisedTransaction], float]:
    revised: List[RevisedTransaction] = []
    total_utility = 0.0
    for tx in transactions:
        items = sorted(tx.quantities.keys())
        utilities: List[float] = []
        for item in items:
            util = tx.quantities[item] * profits[item]
            utilities.append(util)
        trans_u = sum(utilities)
        total_utility += trans_u
        revised.append(
            RevisedTransaction(
                tid=tx.tid,
                items=tuple(items),
                utilities=tuple(utilities),
                transaction_utility=trans_u,
            )
        )
    return revised, total_utility


def _local_utility_root(revised: Sequence[RevisedTransaction]) -> Dict[str, float]:
    loc_u: Dict[str, float] = {}
    for t in revised:
        for item in t.items:
            loc_u[item] = loc_u.get(item, 0.0) + t.transaction_utility
    return loc_u


def _filter_and_order_root(
    root_db: Sequence[ProjectedTransaction],
    fi_root: Set[str],
    rank: Dict[str, int],
) -> List[ProjectedTransaction]:
    out: List[ProjectedTransaction] = []
    for tx in root_db:
        pairs = [(i, u) for i, u in zip(tx.items, tx.utilities) if i in fi_root]
        if not pairs:
            continue
        pairs.sort(key=lambda p: rank[p[0]])
        out.append(
            ProjectedTransaction(
                prefix_utility=0.0,
                items=tuple(i for i, _ in pairs),
                utilities=tuple(u for _, u in pairs),
            )
        )
    return out


def _project_and_utility(
    alpha_db: Sequence[ProjectedTransaction],
    item: str,
    stats: MiningStats,
) -> Tuple[float, List[ProjectedTransaction]]:
    beta_utility = 0.0
    projected: List[ProjectedTransaction] = []
    for tx in alpha_db:
        stats.visited_transactions += 1
        try:
            pos = tx.items.index(item)
        except ValueError:
            continue
        util_item = tx.utilities[pos]
        new_prefix = tx.prefix_utility + util_item
        beta_utility += new_prefix
        suffix_items = tx.items[pos + 1 :]
        suffix_utils = tx.utilities[pos + 1 :]
        if suffix_items:
            projected.append(
                ProjectedTransaction(
                    prefix_utility=new_prefix,
                    items=suffix_items,
                    utilities=suffix_utils,
                )
            )
    return beta_utility, projected


def _recursive_search(
    alpha: Tuple[str, ...],
    alpha_db: Sequence[ProjectedTransaction],
    ni: Sequence[str],
    fi: Sequence[str],
    minutil: float,
    config: MinerConfig,
    results: Set[Tuple[str, ...]],
    stats: MiningStats,
) -> None:
    for i in ni:
        stats.candidates += 1
        beta = alpha + (i,)
        utility_beta, beta_db = _project_and_utility(alpha_db, i, stats)
        if utility_beta >= minutil:
            results.add(beta)
        if not beta_db:
            continue
        if config.use_transaction_merge:
            beta_db = merge_projected_transactions(beta_db)

        try:
            idx_i = fi.index(i)
            candidate_z = list(fi[idx_i + 1 :])
        except ValueError:
            candidate_z = [z for z in fi if z != i]
        following_set = set(candidate_z)
        use_star = config.mode.lower() == "hui-pr-star"

        # Keep local upper bound available for optional debugging and conservative fallback.
        _ = compute_local_upper_bounds(
            beta_db,
            candidate_z,
            stats_hook=lambda: _incr_ub(stats),
        )
        ssub_u = compute_strict_subtree_upper_bounds(
            beta_db,
            candidate_z,
            following_items=following_set,
            use_strict_remaining=use_star,
            stats_hook=lambda: _incr_ub(stats),
        )
        sloc_u = compute_strict_local_upper_bounds(
            beta_db,
            candidate_z,
            following_items=following_set,
            use_strict_remaining=use_star,
            use_transaction_skip=use_star,
            stats_hook=lambda: _incr_ub(stats),
        )
        ni_beta = [z for z in candidate_z if ssub_u.get(z, 0.0) >= minutil]
        fi_beta = [z for z in candidate_z if sloc_u.get(z, 0.0) >= minutil]
        if ni_beta:
            _recursive_search(
                alpha=beta,
                alpha_db=beta_db,
                ni=ni_beta,
                fi=fi_beta if fi_beta else candidate_z,
                minutil=minutil,
                config=config,
                results=results,
                stats=stats,
            )


def _incr_ub(stats: MiningStats) -> None:
    stats.upper_bound_calculations += 1
