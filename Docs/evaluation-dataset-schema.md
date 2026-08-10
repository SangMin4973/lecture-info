# Evaluation Dataset Schema

작성일: 2026-08-10

## 목적

현재 `baseline-v0` RAG의 retrieval 성능을 측정하기 위한 평가 데이터셋 구조를 정의한다.

이번 evaluation dataset은 최종 답변 품질만 보는 데이터가 아니라, **질문에 대해 어떤 document가 검색되어야 하는지**를 ground truth로 남기는 것을 우선한다. 그래야 Retrieval 실패와 Generation 실패를 분리해서 볼 수 있다.

## File Format

권장 포맷은 JSONL이다.

- 파일 경로: `eval/evaluation_dataset.jsonl`
- 한 줄에 질문 1개
- 사람이 직접 추가/수정하기 쉽고, 나중에 Python script에서 line-by-line으로 읽기 쉽다.

CSV도 가능하지만, `relevant_docs`처럼 여러 개의 정답 document를 담아야 하므로 JSONL이 더 적합하다.

## Query Type

`query_type`은 평가 질문을 유형별로 나누기 위한 필드다.

오늘 30개 질문은 다음 비율을 기준으로 만든다.

- `fact`: 10개
- `conditional`: 5개
- `semantic`: 5개
- `comparison_recommendation`: 5개
- `unanswerable`: 5개

## Top-Level Schema

```json
{
  "id": "EV-001",
  "question": "운영체제 별점은?",
  "query_type": "fact",
  "answerable": true,
  "expected_answer": "운영체제 강의의 별점 정보",
  "expected_fields": ["강의평가"],
  "relevant_docs": [
    {
      "course": "운영체제",
      "professor": "교수명",
      "field": "강의평가"
    }
  ],
  "notes": ""
}
```

## Field Definition

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | yes | 평가 질문 고유 ID. `EV-001` 형식 사용 |
| `question` | string | yes | 사용자 질문 원문 |
| `query_type` | string | yes | 질문 유형. `fact`, `conditional`, `semantic`, `comparison_recommendation`, `unanswerable` 중 하나 |
| `answerable` | boolean | yes | 현재 데이터로 답변 가능한 질문인지 여부 |
| `expected_answer` | string | yes | 기대 답변 요약. 정답 문장을 엄격히 고정하기보다 확인해야 할 핵심 정보 기록 |
| `expected_fields` | string[] | yes | 검색되어야 하는 정보 필드 목록 |
| `relevant_docs` | object[] | yes | 검색되어야 하는 ground truth document 목록 |
| `notes` | string | no | 애매한 점, 평가 시 주의할 점 |

## relevant_docs Schema

```json
{
  "course": "데이터베이스",
  "professor": "홍은지",
  "field": "학습내용"
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `course` | string or null | yes | 정답 document의 `강의명`. 특정 강의가 없으면 `null` |
| `professor` | string or null | yes | 정답 document의 `교수명`. 특정 교수가 없거나 다수면 `null` |
| `field` | string | yes | 정답 document type |

`field` 값은 현재 Chroma document type과 맞춘다.

- `이수구분`
- `선수과목과수강요건`
- `학습내용`
- `수업진행방식`
- `강의평가`

## expected_fields Rule

`expected_fields`는 Query Analyzer의 `필요 정보`와 비교할 수 있도록 현재 Analyzer 필드명과 최대한 맞춘다.

사용 가능한 값:

- `학부명`
- `학과명`
- `강의명`
- `교수명`
- `이수구분`
- `학습내용`
- `수업방식`
- `선수요건`
- `별점`
- `강의평가`

단, retrieval ground truth인 `relevant_docs.field`는 실제 document type 기준이므로 아래처럼 매핑한다.

| Analyzer Field | Document Field |
| --- | --- |
| `수업방식` | `수업진행방식` |
| `선수요건` | `선수과목과수강요건` |
| `별점` | `강의평가` |
| `강의평가` | `강의평가` |

## Evaluation Unit

기본 평가는 retrieved document가 아래 3개 값을 맞췄는지로 판단한다.

- `강의명`
- `교수명`
- `type`

즉, 현재 Chroma document의 metadata 기준으로는 다음과 같이 비교한다.

```json
{
  "강의명": "데이터베이스",
  "교수명": "홍은지",
  "type": "학습내용"
}
```

## Metric Plan

Day 2에서 구현할 첫 metric은 retrieval 중심으로 잡는다.

- `Hit@K`
  - 질문별 `relevant_docs` 중 하나라도 top-k 검색 결과에 있으면 1
- `Recall@K`
  - 질문별 `relevant_docs` 중 top-k 안에 들어온 비율
- `Analyzer Field Match`
  - Query Analyzer의 `필요 정보`가 `expected_fields`와 얼마나 맞는지 확인

Baseline은 현재 구현 그대로 fixed `k=10`으로 측정한다.

## Example Records

```jsonl
{"id":"EV-001","question":"데이터베이스 강의의 학습 내용은 어떻게 돼?","query_type":"fact","answerable":true,"expected_answer":"데이터베이스 강의의 학습내용을 설명해야 한다.","expected_fields":["학습내용"],"relevant_docs":[{"course":"데이터베이스","professor":"홍은지","field":"학습내용"}],"notes":""}
{"id":"EV-002","question":"Python프로그래밍을 선수과목으로 하는 강의를 알려줘","query_type":"conditional","answerable":true,"expected_answer":"선수과목과수강요건에 Python프로그래밍이 포함된 강의를 찾아야 한다.","expected_fields":["선수요건","강의명","교수명"],"relevant_docs":[{"course":null,"professor":null,"field":"선수과목과수강요건"}],"notes":"조건 검색이므로 relevant_docs는 질문 작성 후 실제 데이터 확인을 통해 여러 개로 확정한다."}
{"id":"EV-003","question":"성공회대학교에 의과대학 해부학 강의가 있어?","query_type":"unanswerable","answerable":false,"expected_answer":"현재 데이터 범위에서는 답할 수 없다고 말해야 한다.","expected_fields":["강의명","학과명"],"relevant_docs":[],"notes":"데이터 범위 밖 질문"}
```

## 작성 규칙

1. `expected_answer`는 긴 모범 답안이 아니라 핵심 확인 기준만 적는다.
2. `relevant_docs`는 가능하면 `course`, `professor`, `field`를 모두 채운다.
3. 조건형 질문처럼 정답 강의가 여러 개인 경우 `relevant_docs`에 여러 document를 넣는다.
4. 답변 불가능 질문은 `answerable=false`, `relevant_docs=[]`로 둔다.
5. 평가 질문 30개를 만들 때는 쉬운 fact 질문만 만들지 않고 query type 비율을 지킨다.

