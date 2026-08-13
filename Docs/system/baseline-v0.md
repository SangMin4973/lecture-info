# Baseline v0 - Current System

작성일: 2026-08-10

## 목적

현재 RAG 시스템을 개선 전 기준선으로 고정하고, 이후 Chunking, Adaptive Top-K, BM25, Reranker, embedding model 변경 등의 실험 결과를 비교하기 위한 기준 상태를 기록한다.

오늘 기준으로는 코드 동작을 개선하지 않고, 현재 구현 상태 자체를 baseline으로 본다.

## Repository Snapshot

- Branch: `main`
- HEAD: `49b4e1800680865690a2a91669dca9275cff47cc`
- Git 상태 확인 이슈: 현재 Windows 사용자/소유자 차이로 `git status`가 `dubious ownership` 오류를 반환한다.
- 기록 대상: 현재 워크스페이스의 로컬 파일 상태

## Runtime Structure

- Frontend: Streamlit
  - Entry: `ui_app.py`
  - API endpoint: `API_URL`, 기본값 `http://127.0.0.1:8000/chat`
- Backend: FastAPI
  - Entry: `api_server.py`
  - Endpoint: `POST /chat`
  - Request: `{ "query": string }`
  - Response: `{ "answer": string }`
- RAG pipeline:
  - Orchestrator: `utils/chatbot.py`
  - Retriever: `utils/rag.py`
  - Prompt / Query Analyzer: `utils/prompt.py`
  - LLM loader: `utils/llm.py`
  - Embedding loader: `utils/embedding.py`
  - Vector DB ingest: `utils/ingest.py`

## Model Configuration

### LLM

- Model: `Qwen/Qwen3-4B`
- Loader: Hugging Face `AutoTokenizer`, `AutoModelForCausalLM`, `pipeline("text-generation")`
- Quantization: BitsAndBytes 4-bit
  - `load_in_4bit=True`
  - `bnb_4bit_compute_dtype=torch.float16`
  - `bnb_4bit_quant_type="nf4"`
- Device placement: `device_map="auto"`
- Cache directory: `./models`
- Usage:
  - Query Analyzer와 최종 답변 생성 모두 같은 Qwen3-4B pipeline을 사용한다.

### Embedding

- Model: `Snowflake/snowflake-arctic-embed-l-v2.0`
- Loader: `SentenceTransformerEmbeddings`
- Cache directory: `./models`
- Device:
  - `cuda:0` if available
  - otherwise `cpu`
- Encode options:
  - `normalize_embeddings=True`
  - `prompt_name="query"`

## Data And Vector DB

- Source text data: `data/text_data.txt`
  - 현재 라인 수: 1174
- Cleaned CSV: `data/cleaned_data.csv`
  - 현재 row 수: 52
- Vector DB:
  - Type: ChromaDB
  - Persist directory: `./rag_output/vectordb`
  - Collection name: `lecture_info`
- Ingest script: `utils/ingest.py`

## Document Construction

`utils/ingest.py` 기준으로 원본 텍스트를 강의명과 교수명 단위로 병합한 뒤, 강의별 필드 문서로 분리한다.

생성되는 주요 document type:

- `이수구분`
- `선수과목과수강요건`
- `학습내용`
- `수업진행방식`
- `강의평가`

각 문서는 공통 header를 포함한다.

```text
강의명: ...
교수명: ...
학부명: ...
학과명: ...
```

그 뒤 `[학습내용]`, `[수업진행방식]` 같은 필드 태그와 본문이 이어진다.

Chunking 설정:

- Splitter: `RecursiveCharacterTextSplitter`
- `chunk_size=3000`
- `chunk_overlap=200`

현재 구조상 대부분은 "강의 + 정보 필드" 단위 document를 만든 뒤 필요 시 3000자 기준으로 split한다.

## Query Analyzer

Implementation: `utils/prompt.py`

Query Analyzer는 사용자 질문을 받아 다음 JSON을 생성하도록 프롬프트된다.

```json
{
  "k": 10,
  "필요 정보": ["필드1", "필드2"]
}
```

Analyzer 기준:

- 단일 강의 단일 정보 조회: `k=3`
- 강의 세부 필드 조회: `k=5`
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

Analyzer 실패 시 fallback:

```json
{
  "k": 10,
  "필요 정보": []
}
```

## Retrieval Flow

Implementation: `utils/rag.py`

현재 `retrieve(query, pipe, tokenizer, vectordb)` 흐름:

1. `run_query_analyzer()`로 `k`, `필요 정보` 추출
2. Chroma `similarity_search_with_score(query, k=10)` 실행
3. 검색 결과에서 document만 추출
4. Analyzer의 `필요 정보`를 기준으로 field filtering
5. 같은 `강의명::교수명` 기준으로 document 병합
6. 병합된 document의 `page_content`를 최종 context string으로 결합
7. `utils/prompt.py`의 `build_prompt()`로 최종 답변 프롬프트 생성
8. Qwen3-4B로 답변 생성

현재 retrieval method:

- Dense vector similarity search only
- Chroma `similarity_search_with_score`
- BM25 없음
- Reranker 없음
- Hybrid search 없음
- Metadata filter 기반 검색 없음

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

## Known Issues

1. Analyzer가 반환한 `k`가 실제 검색에 적용되지 않는다.
   - `utils/rag.py`에서 `k = qa.get("k", 10)`로 값을 읽지만, 실제 검색은 `vectordb.similarity_search_with_score(query, k=10)`으로 고정되어 있다.
   - 이 문제는 오늘 수정하지 않는다.
   - Adaptive Top-K 실험의 비교 기준으로 남긴다.

2. README의 데이터 흐름 설명과 실제 구현이 다르다.
   - README는 Analyzer가 결정한 k만큼 검색한다고 설명한다.
   - 실제 구현은 fixed `k=10`이다.

3. `utils/chatbot.py`의 `__main__` 테스트 코드가 analyzer 결과를 기록하는 것처럼 보이지만, 실제 `chatbot(q)`의 반환값은 최종 답변이다.
   - `run_query_analyzer() 결과` 라벨로 최종 답변을 기록할 가능성이 있다.

4. Retrieval debug output이 충분하지 않다.
   - 현재 최종 답변 생성 전 단계의 analyzer 결과, retrieved documents, similarity score를 구조적으로 저장하지 않는다.
   - Retrieval 실패와 Generation 실패를 분리해서 보기 어렵다.

5. `utils/rag.py`의 `_retriever` 캐시 변수가 실제로 설정되지 않는다.
   - `_load_vectordb()`는 `_retriever`가 있으면 반환하지만, 새로 만든 `vectordb`를 `_retriever`에 저장하지 않는다.

6. Embedding 설정이 ingest와 runtime에서 완전히 동일하지 않다.
   - `utils/embedding.py` runtime loader는 `model_kwargs={"device": device}`를 전달한다.
   - `utils/ingest.py`에서는 device를 출력하지만 `SentenceTransformerEmbeddings`에 `model_kwargs`를 전달하지 않는다.

7. `requirements.txt`에 `langchain-huggingface`가 중복 기재되어 있고, `rank_bm25`가 포함되어 있으나 현재 retrieval baseline에서는 사용하지 않는다.

## Today Baseline Rule

오늘은 위 known issue를 고치지 않는다. 이 상태를 `baseline-v0`로 기록하고, 다음 단계에서 evaluation dataset과 retrieval debug script를 만든 뒤 fixed `k=10` 기준 성능을 측정한다.

