# Adaptive Top-K v1

## Overall

| Strategy | Hit | Recall | Avg Docs | Field P | Field R | Scope Acc |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Fixed K=1 | 0.6800 | 0.4480 | 1.00 | 0.7600 | 0.7000 | 0.7600 |
| Fixed K=3 | 0.8400 | 0.6740 | 3.00 | 0.7600 | 0.7000 | 0.7600 |
| Fixed K=5 | 0.8800 | 0.7320 | 5.00 | 0.7600 | 0.7000 | 0.7600 |
| Fixed K=10 | 0.9200 | 0.7687 | 10.00 | 0.7600 | 0.7000 | 0.7600 |
| Fixed K=15 | 0.9200 | 0.7687 | 15.00 | 0.7600 | 0.7000 | 0.7600 |
| Adaptive | 0.9200 | 0.7687 | 8.48 | 0.7600 | 0.7000 | 0.7600 |

## Query Type

### Fixed K=1

| Type | Hit | Recall | Avg Docs |
| --- | ---: | ---: | ---: |
| comparison_recommendation | 0.8000 | 0.3167 | 1.00 |
| conditional | 0.4000 | 0.1067 | 1.00 |
| fact | 0.8000 | 0.8000 | 1.00 |
| semantic | 0.6000 | 0.2167 | 1.00 |

### Fixed K=3

| Type | Hit | Recall | Avg Docs |
| --- | ---: | ---: | ---: |
| comparison_recommendation | 1.0000 | 0.7500 | 3.00 |
| conditional | 0.6000 | 0.3200 | 3.00 |
| fact | 0.9000 | 0.9000 | 3.00 |
| semantic | 0.8000 | 0.5000 | 3.00 |

### Fixed K=5

| Type | Hit | Recall | Avg Docs |
| --- | ---: | ---: | ---: |
| comparison_recommendation | 1.0000 | 0.9000 | 5.00 |
| conditional | 0.8000 | 0.3933 | 5.00 |
| fact | 0.9000 | 0.9000 | 5.00 |
| semantic | 0.8000 | 0.5667 | 5.00 |

### Fixed K=10

| Type | Hit | Recall | Avg Docs |
| --- | ---: | ---: | ---: |
| comparison_recommendation | 1.0000 | 0.9000 | 10.00 |
| conditional | 0.8000 | 0.3933 | 10.00 |
| fact | 0.9000 | 0.9000 | 10.00 |
| semantic | 1.0000 | 0.7500 | 10.00 |

### Fixed K=15

| Type | Hit | Recall | Avg Docs |
| --- | ---: | ---: | ---: |
| comparison_recommendation | 1.0000 | 0.9000 | 15.00 |
| conditional | 0.8000 | 0.3933 | 15.00 |
| fact | 0.9000 | 0.9000 | 15.00 |
| semantic | 1.0000 | 0.7500 | 15.00 |

### Adaptive

| Type | Hit | Recall | Avg Docs |
| --- | ---: | ---: | ---: |
| comparison_recommendation | 1.0000 | 0.9000 | 10.00 |
| conditional | 0.8000 | 0.3933 | 10.00 |
| fact | 0.9000 | 0.9000 | 6.20 |
| semantic | 1.0000 | 0.7500 | 10.00 |

## Failure Cases

- EV-003 [fact] Type C: adaptive_success_with_less_context: fixed10 Hit=1.0, adaptive Hit=1.0, adaptive K=5
- EV-004 [fact] Type C: adaptive_success_with_less_context: fixed10 Hit=1.0, adaptive Hit=1.0, adaptive K=3
- EV-005 [fact] Type C: adaptive_success_with_less_context: fixed10 Hit=1.0, adaptive Hit=1.0, adaptive K=3
- EV-007 [fact] Type C: adaptive_success_with_less_context: fixed10 Hit=1.0, adaptive Hit=1.0, adaptive K=5
- EV-008 [fact] Type B: fixed_k10_fail_adaptive_fail: fixed10 Hit=0.0, adaptive Hit=0.0, adaptive K=10
- EV-009 [fact] Type C: adaptive_success_with_less_context: fixed10 Hit=1.0, adaptive Hit=1.0, adaptive K=3
- EV-010 [fact] Type C: adaptive_success_with_less_context: fixed10 Hit=1.0, adaptive Hit=1.0, adaptive K=3
- EV-012 [conditional] Type B: fixed_k10_fail_adaptive_fail: fixed10 Hit=0.0, adaptive Hit=0.0, adaptive K=10

## Interpretation

Adaptive Top-K v1 preserved the same Hit@10 and Recall@10 as Fixed K=10 while reducing the average retrieved documents from 10.00 to 8.48.

The remaining hard failures are not solved by increasing K:

- EV-008 still fails at Fixed K=15 and Adaptive K=10, so course/field matching needs stronger metadata or keyword support.
- EV-012 still fails at Fixed K=15 and Adaptive K=10. This is a reverse-condition search: the query asks for courses whose prerequisite field contains "데이터베이스", but dense retrieval returns the "데이터베이스" course itself.

## Next Step

Adaptive Top-K is useful as a context reduction mechanism, but the next retrieval-quality work should focus on Metadata Filtering and keyword/BM25 retrieval.

Supporting artifacts:

- `Docs/evaluation/conditional-query-analysis.md`
- `eval/results/comparison/conditional_analysis.json`
- `eval/run_metadata_filter_poc.py`
