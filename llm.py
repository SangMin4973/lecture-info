from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

## Qwen3 4B ##
model_name = "Qwen/Qwen3-4B"

quantization_config = BitsAndBytesConfig(
    # load_in_8bit = True,
    load_in_4bit=True,                       # 모델 가중치를 4비트로 load
    bnb_4bit_compute_dtype = torch.bfloat16, # 가중치는 4비트로 저장되지만, 실제 행렬 계산은 bfloat16으로 진행되도록
    bnb_4bit_quant_type="nf4"                # 4비트 양자화 지정, nf4는 Qloar 논문에서 제안된 포맷으로 일반적인 4비트 양자화보다 정보 손실이 적게함
)

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype= "auto", #  'torch.bfloat16'
    quantization_config = quantization_config,
    device_map="auto",
    cache_dir="./"
)

model.eval()

# 모델 저장
model.save_pretrained('./model/')

# 토크나이저 저장 
tokenizer.save_pretrained('./model/')

def generate_response(query, context):
    """
    질문(query)과 검색된 문서(context)를 받아 답변을 생성합니다.
    """
    # 프롬프트 템플릿 (Qwen 스타일에 맞게 조정 가능)
    prompt = f"""당신은 강의 추천을 돕는 AI 조교입니다. 아래 정보를 바탕으로 학생의 질문에 친절하게 답해주세요.

[강의 정보]
{context}

[질문]
{query}

[답변]
"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # 답변 생성
    with torch.no_grad():
        outputs = model.generate(
            **inputs, 
            max_new_tokens=512,  # 답변 길이 조절
            temperature=0.3,     # 창의성 조절
            repetition_penalty=1.1
        )
    
    response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # 프롬프트 부분 제거하고 답변만 반환하는 전처리 
    return response_text.replace(prompt, "").strip()