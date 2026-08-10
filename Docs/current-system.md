# 01. Current System

작성일: 2026-08-10

현재 시스템은 `baseline-v0`로 기록한다. 오늘은 RAG 성능 개선이나 버그 수정을 하지 않고, 현재 구현 상태를 평가 기준선으로 고정한다.

---

# Current RAG Pipeline

## LLM

- Model: `Qwen/Qwen3-4B`
- Loader: Hugging Face `AutoTokenizer`, `AutoModelForCausalLM`, `pipeline("text-generation")`
- Quantization: BitsAndBytes 4-bit
  - `load_in_4bit=True`
  - `bnb_4bit_compute_dtype=torch.float16`
  - `bnb_4bit_quant_type="nf4"`
- Device: `device_map="auto"`
- Cache path: `./models`
- Usage:
  - Query Analyzer
  - Final answer generation

## Embedding Model

- Model: `Snowflake/snowflake-arctic-embed-l-v2.0`
- Loader: LangChain `SentenceTransformerEmbeddings`
- Cache path: `./models`
- Runtime device:
  - GPU available: `cuda:0`
  - otherwise: `cpu`
- Encode options:
  - `normalize_embeddings=True`
  - `prompt_name="query"`

## Retrieval Method

현재 검색 방식은 ChromaDB dense vector similarity search만 사용한다.

Retrieval flow:

1. 사용자 질문 입력
2. Query Analyzer가 `k`와 `필요 정보` 추출
3. Chroma `similarity_search_with_score(query, k=10)` 실행
4. 검색된 document를 Analyzer의 `필요 정보` 기준으로 필터링
5. 같은 `강의명::교수명` document를 병합
6. 병합된 context를 최종 LLM prompt에 삽입
7. Qwen3-4B가 최종 답변 생성

현재 사용하지 않는 방식:

- BM25 없음
- Reranker 없음
- Hybrid search 없음
- Metadata filter 기반 검색 없음

## Query Analyzer

Query Analyzer는 사용자 질문을 분석해 JSON을 반환하도록 프롬프트된다.

```json
{
  "k": 10,
  "필요 정보": ["강의명", "교수명", "학습내용"]
}
```

Analyzer 기준:

- 단일 강의의 단일 정보 조회: `k=3`
- 강의의 세부 필드 조회: `k=5`
- 조건 기반 강의 검색: `k=10`
- 특정 교수/학부/전공 전체 조회: `k=15`

지원 필드:

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

Analyzer parsing 실패 시 fallback:

```json
{
  "k": 10,
  "필요 정보": []
}
```

## Generation Prompt

최종 답변 프롬프트는 다음 구조다.

```text
당신은 강의 추천을 돕는 AI 조교입니다. 아래 정보를 바탕으로 질문에 답해주세요.

[정보]
{context}

[질문]
{query}

[규칙]
**반드시 한글로 답변해주세요**

[답변]
```

## Known Issue

현재 `utils/rag.py`에서 Query Analyzer가 `k`를 반환하지만, 실제 검색은 아래처럼 `k=10`으로 고정되어 있다.

```python
results = vectordb.similarity_search_with_score(query, k=10)
```

이 문제는 오늘 수정하지 않고 baseline의 known issue로 기록한다. 이후 Adaptive Top-K 실험에서 비교 기준으로 사용한다.

---

# DATA

## Source Data

- Source text data: `data/text_data.txt`
  - 현재 라인 수: 1174
- Cleaned CSV: `data/cleaned_data.csv`
  - 현재 row 수: 52
- Raw CSV: `data/raw_data.csv`
- 데이터 내용:
  - 강의계획서 정보
  - 에브리타임 강의평가
  - 강의명, 교수명, 학부명, 학과명, 이수구분, 선수요건, 학습내용, 수업진행방식, 별점, 강의평가 등

## Vector DB

- Vector DB: ChromaDB
- Persist directory: `./rag_output/vectordb`
- Collection name: `lecture_info`
- Ingest script: `utils/ingest.py`

## Document Construction

원본 강의 데이터를 `강의명 + 교수명` 기준으로 병합한 뒤, 정보 필드별 document를 만든다.

Document types:

- `이수구분`
- `선수과목과수강요건`
- `학습내용`
- `수업진행방식`
- `강의평가`

각 document는 다음 header를 포함한다.

```text
강의명: ...
교수명: ...
학부명: ...
학과명: ...
```

그 뒤 `[학습내용]`, `[수업진행방식]`, `[강의평가]` 같은 field tag와 본문이 이어진다.

## Chunk Structure

- Splitter: `RecursiveCharacterTextSplitter`
- `chunk_size=3000`
- `chunk_overlap=200`

현재 구조상 대부분은 "강의 + 정보 필드" 단위 document를 만든 뒤 필요 시 3000자 기준으로 split한다.

## Field Filtering

`filter_by_fields()`는 Analyzer가 반환한 `필요 정보`를 document tag와 매칭한다.

현재 field alias:

- `학습내용` -> `학습내용`
- `수업방식` -> `수업진행방식`
- `수업진행방식` -> `수업진행방식`
- `선수요건` -> `선수과목과수강요건`
- `선수과목과수강요건` -> `선수과목과수강요건`
- `별점` -> `강의평가`
- `강의평가` -> `강의평가`

필터링 결과가 비어 있으면 원본 검색 문서를 그대로 사용한다.

---

# Architecture

## Runtime Structure

- Frontend: Streamlit
  - Entry: `ui_app.py`
  - API endpoint: `API_URL`
  - Default API URL: `http://127.0.0.1:8000/chat`
- Backend: FastAPI
  - Entry: `api_server.py`
  - Endpoint: `POST /chat`
  - Request: `{ "query": string }`
  - Response: `{ "answer": string }`
- RAG modules:
  - Orchestrator: `utils/chatbot.py`
  - Retriever: `utils/rag.py`
  - Prompt / Query Analyzer: `utils/prompt.py`
  - LLM loader: `utils/llm.py`
  - Embedding loader: `utils/embedding.py`
  - Vector DB ingest: `utils/ingest.py`

## Request Flow

```text
User
  -> Streamlit UI
  -> FastAPI /chat
  -> utils.chatbot.chatbot()
  -> utils.rag.retrieve()
  -> Query Analyzer
  -> ChromaDB similarity search
  -> Field filtering
  -> Course/professor document merge
  -> Final prompt construction
  -> Qwen3-4B answer generation
  -> FastAPI response
  -> Streamlit UI
```

## Repository Snapshot

- Branch: `main`
- HEAD: `49b4e1800680865690a2a91669dca9275cff47cc`
- Git 상태 확인 이슈:
  - 현재 Windows 사용자/소유자 차이로 `git status`가 `dubious ownership` 오류를 반환한다.
  - 따라서 이 문서는 현재 워크스페이스의 로컬 파일 상태를 기준으로 작성했다.

## Baseline Notes

- 현재 baseline은 fixed `k=10` retrieval이다.
- Query Analyzer의 `k`는 기록되지만 실제 검색에는 반영되지 않는다.
- Retrieval 결과와 similarity score를 구조적으로 저장하는 evaluation/debug script는 아직 없다.
- Retrieval 실패와 Generation 실패를 분리해 보기 어렵다.

