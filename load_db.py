import os
from langchain_community.vectorstores import Chroma
from langchain_core.retrievers import BaseRetriever
from utils.embedding import get_embedding_model

# 경로 및 설정 
output_dir = './rag_output'
collection_name = 'lecture_info'
vectordb_dir = os.path.join(output_dir, 'vectordb')

# 임베딩 모델 로드 
embedding_model = get_embedding_model() 

# Chroma 객체 로드 및 검색기 준비 
retriever = None

try:
    print(f"📂 벡터 DB 경로 확인: {vectordb_dir}")
    
    # Chroma 객체 로드
    loaded_vectordb = Chroma(
        persist_directory=vectordb_dir,
        collection_name=collection_name,
        embedding_function=embedding_model 
    )
    print("✅ Chroma 벡터 DB 로드 완료.")

    # 검색기(Retriever) 설정 (k=5)
    retriever = loaded_vectordb.as_retriever(search_kwargs={'k': 5})
    print("🔍 검색기(Retriever) 준비 완료.")

except Exception as e:
    print(f"❌ Chroma DB 로드 중 오류 발생: {e}")
    print("저장 경로, 컬렉션 이름, 임베딩 모델 설정을 다시 확인하세요.")

