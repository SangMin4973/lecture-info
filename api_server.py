from fastapi import FastAPI
from fastapi import Request
from contextlib import asynccontextmanager

from utils.chatbot import init_chatbot, chatbot
from pydantic import BaseModel
import uvicorn
import os

# ------------------ ⭐ Lifespan 정의 ⭐ ------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 FastAPI 시작 → LLM + VectorDB 로딩 시작...")
    init_chatbot()        # ← 여기서 LLM, tokenizer, vectordb 로딩됨
    print("✅ FastAPI 준비 완료!")
    yield
    print("🛑 FastAPI 종료 → 리소스 정리 중...")
# ---------------------------------------------------------

# lifespan 적용된 FastAPI 인스턴스 생성
app = FastAPI(lifespan=lifespan)

# ------------------ API ------------------
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str

@app.post("/chat", response_model=ChatResponse)
def handle_chat(request: ChatRequest):
    answer = chatbot(request.query)
    return ChatResponse(answer=answer)
# -------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
