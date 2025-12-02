# 🎓 강의 정보 및 평가 통합 RAG 챗봇 (Lecture Info AI Assistant)

> **강의계획서와 강의평가를 한 번에!** > 대학생들의 수강 신청을 돕기 위한 **RAG(Retrieval-Augmented Generation)** 기반의 AI 챗봇 서비스입니다.

![Python](https://img.shields.io/badge/Python-3.10-blue) 
![Framework](https://img.shields.io/badge/LangChain-1.0-green) 
![Model](https://img.shields.io/badge/LLM-Qwen3--4B-purple) 
![Deploy](https://img.shields.io/badge/Docker-Enabled-blue) 
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📖 프로젝트 소개 (Overview)

대학생들이 수강 신청 정보를 얻기 위해 학교 포털(강의계획서)과 커뮤니티(에브리타임 강의평가)를 번갈아 확인해야 하는 불편함을 해결하고자 개발되었습니다.
**LangChain**과 **Open Source LLM**을 활용하여 흩어진 강의 정보를 통합하고, 자연어 대화를 통해 원하는 정보를 쉽고 빠르게 얻을 수 있습니다.

### 🎯 주요 기능
* **자연어 질의응답:** "머신러닝입문 선수과목 알려줘", "이 수업 학점 잘 주나요?" 등 대화형 정보 검색.
* **통합 정보 제공:** 강의 학습 내용, 선수 과목, 수업 방식, 그리고 실제 수강생들의 장단점 평가 요약 제공.
* **검색 증강 생성 (RAG):** 환각(Hallucination)을 최소화하고 정확한 데이터베이스 기반 답변 생성.

---

## 🛠️ 기술 스택 (Tech Stack)

| 구분 | 기술 / 도구 | 설명 |
| :--- | :--- | :--- |
| **LLM** | **Qwen/Qwen3-4B** | 한국어 성능이 우수한 4B 경량화 모델 (4-bit Quantization 적용) |
| **Embedding** | **Snowflake/arctic-embed-l-v2.0** | 다국어 및 검색 성능이 최적화된 임베딩 모델 |
| **Vector DB** | **ChromaDB** | 로컬 환경에서의 문서 벡터 저장 및 검색 |
| **Backend** | **FastAPI** | REST API 서버 구축 및 모델 서빙 |
| **Frontend** | **Streamlit** | 사용자 친화적인 채팅 인터페이스 구현 |
| **Infra** | **Docker & NVIDIA CUDA** | GPU 가속 환경 및 배포 자동화 (CUDA 12.1) |

---

## 📂 프로젝트 구조 (Directory Structure)

```bash
.
├── api_server.py       # FastAPI 백엔드 서버 (LLM 통신)
├── ui_app.py           # Streamlit 프론트엔드 (채팅 UI)
├── data/
│   └── text_data.txt   # 강의 정보 원본 데이터
├── utils/              # 핵심 로직 모듈
│   ├── chatbot.py      # RAG 파이프라인 제어
│   ├── ingest.py       # 텍스트 데이터 전처리 및 Vector DB 생성
│   ├── llm.py          # LLM 모델 로딩 (BitsAndBytes 4-bit)
│   ├── rag.py          # 문서 검색 (Retriever) 로직
│   ├── prompt.py       # 프롬프트 엔지니어링 템플릿
│   └── embedding.py    # 임베딩 모델 설정
├── Dockerfile          # Docker 이미지 빌드 설정
├── start.sh            # 서비스 실행 스크립트 (Backend + Frontend)
└── requirements.txt    # 의존성 패키지 목록
```

### 서비스링크
http://192.168.63.230:8501
