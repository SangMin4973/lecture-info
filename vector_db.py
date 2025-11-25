import os
import shutil
from tqdm import tqdm
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from utils.embedding import get_embedding_model
from utils.ingest import get_docs_from_file, add_title

# --- 설정 ---
OUTPUT_DIR = './rag_output'
VECTORDB_DIR = os.path.join(OUTPUT_DIR, 'vectordb')
COLLECTION_NAME = 'lecture_info'
DATA_FILE = './data/text_data.txt'

def build_vector_db():
    # 1. 기존 DB 삭제 (초기화)
    if os.path.exists(VECTORDB_DIR):
        try:
            shutil.rmtree(VECTORDB_DIR)
            print(f"🗑️ 기존 DB 폴더 삭제 완료: {VECTORDB_DIR}")
        except Exception as e:
            print(f"⚠️ 삭제 실패: {e}")

    # 2. 데이터 로드 및 청크 분할
    print("📂 데이터 로드 시작...")
    raw_docs = get_docs_from_file(DATA_FILE)
    if not raw_docs:
        print("🛑 데이터가 없습니다.")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
    split_docs = text_splitter.split_documents(raw_docs)
    final_docs = [add_title(doc) for doc in split_docs]
    
    print(f"📚 {len(final_docs)}개의 청크(Chunk) 생성 완료.")

    # 3. 벡터 DB 생성 및 저장
    embedding_model = get_embedding_model()
    
    print("⏳ 벡터 DB 생성 중...")
    vectordb = Chroma.from_documents(
        documents=final_docs,
        embedding=embedding_model,
        persist_directory=VECTORDB_DIR,
        collection_name=COLLECTION_NAME
    )
    print("✅ 벡터 DB 구축 완료!")

if __name__ == "__main__":
    build_vector_db()