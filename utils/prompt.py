import json
import re

def build_prompt(query, context):
    """
    질문과 검색된 문서를 합쳐서 프롬프트 내용을 구성합니다.
    """
    return f"""당신은 강의 추천을 돕는 AI 조교입니다. 아래 정보를 바탕으로 질문에 답해주세요.

[정보]
{context}

[질문]
{query}

[규칙]
**반드시 한글로 답변해주세요**

[답변]
"""

def analyze_query(query):
    return  f"""
너는 RAG 검색 최적화를 위한 Query Analyzer 역할을 한다.

아래 질문을 분석하여 다음 두 가지를 결정하라:

1) 이 질문을 정확히 답하기 위해 필요한 검색 문서 수 k  
   - k는 chunk 단위이며, 한 강의는 평균 7개의 chunk로 구성된다.
   - 다음 기준으로 판단한다:

     ● 단일 강의의 단일 정보 조회
     ex) 백엔드프레임워크 교수님은 누구야?
        → k = 3

     ● 강의의 세부 필드 조회 (학습내용/수업방식/이수구분/선수요건/별점 등)
     ex) 데이터베이스 강의의 학습 내용은 어떻게 돼?
     ex) 노은하 교수님 수업으로는 어떤것들이 있어?
        → k = 5

     ● 조건 기반 강의 검색 (별점 조건, 선수요건 조건, 파이썬 사용 여부 등)
     ex) Python프로그래밍를 선수과목으로 하는 강의를 알려줘
        → k = 10

     ● 특정 교수의 모든 강의 조회, 특정 학부/전공 전체 조회
     ex) 인공지능학과 과목은 어떤것들이 있어?
        → k = 15

2) 이 질문을 답하기 위해 필요한 "강의 정보 필드" 목록을 추출하라.
   가능한 필드들은 다음과 같다:

   ["학부명", "학과명", "강의명", "교수명", "이수구분",
    "학습내용", "수업방식", "선수요건",
    "별점", "강의평가_장점", "강의평가_단점"]

   ● 질문의 의도를 파악하여 필수 필드만 선택한다.
     예)
       - "강의 내용"을 물으면 → ["학습내용"]
       - "어떤 강의가 있어?" → ["강의명"]
       - "교수님 수업" → ["강의명", "교수명"]
       - "별점 높은 강의" → ["별점", "강의명", "교수명"]

출력 형식 (JSON):
{{
  "k": 숫자,
  "필요 정보": ["필드1", "필드2", ...]
}}

질문: {query}
    """



def apply_chat_template(tokenizer, content):
    """
    모델의 토크나이저에 맞는 채팅 템플릿(ChatML 등)을 적용합니다.
    """
    messages = [
        {"role": "system", "content": "당신은 유용한 AI 어시스턴트입니다."},
        {"role": "user", "content": content}
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False
    )
    return prompt

def extract_answer(generated_text):
    """
    모델이 생성한 전체 텍스트에서 '답변' 부분만 추출합니다.
    (Qwen 등은 프롬프트 뒤에 답변을 이어 붙이므로, 필요한 경우 파싱 로직 추가)
    """
    if '</think>' in generated_text:
        return generated_text.split('</think>', 1)[1].strip()


def run_query_analyzer(query: str, pipe, tokenizer):
    prompt = analyze_query(query)
    messages = [
        {"role": "system", "content": "당신은 유용한 AI 어시스턴트입니다."},
        {"role": "user", "content": prompt}
    ]   
    applied = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False
    )

    raw = pipe(applied, max_new_tokens=512, do_sample=False)
    txt = extract_answer(raw[0]["generated_text"])

    match = re.search(r"\{.*\}", txt, re.DOTALL)
    if not match:
        return {"k": 10, "필요 정보": []}

    try:
        return json.loads(match.group(0))
    except:
        return {"k": 10, "필요 정보": []}