# Development Log - Day 1

작성일: 2026-08-10

## 오늘 한 일

- 현재 RAG 시스템을 `baseline-v0`로 기록했다.
  - LLM: `Qwen/Qwen3-4B`
  - Embedding: `Snowflake/snowflake-arctic-embed-l-v2.0`
  - Vector DB: ChromaDB, `lecture_info` collection
  - Retrieval: Chroma dense similarity search
  - 현재 baseline 검색은 fixed `k=10`
- Notion `01. Current System` 구조에 맞춰 `Current RAG Pipeline`, `DATA`, `Architecture` 문서를 작성했다.
- Evaluation Dataset 스키마를 설계했다.
- `data/text_data.txt`, `data/cleaned_data.csv` 기반으로 평가 질문 30개를 만들었다.
  - Fact 10개
  - Conditional 5개
  - Semantic 5개
  - Comparison/Recommendation 5개
  - Unanswerable 5개
- Retrieval debug script를 작성했다.
  - 질문별 `query`, Query Analyzer 결과, retrieved document, similarity score를 JSONL로 저장한다.
  - `EV-001` 1개 질문 smoke 실행을 완료했다.
- commit rule을 작성하고, 오늘 작업 내용을 commit rule에 맞춰 분리 commit 후 GitHub `origin/main`에 push했다.

## 결정한 Evaluation Schema

- 평가 데이터 포맷은 JSONL로 결정했다.
- 파일 경로는 `eval/evaluation_dataset.jsonl`로 둔다.
- 질문 1개는 다음 필드를 가진다.
  - `id`
  - `question`
  - `query_type`
  - `answerable`
  - `expected_answer`
  - `expected_fields`
  - `relevant_docs`
  - `notes`
- Retrieval ground truth는 `relevant_docs`에 기록한다.
- `relevant_docs`는 현재 Chroma document metadata와 맞추기 위해 다음 기준을 사용한다.
  - `course`
  - `professor`
  - `field`
- 기본 평가 단위는 `강의명 + 교수명 + document type`으로 잡는다.
- 답변 불가능 질문은 `answerable=false`, `relevant_docs=[]`로 기록한다.
- Day 2에서 먼저 구현할 metric은 `Hit@K`, `Recall@K`, `Analyzer Field Match`로 정한다.

## 발견한 문제

- Query Analyzer가 `k`를 반환하지만 실제 retrieval 코드는 `k=10`으로 고정되어 있다.
  - 오늘은 수정하지 않고 baseline known issue로 남겼다.
  - 이후 Adaptive Top-K 실험의 비교 기준으로 사용한다.
- README의 설명은 Analyzer가 결정한 k만큼 검색한다고 되어 있지만, 실제 구현은 fixed `k=10`이다.
- 현재 retrieval 결과를 보기 전에는 Retrieval 실패와 Generation 실패를 구분하기 어렵다.
  - 이를 위해 debug script를 만들었지만, 아직 metric 계산은 없다.
- `강의평가`를 하나의 relevant document로 볼지, 리뷰 단위로 쪼개서 볼지 결정이 필요하다.
  - 현재는 `강의평가` 전체를 하나의 document로 평가한다.
  - 이후 `Field-level + Review-level Chunk` 실험에서 다시 검토한다.
- 교수명/강의명은 모든 document header에 반복되어 있다.
  - 예: "백엔드프레임워크 교수님은 누구야?" 같은 질문은 특정 field document 하나만 정답으로 보기 애매하다.
  - 현재 evaluation dataset에서는 대표 field를 지정했지만, 평가 기준을 더 정교하게 만들 필요가 있다.
- 조건형 질문은 정답 document가 여러 개일 수 있다.
  - 현재 30개 질문에서는 일부 대표 relevant document를 기록했다.
  - 전체 정답 집합을 완전히 확정하려면 데이터 검수 시간이 더 필요하다.

## 내일 할 일

- `eval/evaluation_dataset.jsonl` 30개 질문 전체에 대해 fixed `k=10` baseline retrieval을 실행한다.
- Retrieval debug 결과를 바탕으로 `Hit@K`, `Recall@K` 계산 script를 만든다.
- 실패 케이스를 유형별로 분류한다.
  - 강의명/교수명 keyword matching 실패
  - field filtering 실패
  - semantic query 실패
  - conditional query에서 정답 일부 누락
  - unanswerable 질문에 관련 없는 문서가 검색되는 문제
- Query Analyzer 결과와 `expected_fields`를 비교해 Analyzer가 필요한 정보를 잘 뽑는지 확인한다.
- 실패 분석 후 Chunking 실험의 첫 가설을 정한다.
  - 현재 Field-level Chunk 유지
  - Course-level Chunk와 비교
  - 강의평가 Review-level Chunk 필요 여부 검토

