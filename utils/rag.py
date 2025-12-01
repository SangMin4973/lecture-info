import os
from langchain_community.vectorstores import Chroma
from utils.embedding import get_embedding_model

# --- 설정 ---
OUTPUT_DIR = './rag_output'
VECTORDB_DIR = os.path.join(OUTPUT_DIR, 'vectordb')
COLLECTION_NAME = 'lecture_info'

_retriever = None

def _load_retriever():
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
    _retriever = vectordb.as_retriever(search_kwargs={'k': 10}) # k값은 조절 가능
    return _retriever

def retrieve(query):
    """
    chatbot.py에서 호출하는 함수.
    질문을 받아 관련 문서를 텍스트로 합쳐서 반환합니다.
    """
    retriever = _load_retriever()
    if not retriever:
        return ""
        
    # 문서 검색
    docs = retriever.invoke(query)
    
    # 검색된 문서들의 내용을 하나의 문자열로 합침 (List[Document] -> str)
    context_text = "\n\n".join([doc.page_content for doc in docs])
    return context_text