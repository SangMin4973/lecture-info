import os
import torch
from tqdm import tqdm
import chromadb

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# --- 경로 설정 ---
output_dir = os.path.join(BASE_DIR, "rag_output")
vectordb_dir = os.path.join(output_dir, "vectordb")
os.makedirs(vectordb_dir, exist_ok=True)

cache_folder = './models'
data_path = os.path.join(BASE_DIR, "data", "text_data.txt")
collection_name = "lecture_info"
model_name = "Snowflake/snowflake-arctic-embed-l-v2.0"


# ===============================
# 1. Embedding Model
# ===============================
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"🛠️ Embedding device: {device}")

embedding_model = SentenceTransformerEmbeddings(
    model_name=model_name,
    cache_folder=cache_folder,
    encode_kwargs={"normalize_embeddings": True, "prompt_name": "query"},
)


# ===============================
# 2. 라인 파싱
# ===============================
def parse_metadata(line):
    meta = {}
    fields = line.split("#")
    
    for f in fields:
        if ":" in f:
            k, v = f.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


# ===============================
# 3. 강의 단위로 여러 줄 merge
# ===============================
def load_and_merge_lectures(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f.readlines() if ln.strip()]

    lectures = {}

    for line in lines:
        meta = parse_metadata(line)

        course = meta.get("강의명")
        prof = meta.get("교수명")

        if not course or not prof:
            continue

        key = f"{course}_{prof}"

        if key not in lectures:
            lectures[key] = {
                "학부명": None,
                "학과명": None,
                "강의명": course,
                "교수명": prof,

                "이수구분": [],
                "선수과목과수강요건": [],

                "학습내용": [],
                "수업진행방식": [],

                "별점": None,
                "강의평가_낮음": [],
                "강의평가_높음": [],
            }

        lec = lectures[key]

        for k, v in meta.items():
            if k == "이수구분":
                lec["이수구분"].append(v)
            elif k == "선수과목과수강요건":
                lec["선수과목과수강요건"].append(v)
            elif k == "학습내용":
                lec["학습내용"].append(v)
            elif k == "수업진행방식":
                lec["수업진행방식"].append(v)
            elif k == "강의평가_낮음":
                lec["강의평가_낮음"].append(v)
            elif k == "강의평가_높음":
                lec["강의평가_높음"].append(v)
            else:
                if lec.get(k) is None:
                    lec[k] = v

    return list(lectures.values())


# ===============================
# 4. Header 생성 (모든 문서 공통)
# ===============================
def make_header(meta):
    return (
        f"강의명: {meta['강의명']}\n"
        f"교수명: {meta['교수명']}\n"
        f"학부명: {meta['학부명']}\n"
        f"학과명: {meta['학과명']}\n"
    )


# ===============================
# 5. 강의 → 여러 Document 생성
# ===============================
def build_documents(lectures):
    docs = []

    for meta in lectures:
        header = make_header(meta)

        # ------------------------ #
        #  1) 이수구분
        # ------------------------ #
        if meta["이수구분"]:
            body = "\n".join(f"- {v}" for v in meta["이수구분"])
            text = header + "\n[이수구분]\n" + body
            docs.append(Document(
                page_content=text,
                metadata={"강의명": meta["강의명"], "교수명": meta["교수명"], "type": "이수구분"}
            ))                

        # ------------------------ #
        #  1) 선수과목과수강요건
        # ------------------------ #
        if meta["선수과목과수강요건"]:
            body = "\n".join(f"- {v}" for v in meta["선수과목과수강요건"])
            text = header + "\n[선수과목과수강요건]\n" + body
            docs.append(Document(
                page_content=text,
                metadata={"강의명": meta["강의명"], "교수명": meta["교수명"], "type": "선수과목과수강요건"}
            ))        

        # ------------------------ #
        #  1) 학습내용
        # ------------------------ #
        if meta["학습내용"]:
            body = "\n".join(f"- {v}" for v in meta["학습내용"])
            text = header + "\n[학습내용]\n" + body
            docs.append(Document(
                page_content=text,
                metadata={"강의명": meta["강의명"], "교수명": meta["교수명"], "type": "학습내용"}
            ))

        # ------------------------ #
        #  2) 수업진행방식
        # ------------------------ #
        if meta["수업진행방식"]:
            body = "\n".join(f"- {v}" for v in meta["수업진행방식"])
            text = header + "\n[수업진행방식]\n" + body
            docs.append(Document(
                page_content=text,
                metadata={"강의명": meta["강의명"], "교수명": meta["교수명"], "type": "수업진행방식"}
            ))

        # ------------------------ #
        #  3) 강의평가
        # ------------------------ #
        eval_text = header + "\n[강의평가]\n"
        eval_text += f"별점: {meta['별점']}\n\n"

        if meta["강의평가_낮음"]:
            eval_text += "낮음 리뷰:\n"
            eval_text += "\n".join(f"- {v}" for v in meta["강의평가_낮음"])
            eval_text += "\n\n"

        if meta["강의평가_높음"]:
            eval_text += "높음 리뷰:\n"
            eval_text += "\n".join(f"- {v}" for v in meta["강의평가_높음"])
            eval_text += "\n"

        docs.append(Document(
            page_content=eval_text,
            metadata={"강의명": meta["강의명"], "교수명": meta["교수명"], "type": "강의평가"}
        ))

    return docs


# ===============================
# 6. ingest 실행
# ===============================
def run_ingest():
    print("📌 Step1: 병합")
    merged = load_and_merge_lectures(data_path)
    print(f"총 {len(merged)}개 강의 병합 완료")

    print("📌 Step2: Document 생성")
    docs = build_documents(merged)
    print(f"총 {len(docs)}개의 Document 생성 완료")

    print("📌 Step3: split (필요 시)")
    splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)
    split_docs = splitter.split_documents(docs)
    print(f"split 후 Document 수: {len(split_docs)}")

    with open('ingest.txt', 'w', encoding='utf-8') as f:
        for doc in split_docs:
            doc = str(doc)
            f.write(doc + '\n')
            f.write('='*50+'\n')
    print("📌 Step4: VectorDB 생성")
    client = chromadb.PersistentClient(vectordb_dir)
    try:
        client.delete_collection(collection_name)
    except:
        pass

    vectordb = Chroma(
        collection_name=collection_name,
        persist_directory=vectordb_dir,
        embedding_function=embedding_model,
    )

    vectordb.add_documents(split_docs)
    print("✅ RAG ingest 완료!")


if __name__ == "__main__":
    run_ingest()
