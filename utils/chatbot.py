# chatbot.py
from llm import get_llm
from rag import retrieve, _load_vectordb
from prompt import build_prompt, apply_chat_template, extract_answer, analyze_query
import time

# 전역 로드 (서버 켜질 때 실행됨)
pipe, tokenizer = get_llm()
vectordb = _load_vectordb()

def chatbot(query: str):
    # 1) RAG 검색 (rag.retrieve 호출)
    info = retrieve(query, pipe, tokenizer, vectordb)
    # 2) 프롬프트 생성 (prompt 호출)
    full_prompt = build_prompt(query, info)
    prompt = apply_chat_template(tokenizer, full_prompt)

    # 3) LLM 실행 (Pipeline 사용)
    # CPU라 느릴 수 있으니 max_new_tokens 조절 가능
    # raw = pipe(prompt, max_new_tokens=256, do_sample=False)
    raw = pipe(prompt, max_new_tokens=1024, do_sample=False)
    generated = raw[0]["generated_text"]

    # 4) 답변 파싱
    answer = extract_answer(generated)

    return answer