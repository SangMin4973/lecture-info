import os
from langchain_community.vectorstores import Chroma
from utils.embedding import get_embedding_model

# --- 설정 ---
OUTPUT_DIR = './rag_output'
VECTORDB_DIR = os.path.join(OUTPUT_DIR, 'vectordb')
COLLECTION_NAME = 'lecture_info'

def get_retriever(k=5):
    """저장된 Vector DB를 로드하고 검색기를 반환합니다."""
    try:
        embedding_model = get_embedding_model()
        
        if not os.path.exists(VECTORDB_DIR):
            print("⚠️ Vector DB 경로가 없습니다. vector_db.py를 먼저 실행하세요.")
            return None

        vectordb = Chroma(
            persist_directory=VECTORDB_DIR,
            collection_name=COLLECTION_NAME,
            embedding_function=embedding_model
        )
        print("✅ Chroma DB 로드 완료.")
        return vectordb.as_retriever(search_kwargs={'k': k})
        
    except Exception as e:
        print(f"❌ Retriever 로드 실패: {e}")
        return None

# 싱글톤처럼 모듈 로드 시 바로 준비 (선택 사항)
retriever = get_retriever()