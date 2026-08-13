import argparse
import json
from pathlib import Path
from typing import Any


RESULTS_DIR = Path("eval/results")
FIXED_RESULTS_DIR = RESULTS_DIR / "fixed"
ADAPTIVE_RESULTS_DIR = RESULTS_DIR / "adaptive"
COMPARISON_RESULTS_DIR = RESULTS_DIR / "comparison"
FIXED_K_VALUES = [1, 3, 5, 10, 15]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def strategy_summary(name: str, metrics: dict[str, Any], metric_k: int) -> dict[str, Any]:
    overall = metrics["overall_answerable"]
    return {
        "strategy": name,
        "hit": overall["hit"].get(f"Hit@{metric_k}", 0.0),
        "recall": overall["recall"].get(f"Recall@{metric_k}", 0.0),
        "avg_docs": overall.get("average_retrieved_documents", 0.0),
        "field_precision": overall.get("field_precision", 0.0),
        "field_recall": overall.get("field_recall", 0.0),
        "scope_accuracy": overall.get("scope_accuracy", 0.0),
    }


def per_query_map(metrics: dict[str, Any], metric_k: int) -> dict[str, dict[str, Any]]:
    return {
        row["id"]: {
            "id": row["id"],
            "query": row["query"],
            "query_type": row["query_type"],
            "hit": row["metrics"].get(f"Hit@{metric_k}", 0.0),
            "recall": row["metrics"].get(f"Recall@{metric_k}", 0.0),
            "actual_retrieval_k": row.get("actual_retrieval_k"),
            "retrieved_count": row.get("retrieved_count"),
            "missed_relevant_docs": row.get(f"missed_relevant_docs_at_{min(metric_k, 10)}")
            or row.get("missed_relevant_docs_at_10")
            or [],
        }
        for row in metrics.get("per_query", [])
    }


def query_type_summary(metrics: dict[str, Any], metric_k: int) -> dict[str, dict[str, float]]:
    return {
        query_type: {
            "hit": bucket["hit"].get(f"Hit@{metric_k}", 0.0),
            "recall": bucket["recall"].get(f"Recall@{metric_k}", 0.0),
            "avg_docs": bucket.get("average_retrieved_documents", 0.0),
        }
        for query_type, bucket in metrics["by_query_type"].items()
    }


def classify_failures(
    fixed10: dict[str, dict[str, Any]],
    fixed15: dict[str, dict[str, Any]],
    adaptive: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for query_id, adaptive_row in adaptive.items():
        fixed10_row = fixed10.get(query_id)
        fixed15_row = fixed15.get(query_id)
        if not fixed10_row or not fixed15_row:
            continue

        fixed10_hit = fixed10_row["hit"] > 0
        fixed15_hit = fixed15_row["hit"] > 0
        adaptive_hit = adaptive_row["hit"] > 0

        failure_type = None
        if fixed10_hit and not adaptive_hit:
            failure_type = "Type A: fixed_k10_success_adaptive_fail"
        elif not fixed10_hit and not adaptive_hit:
            failure_type = "Type B: fixed_k10_fail_adaptive_fail"
        elif fixed10_hit and adaptive_hit and (adaptive_row.get("actual_retrieval_k") or 0) < 10:
            failure_type = "Type C: adaptive_success_with_less_context"
        elif not fixed15_hit:
            failure_type = "Type D: fixed_k15_fail"

        if failure_type:
            rows.append(
                {
                    "id": query_id,
                    "query": adaptive_row["query"],
                    "query_type": adaptive_row["query_type"],
                    "failure_type": failure_type,
                    "fixed_k10_hit": fixed10_row["hit"],
                    "fixed_k10_recall": fixed10_row["recall"],
                    "fixed_k15_hit": fixed15_row["hit"],
                    "adaptive_hit": adaptive_row["hit"],
                    "adaptive_recall": adaptive_row["recall"],
                    "adaptive_actual_k": adaptive_row.get("actual_retrieval_k"),
                    "missed_relevant_docs": adaptive_row.get("missed_relevant_docs", []),
                }
            )
    return rows


def write_markdown(result: dict[str, Any], path: Path, metric_k: int) -> None:
    lines = [
        "# Adaptive Top-K v1",
        "",
        "## Overall",
        "",
        "| Strategy | Hit | Recall | Avg Docs | Field P | Field R | Scope Acc |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["overall"]:
        lines.append(
            "| {strategy} | {hit:.4f} | {recall:.4f} | {avg_docs:.2f} | "
            "{field_precision:.4f} | {field_recall:.4f} | {scope_accuracy:.4f} |".format(**row)
        )

    lines.extend(["", "## Query Type", ""])
    for strategy, by_type in result["by_query_type"].items():
        lines.extend(
            [
                f"### {strategy}",
                "",
                "| Type | Hit | Recall | Avg Docs |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for query_type, row in by_type.items():
            lines.append(
                f"| {query_type} | {row['hit']:.4f} | {row['recall']:.4f} | {row['avg_docs']:.2f} |"
            )
        lines.append("")

    lines.extend(["## Failure Cases", ""])
    for row in result["failure_cases"]:
        lines.append(
            f"- {row['id']} [{row['query_type']}] {row['failure_type']}: "
            f"fixed10 Hit={row['fixed_k10_hit']:.1f}, adaptive Hit={row['adaptive_hit']:.1f}, "
            f"adaptive K={row['adaptive_actual_k']}"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare fixed-k and adaptive retrieval results.")
    parser.add_argument("--fixed-dir", default=str(FIXED_RESULTS_DIR))
    parser.add_argument("--adaptive-dir", default=str(ADAPTIVE_RESULTS_DIR))
    parser.add_argument("--output", default=str(COMPARISON_RESULTS_DIR / "comparison.json"))
    parser.add_argument("--markdown", default="Docs/evaluation/adaptive-topk-v1.md")
    parser.add_argument("--metric-k", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fixed_dir = Path(args.fixed_dir)
    adaptive_dir = Path(args.adaptive_dir)

    fixed_metrics = {
        k: load_json(fixed_dir / f"fixed_k{k}_metrics.json") for k in FIXED_K_VALUES
    }
    adaptive_metrics = load_json(adaptive_dir / "adaptive_topk_metrics.json")

    overall = [
        strategy_summary(f"Fixed K={k}", metrics, args.metric_k)
        for k, metrics in fixed_metrics.items()
    ]
    overall.append(strategy_summary("Adaptive", adaptive_metrics, args.metric_k))

    by_query_type = {
        f"Fixed K={k}": query_type_summary(metrics, args.metric_k)
        for k, metrics in fixed_metrics.items()
    }
    by_query_type["Adaptive"] = query_type_summary(adaptive_metrics, args.metric_k)

    failure_cases = classify_failures(
        per_query_map(fixed_metrics[10], args.metric_k),
        per_query_map(fixed_metrics[15], args.metric_k),
        per_query_map(adaptive_metrics, args.metric_k),
    )

    result = {
        "metric_k": args.metric_k,
        "overall": overall,
        "by_query_type": by_query_type,
        "failure_cases": failure_cases,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result, Path(args.markdown), args.metric_k)

    print(f"Saved comparison: {output_path}")
    print(f"Saved markdown: {args.markdown}")


if __name__ == "__main__":
    main()
