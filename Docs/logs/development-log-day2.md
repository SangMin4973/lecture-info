# Development Log - Day 2

작성일: 2026-08-11

## 오늘 한 일

- Day 2 작업 방향을 `Fixed K=10 Baseline Retrieval Evaluation`으로 정리했다.
- `eval/evaluation_dataset.jsonl`의 30개 질문 전체에 대해 fixed `k=10` baseline retrieval을 실행했다.
- Retrieval debug 결과를 `eval/results/baseline_k10_debug.jsonl`에 저장했다.
- Retrieval metric script `eval/evaluate_retrieval.py`를 작성했다.
- `Hit@1/3/5/10`, `Recall@1/3/5/10`, query type별 metric, Analyzer Field Precision/Recall을 계산했다.
- metric 결과를 `eval/results/baseline_k10_metrics.json`에 저장했다.
- `Docs/evaluation/baseline-k10-metrics.md`에 baseline 결과, 해석, 실패 케이스 분석을 기록했다.

## 나온 숫자

Answerable 25개 기준:

```text
Hit@1:  0.6000
Hit@3:  0.7600
Hit@5:  0.8400
Hit@10: 0.8800

Recall@1:  0.3680
Recall@3:  0.5940
Recall@5:  0.6920
Recall@10: 0.7287

Analyzer Field Precision: 0.5300
Analyzer Field Recall:    0.8133
```

Query type별 `Hit@10 / Recall@10`:

```text
fact:                      0.8000 / 0.8000
conditional:               0.8000 / 0.3933
semantic:                  1.0000 / 0.7500
comparison_recommendation: 1.0000 / 0.9000
```

Analyzer k 분포:

```text
k=3:  9개
k=5:  6개
k=10: 15개
```

## 발견한 문제

- Fixed `k=10`은 top-10 안에 정답 document를 하나 이상 포함하는 능력은 괜찮다.
  - `Hit@10 = 0.8800`
- 하지만 여러 정답 document를 찾아야 하는 조건형 질문에서는 회수율이 낮다.
  - `conditional Recall@10 = 0.3933`
- `EV-012`는 "데이터베이스를 선수요건으로 요구하는 강의"를 찾아야 하지만, dense retrieval이 `데이터베이스` 강의 자체에 끌렸다.
  - 조건형 역방향 검색은 Adaptive Top-K만으로 해결되기 어렵고 metadata filtering 또는 keyword/BM25가 필요할 수 있다.
- `EV-005`는 검색 결과에 `백엔드프레임워크 / 이승진` 문서들이 있었지만, ground truth field를 `학습내용`으로 고정해 실패로 계산됐다.
  - 교수명/강의명처럼 header 정보가 정답인 질문은 평가 기준을 보정해야 한다.
- Analyzer Field Precision이 낮다.
  - Analyzer가 `강의명`, `교수명`, `학과명` 같은 식별 정보를 함께 반환한다.
  - 이 값들은 현재 field filtering에는 직접 쓰이지 않으므로 불필요 field처럼 계산된다.
- `required_fields`와 metadata hint가 한 필드에 섞여 있는 구조가 애매하다.

## 내일 할 일

- Evaluation matching rule을 보정한다.
  - 교수명/강의명 조회 질문에서 `field=null` 또는 wildcard ground truth를 허용할지 결정한다.
- Query Analyzer 출력 구조 개선안을 정한다.
  - `required_fields`
  - `metadata_hints`
  - `information_scope`
  - `top_k`
- 현재 30개 evaluation dataset의 `relevant_docs`를 다시 검수한다.
- 그 다음 Adaptive Top-K를 실제 retrieval에 연결한다.
  - 현재 `similarity_search_with_score(query, k=10)` 고정을 Analyzer의 `k`로 바꾸는 실험을 진행한다.
- Adaptive Top-K 적용 후 fixed `k=10` baseline과 같은 metric으로 비교한다.
