import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from debug_retrieval import load_jsonl, serialize_doc
from evaluate_retrieval import evaluate


DEFAULT_DATASET = Path("eval/evaluation_dataset.jsonl")
DEFAULT_OUTPUT_DIR = Path("eval/results/metadata_filter_poc")
DEFAULT_MODE = "oracle"
FIELD_TO_TYPE = {
    "이수구분": "이수구분",
    "선수요건": "선수과목과수강요건",
    "선수과목과수강요건": "선수과목과수강요건",
    "학습내용": "학습내용",
    "수업방식": "수업진행방식",
    "수업진행방식": "수업진행방식",
    "별점": "강의평가",
    "강의평가": "강의평가",
}


def metadata_value(doc: Any, key: str) -> str | None:
    return doc.metadata.get(key)


def build_filter_from_relevant(row: dict[str, Any]) -> dict[str, Any]:
    relevant_docs = row.get("relevant_docs") or []
    if len(relevant_docs) != 1:
        return {}

    relevant = relevant_docs[0]
    filters = {}
    if relevant.get("course"):
        filters["강의명"] = relevant["course"]
    if relevant.get("professor"):
        filters["교수명"] = relevant["professor"]
    if relevant.get("field"):
        filters["type"] = relevant["field"]
    return filters


def build_filter_from_analyzer(analyzer: dict[str, Any]) -> dict[str, Any]:
    hints = analyzer.get("metadata_hints") or {}
    required_fields = analyzer.get("required_fields") or analyzer.get("필요 정보") or []
    filters = {}

    if hints.get("course"):
        filters["강의명"] = hints["course"]
    if hints.get("professor"):
        filters["교수명"] = hints["professor"]

    mapped_fields = [FIELD_TO_TYPE.get(field, field) for field in required_fields]
    mapped_fields = [field for field in mapped_fields if field in set(FIELD_TO_TYPE.values())]
    if len(mapped_fields) == 1:
        filters["type"] = mapped_fields[0]

    return filters


def matches_filter(doc: Any, filters: dict[str, Any]) -> bool:
    for key, value in filters.items():
        if value and metadata_value(doc, key) != value:
            return False
    return True


def search_with_filter(
    vectordb: Any,
    query: str,
    filters: dict[str, Any],
    *,
    k: int,
    candidate_k: int,
) -> tuple[list[tuple[Any, float]], str]:
    if not filters:
        return vectordb.similarity_search_with_score(query, k=k), "dense_only"

    try:
        return (
            vectordb.similarity_search_with_score(query, k=k, filter=filters),
            "chroma_filter",
        )
    except TypeError:
        pass
    except Exception:
        pass

    candidates = vectordb.similarity_search_with_score(query, k=candidate_k)
    filtered = [(doc, score) for doc, score in candidates if matches_filter(doc, filters)]
    return filtered[:k], "post_filter"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Metadata filtering POC for retrieval.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--mode", choices=["oracle", "analyzer"], default=DEFAULT_MODE)
    parser.add_argument("--query-type", nargs="*", default=["fact", "comparison_recommendation"])
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--candidate-k", type=int, default=50)
    parser.add_argument("--preview-chars", type=int, default=500)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading LLM")
    from utils.llm import get_llm
    from utils.prompt import run_query_analyzer
    from utils.rag import _load_vectordb

    pipe, tokenizer = get_llm("Qwen/Qwen3-4B")
    if pipe is None or tokenizer is None:
        raise RuntimeError("LLM/tokenizer load failed.")

    print("Loading Vector DB")
    vectordb = _load_vectordb()
    dataset_rows = [
        row
        for row in load_jsonl(Path(args.dataset))
        if row.get("answerable") is True and row.get("query_type") in set(args.query_type)
    ]

    debug_rows = []
    for idx, row in enumerate(dataset_rows, start=1):
        print(f"[{idx}/{len(dataset_rows)}] {row['id']} {row['question']}")
        analyzer = run_query_analyzer(row["question"], pipe, tokenizer)
        filters = (
            build_filter_from_relevant(row)
            if args.mode == "oracle"
            else build_filter_from_analyzer(analyzer)
        )
        results, filter_method = search_with_filter(
            vectordb,
            row["question"],
            filters,
            k=args.k,
            candidate_k=args.candidate_k,
        )

        debug_rows.append(
            {
                "id": row.get("id"),
                "query": row.get("question"),
                "query_type": row.get("query_type"),
                "answerable": row.get("answerable"),
                "expected_fields": row.get("expected_fields"),
                "expected_scope": row.get("expected_scope"),
                "relevant_docs": row.get("relevant_docs"),
                "analyzer": analyzer,
                "analyzer_k": analyzer.get("top_k", analyzer.get("k")),
                "required_fields": analyzer.get("required_fields") or analyzer.get("필요 정보") or [],
                "metadata_hints": analyzer.get("metadata_hints") or {},
                "information_scope": analyzer.get("information_scope"),
                "filter_mode": args.mode,
                "metadata_filter": filters,
                "filter_method": filter_method,
                "actual_retrieval_k": args.k,
                "retrieved_count": len(results),
                "retrieved_documents": [
                    serialize_doc(doc, score, args.preview_chars) for doc, score in results
                ],
            }
        )

    debug_path = output_dir / f"metadata_filter_{args.mode}_debug.jsonl"
    metrics_path = output_dir / f"metadata_filter_{args.mode}_metrics.json"
    write_jsonl(debug_path, debug_rows)
    write_json(metrics_path, evaluate(debug_rows, [1, 3, 5, 10]))
    print(f"Saved debug: {debug_path}")
    print(f"Saved metrics: {metrics_path}")


if __name__ == "__main__":
    main()
