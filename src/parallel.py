from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from math import floor
from typing import Dict, List, Sequence, Tuple

from .model import RevisedTransaction


def _chunk_bounds(size: int, n_threads: int, i: int) -> Tuple[int, int]:
    interval = size / float(n_threads)
    start = int(round(interval * i))
    if i != n_threads - 1:
        stop = int(round(interval * (i + 1))) - 1
    else:
        stop = size - 1
    return start, stop


def accumulate_local_utility_parallel(
    transactions: Sequence[RevisedTransaction], n_threads: int
) -> Dict[str, float]:
    if n_threads <= 1:
        return _accumulate_local_utility_chunk(transactions, 0, len(transactions) - 1)

    def worker(thread_idx: int) -> Dict[str, float]:
        start, stop = _chunk_bounds(len(transactions), n_threads, thread_idx)
        if start > stop:
            return {}
        return _accumulate_local_utility_chunk(transactions, start, stop)

    partials: List[Dict[str, float]] = []
    with ThreadPoolExecutor(max_workers=n_threads) as ex:
        partials = list(ex.map(worker, range(n_threads)))

    merged: Dict[str, float] = {}
    for part in partials:
        for item, value in part.items():
            merged[item] = merged.get(item, 0.0) + value
    return merged


def _accumulate_local_utility_chunk(
    transactions: Sequence[RevisedTransaction], start: int, stop: int
) -> Dict[str, float]:
    loc_u: Dict[str, float] = {}
    for idx in range(start, stop + 1):
        t = transactions[idx]
        for item in t.items:
            loc_u[item] = loc_u.get(item, 0.0) + t.transaction_utility
    return loc_u
