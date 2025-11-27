from langchain_core.documents import Document

def parse_lecture_info(text_block):
    """텍스트 블록을 파싱하여 메타데이터 딕셔너리로 변환"""
    metadata = {}
    fields = text_block.strip().split('-')
    for field in fields:
        if ':' in field:
            key, value = field.split(':', 1)
            metadata[key.strip()] = value.strip()
    return metadata

def add_title(doc):
    """Document 객체에 Title 정보를 본문에 추가"""
    title = doc.metadata.get('title', '')
    if title:
        doc.page_content = f"Title : {title}\n\n{doc.page_content}"
    return doc

def get_docs_from_file(file_path):
    """파일 경로를 받아 Document 리스트 반환"""
    print(f"📖 파일 읽는 중: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        blocks = [b.strip() for b in content.split('\n') if b.strip()]
    except Exception as e:
        print(f"❌ 파일 읽기 오류: {e}")
        return []

    docs = []
    for block in blocks:
        meta = parse_lecture_info(block)
        course = meta.get('강의명', '미정')
        prof = meta.get('교수명', '미상')
        
        # 본문 구성
        content_parts = []
        if '학습내용' in meta: content_parts.append(f"**학습 내용:** {meta.pop('학습내용')}")
        if '수업진행방식' in meta: content_parts.append(f"**수업 방식:** {meta.pop('수업진행방식')}")
        if '선수과목과수강요건' in meta: content_parts.append(f"**선수 요건:** {meta.pop('선수과목과수강요건')}")
        
        # 강의평가 처리
        reviews = []
        if '별점' in meta: reviews.append(f"별점: {meta.pop('별점')}")
        if '강의평가_낮음' in meta: reviews.append(f"단점: {meta.pop('강의평가_낮음')}")
        if '강의평가_높음' in meta: reviews.append(f"장점: {meta.pop('강의평가_높음')}")
        if reviews: content_parts.append(f"**평가:** {' / '.join(reviews)}")

        page_content = "\n".join(content_parts)
        
        if len(page_content) > 10:
            final_meta = {'source': file_path, 'title': f"{course} ({prof})", **meta}
            docs.append(Document(page_content=page_content, metadata=final_meta))
            
    return docs