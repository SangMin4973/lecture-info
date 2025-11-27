import time
import os
import sys

# utils 모듈을 가져오기 위한 경로 설정 (필요시)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 우리가 만든 모듈 가져오기
import utils.llm as llm_module
import utils.rag as rag_module

def main():
    print("\n" + "="*50)
    print("🧪 RAG 챗봇 로직 테스트 (Server-less Mode)")
    print("="*50)

    # 1. 모델 및 DB 로드 (수동 실행)
    print("Loading Models & DB... (시간이 좀 걸립니다)")
    start_load = time.time()
    
    # Lifespan 패턴을 적용했다면 load 함수를 직접 호출해야 합니다.
    # 만약 load 함수 없이 import만으로 로드되게 했다면 이 두 줄은 주석 처리해도 됩니다.
    if hasattr(llm_module, 'load_model'):
        llm_module.load_model()
    
    if hasattr(rag_module, 'load_retriever'):
        rag_module.load_retriever()
        
    end_load = time.time()
    print(f"✅ 로딩 완료! (소요 시간: {end_load - start_load:.2f}초)")
    print("-" * 50)

    # 2. 질의응답 루프
    while True:
        query = input("\n🗣️  질문 입력 (종료하려면 'q' 입력): ")
        if query.lower() in ['q', 'quit', 'exit']:
            print("테스트를 종료합니다. 👋")
            break
        
        if not query.strip():
            continue

        print(f"\n🔍 '{query}' 검색 중...")
        
        # --- 검색 (Retrieval) ---
        retriever = rag_module.retriever
        if not retriever:
            print("❌ 오류: Retriever가 로드되지 않았습니다.")
            continue
            
        start_search = time.time()
        docs = retriever.invoke(query)
        end_search = time.time()
        
        # 검색된 문서 보여주기 (디버깅용)
        print(f"   ㄴ 문서 {len(docs)}개 발견 ({end_search - start_search:.4f}초)")
        for i, doc in enumerate(docs):
            # 문서 내용이 너무 길면 잘라서 보여줌
            content_preview = doc.page_content.replace('\n', ' ')[:100]
            print(f"      [{i+1}] {content_preview}...")

        # --- 답변 생성 (Generation) ---
        print("\n🤖 답변 생성 중... (CPU라 조금 걸려요)")
        start_gen = time.time()
        
        context = "\n\n".join([doc.page_content for doc in docs])
        answer = llm_module.generate_response(query, context)
        
        end_gen = time.time()
        
        print("\n" + "="*20 + " [AI 답변] " + "="*20)
        print(answer)
        print("="*50)
        print(f"⏱️  생성 소요 시간: {end_gen - start_gen:.2f}초")

if __name__ == "__main__":
    main()