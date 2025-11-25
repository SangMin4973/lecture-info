import torch
from langchain_community.embeddings import SentenceTransformerEmbeddings

def get_embedding_model(model_name="Snowflake/snowflake-arctic-embed-l-v2.0", cache_folder="./"):
    """
    임베딩 모델을 로드하여 반환합니다.
    - model_name: 사용할 모델 이름 (기본값 설정됨)
    - cache_folder: 캐시 저장 경로
    """
    # 디바이스 설정 (GPU 우선)
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"🛠️ Embedding device: {device}")

    final_model_kwargs = {
        "device": device,
    }
    
    # GPU 사용 시 fp16 설정으로 메모리 절약
    if "cuda" in device:
        final_model_kwargs["torch_dtype"] = torch.float16

    # 모델 초기화
    embedding_model = SentenceTransformerEmbeddings(
        model_name=model_name,
        cache_folder=cache_folder,
        model_kwargs=final_model_kwargs,
        encode_kwargs={
            "normalize_embeddings": True,
            "prompt_name": "query" 
        }
    )
    
    return embedding_model