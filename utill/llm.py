import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- 설정 ---
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"  # CPU용 경량 모델
CACHE_DIR = "./"
MODEL_DIR = "./model/"

# --- 전역 변수 (import 시 로드됨) ---
print(f"🚀 LLM 모델 로드 시작: {MODEL_NAME}")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32,
        device_map="auto",
        cache_dir=CACHE_DIR
    )
    # 모델 저장 (최초 1회 실행 시 유효, 이후엔 로드만 함)
    # tokenizer.save_pretrained(MODEL_DIR)
    # model.save_pretrained(MODEL_DIR)
    print("✅ LLM 모델 로드 완료.")
except Exception as e:
    print(f"❌ LLM 로드 실패: {e}")
    model = None
    tokenizer = None

def generate_response(query, context):
    """질문(query)과 문맥(context)을 받아 답변을 생성합니다."""
    if model is None or tokenizer is None:
        return "모델이 로드되지 않았습니다."

    prompt = f"""당신은 강의 추천을 돕는 AI 조교입니다. 아래 정보를 바탕으로 질문에 답해주세요.

[정보]
{context}

[질문]
{query}

[답변]
"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs, 
            max_new_tokens=256,
            temperature=0.7,
            repetition_penalty=1.1
        )
    
    response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response_text.replace(prompt, "").strip()