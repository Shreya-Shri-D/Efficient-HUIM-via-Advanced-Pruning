from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Set, Tuple

from .model import ProjectedTransaction


def compute_subtree_utility_root(
    revised_db: Sequence[ProjectedTransaction],
    ordered_items: Sequence[str],
) -> Dict[str, float]:
    sub_u: Dict[str, float] = {i: 0.0 for i in ordered_items}
    for tx in revised_db:
        pos_map = {item: idx for idx, item in enumerate(tx.items)}
        for item in ordered_items:
            idx = pos_map.get(item)
            if idx is None:
                continue
            sub_u[item] += sum(tx.utilities[idx:])
    return sub_u


def compute_local_upper_bounds(
    alpha_db: Sequence[ProjectedTransaction],
    candidate_items: Sequence[str],
    stats_hook=None,
) -> Dict[str, float]:
    loc_u: Dict[str, float] = {z: 0.0 for z in candidate_items}
    for tx in alpha_db:
        tx_sum = tx.prefix_utility + sum(tx.utilities)
        item_set = set(tx.items)
        for z in candidate_items:
            if z in item_set:
                loc_u[z] += tx_sum
                if stats_hook:
                    stats_hook()
    return loc_u


def compute_strict_local_upper_bounds(
    alpha_db: Sequence[ProjectedTransaction],
    candidate_items: Sequence[str],
    following_items: Set[str],
    use_strict_remaining: bool,
    use_transaction_skip: bool,
    stats_hook=None,
) -> Dict[str, float]:
    sloc_u: Dict[str, float] = {z: 0.0 for z in candidate_items}
    for tx in alpha_db:
        pos_map = {item: idx for idx, item in enumerate(tx.items)}
        for z in candidate_items:
            p = pos_map.get(z)
            if p is None:
                continue
            if use_transaction_skip and p == 0:
                continue
            if use_strict_remaining:
                srem = 0.0
                for item, util in zip(tx.items, tx.utilities):
                    if item in following_items:
                        srem += util
            else:
                srem = sum(tx.utilities)
            sloc_u[z] += tx.prefix_utility + srem
            if stats_hook:
                stats_hook()
    return sloc_u


def compute_strict_subtree_upper_bounds(
    alpha_db: Sequence[ProjectedTransaction],
    candidate_items: Sequence[str],
    following_items: Set[str],
    use_strict_remaining: bool,
    stats_hook=None,
) -> Dict[str, float]:
    ssub_u: Dict[str, float] = {z: 0.0 for z in candidate_items}
    for tx in alpha_db:
        pos_map = {item: idx for idx, item in enumerate(tx.items)}
        for z in candidate_items:
            p = pos_map.get(z)
            if p is None:
                continue
            s = tx.prefix_utility + tx.utilities[p]
            if use_strict_remaining:
                for item, util in zip(tx.items[p + 1 :], tx.utilities[p + 1 :]):
                    if item in following_items:
                        s += util
            else:
                s += sum(tx.utilities[p + 1 :])
            ssub_u[z] += s
            if stats_hook:
                stats_hook()
    return ssub_u
