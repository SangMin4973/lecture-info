# chatbot.py
from utils.llm import get_llm
from utils.rag import retrieve, _load_vectordb
from utils.prompt import build_prompt, apply_chat_template, extract_answer, analyze_query
import time
from pprint import pformat

# 전역 로드 (서버 켜질 때 실행됨)
MODEL_NAME_MAIN = "Qwen/Qwen3-4B"
_pipe, _tokenizer = get_llm(MODEL_NAME_MAIN)
vectordb = _load_vectordb()

def chatbot(query: str):
    print(f"🚀 답변 생성중... (질문: {query})")
    # 1) RAG 검색 (rag.retrieve 호출)
    info = retrieve(query, _pipe, _tokenizer, vectordb)
    # 2) 프롬프트 생성 (prompt 호출)
    full_prompt = build_prompt(query, info)
    prompt = apply_chat_template(_tokenizer, full_prompt)

    # 3) LLM 실행 (Pipeline 사용)
    # CPU라 느릴 수 있으니 max_new_tokens 조절 가능
    raw = _pipe(prompt, max_new_tokens=1024, do_sample=False)
    generated = raw[0]["generated_text"]

    # 4) 답변 파싱
    answer = extract_answer(generated)
    print("✅ 답변 생성 완료")

    return answer

if __name__ == '__main__':
    querys = [
        "데이터베이스 강의의 학습 내용은 어떻게 돼?",
        "데이터사이언스입문 강의는 어때?",
        "인공지능전공 과목은 어떤것들이 있어?,",
        "노은하 교수님 수업으로는 어떤것들이 있어?",
        "백엔드프레임워크 교수님은 누구야?",
        "Python프로그래밍를 선수과목으로 하는 강의를 알려줘",
        "소프트웨어공학전공의 전공필수과목의 선수필수과목들을 알려줘",
        "자료구조 강의를 진행하는 교수님 중 강의평이 좋은 교수님은 누구야",
        "내가 웹개발 입문 , java프로그래밍을 수강한 상태인데 수강가능한 강의가 뭐가있어?",
        "강의평가 별점이 5.0인 강의를 알려줘",
        "쪽지시험 혹은 퀴즈가 있는 강의를 알려줘",
        "빅데이터응용전공인 강의를 알려줘",
        "강의평가 별점이 3점대 이하인 강의를 알려줘",
        "파이썬을 사용하는 강의를 알려줘",
        "노은하교수님의 운영체제 별점을 알려줘",
        "오픈소스SW개발의 수업 방식을 알려줘",
        "홍성준 교수님의 Python프로그래밍수업의 학습 내용을 알려줘",
        "홍성준 교수님의 Python프로그래밍수업의 강의평가는 어때?",
        "소프트웨어융합학부 수업 중 강의평가가 높은 수업은 어떤게 있어?"
    ]

    output_chatbot_path = "qwen3B.txt"
    timer = 0
    with open(output_chatbot_path, "w", encoding="utf-8") as f:
        for q in querys:
            start = time.time()
            print(f"📝 실행 중: {q}")
            qa = chatbot(q)
            f.write(f"질문: {q}\n")
            f.write("=========================================================================================\n")
            f.write(f"run_query_analyzer() 결과: \n{pformat(qa)}\n")
            # f.write("=========================================================================================\n")
            # f.write(f"similarity_search_with_score 결과: \n{pformat(results)}\n")
            # f.write("=========================================================================================\n")
            # f.write(f"docs 결과: \n{pformat(results)}\n")
            # f.write("=========================================================================================\n")
            # f.write(f"dedup_docs 결과: \n{pformat(dedup_docs)}\n")
            # f.write("=========================================================================================\n") 
            # f.write(f"filtered_docs 결과: \n{pformat(filtered_docs)}\n")
            # f.write("=========================================================================================\n") 
            # f.write(f"full_prompt 결과: \n{full_prompt}\n")
            # f.write("=========================================================================================\n") 
            # f.write(f"prompt 결과: \n{prompt}\n")
            # f.write("=========================================================================================\n") 
            # f.write(f"답변: {answer}\n")
            # f.write("=========================================================================================\n")           
            end = time.time()
            timer += end-start
        f.write(f"평균 소요 시간: {timer/len(querys)}")

    print(f"📄 결과 저장 완료")
