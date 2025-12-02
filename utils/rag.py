import os
from langchain_community.vectorstores import Chroma
from utils.embedding import get_embedding_model
from utils.prompt import run_query_analyzer
import re
from langchain_core.documents import Document
from utils.llm import get_llm

# --- 설정 ---
OUTPUT_DIR = './rag_output'
VECTORDB_DIR = os.path.join(OUTPUT_DIR, 'vectordb')
COLLECTION_NAME = 'lecture_info'

_retriever = None

def _load_vectordb():
    """내부적으로만 사용하는 로더"""
    global _retriever
    if _retriever is not None:
        return _retriever
        
    print("🚀 Vector DB 로딩 시작...")
    embedding_model = get_embedding_model() # CPU/GPU 자동 감지
    
    vectordb = Chroma(
        persist_directory=VECTORDB_DIR,
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_model
    )

    return vectordb

# --------------------------------------------------------
# 🔥 필요 정보 기반 필터
# --------------------------------------------------------
def filter_by_fields(docs, needed_fields):
    if not needed_fields:
        return docs

    field_map = {
        "학습내용": "학습내용",
        "수업방식": "수업진행방식",
        "수업진행방식": "수업진행방식",
        "선수요건": "선수과목과수강요건",
        "선수과목과수강요건": "선수과목과수강요건",
        "별점": "강의평가",
        "강의평가": "강의평가"
    }

    mapped = set(field_map.get(f, f) for f in needed_fields)

    final = []
    for doc in docs:
        tag_match = re.search(r"\[(.+?)\]", doc.page_content)
        if tag_match:
            tag = tag_match.group(1).strip()
            if tag in mapped:
                final.append(doc)
        else:
            final.append(doc)

    return final if final else docs

def merge_docs_by_course(docs):
    merged = {}

    for d in docs:
        course = d.metadata.get("강의명", "")
        prof = d.metadata.get("교수명", "")
        key = f"{course}::{prof}"

        if key not in merged:
            merged[key] = {
                "metadata": {"강의명": course, "교수명": prof},
                "contents": []
            }

        # page_content 추가 (순서 유지)
        merged[key]["contents"].append(d.page_content)

    # 최종 Document 리스트 생성
    final_docs = []
    for key, value in merged.items():
        combined_content = "\n\n".join(value["contents"])
        final_docs.append(
            Document(
                metadata=value["metadata"],
                page_content=combined_content
            )
        )

    return final_docs

# --------------------------------------------------------
# 🎯 최종 retrieve(query)
# --------------------------------------------------------
def retrieve(query: str, pipe, tokenizer, vectordb):
    
    # ---------- 1) Query Analyzer ----------
    qa = run_query_analyzer(query, pipe, tokenizer)
    k = qa.get("k", 10)
    needed_fields = qa.get("필요 정보", [])

    print(f"🔍 Query Analyzer → k={k}, 필요정보={needed_fields}")

    #---------- 2) similarity search ----------
    results = vectordb.similarity_search_with_score(query, k=10)
    docs = [r[0] for r in results]
    if not docs:
        return ""
    
    # #---------- 필요 정보 기반 필터링 ----------
    filtered_docs = filter_by_fields(docs, needed_fields)

    # #---------- 같은 헤더 문서 병합 ----------
    merged_docs =  merge_docs_by_course(filtered_docs)
    context_str = "\n\n".join([d.page_content for d in merged_docs])
    # context_str = "\n\n".join([d.page_content for d in docs])
    return context_str