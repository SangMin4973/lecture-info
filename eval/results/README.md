# Evaluation Results

Generated retrieval evaluation artifacts are grouped by experiment role.

## Folders

- `fixed/`: Day 3 fixed-k benchmark outputs.
  - `fixed_k{K}_debug.jsonl`
  - `fixed_k{K}_metrics.json`
- `adaptive/`: Day 3 Adaptive Top-K benchmark outputs.
  - `adaptive_topk_debug.jsonl`
  - `adaptive_topk_metrics.json`
- `comparison/`: fixed-vs-adaptive aggregate comparison.
  - `comparison.json`
  - `conditional_analysis.json`
- `metadata_filter_poc/`: optional Metadata Filtering POC outputs.
  - `metadata_filter_oracle_debug.jsonl`
  - `metadata_filter_oracle_metrics.json`
  - `metadata_filter_analyzer_debug.jsonl`
  - `metadata_filter_analyzer_metrics.json`
- `archive/`: older or manual-check outputs kept for reference.
  - `day1-smoke/`
  - `day2-baseline/`
  - `manual-checks/`

## Regenerate

Run from the project root:

```powershell
.\venv\Scripts\python.exe eval\run_fixed_k_benchmark.py --k 1 3 5 10 15
.\venv\Scripts\python.exe eval\run_adaptive_benchmark.py
.\venv\Scripts\python.exe eval\analyze_failures.py
.\venv\Scripts\python.exe eval\analyze_conditional_queries.py
.\venv\Scripts\python.exe eval\run_metadata_filter_poc.py --mode oracle
.\venv\Scripts\python.exe eval\run_metadata_filter_poc.py --mode analyzer
```
