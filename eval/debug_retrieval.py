import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_MODEL = "Qwen/Qwen3-4B"
DEFAULT_DATASET = ROOT_DIR / "eval" / "evaluation_dataset.jsonl"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "eval" / "results"
FIXED_BASELINE_K = 10
ALLOWED_K = {3, 5, 10}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def doc_field(page_content: str) -> str | None:
    start = page_content.find("[")
    end = page_content.find("]", start + 1)
    if start == -1 or end == -1:
        return None
    return page_content[start + 1 : end].strip()


def preview_text(text: str, max_chars: int) -> str:
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def serialize_doc(doc: Any, score: float | None = None, preview_chars: int = 500) -> dict[str, Any]:
    item = {
        "course": doc.metadata.get("강의명"),
        "professor": doc.metadata.get("교수명"),
        "field": doc.metadata.get("type") or doc_field(doc.page_content),
        "metadata": doc.metadata,
        "content_preview": preview_text(doc.page_content, preview_chars),
    }
    if score is not None:
        item["similarity_score"] = float(score)
    return item


def validated_top_k(value: Any, default: int = 5) -> int:
    try:
        top_k = int(value)
    except (TypeError, ValueError):
        return default
    if top_k not in ALLOWED_K:
        return default
    return top_k


def analyze_one(
    query: str,
    pipe: Any,
    tokenizer: Any,
    vectordb: Any,
    run_query_analyzer: Any,
    filter_by_fields: Any,
    merge_docs_by_course: Any,
    *,
    fixed_k: int,
    adaptive: bool,
    preview_chars: int,
) -> dict[str, Any]:
    analyzer = run_query_analyzer(query, pipe, tokenizer)
    analyzer_k = validated_top_k(analyzer.get("top_k", analyzer.get("k")), default=5)
    actual_retrieval_k = analyzer_k if adaptive else fixed_k
    needed_fields = analyzer.get("required_fields") or analyzer.get("필요 정보", [])

    raw_results = vectordb.similarity_search_with_score(query, k=actual_retrieval_k)
    raw_docs = [doc for doc, _score in raw_results]
    filtered_docs = filter_by_fields(raw_docs, needed_fields)
    merged_docs = merge_docs_by_course(filtered_docs)

    return {
        "query": query,
        "analyzer": analyzer,
        "analyzer_k": analyzer_k,
        "baseline_search_k": fixed_k,
        "actual_retrieval_k": actual_retrieval_k,
        "retrieved_count": len(raw_results),
        "needed_fields": needed_fields,
        "required_fields": needed_fields,
        "metadata_hints": analyzer.get("metadata_hints", {}),
        "information_scope": analyzer.get("information_scope"),
        "retrieved_documents": [
            serialize_doc(doc, score, preview_chars) for doc, score in raw_results
        ],
        "filtered_documents": [
            serialize_doc(doc, None, preview_chars) for doc in filtered_docs
        ],
        "merged_documents": [
            serialize_doc(doc, None, preview_chars) for doc in merged_docs
        ],
    }


def output_path(output: str | None) -> Path:
    if output:
        return Path(output).resolve()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_DIR / f"retrieval_debug_{stamp}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Save query -> analyzer result -> retrieved documents -> similarity scores."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--query", help="Single query to inspect.")
    source.add_argument(
        "--dataset",
        nargs="?",
        const=str(DEFAULT_DATASET),
        help="JSONL evaluation dataset path. Defaults to eval/evaluation_dataset.jsonl.",
    )
    parser.add_argument("--limit", type=int, help="Maximum dataset rows to run.")
    parser.add_argument("--output", help="Output JSONL path.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"LLM model. Default: {DEFAULT_MODEL}")
    parser.add_argument("--fixed-k", type=int, default=FIXED_BASELINE_K, help="Baseline retrieval k.")
    parser.add_argument("--adaptive", action="store_true", help="Use analyzer top_k as retrieval k.")
    parser.add_argument("--preview-chars", type=int, default=500, help="Saved content preview length.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.query:
        rows = [{"id": "QUERY-001", "question": args.query}]
    else:
        rows = load_jsonl(Path(args.dataset))
        if args.limit is not None:
            rows = rows[: args.limit]

    out_path = output_path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading LLM: {args.model}")
    from utils.llm import get_llm
    from utils.prompt import run_query_analyzer
    from utils.rag import _load_vectordb, filter_by_fields, merge_docs_by_course

    pipe, tokenizer = get_llm(args.model)
    if pipe is None or tokenizer is None:
        raise RuntimeError("LLM/tokenizer load failed.")

    print("Loading Vector DB")
    vectordb = _load_vectordb()

    with out_path.open("w", encoding="utf-8") as f:
        for idx, row in enumerate(rows, start=1):
            query = row["question"]
            print(f"[{idx}/{len(rows)}] {query}")
            result = analyze_one(
                query,
                pipe,
                tokenizer,
                vectordb,
                run_query_analyzer,
                filter_by_fields,
                merge_docs_by_course,
                fixed_k=args.fixed_k,
                adaptive=args.adaptive,
                preview_chars=args.preview_chars,
            )
            result["id"] = row.get("id")
            result["query_type"] = row.get("query_type")
            result["answerable"] = row.get("answerable")
            result["expected_fields"] = row.get("expected_fields")
            result["relevant_docs"] = row.get("relevant_docs")
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(f"Saved retrieval debug results: {out_path}")


if __name__ == "__main__":
    main()
