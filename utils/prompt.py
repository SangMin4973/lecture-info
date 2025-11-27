def build_prompt(query, context):
    """
    질문과 검색된 문서를 합쳐서 프롬프트 내용을 구성합니다.
    """
    return f"""당신은 강의 추천을 돕는 AI 조교입니다. 아래 정보를 바탕으로 질문에 답해주세요.

[정보]
{context}

[질문]
{query}

[답변]
"""

def apply_chat_template(tokenizer, content):
    """
    모델의 토크나이저에 맞는 채팅 템플릿(ChatML 등)을 적용합니다.
    """
    messages = [
        {"role": "system", "content": "당신은 유용한 AI 어시스턴트입니다."},
        {"role": "user", "content": content}
    ]
    
    # tokenizer.apply_chat_template 기능을 사용하여 포맷팅
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    return prompt

def extract_answer(generated_text):
    """
    모델이 생성한 전체 텍스트에서 '답변' 부분만 추출합니다.
    (Qwen 등은 프롬프트 뒤에 답변을 이어 붙이므로, 필요한 경우 파싱 로직 추가)
    """
    # ChatML 특성상 <|im_start|>assistant 이후가 답변이 될 수 있음
    # 여기서는 간단하게 처리하거나, 모델 특성에 맞춰 split
    if "<|im_start|>assistant" in generated_text:
        return generated_text.split("<|im_start|>assistant")[-1].strip()
    return generated_text