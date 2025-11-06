import streamlit as st
import requests
import json
import os

# FastAPI 서버 주소
# Docker 내부에서 실행될 때:
# 'api_server'는 docker-compose 등에서 정의한 서비스 이름일 수 있습니다.
# 만약 동일 컨테이너에서 실행되면 localhost(127.0.0.1)를 사용합니다.
# start.sh가 동일 컨테이너에서 실행하므로 localhost 사용
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/chat")

st.set_page_config(page_title="RAG 챗봇 (Demo)", layout="centered")
st.title("RAG 챗봇 1주차: 'Hello, World' 뼈대")

# 채팅 기록을 위한 session_state 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 채팅 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 1. 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. FastAPI 서버로 요청 전송
    with st.spinner("답변 생성 중..."):
        try:
            payload = {"query": prompt}
            response = requests.post(
                API_URL, 
                data=json.dumps(payload), 
                headers={"Content-Type": "application/json"}, 
                timeout=30
            )
            
            if response.status_code == 200:
                answer = response.json().get("answer", "오류: 응답 키가 없습니다.")
            else:
                answer = f"오류: {response.status_code} - {response.text}"

        except requests.exceptions.RequestException as e:
            answer = f"API 서버 연결 오류: {e} (API 주소: {API_URL})"

    # 3. 챗봇 응답 표시
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
