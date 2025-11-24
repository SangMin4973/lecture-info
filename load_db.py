import os
import torch
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.retrievers import BaseRetriever

# --- 1. 경로 및 설정 (이전에 저장할 때와 동일하게 정의) ---
output_dir = './rag_output'
collection_name = 'lecture_info'
model_name = "Snowflake/snowflake-arctic-embed-l-v2.0"
cache_folder = './'
vectordb_dir = os.path.join(output_dir, 'vectordb')

# --- 2. 임베딩 모델 정의 (저장 시 사용한 것과 동일해야 함) ---
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"🛠️ Embedding device: {device}")

final_model_kwargs = {
    "device": device,
}
if "cuda" in device:
    final_model_kwargs["torch_dtype"] = torch.float16

embedding_model = SentenceTransformerEmbeddings(
    model_name=model_name,
    cache_folder=cache_folder,
    model_kwargs=final_model_kwargs,
    encode_kwargs={
        "normalize_embeddings": True,
        "prompt_name": "query" # 검색 시 쿼리 벡터 변환을 위해 필요
    }
)

# --- 3. Chroma 객체 로드 및 검색기 준비 ---
try:
    # 🌟 Chroma 객체 로드 (새로운 파일을 생성하지 않고, 기존 데이터 로드)
    loaded_vectordb = Chroma(
        persist_directory=vectordb_dir,
        collection_name=collection_name,
        embedding_function=embedding_model 
    )
    print("✅ Chroma 벡터 DB 로드 완료.")

    # 🌟 검색기(Retriever)로 변환하여 준비
    # k=5 설정은 가장 유사한 5개의 문서를 찾도록 설정합니다.
    retriever: BaseRetriever = loaded_vectordb.as_retriever(search_kwargs={'k': 5})
    
    print("🔍 검색기(Retriever) 준비 완료. (변수명: retriever)")
    
    # 이제 'retriever' 객체를 다른 RAG 구성 요소(LLM 체인 등)에 바로 사용할 수 있습니다.

except Exception as e:
    print(f"❌ Chroma DB 로드 중 오류 발생: {e}")
    print("저장 경로, 컬렉션 이름, 임베딩 모델 설정을 다시 확인하세요.")