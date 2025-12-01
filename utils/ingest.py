import os
import pandas as pd
import numpy as np
import torch
from tqdm import tqdm
import pickle

# LangChain 및 관련 모듈
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from langchain_core.documents import Document

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# --- 경로 및 설정 ---
output_dir = os.path.join(BASE_DIR, "rag_output")
collection_name = 'lecture_info'
model_name = "Snowflake/snowflake-arctic-embed-l-v2.0"
cache_folder = './'

# --- Chroma ---
vectordb_dir = os.path.join(output_dir, 'vectordb')
os.makedirs(vectordb_dir, exist_ok=True)
client = chromadb.PersistentClient(path=vectordb_dir)
data_path = os.path.join(BASE_DIR, "data", "text_data.txt")

# 기존 컬렉션 삭제
try:
    client.delete_collection(name=collection_name)
except:
    pass


# --- 2. Embedding Model ---
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"🛠️ Embedding device: {device}")

embedding_model = SentenceTransformerEmbeddings(
    model_name=model_name,
    cache_folder=cache_folder,
    encode_kwargs={
        "normalize_embeddings": True,
        "prompt_name": "query"
    }
)



# ================================
#  핵심: 문서를 통합된 텍스트로 재구성
# ================================
def flatten_document_content(metadata, page_content_parts):
    """
    강의명, 교수명, 학부명, 학과명, 이수구분, 학습내용 등을 하나의 텍스트로 통합한다.
    """
    course_name = metadata.get('강의명', '미정 강의')
    professor_name = metadata.get('교수명', '미상 교수')
    department = metadata.get('학부명', '')
    major = metadata.get('학과명', '')

    header = (
        f"강의명: {course_name}\n"
        f"교수명: {professor_name}\n"
        f"학부명: {department}\n"
        f"학과명: {major}\n"
    )

    body = "\n".join(page_content_parts)

    final_text = header + "\n" + body
    return final_text


# 기존 parse 함수 그대로 유지
def parse_lecture_info(text_block):
    metadata = {}
    fields = text_block.strip().split('#')
    for field in fields:
        if ':' in field:
            key, value = field.split(':', 1)
            metadata[key.strip()] = value.strip()
    return metadata

def merge_blocks_by_course(raw_lines):
    """
    동일 '강의명'을 가진 여러 줄을 하나로 병합한다.
    """
    merged = {}
    
    for line in raw_lines:
        metadata = parse_lecture_info(line)
        course_name = metadata.get("강의명")
        if not course_name:
            # 강의명이 없는 줄은 skip
            continue
        
        if course_name not in merged:
            merged[course_name] = metadata
        else:
            # 이미 존재하면 병합
            merged[course_name].update(metadata)
    
    return list(merged.values())

# ================================
#       파일 로드 → Document 변환
# ================================
def get_docs_from_file(file_path):

    print(f"📖 파일 로드 중: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        raw_lines = [l.strip() for l in f.readlines() if l.strip()]

    merged_blocks = merge_blocks_by_course(raw_lines)
    docs = []

    for metadata in merged_blocks:

        # 공통 header (⭐ 모든 chunk에 동일하게 들어감)
        header = (
            f"강의명: {metadata.get('강의명','')}\n"
            f"교수명: {metadata.get('교수명','')}\n"
            f"학부명: {metadata.get('학부명','')}\n"
            f"학과명: {metadata.get('학과명','')}\n"
            f"이수구분: {metadata.get('이수구분','')}\n"
        )

        # ⭐ 각 필드별로 chunk 생성
        field_chunks = {
            "학습내용": metadata.get("학습내용"),
            "수업진행방식": metadata.get("수업진행방식"),
            "선수과목과수강요건": metadata.get("선수과목과수강요건"),
            "강의평가": "별점: " + str(metadata.get("별점", "")) +
                      " / 낮음: " + str(metadata.get("강의평가_낮음","")) +
                      " / 높음: " + str(metadata.get("강의평가_높음",""))
        }

        for field_name, field_value in field_chunks.items():
            if field_value and field_value != "없음":
                page_content = header + f"\n[{field_name}]\n{field_value}"
                docs.append(Document(page_content=page_content, metadata={"source": file_path}))

    print(f"   - 총 {len(docs)}개의 청크 문서를 생성했습니다.")
    return docs



# ================================
#         Chunking 최소화
# ================================
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=3000,    # 강의 하나가 거의 1 chunk로 유지됨
    chunk_overlap=0
)


# ================================
#      문서 로드 및 DB 구축
# ================================
file_paths = [data_path]
doc_list = []

for file_path in tqdm(file_paths):
    docs = get_docs_from_file(file_path)
    doc_list.extend(docs)

if doc_list:
    split_docs = text_splitter.split_documents(doc_list)

    vectordb = Chroma(
        persist_directory=vectordb_dir,
        collection_name=collection_name,
        embedding_function=embedding_model
    )

    vectordb.add_documents(split_docs)
    print("✅ 벡터 DB 저장 완료!")

else:
    print("🛑 로드할 문서가 없습니다.")