from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os
from utils.chatbot import *

# Pydantic 모델: 요청 Body 형식 정의
class ChatRequest(BaseModel):
    query: str

# Pydantic 모델: 응답 Body 형식 정의
class ChatResponse(BaseModel):
    answer: str

app = FastAPI()

@app.post("/chat", response_model=ChatResponse)
def handle_chat(request: ChatRequest):
    """
    사용자의 쿼리를 받아 "Hello, "를 붙여 응답합니다.
    (1주 차 목표: 이 부분이 동작하게 하는 것)
    (3주 차 목표: 이 부분을 RAG+LLM 답변으로 교체)
    """
    print(f"Received query: {request.query}")
    
    # 1주 차: 간단한 응답 로직
    response_text = f"{chatbot(request.query)}"
    
    return ChatResponse(answer=response_text)

if __name__ == "__main__":
    # 0.0.0.0: 모든 IP에서의 접속을 허용합니다. (Docker 내부 실행)
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    
    # start.sh 스크립트에서 python3 api_server.py로 직접 실행하므로
    # uvicorn을 직접 실행하는 코드로 변경합니다.
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
