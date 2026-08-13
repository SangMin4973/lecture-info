import argparse
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from debug_retrieval import analyze_one, load_jsonl
from evaluate_retrieval import evaluate
import json


RESULTS_DIR = Path("eval/results/adaptive")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_metrics(path: Path, rows: list[dict[str, Any]]) -> None:
    result = evaluate(rows, [1, 3, 5, 10, 15])
    with path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run adaptive top-k retrieval benchmark.")
    parser.add_argument("--dataset", default="eval/evaluation_dataset.jsonl")
    parser.add_argument("--results-dir", default=str(RESULTS_DIR))
    parser.add_argument("--preview-chars", type=int, default=500)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    debug_path = results_dir / "adaptive_topk_debug.jsonl"
    metrics_path = results_dir / "adaptive_topk_metrics.json"
    debug_rows = []

    print("Loading LLM")
    from utils.llm import get_llm
    from utils.prompt import run_query_analyzer
    from utils.rag import _load_vectordb, filter_by_fields, merge_docs_by_course

    pipe, tokenizer = get_llm("Qwen/Qwen3-4B")
    if pipe is None or tokenizer is None:
        raise RuntimeError("LLM/tokenizer load failed.")

    print("Loading Vector DB")
    vectordb = _load_vectordb()
    dataset_rows = load_jsonl(Path(args.dataset))

    for idx, row in enumerate(dataset_rows, start=1):
        print(f"[adaptive {idx}/{len(dataset_rows)}] {row['question']}")
        result = analyze_one(
            row["question"],
            pipe,
            tokenizer,
            vectordb,
            run_query_analyzer,
            filter_by_fields,
            merge_docs_by_course,
            fixed_k=10,
            adaptive=True,
            preview_chars=args.preview_chars,
        )
        result["id"] = row.get("id")
        result["query_type"] = row.get("query_type")
        result["answerable"] = row.get("answerable")
        result["expected_fields"] = row.get("expected_fields")
        result["expected_scope"] = row.get("expected_scope")
        result["relevant_docs"] = row.get("relevant_docs")
        debug_rows.append(result)

    write_jsonl(debug_path, debug_rows)
    write_metrics(metrics_path, debug_rows)
    print(f"Saved {debug_path}")
    print(f"Saved {metrics_path}")


if __name__ == "__main__":
    main()
