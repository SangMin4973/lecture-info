import os
import sys
import time

# utils 모듈 가져오기
from utils.rag import _load_retriever

def main():
    print("\n" + "="*50)
    print("🔍 Retriever 검색 성능 테스트 (LLM 생성 X)")
    print("="*50)

    # 1. Retriever 로드
    # (rag.py 내부의 _load_retriever 함수를 사용하여 검색 객체만 가져옵니다)
    print("Vector DB 로딩 중...")
    retriever = _load_retriever()
    
    if not retriever:
        print("❌ 오류: Retriever를 로드할 수 없습니다. vector_db.py를 먼저 실행했는지 확인하세요.")
        return

    print("✅ Retriever 준비 완료!")
    print("-" * 50)

    # 2. 검색 루프
    while True:
        query = input("\n🗣️  검색할 질문 입력 (종료: 'q'): ")
        if query.lower() in ['q', 'quit', 'exit']:
            break
        
        if not query.strip():
            continue

        print(f"\n🔎 [{query}] 에 대한 문서 검색 시작...")
        
        start_time = time.time()
        # 🌟 핵심: invoke() 함수로 문서 검색만 수행
        docs = retriever.invoke(query)
        end_time = time.time()

        print(f"⏱️  소요 시간: {end_time - start_time:.4f}초")
        print(f"📚 검색된 문서 개수: {len(docs)}개")
        
        # 3. 결과 출력
        if len(docs) == 0:
            print("   ⚠️ 검색 결과가 없습니다.")
        else:
            for i, doc in enumerate(docs):
                print(f"\n--- [문서 {i+1}] -----------------------")
                # 메타데이터 출력 (제목, 파일명 등)
                source = doc.metadata.get('source', '알 수 없음')
                title = doc.metadata.get('title', '제목 없음')
                print(f"📄 출처: {source}")
                print(f"🏷️ 제목: {title}")
                
                # 본문 내용 출력 (너무 길면 자름)
                content = doc.page_content
                print(f"📝 내용:\n{content}")
                print("---------------------------------------")

if __name__ == "__main__":
    main()