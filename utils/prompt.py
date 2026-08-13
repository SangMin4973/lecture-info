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

아래 질문을 분석하여 검색에 필요한 구조화 정보를 결정하라.

1) 이 질문을 정확히 답하기 위해 필요한 검색 문서 수 top_k
   - k는 chunk 단위이며, 한 강의는 평균 7개의 chunk로 구성된다.
   - top_k는 반드시 3, 5, 10 중 하나로 고른다.
   - 다음 기준으로 판단한다:

     ● 단일 강의의 단일 정보 조회
     ex) 백엔드프레임워크 교수님은 누구야?
        → top_k = 3, information_scope = "narrow"

     ● 강의의 세부 필드 조회 (학습내용/수업방식/이수구분/선수요건/별점 등)
     ex) 데이터베이스 강의의 학습 내용은 어떻게 돼?
     ex) 노은하 교수님 수업으로는 어떤것들이 있어?
        → top_k = 5, information_scope = "medium"

     ● 조건 기반 강의 검색 (별점 조건, 선수요건 조건, 파이썬 사용 여부 등)
     ex) Python프로그래밍를 선수과목으로 하는 강의를 알려줘
        → top_k = 10, information_scope = "broad"

     ● 특정 교수의 모든 강의 조회, 특정 학부/전공 전체 조회
     ex) 인공지능학과 과목은 어떤것들이 있어?
        → top_k = 10, information_scope = "broad"

2) required_fields에는 실제 문서 종류만 넣어라.
   가능한 값은 다음 5개뿐이다:

   ["이수구분", "선수과목과수강요건", "학습내용", "수업진행방식", "강의평가"]

   매핑 규칙:
   - "선수요건", "선수과목" → "선수과목과수강요건"
   - "수업방식", "수업 진행" → "수업진행방식"
   - "별점", "평점", "강의평" → "강의평가"
   - 교수명/강의명/학과명/학부명은 required_fields에 넣지 말고 metadata_hints에 넣는다.

   ● 질문의 의도를 파악하여 필수 필드만 선택한다.
     예)
       - "강의 내용"을 물으면 → ["학습내용"]
       - "별점 높은 강의" → ["강의평가"]
       - "교수님은 누구야?" → []

3) metadata_hints에는 질문에 명시된 entity 조건을 넣어라.
   가능한 키는 다음과 같다:

   {{
     "course": 강의명 또는 null,
     "professor": 교수명 또는 null,
     "department": 학과명 또는 null,
     "faculty": 학부명 또는 null
   }}

4) intent는 다음 중 가장 가까운 값으로 고른다:
   "course_detail", "course_lookup", "conditional_search", "semantic_search", "comparison", "unanswerable_check"

출력 형식 (JSON):
{{
  "intent": "course_detail",
  "required_fields": ["필드1", "필드2"],
  "metadata_hints": {{
    "course": null,
    "professor": null,
    "department": null,
    "faculty": null
  }},
  "information_scope": "narrow",
  "top_k": 3
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
    else:
        return generated_text.strip()


FIELD_ALIASES = {
    "이수구분": "이수구분",
    "선수요건": "선수과목과수강요건",
    "선수과목": "선수과목과수강요건",
    "선수과목과수강요건": "선수과목과수강요건",
    "학습내용": "학습내용",
    "수업방식": "수업진행방식",
    "수업진행방식": "수업진행방식",
    "별점": "강의평가",
    "평점": "강의평가",
    "강의평": "강의평가",
    "강의평가": "강의평가",
}

REQUIRED_FIELD_VALUES = set(FIELD_ALIASES.values())
METADATA_FIELD_VALUES = {"강의명", "교수명", "학과명", "학부명"}
ALLOWED_K = {3, 5, 10}
DEFAULT_ANALYZER = {
    "intent": "course_detail",
    "required_fields": [],
    "metadata_hints": {
        "course": None,
        "professor": None,
        "department": None,
        "faculty": None,
    },
    "information_scope": "medium",
    "top_k": 5,
}


def normalize_required_fields(fields):
    normalized = []
    for field in fields or []:
        mapped = FIELD_ALIASES.get(str(field).strip())
        if mapped and mapped not in normalized:
            normalized.append(mapped)
    return normalized


def normalize_query_analysis(raw):
    if not isinstance(raw, dict):
        raw = {}

    legacy_fields = raw.get("필요 정보") or []
    required_fields = raw.get("required_fields")
    if required_fields is None:
        required_fields = [
            field for field in legacy_fields if str(field).strip() not in METADATA_FIELD_VALUES
        ]
    required_fields = normalize_required_fields(required_fields)

    top_k = raw.get("top_k", raw.get("k", DEFAULT_ANALYZER["top_k"]))
    try:
        top_k = int(top_k)
    except (TypeError, ValueError):
        top_k = DEFAULT_ANALYZER["top_k"]
    if top_k not in ALLOWED_K:
        top_k = DEFAULT_ANALYZER["top_k"]

    metadata_hints = DEFAULT_ANALYZER["metadata_hints"].copy()
    if isinstance(raw.get("metadata_hints"), dict):
        for key in metadata_hints:
            value = raw["metadata_hints"].get(key)
            metadata_hints[key] = value if value else None

    information_scope = raw.get("information_scope") or DEFAULT_ANALYZER["information_scope"]
    if information_scope not in {"narrow", "medium", "broad"}:
        information_scope = DEFAULT_ANALYZER["information_scope"]

    normalized = {
        "intent": raw.get("intent") or DEFAULT_ANALYZER["intent"],
        "required_fields": required_fields,
        "metadata_hints": metadata_hints,
        "information_scope": information_scope,
        "top_k": top_k,
    }
    normalized["k"] = top_k
    normalized["필요 정보"] = required_fields
    return normalized


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
        return normalize_query_analysis({})

    try:
        return normalize_query_analysis(json.loads(match.group(0)))
    except json.JSONDecodeError:
        return normalize_query_analysis({})
