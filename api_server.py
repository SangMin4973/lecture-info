# api_server.py
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os

# 🌟 utils 폴더에서 가져오기
from utils.rag import retriever
from utils.llm import generate_response

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str

app = FastAPI()

@app.post("/chat", response_model=ChatResponse)
def handle_chat(request: ChatRequest):
    print(f"User Query: {request.query}")
    
    if not retriever:
        return ChatResponse(answer="⚠️ 서버 준비 중: DB가 로드되지 않았습니다.")

    # 1. RAG 검색
    retrieved_docs = retriever.invoke(request.query)
    context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
    
    # 2. 답변 생성
    final_answer = generate_response(request.query, context_text)
    
    return ChatResponse(answer=final_answer)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)