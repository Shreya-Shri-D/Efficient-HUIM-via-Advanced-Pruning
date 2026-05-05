# Efficient HUIM via Advanced Pruning

A compact Python implementation of **HUI-PR** algorithm for **high-utility itemset mining** with a **minimum utility threshold expressed as a ratio** of total database utility. The implementation focuses on **strong upper-bound pruning** (local, strict local, and strict subtree utilities), **transaction merging** on projected databases, and **optional parallel preprocessing** for scalable runs on dense transactional data.

---

## Why this project

| Capability | Details |
|------------|---------|
| **Two modes** | `hui-pr` — practical pruning; `hui-pr-star` — stricter bounds for fewer candidates |
| **Pruning strategy** | Subtree utility at the root; recursive strict local / strict subtree upper bounds during search |
| **Throughput** | Projected-transaction merging by identical suffix; threaded accumulation of root-level local utilities |
| **Transparency** | JSON output with HUIs, `minutil`, and counters (candidates, visited transactions, upper-bound evaluations) |

---

## Requirements

- **Python 3.9+** (stdlib only — no pip packages required)

---

## Repository layout

```
├── cli.py                 # Main CLI: mine and write results + optional metrics JSON
├── src/
│   ├── miner.py           # Core HUI-PR / HUI-PR* search
│   ├── bounds.py          # Upper-bound computations
│   ├── model.py           # Transactions, merging, stats
│   ├── io.py              # Parsers for transaction / profit files
│   ├── metrics.py         # Timing and metrics export
│   └── parallel.py        # Parallel root local-utility accumulation
├── scripts/
│   ├── benchmark.py       # CSV benchmark across thresholds and modes
│   ├── run_paper_datasets.py   # Table 7–style runs on bundled datasets
│   ├── build_dashboard.py
│   └── build_simple_viz.py
├── datasets/              # chess, connect, mushroom, retail, accidents, foodmart, …
├── tests/                 # pytest correctness & bound tests
└── results/               # Sample logs / tables / HTML viz from paper-aligned runs
```

---

## Data formats

**Transactions** (`--transactions`): one transaction per line — items with quantities, space- or comma-separated:

```text
a:2 b:1 c:3
a:1,c:2
```

**Profits** (`--profits`): one item per line — whitespace or CSV:

```text
a 1.5
b 2.0
```

Lines starting with `#` are ignored.

---

## Quick start

From the repository root:

```bash
python cli.py \
  --transactions datasets/mushroom.txt \
  --profits path/to/mushroom_profits.txt \
  --minutil-ratio 0.14 \
  --mode hui-pr-star \
  --threads 4 \
  --out hui_results.json \
  --metrics-out run_metrics.json
```

- **`--minutil-ratio`** — threshold as a fraction of **total database utility** (`minutil = ratio × total_utility`).
- **`--no-merge`** — disable projected-database merging (for debugging or comparison).
- **`--threads`** — parallelize only the root-phase local utility scan (`>1`); tree search remains single-threaded.

---

## Benchmarking

Sweep thresholds and both modes to CSV:

```bash
python scripts/benchmark.py \
  --transactions datasets/retail.txt \
  --profits path/to/retail_profits.txt \
  --thresholds 0.003,0.004,0.005 \
  --out benchmark.csv \
  --threads 2
```

Paper-aligned Table 7-style runs (dataset names and δ grids as in the script):

```bash
python scripts/run_paper_datasets.py --help
```

---

## Tests

```bash
python -m pytest tests/ -q
```

---

## Results and reproducibility

The `results/` directory contains merged CSVs, run logs, and HTML visualizations produced from paper-style experiments. Regenerate or update them with the scripts under `scripts/` as needed.

---

**Maintainer:** [Shreya-Shri-D](https://github.com/Shreya-Shri-D) · Repository: [Efficient-HUIM-via-Advanced-Pruning](https://github.com/Shreya-Shri-D/Efficient-HUIM-via-Advanced-Pruning)
