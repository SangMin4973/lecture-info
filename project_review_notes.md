# Lecture Info 프로젝트 실행/평가 메모

작성일: 2026-08-10

## 1. 프로젝트 실행 방법

현재 프로젝트는 `FastAPI` 백엔드와 `Streamlit` 프론트엔드로 구성되어 있다.

### 프로젝트 폴더 이동

```powershell
cd "C:\Users\dltkd\OneDrive\바탕 화면\이상민\취업준비\project\lecture-info"
```

### 가상환경 활성화

```powershell
.\venv\Scripts\Activate.ps1
```

실행 정책 오류가 발생하면 아래 명령을 먼저 실행한다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

한 줄로 실행할 경우에는 세미콜론으로 구분해야 한다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\venv\Scripts\Activate.ps1
```

정상 활성화되면 PowerShell 프롬프트 앞에 `(venv)`가 표시된다.

## 2. 의존성 설치

기본 명령:

```powershell
pip install -r requirements.txt
```

Windows에서 다음과 같은 인코딩 오류가 발생할 수 있다.

```text
UnicodeDecodeError: 'cp949' codec can't decode byte ...
```

이 경우 UTF-8 모드로 실행한다.

```powershell
$env:PYTHONUTF8="1"
python -m pip install -r requirements.txt
```

그래도 실패하면 콘솔 코드페이지도 UTF-8로 변경한다.

```powershell
chcp 65001
$env:PYTHONUTF8="1"
python -m pip install -r requirements.txt
```

## 3. 서버 실행

터미널 1에서 백엔드 실행:

```powershell
cd "C:\Users\dltkd\OneDrive\바탕 화면\이상민\취업준비\project\lecture-info"
.\venv\Scripts\Activate.ps1
python api_server.py
```

백엔드는 기본적으로 다음 주소에서 실행된다.

```text
http://127.0.0.1:8000
```

터미널 2에서 프론트엔드 실행:

```powershell
cd "C:\Users\dltkd\OneDrive\바탕 화면\이상민\취업준비\project\lecture-info"
.\venv\Scripts\Activate.ps1
$env:PYTHONUTF8="1"
streamlit run ui_app.py
```

Streamlit UI는 보통 다음 주소에서 열린다.

```text
http://localhost:8501
```

참고로 `start.sh`는 Linux/Docker용 스크립트이므로 Windows PowerShell에서 직접 실행하는 방식은 적합하지 않다.

## 4. 프로젝트 구조 요약

확인된 주요 파일 구조:

```text
api_server.py
ui_app.py
utils/
  chatbot.py
  rag.py
  llm.py
  embedding.py
  ingest.py
  prompt.py
data/
rag_output/
Dockerfile
requirements.txt
start.sh
README.md
```

역할:

- `api_server.py`: FastAPI 백엔드 API 서버
- `ui_app.py`: Streamlit 기반 채팅 UI
- `utils/chatbot.py`: 전체 RAG 흐름 제어
- `utils/rag.py`: ChromaDB 검색 및 문서 병합
- `utils/llm.py`: HuggingFace LLM 로딩
- `utils/embedding.py`: 임베딩 모델 로딩
- `utils/ingest.py`: 원본 데이터 기반 벡터 DB 생성
- `utils/prompt.py`: 프롬프트 생성, Query Analyzer, 응답 파싱

## 5. 프로젝트 레벨 평가

종합 판단:

```text
대학생 팀 프로젝트/포트폴리오 중상급 프로토타입
실무 서비스 기준으로는 초기 MVP 단계
```

대략적인 점수:

```text
아이디어/주제 적합성: 8/10
기능 구현 완성도:    7/10
코드 구조화:         6.5/10
실행/배포 준비도:    5.5/10
실무 품질:           4.5/10
포트폴리오 가치:     7/10
```

종합 점수는 10점 만점 기준 약 `6.5~7점` 정도로 판단된다.

## 6. 잘한 부분

- 강의계획서/강의평가 데이터를 RAG로 검색하는 주제가 명확하다.
- 단순 CRUD가 아니라 LLM, Embedding, Vector DB를 활용했다.
- FastAPI 백엔드와 Streamlit 프론트엔드가 분리되어 있다.
- LangChain, ChromaDB, HuggingFace 모델 사용 경험을 보여줄 수 있다.
- Dockerfile과 GitHub Actions 배포 워크플로우가 존재한다.
- 도메인 데이터 수집, 정제, 벡터화 흐름이 포함되어 있다.

## 7. 주요 약점

### 테스트 부재

단위 테스트, API 테스트, RAG 검색 품질 테스트가 없다. 현재는 실행해봐야 정상 여부를 알 수 있는 구조다.

### 에러 처리 부족

LLM 로딩 실패 시 `None`이 반환되지만 이후 단계에서 명확하게 처리하지 않는다. API에서도 예외 응답 처리가 충분하지 않다.

### RAG 로직의 미완성 부분

`Query Analyzer`가 `k` 값을 계산하지만 실제 검색에서는 `k=10`이 고정되어 있다.

```python
k = qa.get("k", 10)
results = vectordb.similarity_search_with_score(query, k=10)
```

분석 결과를 실제 검색에 반영하려면 `k=k`로 바꾸는 것이 맞다.

### JSON 파싱 취약성

LLM이 JSON을 조금만 잘못 출력해도 기본값으로 fallback된다. 실서비스라면 구조화 출력, 재시도, 검증 로직이 필요하다.

### 전역 상태 사용

`s_pipe`, `s_tokenizer`, `vectordb` 같은 전역 상태가 사용된다. 프로토타입에서는 가능하지만 운영 환경에서는 초기화 실패, 동시성, 재시작 문제를 만들 수 있다.

### 의존성 관리 부족

`requirements.txt`에 버전 고정이 부족하고 중복 항목도 있다.

```text
langchain-huggingface==1.0.1
langchain-huggingface
```

다른 PC에서 설치할 때 버전 차이로 깨질 가능성이 있다.

### Windows 로컬 실행성 낮음

`bitsandbytes`, CUDA, Qwen 모델 로딩 때문에 Windows 일반 환경에서는 실행 실패 가능성이 있다. Docker/GPU 서버 중심 프로젝트에 가깝다.

### README/한글 인코딩 문제

README와 PowerShell 출력에서 한글이 깨져 보인다. 포트폴리오 제출 시 큰 감점 요소가 될 수 있다.

### HTML escape 문제

Streamlit UI에서 `unsafe_allow_html=True`를 사용하면서 사용자 입력을 직접 HTML에 넣는다. 실무 기준에서는 XSS/표시 오류 가능성이 있다.

## 8. 면접에서 예상되는 질문

- 검색 정확도는 어떻게 평가했는가?
- hallucination을 어떻게 줄였는가?
- Query Analyzer가 실패하면 어떻게 되는가?
- 왜 Qwen3-4B를 선택했는가?
- 응답 속도는 어느 정도인가?
- GPU 없는 환경에서는 어떻게 실행하는가?
- 테스트는 왜 없는가?
- requirements 버전이 고정되지 않은 이유는?
- Docker 이미지 크기와 모델 캐시는 어떻게 관리하는가?

## 9. 개선 우선순위

1. README 인코딩 깨짐 수정
2. `requirements.txt` 버전 고정
3. Query Analyzer의 `k` 값을 실제 검색에 반영
4. API 예외 처리 추가
5. `/health` 엔드포인트 추가
6. 샘플 질문 10~20개 기준 RAG 평가 결과 작성
7. 테스트 코드 최소 3개 추가
8. Docker 실행 방법 검증
9. 사용자 입력 HTML escape 처리
10. 모델 로딩 실패 시 명확한 에러 메시지 반환

## 10. 최종 평가 문장

이 프로젝트는 RAG 앱의 전체 흐름을 이해하고 구현한 초중급 이상 프로젝트다. 다만 실무형 서비스로 보기에는 테스트, 안정성, 의존성 관리, 배포 재현성이 부족하다. 위 개선 항목을 정리하면 포트폴리오 완성도는 현재 약 6.5~7점에서 8점 근처까지 올릴 수 있다.
