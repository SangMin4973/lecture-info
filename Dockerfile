# 1. 기본 이미지: NVIDIA CUDA + Python 3.10
# (서버 PC의 NVIDIA 드라이버와 호환되는 CUDA 버전을 선택하세요)
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# 2. 시스템 환경 설정
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y python3.10 python3-pip python3.10-venv git-lfs && \
    rm -rf /var/lib/apt/lists/*

# 3. Python 가상환경 설정
RUN python3.10 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 4. 작업 디렉터리 설정
WORKDIR /app

# 5. 의존성 설치 (빌드 캐시 활용을 위해 코드를 복사하기 전 실행)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126
    

# 6. 애플리케이션 코드 복사
COPY . .

# 7. 포트 노출 (FastAPI: 8000, Streamlit: 8501)
EXPOSE 8000
EXPOSE 8501

# 8. 시작 스크립트 실행
COPY start.sh /start.sh
RUN apt-get update && apt-get install -y dos2unix
RUN dos2unix /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
