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

model.save_pretrained('./model/')

