# Retrieval Debug Script

작성일: 2026-08-10

## 목적

최종 답변만 보지 않고, 질문별 retrieval 중간 결과를 저장한다.

저장되는 정보:

- `query`
- Query Analyzer 결과
- Analyzer가 반환한 `k`
- 실제 baseline 검색에 사용한 fixed `k`
- retrieved document 목록
- similarity score
- field filtering 이후 document
- course/professor 기준 merge 이후 document
- evaluation dataset의 `expected_fields`, `relevant_docs`

## Script

```bash
python eval/debug_retrieval.py --query "운영체제 별점은 몇 점이야?"
```

평가 데이터셋 일부 실행:

```bash
python eval/debug_retrieval.py --dataset --limit 3
```

전체 평가 데이터셋 실행:

```bash
python eval/debug_retrieval.py --dataset
```

출력 경로 지정:

```bash
python eval/debug_retrieval.py --dataset --output eval/results/baseline_v0_debug.jsonl
```

## Output

기본 출력 위치:

```text
eval/results/retrieval_debug_YYYYMMDD_HHMMSS.jsonl
```

각 줄은 질문 하나의 debug record다.

## Baseline Rule

현재 baseline은 Query Analyzer가 반환한 `k`를 실제 검색에 적용하지 않는다.

스크립트도 baseline 관찰 목적이므로 기본값은 fixed `k=10`이다.

```json
{
  "analyzer_k": 5,
  "baseline_search_k": 10
}
```

이 차이를 기록해 두면 이후 Adaptive Top-K 실험에서 비교할 수 있다.

