# chatbot.py
from utils.llm import get_llm
from utils.rag import retrieve
from utils.prompt import build_prompt, apply_chat_template, extract_answer

# 전역 로드 (서버 켜질 때 실행됨)
pipe, tokenizer = get_llm()

def chatbot(query: str):
    # 1) RAG 검색 (utils.rag.retrieve 호출)
    info = retrieve(query)

    # 2) 프롬프트 생성 (utils.prompt 호출)
    full_prompt = build_prompt(query, info)
    prompt = apply_chat_template(tokenizer, full_prompt)
    print(prompt)
    # 3) LLM 실행 (Pipeline 사용)
    # CPU라 느릴 수 있으니 max_new_tokens 조절 가능
    raw = pipe(prompt, max_new_tokens=256, do_sample=False)
    generated = raw[0]["generated_text"]

    # 4) 답변 파싱
    answer = extract_answer(generated)

    return answer