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