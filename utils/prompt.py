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