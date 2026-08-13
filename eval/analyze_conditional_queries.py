import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_DEBUG = Path("eval/results/adaptive/adaptive_topk_debug.jsonl")
DEFAULT_METRICS = Path("eval/results/adaptive/adaptive_topk_metrics.json")
DEFAULT_OUTPUT = Path("eval/results/comparison/conditional_analysis.json")
DEFAULT_MARKDOWN = Path("Docs/evaluation/conditional-query-analysis.md")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def summarize_problem(row: dict[str, Any]) -> str:
    recall = row["recall_at_10"]
    if row["hit_at_10"] == 0:
        return "dense semantic mismatch / reverse-condition search"
    if recall < 0.5:
        return "partial recall; top-k finds some relevant docs but misses full set"
    if recall < 1.0:
        return "minor partial recall"
    return "retrieval success"


def write_markdown(rows: list[dict[str, Any]], path: Path) -> None:
    lines = [
        "# Conditional Query Analysis",
        "",
        "## Summary",
        "",
        "| Query | GT Docs | Retrieved | Hit@10 | Recall@10 | Problem |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['gt_docs']} | {row['retrieved_count']} | "
            f"{row['hit_at_10']:.1f} | {row['recall_at_10']:.4f} | {row['problem']} |"
        )

    lines.extend(["", "## Details", ""])
    for row in rows:
        lines.extend(
            [
                f"### {row['id']}",
                "",
                f"- Query: {row['query']}",
                f"- Analyzer K: {row['analyzer_k']}",
                f"- Required fields: {', '.join(row['required_fields']) if row['required_fields'] else '(none)'}",
                f"- Problem: {row['problem']}",
                "- Missed relevant docs:",
            ]
        )
        if row["missed_relevant_docs"]:
            for doc in row["missed_relevant_docs"]:
                lines.append(
                    f"  - {doc.get('course')} / {doc.get('professor')} / {doc.get('field')}"
                )
        else:
            lines.append("  - (none)")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze conditional query retrieval failures.")
    parser.add_argument("--debug", default=str(DEFAULT_DEBUG))
    parser.add_argument("--metrics", default=str(DEFAULT_METRICS))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--markdown", default=str(DEFAULT_MARKDOWN))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    debug_rows = {row["id"]: row for row in load_jsonl(Path(args.debug))}
    metrics = load_json(Path(args.metrics))

    rows = []
    for metric_row in metrics["per_query"]:
        if metric_row["query_type"] != "conditional":
            continue
        debug_row = debug_rows[metric_row["id"]]
        summary = {
            "id": metric_row["id"],
            "query": metric_row["query"],
            "gt_docs": len(debug_row.get("relevant_docs") or []),
            "retrieved_count": metric_row.get("retrieved_count", 0),
            "hit_at_10": metric_row["metrics"].get("Hit@10", 0.0),
            "recall_at_10": metric_row["metrics"].get("Recall@10", 0.0),
            "analyzer_k": metric_row.get("actual_retrieval_k"),
            "required_fields": debug_row.get("required_fields") or [],
            "missed_relevant_docs": metric_row.get("missed_relevant_docs_at_10") or [],
        }
        summary["problem"] = summarize_problem(summary)
        rows.append(summary)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(rows, Path(args.markdown))
    print(f"Saved conditional analysis: {output_path}")
    print(f"Saved markdown: {args.markdown}")


if __name__ == "__main__":
    main()
