import os
from langchain_community.vectorstores import Chroma
from utils.embedding import get_embedding_model
from utils.prompt import run_query_analyzer
import re
from langchain_core.documents import Document


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
        "강의평가_장점": "강의평가",
        "강의평가_단점": "강의평가",
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

# --------------------------------------------------------
# 🔥 강의명 + 교수명 기반 dedup
# --------------------------------------------------------
def extract_course_key(doc: Document):
    course = ""
    prof = ""

    for line in doc.page_content.splitlines():
        l = line.strip()
        if l.startswith("강의명:"):
            course = l.replace("강의명:", "").strip()
        elif l.startswith("교수명:"):
            prof = l.replace("교수명:", "").strip()
        if course and prof:
            break

    return f"{course}::{prof}" if course or prof else "UNKNOWN"


def dedup_by_course(docs):
    grouped = {}
    for d in docs:
        key = extract_course_key(d)
        grouped.setdefault(key, []).append(d)

    # 우선 가장 score 높은 chunk(=첫 chunk) 사용
    return [group[0] for group in grouped.values()]


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
    results = vectordb.similarity_search_with_score(query, k=k)
    docs = [r[0] for r in results]
    if not docs:
        return ""
    
    # ----------  dedup(중복 강의 제거) ----------
    dedup_docs = dedup_by_course(docs)
    # #---------- 필요 정보 기반 필터링 ----------
    filtered_docs = filter_by_fields(dedup_docs, needed_fields)

    context_str = "\n\n".join([d.page_content for d in filtered_docs])

    return context_str