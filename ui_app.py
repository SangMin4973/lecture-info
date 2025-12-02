import streamlit as st
import requests
import os
from PIL import Image
import base64
from io import BytesIO

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/chat")

# 이미지 경로
skhulogo2_img = Image.open("images/skhulogo2.png")
skhulogo3_img = Image.open("images/skhulogo3.png")
user_icon = Image.open("images/icon_user.png")
bot_icon = Image.open("images/icon_bot.png")
lecturebot_light = Image.open("images/lecturebot.png")
lecturebot_dark = Image.open("images/lecturebot_dark.png")

def image_to_base64(img: Image.Image) -> str:
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

user_icon_b64 = image_to_base64(user_icon)
bot_icon_b64 = image_to_base64(bot_icon)
skhulogo2_b64 = image_to_base64(skhulogo2_img)
skhulogo3_b64 = image_to_base64(skhulogo3_img)

st.set_page_config(page_title="SKHU Lecture Info", layout="centered")

# ------------------------- 라이트/다크 테마 설정 -------------------------
LIGHT_THEME = {
    "bg": "#117FD6",
    "side": "#117FD6",
    "block": "#FFFFFF",
    "text": "#2C2C2C",
    "user_bubble": "#257BFC",
    "bot_bubble": "#eaeaea",
    "user_text": "#FFFFFF",
    "lecturebot": lecturebot_light,
    "placeholder": "#888888"
}

DARK_THEME = {
    "bg": "#121212",
    "side": "#121212",
    "block": "#121212",
    "text": "#E5E5E5",
    "user_bubble": "#257BFC",
    "bot_bubble": "#2c2c2c",
    "user_text": "#FFFFFF",
    "lecturebot": lecturebot_dark,
    "placeholder": "#FFFFFF"
}
# -------------------------------------------------------------------------

# 토글 + 라벨
col_toggle, col_label = st.columns([0.3, 6])
with col_toggle:
    mode = st.toggle("", key="dark_mode")

THEME = DARK_THEME if mode else LIGHT_THEME

icon = "🌙" if mode else "☀️"
label_text = "다크모드" if mode else "라이트모드"
with col_label:
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:8px; height:32px; margin-top:6px;">
            <span style="font-size:16px; line-height:1; color:{THEME['text']};">{icon}</span>
            <span style="font-size:15px; font-weight:600; color:{THEME['text']};">{label_text}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

# Navbar (항상 파란색 유지)
st.markdown(f"""
    <div class="navbar">
        <img src="data:image/png;base64,{skhulogo3_b64}" class="navbar-logo">
    </div>
""", unsafe_allow_html=True)

# CSS (THEME 적용)
st.markdown(f"""
<style>
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stSidebar"],
[data-testid="stBottom"] {{
    background-color: {THEME["block"]} !important;
    color: {THEME["text"]} !important;
}}

.navbar {{
    width: 100%;
    background-color: #117FD6;
    padding: 30px 0;
    border-bottom: 1px solid #117FD6;
    text-align: center;
}}
.navbar-logo {{
    width: 150px;
    height: auto;
}}

/* 하단 전체 영역 다크 */
[data-testid="stBottom"],
[data-testid="stBottom"] * {{
    background-color: {THEME["block"]} !important;
    color: {THEME["text"]} !important;
    border-color: #333 !important;
    box-shadow: none !important;
}}

/* 입력창 및 placeholder */
[data-testid="stChatInput"] {{
    background-color: {THEME["block"]} !important;
}}
textarea[data-testid="stChatInput"] {{
    background-color: {THEME["block"]} !important;
    color: {THEME["text"]} !important;
    border: 1px solid #444 !important;
}}
textarea::placeholder {{
    color: {THEME["placeholder"]} !important;
}}
div[data-baseweb="textarea"] textarea::placeholder {{
    color: {THEME["placeholder"]} !important;
}}

textarea[data-testid="stChatInput"]::placeholder {{
    color: #FFFFFF !important;
}}

div[data-baseweb="textarea"],
div[data-baseweb="input"] {{
    background-color: {THEME["block"]} !important;
    color: {THEME["text"]} !important;
    border-color: #444 !important;
}}
div[data-baseweb="textarea"] > div {{
    background-color: {THEME["block"]} !important;
}}
div[data-baseweb="textarea"] textarea {{
    background-color: {THEME["block"]} !important;
    color: {THEME["text"]} !important;
}}

::-webkit-scrollbar {{ width: 8px; }}
::-webkit-scrollbar-track {{ background: #1A1A1A; }}
::-webkit-scrollbar-thumb {{ background: #444; border-radius: 4px; }}

.chat-row-left, .chat-row-right {{
    display: flex;
    align-items: flex-start;
    margin-bottom: 12px;
}}
.chat-row-right {{ justify-content: flex-end; }}
.chat-icon {{
    width: 38px; height: 38px; border-radius: 50%; object-fit: cover;
}}
.chat-bubble {{
    padding: 12px 18px; border-radius: 18px; max-width: 70%;
    margin: 0 10px; display: inline-block;
}}
.user-bubble {{ background: {THEME["user_bubble"]}; color: {THEME["user_text"]}; }}
.bot-bubble {{ background: {THEME["bot_bubble"]}; color: {THEME["text"]}; }}

</style>
""", unsafe_allow_html=True)

# Header area
col1, col2 = st.columns([2, 6])
with col1:
    st.image(THEME["lecturebot"], use_container_width=True)
with col2:
    st.markdown(f"<h1 style='color:{THEME['text']}; font-weight:800;'>SKHU Lecture Info</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{THEME['text']}; font-size:18px;'>2025-2학기 강의계획서 및 에브리타임 강의평가 기반 강의 정보 제공</p>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:{THEME['text']}; font-size:15px; margin-top:-6px;'>※ IT융합자율학부 · 소프트웨어융합학부 · 미래융합학부 강의만 질문할 수 있습니다.</p>",
        unsafe_allow_html=True
    )

st.markdown("<div style='margin:40px;'></div>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        st.markdown(
            f"""
            <div class="chat-row-left">
                <img src="data:image/png;base64,{bot_icon_b64}" class="chat-icon">
                <div class="chat-bubble bot-bubble">{msg["content"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="chat-row-right">
                <div class="chat-bubble user-bubble">{msg["content"]}</div>
                <img src="data:image/png;base64,{user_icon_b64}" class="chat-icon">
            </div>
            """,
            unsafe_allow_html=True,
        )

prompt = st.chat_input("메시지를 입력하세요...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        res = requests.post(API_URL, json={"query": prompt}, timeout=30)
        answer = res.json().get("answer", "응답 오류")
    except:
        answer = "서버와의 통신 중 오류가 발생했습니다."

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()