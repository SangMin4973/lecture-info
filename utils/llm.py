import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig

MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"
CACHE_DIR = "./"

# 전역 변수
_pipe = None
_tokenizer = None

def get_llm():
    """
    chatbot.py에서 호출하는 함수.
    GPU 설정이 적용된 Pipeline 객체와 Tokenizer를 반환합니다.
    """
    global _pipe, _tokenizer
    
    if _pipe is not None and _tokenizer is not None:
        return _pipe, _tokenizer
        
    print(f"🚀 LLM 모델 로딩 시작 (GPU Mode)... ({MODEL_NAME})")
    try:
        # 1. 4비트 양자화 설정 (GPU 전용)
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16, # GPU 연산 가속
            bnb_4bit_quant_type="nf4"
        )

        # 2. 토크나이저 로드
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        
        # 3. 모델 로드 (GPU 설정 적용)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            quantization_config=bnb_config, # 4비트 적용
            device_map="auto",              # GPU 자동 할당
            trust_remote_code=True,
            cache_dir=CACHE_DIR
        )

        # 4. 파이프라인 생성
        _pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=_tokenizer
        )
        print("✅ LLM(Pipeline) 로드 완료! (GPU 가속 활성화)")
        
    except Exception as e:
        print(f"❌ LLM 로드 실패: {e}")
        return None, None

    return _pipe, _tokenizer