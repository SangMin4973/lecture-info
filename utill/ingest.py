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

