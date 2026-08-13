# Metadata Filtering POC

## Scope

This POC evaluated metadata filtering on 15 answerable queries:

- 10 fact queries
- 5 comparison/recommendation queries

Conditional and semantic queries were intentionally excluded from this first POC because their answer sets are broader and often require keyword/BM25-style matching rather than exact metadata constraints.

## Results

| Strategy | Hit@10 | Recall@10 | Avg Docs | Notes |
| --- | ---: | ---: | ---: | --- |
| Adaptive subset baseline | 0.9333 | 0.9000 | 7.47 | Fact + comparison rows from Adaptive Top-K result |
| Metadata filter oracle | 1.0000 | 0.9667 | 4.53 | Uses ground-truth metadata as the filter |
| Metadata filter analyzer | 0.6000 | 0.5333 | 0.60 | Uses current Analyzer `metadata_hints` as the filter |

## By Query Type

### Oracle

| Type | Hit@10 | Recall@10 | Avg Docs |
| --- | ---: | ---: | ---: |
| fact | 1.0000 | 1.0000 | 1.80 |
| comparison_recommendation | 1.0000 | 0.9000 | 10.00 |

### Analyzer

| Type | Hit@10 | Recall@10 | Avg Docs |
| --- | ---: | ---: | ---: |
| fact | 0.7000 | 0.7000 | 0.70 |
| comparison_recommendation | 0.4000 | 0.2000 | 0.40 |

## Interpretation

Metadata filtering has clear upside when the filter is correct.

The oracle run improved the fact/comparison subset from:

- Hit@10: 0.9333 to 1.0000
- Recall@10: 0.9000 to 0.9667
- Avg Docs: 7.47 to 4.53

This means exact metadata constraints can both improve retrieval quality and reduce context size.

The Analyzer-based run performed much worse because current `metadata_hints` are not reliable enough for hard filtering. Examples observed in Adaptive debug output:

- `백엔드프레임워크 교수님은 누구야?` placed `백엔드프레임워크` under `professor` instead of `course`.
- `데이터베이스 강의의 학습 내용은 어떻게 돼?` extracted `데이터베이스 강의` instead of the exact course name `데이터베이스`.
- Comparison queries often contain multiple course names, but the current schema stores only one `course` string, causing over-restrictive filters.

## Decision

Do not connect Analyzer-based metadata filtering directly to production retrieval yet.

Next work should be:

1. Improve entity extraction for `metadata_hints`.
2. Support multi-value metadata hints for comparison queries.
3. Apply metadata filtering only when confidence is high.
4. Use keyword/BM25 for reverse-condition queries such as `EV-012`.

The oracle result is strong enough to justify Metadata Filtering as the next retrieval workstream, but only after Analyzer metadata extraction is made safer.
