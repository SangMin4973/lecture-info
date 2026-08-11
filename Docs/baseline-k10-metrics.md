# Baseline K=10 Metrics

작성일: 2026-08-11

## 대상 파일

- Debug input: `eval/results/baseline_k10_debug.jsonl`
- Metrics output: `eval/results/baseline_k10_metrics.json`
- Evaluation script: `eval/evaluate_retrieval.py`

## 평가 목적

현재 `baseline-v0`의 fixed `k=10` retrieval이 평가 질문 30개에서 정답 document를 얼마나 잘 검색하는지 확인한다.

이번 평가는 최종 답변 생성 품질이 아니라 **Retrieval 품질**만 본다.

즉 질문에 대해 LLM이 답을 잘 썼는지가 아니라, 답변에 필요한 document가 검색 결과 안에 들어왔는지를 측정한다.

## 평가 대상

- 전체 질문 수: 30
- Answerable 질문: 25
- Unanswerable 질문: 5

`Hit@K`, `Recall@K`는 `answerable=true`인 25개 질문만 대상으로 계산한다.

`unanswerable` 질문은 아직 정량 metric에 포함하지 않고, 어떤 문서가 검색되는지 관찰 대상으로만 둔다.

## 정답 Document 기준

평가 데이터셋의 `relevant_docs`를 ground truth로 사용한다.

예:

```json
{
  "course": "운영체제",
  "professor": "노은하",
  "field": "강의평가"
}
```

검색된 document가 아래 세 값을 만족하면 정답으로 본다.

- `course`
- `professor`
- `field`

현재 Chroma document 기준으로는 다음 metadata와 대응된다.

- `course` -> `metadata["강의명"]`
- `professor` -> `metadata["교수명"]`
- `field` -> `metadata["type"]`

## Metric 의미

### Hit@K

Top-K 검색 결과 안에 정답 document가 하나라도 있으면 1, 없으면 0이다.

예:

- `Hit@10 = 1`: top-10 안에 정답 document가 최소 1개 있음
- `Hit@10 = 0`: top-10 안에 정답 document가 하나도 없음

Hit@K는 "최소 하나라도 찾았는가"를 보는 지표라 조건형 질문처럼 정답이 여러 개인 경우에는 충분하지 않을 수 있다.

### Recall@K

정답 document 전체 중 top-K 안에 들어온 비율이다.

예:

- relevant document 4개 중 2개가 top-10 안에 있으면 `Recall@10 = 0.5`
- relevant document 1개짜리 fact 질문에서는 정답이 들어오면 `Recall@K = 1.0`, 없으면 `0.0`

조건형/비교형 질문에서는 Hit@K보다 Recall@K가 더 중요하다.

### Analyzer Field Precision

Query Analyzer가 뽑은 `필요 정보` 중 evaluation dataset의 `expected_fields`와 겹치는 비율이다.

높을수록 불필요한 field를 덜 뽑았다는 뜻이다.

### Analyzer Field Recall

Evaluation dataset의 `expected_fields` 중 Query Analyzer가 맞게 뽑은 비율이다.

높을수록 필요한 field를 잘 놓치지 않았다는 뜻이다.

## 전체 결과

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

## Query Type별 결과

```text
fact:
  Hit@10 = 0.8000
  Recall@10 = 0.8000

conditional:
  Hit@10 = 0.8000
  Recall@10 = 0.3933

semantic:
  Hit@10 = 1.0000
  Recall@10 = 0.7500

comparison_recommendation:
  Hit@10 = 1.0000
  Recall@10 = 0.9000
```

## 해석

Fixed `k=10` baseline은 전체적으로 top-10 안에 정답 document를 하나 이상 포함하는 비율은 높다.

- `Hit@10 = 0.88`

하지만 정답 document를 여러 개 찾아야 하는 질문에서는 회수율이 낮아진다.

특히 `conditional` 질문의 `Recall@10`이 낮다.

- `conditional Recall@10 = 0.3933`

이는 조건형 질문에서 정답 강의 중 일부만 검색되고, 전체 정답 집합을 충분히 회수하지 못한다는 뜻이다.

## Hit@10 실패 케이스

```text
EV-005 fact:
백엔드프레임워크 교수님은 누구야?

EV-008 fact:
프론트엔드프레임워크 별점은 몇 점이야?

EV-012 conditional:
데이터베이스를 먼저 들어야 하는 강의가 뭐가 있어?
```

## 현재 관찰

- Fact 질문에서도 강의명/교수명처럼 keyword matching이 중요한 질문에서 실패가 발생했다.
- 조건형 질문은 top-10 안에 일부 관련 문서가 들어오더라도 전체 정답 document를 충분히 찾지 못한다.
- Analyzer Field Recall은 높지만 Precision은 낮다.
  - 필요한 field는 비교적 잘 포함한다.
  - 하지만 불필요한 field도 함께 뽑는 경향이 있다.
- 현재 fixed `k=10`은 broad/comparison 질문에서는 어느 정도 작동하지만, 조건형 검색의 정답 회수에는 부족하다.

## 주의점

- 이 결과는 Retrieval 품질만 평가한다.
- 최종 LLM 답변의 정확성, 충실성, hallucination 여부는 아직 평가하지 않았다.
- `unanswerable` 질문은 아직 정량 평가에 포함하지 않았다.
- `relevant_docs` 자체가 완전한 정답 집합인지 추가 검수가 필요하다.
- 특히 조건형 질문은 정답 document가 여러 개일 수 있어 ground truth 보강이 필요하다.

## 다음 작업

- `Hit@10` 실패 3개 질문의 retrieved documents를 직접 확인한다.
- 조건형 질문의 낮은 `Recall@10` 원인을 분석한다.
- Query Analyzer의 `필요 정보`와 실제 검색 결과의 field filtering 관계를 확인한다.
- Day 3에서 Adaptive Top-K를 적용하기 전, fixed baseline의 실패 유형을 문서화한다.

## Failure Analysis

### Hit@10 실패 케이스 상세

#### EV-005: 백엔드프레임워크 교수님은 누구야?

- Query type: `fact`
- Analyzer result:
  - `k=3`
  - `필요 정보=["교수명"]`
- Ground truth:
  - `백엔드프레임워크 / 이승진 / 학습내용`
- Top-10 검색 결과 관찰:
  - `백엔드프레임워크 / 이승진 / 이수구분`
  - `백엔드프레임워크 / 이승진 / 강의평가`
  - `백엔드프레임워크 / 이승진 / 수업진행방식`
  - `백엔드프레임워크 / 이승진 / 선수과목과수강요건`

해석:

검색 자체는 `백엔드프레임워크 / 이승진`을 잘 찾았다. 하지만 evaluation dataset에서 ground truth field를 `학습내용`으로 지정했기 때문에 Hit@10 실패로 계산됐다.

이 케이스는 retrieval 실패라기보다 **교수명처럼 모든 document header에 반복되는 정보의 평가 기준이 애매한 문제**에 가깝다.

개선 후보:

- 교수명/강의명 조회 질문은 field를 엄격하게 하나로 고정하지 않는 방식이 필요하다.
- 예: `course + professor`만 맞으면 hit로 인정하거나, `field=null` wildcard ground truth를 허용한다.

#### EV-008: 프론트엔드프레임워크 별점은 몇 점이야?

- Query type: `fact`
- Analyzer result:
  - `k=3`
  - `필요 정보=["별점", "강의명", "교수명"]`
- Ground truth:
  - `프론트엔드프레임워크 / 이승진 / 강의평가`
- Top-10 검색 결과 관찰:
  - `프론트엔드프레임워크 / 이승진 / 이수구분`
  - `프론트엔드프레임워크 / 이승진 / 선수과목과수강요건`
  - `프론트엔드프레임워크 / 이승진 / 수업진행방식`
  - `백엔드프레임워크 / 이승진 / 강의평가`
  - `프론트엔드 개발 / 이승진 / 강의평가`
  - `프론트엔드프레임워크 / 이승진 / 학습내용`

해석:

강의명은 맞게 찾았지만 정작 별점이 들어 있는 `강의평가` document가 top-10 안에 없다. 대신 비슷한 강의명인 `백엔드프레임워크`, `프론트엔드 개발`의 강의평가가 검색됐다.

이 케이스는 **강의명 keyword matching과 field matching이 동시에 필요한 질문에서 dense retrieval이 흔들린 사례**다.

개선 후보:

- 강의명/교수명 같은 고유명사는 metadata filtering 또는 keyword matching을 먼저 적용한다.
- `별점`은 `강의평가` field로 강하게 매핑하여 field filter를 retrieval 이전에 적용하는 실험이 필요하다.

#### EV-012: 데이터베이스를 먼저 들어야 하는 강의가 뭐가 있어?

- Query type: `conditional`
- Analyzer result:
  - `k=10`
  - `필요 정보=["선수요건", "강의명", "교수명"]`
- Ground truth:
  - `백엔드프레임워크 / 이승진 / 선수과목과수강요건`
  - `백엔드프로그래밍 / 김선형 / 선수과목과수강요건`
- Top-10 검색 결과 관찰:
  - `데이터베이스 / 홍은지 / 학습내용`
  - `데이터베이스 / 홍은지 / 선수과목과수강요건`
  - `데이터베이스 / 홍은지 / 강의평가`
  - `데이터베이스 / 홍은지 / 이수구분`
  - `데이터베이스 / 홍은지 / 수업진행방식`
  - `데이터사이언스입문 / 이상윤 / ...`

해석:

질문 의도는 "데이터베이스를 선수요건으로 요구하는 강의"를 찾는 것이다. 하지만 dense retrieval은 `데이터베이스`라는 강의명 자체에 강하게 끌려 `데이터베이스` 강의 document들을 먼저 반환했다.

이 케이스는 **조건형 역방향 검색 실패**다. "A를 먼저 들어야 하는 강의"는 A 강의 자체가 아니라 다른 강의들의 선수요건 field에서 A를 포함하는 document를 찾아야 한다.

개선 후보:

- 조건형 선수요건 검색에는 metadata/field filtering 후 keyword matching 또는 BM25가 필요하다.
- Query Analyzer가 `search_target="prerequisite_contains"` 같은 의도를 구분하도록 확장할 필요가 있다.

### 조건형 질문 Recall 저하 원인

조건형 질문의 결과:

```text
conditional Hit@10 = 0.8000
conditional Recall@10 = 0.3933
```

Hit@10은 나쁘지 않지만 Recall@10이 낮다. 이는 조건형 질문에서 정답 중 하나는 찾더라도 전체 정답 집합을 충분히 회수하지 못한다는 뜻이다.

대표 사례:

- `EV-013`: 퀴즈가 자주 있거나 정기적으로 있는 강의
  - Recall@10 = 0.4
  - `운영체제`, `알고리즘`은 찾았지만 `백엔드프레임워크`, `서버구축및형상관리`, `데이터사이언스입문`은 top-10에 없음
- `EV-014`: 팀 프로젝트나 조별 활동이 있는 강의
  - Recall@10 = 0.4
  - `컴퓨터공학캡스톤디자인`, `시스템분석 및 설계`는 찾았지만 나머지 관련 강의는 누락
- `EV-015`: 별점이 5.0인 강의
  - Recall@10 = 0.1667
  - `정보보호개론`만 relevant doc 기준에 매칭됨
  - top-10에는 별점 5.0이 아닌 강의평가도 함께 포함됨

원인:

- 조건형 질문은 정답 document가 여러 개인데 fixed `k=10`과 dense similarity만으로 전체 집합을 회수하기 어렵다.
- "퀴즈", "팀 프로젝트", "별점 5.0" 같은 조건은 semantic similarity보다 field 제한 + keyword/metadata matching이 더 중요할 수 있다.
- 현재 relevant_docs도 대표 정답 위주라, 조건형 질문의 전체 정답 집합 검수가 더 필요하다.

### Query Analyzer 관찰

Analyzer k 분포:

```text
k=3:  9개
k=5:  6개
k=10: 15개
```

질문 유형별 관찰:

- `fact`
  - 대부분 `k=3` 또는 `k=5`
  - 단순 조회에 작은 k를 선택하는 경향은 적절하다.
- `conditional`
  - 전부 `k=10`
  - 조건형 검색이 여러 document를 요구한다는 판단은 적절하다.
- `semantic`
  - 대부분 `k=10`
  - 의미 기반 추천/탐색 질문을 넓게 보는 경향은 적절하다.
- `comparison_recommendation`
  - 전부 `k=10`
  - 비교/추천 질문을 broad query로 본 것은 적절하다.

Field 분석:

- Analyzer Field Recall은 `0.8133`으로 비교적 높다.
- Analyzer Field Precision은 `0.5300`으로 낮다.
- 즉 필요한 field는 꽤 잘 포함하지만, 불필요한 field도 함께 뽑는 경향이 있다.

특히 `EV-008`처럼 `별점` 질문에서 `강의명`, `교수명`까지 함께 뽑는 것은 자연스럽지만, 현재 field filtering은 실제 document type과 직접 맞지 않는 `강의명`, `교수명`을 효과적으로 활용하지 못한다.

### Analyzer Field 실패/과잉 사례

Field Recall이 낮은 대표 사례:

```text
EV-001 운영체제 별점은 몇 점이야?
- missing: 강의평가
- extra: 강의명, 교수명

EV-008 프론트엔드프레임워크 별점은 몇 점이야?
- missing: 강의평가
- extra: 강의명, 교수명

EV-021 운영체제와 알고리즘 중 퀴즈 부담이 더 커 보이는 강의는 뭐야?
- missing: 강의평가, 수업방식
- extra: 강의명, 교수명, 별점, 학습내용
```

Field Precision이 낮은 이유:

- Analyzer가 답변에 필요한 실제 document field뿐 아니라 `강의명`, `교수명`, `학과명` 같은 식별 정보도 함께 반환한다.
- 이 식별 정보들은 현재 document header에는 존재하지만, `filter_by_fields()`에서 document type으로 직접 활용되지는 않는다.
- 따라서 Analyzer 입장에서는 자연스러운 출력이지만, 현재 retrieval/filtering 구조에서는 불필요 field처럼 계산된다.

해석:

- Analyzer Field Precision `0.5300`은 Query Analyzer가 완전히 나쁘다는 뜻은 아니다.
- 현재 evaluation의 `expected_fields`와 runtime의 `필요 정보` 역할이 섞여 있다.
- `강의명`, `교수명`, `학과명`은 field filtering용 값이라기보다 metadata filtering용 값에 가깝다.

개선 후보:

- Query Analyzer 출력을 `required_fields`와 `metadata_hints`로 분리한다.
- 예:

```json
{
  "required_fields": ["강의평가"],
  "metadata_hints": {
    "강의명": "운영체제",
    "교수명": "노은하"
  }
}
```

이 구조가 되면 field filtering과 metadata filtering의 역할이 분리되어 Analyzer 평가가 더 명확해진다.

### Day 3 개선 후보

Day 3에서 바로 Adaptive Top-K만 적용하기 전에 다음 두 가지를 구분해야 한다.

1. **평가 기준 개선**
   - 교수명/강의명 조회처럼 header 정보가 정답인 경우 field wildcard를 허용할지 결정한다.
   - 조건형 질문의 relevant_docs를 더 완전하게 검수한다.

2. **Retrieval 개선**
   - `k=10` 고정을 Analyzer의 `k`로 연결한다.
   - 단, Adaptive Top-K만으로 `EV-012` 같은 역방향 조건 검색 문제가 해결되지는 않을 가능성이 높다.
   - 강의명/교수명/별점/선수요건 질문에는 metadata filtering 또는 keyword search가 필요할 수 있다.

우선순위 제안:

1. evaluation matching rule에 `field=null` 또는 wildcard 지원 추가
2. 현재 30개 dataset의 relevant_docs 보정
3. Adaptive Top-K 연결 후 fixed k baseline과 비교
4. 조건형 질문 실패가 유지되면 metadata filtering/BM25 실험으로 이동
