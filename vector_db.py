import os
import pandas as pd
import numpy as np
import torch
from tqdm import tqdm

# LangChain 및 관련 모듈
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
import chromadb
from langchain_core.documents import Document

# --- 경로 및 설정 ---
output_dir = './rag_output'
collection_name = 'lecture_info'
model_name = "Snowflake/snowflake-arctic-embed-l-v2.0"
cache_folder = './'

# --- 1. ChromaDB 클라이언트 및 컬렉션 초기화 ---
vectordb_dir = os.path.join(output_dir, 'vectordb')
os.makedirs(vectordb_dir, exist_ok=True)
client = chromadb.PersistentClient(path=vectordb_dir)

# 컬렉션 삭제 (재실행 대비)
try:
    client.delete_collection(name=collection_name)
    print(f"✅ '{collection_name}' collection이 삭제되었습니다.")
except Exception as e:
    # 컬렉션이 없으면 무시
    print(f"⚠️ 컬렉션 삭제 중 오류 발생 (이미 없을 수 있음): {e}")

# --- 2. 임베딩 모델 정의 ---
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"🛠️ Embedding device: {device}")

# SentenceTransformerEmbeddings에 전달할 최종 model_kwargs 구성 (오류 해결 반영)
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
        "prompt_name": "query"  # query prefix 자동 적용
    }
)

# --- 3. 데이터 로딩 및 전처리 함수 정의 (Pandas 로직 대신 텍스트 파싱 로직 적용) ---

# 기존 set_form 함수와 get_docs_csv 함수는 사용하지 않으므로 삭제 또는 주석 처리했습니다.

def parse_lecture_info(text_block):
    """단일 강의 정보 블록 텍스트를 파싱하여 Dictionary 형태로 반환합니다."""
    metadata = {}
    
    # '필드명:값' 형태의 쌍이 ' - '로 분리되어 있다고 가정
    fields = text_block.strip().split('-')
    
    for field in fields:
        # 각 필드는 '키:값' 형태로 되어 있음. 콜론을 기준으로 분리
        if ':' in field:
            # 첫 번째 콜론만 구분자로 사용
            key, value = field.split(':', 1)
            metadata[key.strip()] = value.strip()
    
    return metadata


def get_docs_from_file(file_path):
    """
    특정 포맷의 텍스트 파일을 읽어 LangChain Document 객체 리스트로 반환합니다.
    (강의평가 필드 포함 버전)
    """
    print(f"📖 파일 로드 중: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 파일 내용을 줄바꿈으로 분리하고, 공백인 줄은 제거하여 강의 정보 블록 리스트를 만듭니다.
            lecture_blocks = [block.strip() for block in content.split('\n') if block.strip()]
    except Exception as e:
        print(f"❌ 파일 읽기 오류: {file_path}, {e}")
        return []

    docs = []
    
    for block_text in lecture_blocks:
        if not block_text:
            continue
            
        metadata = parse_lecture_info(block_text)
        
        course_name = metadata.get('강의명', '미정 강의')
        professor_name = metadata.get('교수명', '미상 교수')
        
        # 문서의 주 내용은 '학습내용', '수업진행방식', '선수과목과수강요건' 그리고 강의평가를 조합
        page_content_parts = []
        
        # 1. 학습내용 추출 및 본문 추가 (pop)
        learning_content = metadata.pop('학습내용', None)
        if learning_content:
            page_content_parts.append(f"**학습 내용:** {learning_content}")
            
        # 2. 수업진행방식 추출 및 본문 추가 (pop)
        method_content = metadata.pop('수업진행방식', None)
        if method_content:
            page_content_parts.append(f"**수업 방식:** {method_content}")
            
        # 3. 선수과목과수강요건 추출 및 본문 추가 (pop)
        prerequisite = metadata.pop('선수과목과수강요건', None)
        if prerequisite:
            page_content_parts.append(f"**선수 요건:** {prerequisite}")
            
        # 4. 강의평가 관련 필드 추출 및 본문 추가 (새로 추가된 로직)
        review_score = metadata.pop('별점', None)
        review_low = metadata.pop('강의평가_낮음', None)
        review_high = metadata.pop('강의평가_높음', None)
        
        review_parts = []
        if review_score:
            review_parts.append(f"별점: {review_score}")
        if review_low and review_low != '없음': # '없음' 필터링 추가
            review_parts.append(f"단점: {review_low}")
        if review_high and review_high != '없음': # '없음' 필터링 추가
            review_parts.append(f"장점: {review_high}")
            
        if review_parts:
            # 강의 평가 정보를 하나의 블록으로 묶어 본문에 추가
            page_content_parts.append(f"**강의 평가 정보:** {' / '.join(review_parts)}")


        page_content = "\n".join(page_content_parts)
        
        # 내용이 충분히 길 때만 Document로 생성 (메타데이터만 있는 줄은 제외)
        if len(page_content) > 10:
            
            # 남은 필드들과 'source', 'title'을 정리
            final_metadata = {
                'source': file_path, 
                'title': f"{course_name} ({professor_name})", 
                **metadata 
            }
            
            doc = Document(
                page_content=page_content,
                metadata=final_metadata
            )
            docs.append(doc)

    print(f"   - 총 {len(docs)}개의 기본 문서(Document)를 로드했습니다.")
    return docs

def add_title(doc):
    """청크의 page_content 앞에 Title 메타데이터를 추가합니다."""
    title = doc.metadata.get('title', '')
    if title:
        doc.page_content = f"Title : {title}\n\n{doc.page_content}"
    return doc


# --- 4. 벡터화 실행 ---
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=102)

# file_paths = get_file_paths('./data') # 기존 함수 대신 명시된 파일 경로 사용
file_paths = ['./data/text_data.txt'] # 사용자 입력에 따라 파일 경로 고정

doc_list = []
for file_path in tqdm(file_paths):
    # 파일 확장자 검사 불필요. 모든 파일이 CSV 형식이라고 가정하고 처리
    docs = get_docs_from_file(file_path)
    doc_list.extend(docs)

if doc_list:
    # 텍스트 분할 (청크 생성)
    split_docs = text_splitter.split_documents(doc_list)
    # 청크 내용에 제목 추가
    split_docs_rev = [add_title(doc) for doc in split_docs]
    print(f"📚 총 {len(split_docs_rev)}개의 최종 청크가 생성되었습니다.")
    
    # Chroma 객체 생성 (임베딩 함수 및 persist_directory 설정)
    vectordb = Chroma(
        persist_directory=vectordb_dir,
        collection_name=collection_name,
        embedding_function=embedding_model
    )
    
    # 벡터 DB에 문서 추가
    print("⏳ 벡터 DB에 문서 추가 중...")
    vectordb.add_documents(split_docs_rev, embedding=embedding_model)
    print("✅ 벡터 DB 저장 완료.")

    # 검색기 초기화
    retriever = vectordb.as_retriever(
        search_kwargs={'k': 5}
    )
    bm25_retriever = BM25Retriever.from_documents(
        documents=split_docs_rev,
        k=5,
    )
    print("🔍 검색기 초기화 완료.")

else:
    print("🛑 로드할 문서가 없습니다. 데이터 파일(.txt)을 확인하세요.")

print('\n' + '#'*20, '최종 완료', '#'*20)