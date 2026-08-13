# Development Log - Day 3

작성일: 2026-08-13

## 오늘 목표

Day 3의 목표는 Fixed K=10 baseline에서 멈추지 않고, 평가 기준을 보정한 뒤 Adaptive Top-K를 실제 retrieval에 연결하고 Fixed K 실험군과 비교하는 것이었다.

핵심 질문은 다음이었다.

> Query Analyzer가 선택한 K를 실제 retrieval에 적용했을 때 Fixed K=10 대비 retrieval 성능과 검색량이 어떻게 달라지는가?

추가로 Day 2에서 확인된 conditional query 병목과 metadata filtering 가능성도 확인했다.

## 완료한 작업

### 1. Docs 구조 정리

`Docs/`를 문서 역할별 폴더로 재구성했다.

```text
Docs/
  README.md
  system/
  evaluation/
  logs/
  process/
  reviews/
```

기존 문서는 다음 기준으로 이동했다.

- `system/`: baseline/current system 문서
- `evaluation/`: evaluation schema, retrieval debug, benchmark/report 문서
- `logs/`: 일자별 개발 로그
- `process/`: commit rule
- `reviews/`: project review notes

### 2. Evaluation 기준 보정

`eval/evaluation_dataset.jsonl` 30개 문항을 다시 정리했다.

- `expected_scope` 추가
- `expected_fields`를 실제 document type 기준으로 정리
- header metadata 질문의 field wildcard 지원
- `EV-005`, `EV-009`는 `field: null`로 보정

`field: null`은 다음 의미로 평가한다.

```text
course 일치
AND professor 일치
AND field는 아무 값이나 허용
```

### 3. Query Analyzer schema 개선

기존 Analyzer 출력은 `k`, `필요 정보` 중심이었다. 오늘 다음 구조를 추가했다.

```json
{
  "intent": "course_detail",
  "required_fields": ["강의평가"],
  "metadata_hints": {
    "course": "운영체제",
    "professor": null,
    "department": null,
    "faculty": null
  },
  "information_scope": "narrow",
  "top_k": 3
}
```

기존 코드 호환을 위해 `k`, `필요 정보`도 계속 반환하게 했다.

### 4. Adaptive Top-K 실제 retrieval 연결

`utils/rag.py`에서 fixed `k=10` 대신 Analyzer의 `top_k`를 사용하도록 변경했다.

또한 `eval/debug_retrieval.py`에 다음 필드를 기록하도록 추가했다.

- `actual_retrieval_k`
- `retrieved_count`
- `required_fields`
- `metadata_hints`
- `information_scope`

### 5. Fixed K benchmark runner 추가

`eval/run_fixed_k_benchmark.py`를 추가했다.

실행 대상:

```text
K=1
K=3
K=5
K=10
K=15
```

결과 위치:

```text
eval/results/fixed/
```

### 6. Adaptive benchmark runner 추가

`eval/run_adaptive_benchmark.py`를 추가했다.

Analyzer가 선택한 `top_k`를 실제 retrieval k로 사용해 30개 전체 evaluation dataset을 실행한다.

결과 위치:

```text
eval/results/adaptive/
```

### 7. Fixed vs Adaptive 비교 및 실패 분석

`eval/analyze_failures.py`를 추가했다.

생성 결과:

```text
eval/results/comparison/comparison.json
Docs/evaluation/adaptive-topk-v1.md
```

### 8. eval/results 구조 정리

`eval/results/`도 역할별로 재구성했다.

```text
eval/results/
  README.md
  fixed/
  adaptive/
  comparison/
  metadata_filter_poc/
  archive/
```

이전 Day 1/2 결과와 수동 검증 결과는 `archive/` 아래로 이동했다.

### 9. Conditional query 상세 분석

`eval/analyze_conditional_queries.py`를 추가했다.

생성 결과:

```text
eval/results/comparison/conditional_analysis.json
Docs/evaluation/conditional-query-analysis.md
```

### 10. Metadata Filtering POC

`eval/run_metadata_filter_poc.py`를 추가했다.

두 가지 모드로 실험했다.

- `oracle`: evaluation dataset의 정답 metadata로 filter 생성
- `analyzer`: 현재 Query Analyzer의 `metadata_hints`로 filter 생성

생성 결과:

```text
eval/results/metadata_filter_poc/metadata_filter_oracle_debug.jsonl
eval/results/metadata_filter_poc/metadata_filter_oracle_metrics.json
eval/results/metadata_filter_poc/metadata_filter_analyzer_debug.jsonl
eval/results/metadata_filter_poc/metadata_filter_analyzer_metrics.json
Docs/evaluation/metadata-filter-poc.md
```

## 주요 결과

### Fixed K vs Adaptive Top-K

전체 answerable 25개 기준:

| Strategy | Hit@10 | Recall@10 | Avg Docs |
| --- | ---: | ---: | ---: |
| Fixed K=1 | 0.6800 | 0.4480 | 1.00 |
| Fixed K=3 | 0.8400 | 0.6740 | 3.00 |
| Fixed K=5 | 0.8800 | 0.7320 | 5.00 |
| Fixed K=10 | 0.9200 | 0.7687 | 10.00 |
| Fixed K=15 | 0.9200 | 0.7687 | 15.00 |
| Adaptive | 0.9200 | 0.7687 | 8.48 |

Adaptive Top-K는 Fixed K=10과 같은 Hit/Recall을 유지하면서 평균 검색 문서 수를 줄였다.

```text
Fixed K=10 Avg Docs = 10.00
Adaptive Avg Docs   = 8.48
```

즉 Adaptive Top-K v1은 성능 향상보다는 context 절감 효과를 보였다.

### Query type별 Adaptive 결과

| Query Type | Hit@10 | Recall@10 | Avg Docs |
| --- | ---: | ---: | ---: |
| fact | 0.9000 | 0.9000 | 6.20 |
| conditional | 0.8000 | 0.3933 | 10.00 |
| semantic | 1.0000 | 0.7500 | 10.00 |
| comparison_recommendation | 1.0000 | 0.9000 | 10.00 |

Fact query에서만 검색량 감소가 뚜렷했다.

### Conditional query 분석

| Query | GT Docs | Retrieved | Hit@10 | Recall@10 | 문제 |
| --- | ---: | ---: | ---: | ---: | --- |
| EV-011 | 3 | 10 | 1.0 | 1.0000 | 성공 |
| EV-012 | 2 | 10 | 0.0 | 0.0000 | reverse-condition search 실패 |
| EV-013 | 5 | 10 | 1.0 | 0.4000 | 부분 recall |
| EV-014 | 5 | 10 | 1.0 | 0.4000 | 부분 recall |
| EV-015 | 6 | 10 | 1.0 | 0.1667 | 부분 recall |

`EV-012`는 dense retrieval이 "데이터베이스를 선수요건으로 요구하는 강의"가 아니라 "데이터베이스 강의 자체"를 가져오는 문제다.

### Metadata Filtering POC 결과

Fact + comparison/recommendation 15개 subset 기준:

| Strategy | Hit@10 | Recall@10 | Avg Docs |
| --- | ---: | ---: | ---: |
| Adaptive subset baseline | 0.9333 | 0.9000 | 7.47 |
| Metadata filter oracle | 1.0000 | 0.9667 | 4.53 |
| Metadata filter analyzer | 0.6000 | 0.5333 | 0.60 |

해석:

- Metadata filtering 자체는 효과가 크다.
- 정답 metadata를 알면 Hit/Recall이 오르고 평균 문서 수가 줄어든다.
- 하지만 현재 Analyzer의 `metadata_hints`는 hard filter에 바로 쓰기에는 부정확하다.

예시 문제:

- `백엔드프레임워크 교수님은 누구야?`에서 `백엔드프레임워크`를 `course`가 아니라 `professor`에 넣음
- `데이터베이스 강의의 학습 내용은 어떻게 돼?`에서 `데이터베이스`가 아니라 `데이터베이스 강의`로 추출
- comparison query에서 여러 강의명을 하나의 `course` 문자열에 넣어 hard filter가 과하게 좁아짐

## 오늘의 결론

1. Adaptive Top-K는 유지할 가치가 있다.
   - Fixed K=10과 동일한 retrieval 성능을 유지하면서 평균 context를 줄였다.

2. K를 15로 늘려도 Fixed K=10보다 좋아지지 않았다.
   - 남은 실패는 단순 Top-K 부족 문제가 아니다.

3. Metadata Filtering은 다음 workstream으로 갈 가치가 있다.
   - oracle 결과가 좋다.
   - 다만 Analyzer metadata extraction 개선 전에는 production retrieval에 hard filter로 연결하면 안 된다.

4. `EV-012`는 Metadata Filtering만으로는 부족할 가능성이 높다.
   - reverse-condition search 문제라 keyword/BM25 또는 field-specific inverted search가 필요하다.

## 남은 문제

- Analyzer `metadata_hints` 정확도가 낮다.
- comparison query는 multi-course metadata hint 구조가 필요하다.
- conditional query의 full recall이 낮다.
- unanswerable query는 아직 정량 metric에 포함하지 않았다.
- Metadata Filtering POC는 fact/comparison subset만 평가했다.

## 다음 작업 후보

우선순위:

1. Query Analyzer entity extraction 개선
   - `course`, `professor`, `department`, `faculty` 분리 정확도 개선
   - exact course name normalization
   - comparison query용 multi-value metadata hints 도입

2. Metadata Filtering v1
   - confidence가 높은 metadata hint에만 hard filter 적용
   - filter 실패 시 dense fallback
   - field filter와 metadata filter 분리

3. Keyword/BM25 POC
   - `EV-012` 같은 reverse-condition search 대응
   - `선수과목과수강요건` field 안에서 keyword contains 검색

4. Conditional query recall 개선
   - 조건별 answer set 확장
   - dense + keyword hybrid 실험

## 생성/수정된 주요 파일

```text
Docs/README.md
Docs/logs/development-log-day3.md
Docs/evaluation/adaptive-topk-v1.md
Docs/evaluation/conditional-query-analysis.md
Docs/evaluation/metadata-filter-poc.md

eval/evaluation_dataset.jsonl
eval/evaluate_retrieval.py
eval/debug_retrieval.py
eval/run_fixed_k_benchmark.py
eval/run_adaptive_benchmark.py
eval/analyze_failures.py
eval/analyze_conditional_queries.py
eval/run_metadata_filter_poc.py

utils/prompt.py
utils/rag.py
```

## 재실행 명령

```powershell
.\venv\Scripts\python.exe eval\run_fixed_k_benchmark.py --k 1 3 5 10 15
.\venv\Scripts\python.exe eval\run_adaptive_benchmark.py
.\venv\Scripts\python.exe eval\analyze_failures.py
.\venv\Scripts\python.exe eval\analyze_conditional_queries.py
.\venv\Scripts\python.exe eval\run_metadata_filter_poc.py --mode oracle
.\venv\Scripts\python.exe eval\run_metadata_filter_poc.py --mode analyzer
```
