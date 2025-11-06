#!/bin/bash

# Python 가상환경 활성화 (Dockerfile에서 이미 PATH를 잡았지만 명시)
source /opt/venv/bin/activate

# 1. FastAPI 서버를 백그라운드에서 실행
echo "Starting FastAPI server on port 8000..."
python3 api_server.py &

# 2. Streamlit 서버를 포그라운드에서 실행 (이 프로세스가 컨테이너의 메인 프로세스)
echo "Starting Streamlit server on port 8501..."
streamlit run ui_app.py --server.port 8501 --server.address 0.0.0.0 --server.enableCORS false
