import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("eval/results/baseline_k10_debug.jsonl")
DEFAULT_OUTPUT = Path("eval/results/baseline_k10_metrics.json")
DEFAULT_K_VALUES = [1, 3, 5, 10, 15]
FIELD_ALIASES = {
    "이수구분": "이수구분",
    "선수요건": "선수과목과수강요건",
    "선수과목": "선수과목과수강요건",
    "선수과목과수강요건": "선수과목과수강요건",
    "학습내용": "학습내용",
    "수업방식": "수업진행방식",
    "수업진행방식": "수업진행방식",
    "별점": "강의평가",
    "평점": "강의평가",
    "강의평": "강의평가",
    "강의평가": "강의평가",
}


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


def normalize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def doc_key(doc: dict[str, Any]) -> tuple[str, str, str]:
    return (
        normalize(doc.get("course")),
        normalize(doc.get("professor")),
        normalize(doc.get("field")),
    )


def relevant_key(doc: dict[str, Any]) -> tuple[str, str, str]:
    return (
        normalize(doc.get("course")),
        normalize(doc.get("professor")),
        normalize(doc.get("field")),
    )


def normalize_fields(fields: list[str]) -> list[str]:
    normalized = []
    for field in fields or []:
        mapped = FIELD_ALIASES.get(normalize(field))
        if mapped and mapped not in normalized:
            normalized.append(mapped)
    return normalized


def is_relevant_match(retrieved: dict[str, Any], relevant: dict[str, Any]) -> bool:
    retrieved_course, retrieved_professor, retrieved_field = doc_key(retrieved)
    relevant_course, relevant_professor, relevant_field = relevant_key(relevant)

    if relevant_course and retrieved_course != relevant_course:
        return False
    if relevant_professor and retrieved_professor != relevant_professor:
        return False
    # Empty/null relevant field is an explicit wildcard for header-level questions.
    if relevant_field and retrieved_field != relevant_field:
        return False
    return True


def relevant_hit_count(
    retrieved_docs: list[dict[str, Any]],
    relevant_docs: list[dict[str, Any]],
    k: int,
) -> int:
    top_docs = retrieved_docs[:k]
    matched_relevant_indexes = set()

    for relevant_index, relevant in enumerate(relevant_docs):
        for retrieved in top_docs:
            if is_relevant_match(retrieved, relevant):
                matched_relevant_indexes.add(relevant_index)
                break

    return len(matched_relevant_indexes)


def field_overlap(analyzer_fields: list[str], expected_fields: list[str]) -> dict[str, Any]:
    analyzer_set = set(normalize_fields(analyzer_fields))
    expected_set = set(normalize_fields(expected_fields))
    overlap = analyzer_set & expected_set

    if not analyzer_set and not expected_set:
        precision = 1.0
        recall = 1.0
    else:
        precision = len(overlap) / len(analyzer_set) if analyzer_set else 0.0
        recall = len(overlap) / len(expected_set) if expected_set else 1.0

    return {
        "precision": precision,
        "recall": recall,
        "overlap": sorted(overlap),
        "missing": sorted(expected_set - analyzer_set),
        "extra": sorted(analyzer_set - expected_set),
    }


def empty_metric_bucket(k_values: list[int]) -> dict[str, Any]:
    return {
        "count": 0,
        "hit": {f"Hit@{k}": 0.0 for k in k_values},
        "recall": {f"Recall@{k}": 0.0 for k in k_values},
        "field_precision": 0.0,
        "field_recall": 0.0,
        "scope_accuracy": 0.0,
        "scope_count": 0,
        "average_retrieved_documents": 0.0,
    }


def evaluate(rows: list[dict[str, Any]], k_values: list[int]) -> dict[str, Any]:
    answerable_rows = [row for row in rows if row.get("answerable") is True]
    unanswerable_rows = [row for row in rows if row.get("answerable") is False]

    overall = empty_metric_bucket(k_values)
    by_type = defaultdict(lambda: empty_metric_bucket(k_values))
    per_query = []
    analyzer_k_distribution = Counter()

    for row in rows:
        analyzer_k_distribution[str(row.get("analyzer_k"))] += 1

    for row in answerable_rows:
        query_type = normalize(row.get("query_type")) or "unknown"
        retrieved_docs = row.get("retrieved_documents") or []
        relevant_docs = row.get("relevant_docs") or []
        expected_fields = row.get("expected_fields") or []
        analyzer = row.get("analyzer") or {}
        needed_fields = (
            row.get("required_fields")
            or analyzer.get("required_fields")
            or row.get("needed_fields")
            or analyzer.get("필요 정보")
            or []
        )
        expected_scope = normalize(row.get("expected_scope"))
        actual_scope = normalize(row.get("information_scope") or analyzer.get("information_scope"))
        field_score = field_overlap(needed_fields, expected_fields)
        scope_match = (
            1.0 if expected_scope and actual_scope and expected_scope == actual_scope else 0.0
        )

        query_result = {
            "id": row.get("id"),
            "query_type": query_type,
            "query": row.get("query"),
            "analyzer_k": row.get("analyzer_k"),
            "baseline_search_k": row.get("baseline_search_k"),
            "actual_retrieval_k": row.get("actual_retrieval_k", row.get("baseline_search_k")),
            "retrieved_count": row.get("retrieved_count", len(retrieved_docs)),
            "expected_scope": expected_scope or None,
            "information_scope": actual_scope or None,
            "scope_match": scope_match if expected_scope else None,
            "field_precision": field_score["precision"],
            "field_recall": field_score["recall"],
            "field_missing": field_score["missing"],
            "field_extra": field_score["extra"],
            "metrics": {},
            "missed_relevant_docs_at_10": [],
        }

        for bucket in (overall, by_type[query_type]):
            bucket["count"] += 1
            bucket["field_precision"] += field_score["precision"]
            bucket["field_recall"] += field_score["recall"]
            bucket["average_retrieved_documents"] += len(retrieved_docs)
            if expected_scope:
                bucket["scope_accuracy"] += scope_match
                bucket["scope_count"] += 1

        for k in k_values:
            matched = relevant_hit_count(retrieved_docs, relevant_docs, k)
            hit = 1.0 if matched > 0 else 0.0
            recall = matched / len(relevant_docs) if relevant_docs else 0.0

            query_result["metrics"][f"Hit@{k}"] = hit
            query_result["metrics"][f"Recall@{k}"] = recall

            overall["hit"][f"Hit@{k}"] += hit
            overall["recall"][f"Recall@{k}"] += recall
            by_type[query_type]["hit"][f"Hit@{k}"] += hit
            by_type[query_type]["recall"][f"Recall@{k}"] += recall

        for relevant in relevant_docs:
            if not any(is_relevant_match(doc, relevant) for doc in retrieved_docs[:10]):
                query_result["missed_relevant_docs_at_10"].append(relevant)

        per_query.append(query_result)

    finalize_bucket(overall)
    for bucket in by_type.values():
        finalize_bucket(bucket)

    unanswerable_observations = []
    for row in unanswerable_rows:
        unanswerable_observations.append(
            {
                "id": row.get("id"),
                "query": row.get("query"),
                "analyzer_k": row.get("analyzer_k"),
                "needed_fields": row.get("needed_fields"),
                "required_fields": row.get("required_fields"),
                "information_scope": row.get("information_scope"),
                "top_3_retrieved": [
                    {
                        "course": doc.get("course"),
                        "professor": doc.get("professor"),
                        "field": doc.get("field"),
                        "similarity_score": doc.get("similarity_score"),
                    }
                    for doc in (row.get("retrieved_documents") or [])[:3]
                ],
            }
        )

    return {
        "input_count": len(rows),
        "answerable_count": len(answerable_rows),
        "unanswerable_count": len(unanswerable_rows),
        "k_values": k_values,
        "overall_answerable": overall,
        "by_query_type": dict(sorted(by_type.items())),
        "analyzer_k_distribution": dict(sorted(analyzer_k_distribution.items())),
        "per_query": per_query,
        "unanswerable_observations": unanswerable_observations,
    }


def finalize_bucket(bucket: dict[str, Any]) -> None:
    count = bucket["count"]
    if count == 0:
        return

    for key in bucket["hit"]:
        bucket["hit"][key] = bucket["hit"][key] / count
    for key in bucket["recall"]:
        bucket["recall"][key] = bucket["recall"][key] / count

    bucket["field_precision"] = bucket["field_precision"] / count
    bucket["field_recall"] = bucket["field_recall"] / count
    bucket["average_retrieved_documents"] = bucket["average_retrieved_documents"] / count
    if bucket["scope_count"]:
        bucket["scope_accuracy"] = bucket["scope_accuracy"] / bucket["scope_count"]


def print_summary(result: dict[str, Any]) -> None:
    print("Retrieval Evaluation Summary")
    print(f"- input_count: {result['input_count']}")
    print(f"- answerable_count: {result['answerable_count']}")
    print(f"- unanswerable_count: {result['unanswerable_count']}")

    overall = result["overall_answerable"]
    print("\nOverall answerable")
    print(f"- count: {overall['count']}")
    for key, value in overall["hit"].items():
        print(f"- {key}: {value:.4f}")
    for key, value in overall["recall"].items():
        print(f"- {key}: {value:.4f}")
    print(f"- Analyzer Field Precision: {overall['field_precision']:.4f}")
    print(f"- Analyzer Field Recall: {overall['field_recall']:.4f}")
    print(f"- Scope Accuracy: {overall['scope_accuracy']:.4f}")
    print(f"- Average Retrieved Documents: {overall['average_retrieved_documents']:.2f}")

    print("\nBy query type")
    for query_type, bucket in result["by_query_type"].items():
        print(f"- {query_type} (n={bucket['count']}): ", end="")
        print(
            ", ".join(
                [
                    f"Hit@10={bucket['hit']['Hit@10']:.4f}",
                    f"Recall@10={bucket['recall']['Recall@10']:.4f}",
                    f"FieldRecall={bucket['field_recall']:.4f}",
                ]
            )
        )

    print("\nAnalyzer k distribution")
    for k, count in result["analyzer_k_distribution"].items():
        print(f"- k={k}: {count}")

    misses = [
        query
        for query in result["per_query"]
        if query["metrics"].get("Hit@10", 0.0) == 0.0
    ]
    print(f"\nHit@10 misses: {len(misses)}")
    for miss in misses:
        print(f"- {miss['id']} [{miss['query_type']}]: {miss['query']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate retrieval debug JSONL.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Retrieval debug JSONL path.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Metrics JSON output path.")
    parser.add_argument(
        "--k",
        nargs="+",
        type=int,
        default=DEFAULT_K_VALUES,
        help="K values to evaluate.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = load_jsonl(input_path)
    result = evaluate(rows, sorted(set(args.k)))

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print_summary(result)
    print(f"\nSaved metrics: {output_path}")


if __name__ == "__main__":
    main()
