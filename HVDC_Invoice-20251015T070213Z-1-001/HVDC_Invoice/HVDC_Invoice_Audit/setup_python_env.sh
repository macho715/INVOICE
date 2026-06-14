#!/usr/bin/env bash
# Python 환경 구축 스크립트 (WSL2)
# 실행: wsl bash setup_python_env.sh

set -euo pipefail

PROJECT_DIR="/mnt/c/Users/SAMSUNG/Downloads/HVDC_Invoice-20251015T070213Z-1-001/HVDC_Invoice/HVDC_Invoice_Audit"

echo "🐍 Python 환경 구축 시작..."
echo ""

# 1. 디렉토리 이동
cd "$PROJECT_DIR" || exit 1
echo "📁 프로젝트 디렉토리: $PROJECT_DIR"

# 2. Python 버전 확인
echo ""
echo "🔍 Python 버전 확인..."
python3 --version || {
    echo "❌ Python3가 설치되지 않음. 설치 중..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
}

# 3. 가상 환경 생성 (존재하지 않을 경우)
if [ ! -d "venv" ]; then
    echo ""
    echo "🏗️  가상 환경 생성 중..."
    python3 -m venv venv
    echo "✅ 가상 환경 생성 완료"
else
    echo ""
    echo "✅ 가상 환경이 이미 존재합니다"
fi

# 4. 가상 환경 활성화
echo ""
echo "🔌 가상 환경 활성화..."
source venv/bin/activate
echo "✅ venv 활성화 완료"

# 5. pip 업그레이드
echo ""
echo "⬆️  pip 업그레이드..."
pip install --upgrade pip

# 6. setuptools와 wheel 먼저 설치 (honcho 의존성 해결)
echo ""
echo "🔧 기본 패키지 설치 (setuptools, wheel)..."
pip install setuptools>=65.0.0 wheel>=0.37.0

# 7. requirements 설치
echo ""
echo "📦 패키지 설치 중 (requirements_hybrid.txt)..."
if [ -f "requirements_hybrid.txt" ]; then
    pip install -r requirements_hybrid.txt
    echo "✅ 패키지 설치 완료"
else
    echo "❌ requirements_hybrid.txt 파일을 찾을 수 없습니다"
    exit 1
fi

# 8. 설치된 패키지 확인
echo ""
echo "📋 설치된 패키지 목록:"
pip list | grep -E "(fastapi|uvicorn|celery|redis|honcho|pandas|openpyxl)"

# 9. 환경 변수 파일 확인
echo ""
echo "⚙️  환경 설정 확인..."
if [ -f "hybrid_config.env" ]; then
    echo "✅ hybrid_config.env 파일 존재"
    echo "💡 사용법: source hybrid_config.env 또는 .env로 복사"
else
    echo "⚠️  환경 설정 파일이 없습니다. env.sample을 참조하여 생성하세요."
fi

echo ""
echo "🎉 Python 환경 구축 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. Redis 설치: sudo apt install redis-server"
echo "2. Redis 시작: sudo service redis-server start"
echo "3. Redis 확인: redis-cli ping (PONG 출력)"
echo "4. 시스템 시작: bash start_hybrid_system.sh"
echo ""
echo "🔗 FastAPI Docs: http://localhost:8080/docs"
echo ""










