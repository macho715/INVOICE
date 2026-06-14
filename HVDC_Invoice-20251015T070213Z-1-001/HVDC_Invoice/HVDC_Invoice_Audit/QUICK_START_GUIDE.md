# 🚀 WSL2 Hybrid System 빠른 시작 가이드

**프로젝트**: HVDC Invoice Audit - Hybrid System  
**버전**: v1.0  
**작성일**: 2025-10-15  

---

## 📋 개요

WSL2 + Redis + Honcho 기반 No-Docker 런타임 환경을 빠르게 구축하고 실행하는 가이드입니다.

### 🎯 시스템 구성
- **FastAPI**: PDF 업로드 및 처리 API (Port 8080)
- **Celery Worker**: 비동기 작업 처리 (Redis 기반)
- **Redis**: 메시지 브로커 및 결과 백엔드
- **Honcho**: 멀티 프로세스 관리

---

## ⚡ 빠른 시작 (3단계)

### 1단계: WSL2 업데이트 및 Redis 설치

#### WSL2 업데이트 (Windows PowerShell 관리자 권한)
```powershell
wsl --update
wsl --shutdown
wsl
```

#### Redis 설치 (WSL2 터미널)
```bash
# 패키지 목록 업데이트
sudo apt update

# Redis 설치
sudo apt install -y redis-server

# Redis 서비스 시작
sudo service redis-server start

# 연결 확인 (PONG 출력되어야 함)
redis-cli ping
```

### 2단계: Python 환경 구축

#### 자동 설치 스크립트 실행 (WSL2 터미널)
```bash
# 프로젝트 디렉토리로 이동
cd /mnt/c/Users/SAMSUNG/Downloads/HVDC_Invoice-20251015T070213Z-1-001/HVDC_Invoice/HVDC_Invoice_Audit

# Python 환경 구축 스크립트 실행
bash setup_python_env.sh
```

#### 수동 설치 (필요시)
```bash
# 가상 환경 생성
python3 -m venv venv

# 가상 환경 활성화
source venv/bin/activate

# 패키지 설치
pip install --upgrade pip
pip install setuptools>=65.0.0 wheel>=0.37.0
pip install -r requirements_hybrid.txt
```

### 3단계: 시스템 시작

#### Hybrid System 실행 (WSL2 터미널)
```bash
# 가상 환경 활성화 (필요시)
source venv/bin/activate

# 환경 변수 로드 (선택적)
# cp hybrid_config.env .env

# Hybrid System 시작
bash start_hybrid_system.sh
```

---

## 🔍 실행 확인

### 서비스 상태 확인

#### 1. FastAPI 서비스 확인
브라우저에서 접속: **http://localhost:8080/docs**

예상 응답:
- Swagger UI 인터페이스
- `/upload`, `/health`, `/status/{task_id}` 엔드포인트

#### 2. Health Check API
```bash
curl http://localhost:8080/health
```

예상 응답:
```json
{
  "status": "ok",
  "broker": "redis",
  "workers": 1,
  "version": "1.0.0"
}
```

#### 3. Redis 연결 확인
```bash
redis-cli ping
# 출력: PONG
```

#### 4. Celery Worker 상태
터미널에서 다음과 같은 로그 확인:
```
[worker.1] Celery: concurrency=2 (solo), redis://localhost:6379/0
[web.1] Uvicorn: http://0.0.0.0:8080
```

---

## 📁 파일 구조

```
HVDC_Invoice_Audit/
├── hybrid_doc_system/           # 핵심 시스템
│   ├── api/
│   │   └── main.py             # FastAPI 애플리케이션
│   ├── worker/
│   │   └── celery_app.py       # Celery Worker
│   └── config/
│       ├── routing_rules_hvdc.json
│       └── unified_ir_schema.yaml
├── venv/                       # Python 가상 환경
├── Procfile.dev                # 프로세스 정의
├── requirements_hybrid.txt     # Python 패키지
├── hybrid_config.env           # 환경 변수
├── start_hybrid_system.sh      # 시스템 시작 스크립트
├── setup_python_env.sh         # Python 환경 구축 스크립트
└── QUICK_START_GUIDE.md        # 본 가이드
```

---

## ⚙️ 환경 설정

### 환경 변수 (hybrid_config.env)

주요 설정 항목:
```bash
# 애플리케이션
APP_PORT=8080
LOG_LEVEL=INFO

# Redis 연결
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# 기능 플래그
USE_HYBRID=true
HYBRID_API_URL=http://localhost:8080

# 성능 튜닝
CELERY_TASK_TIMEOUT=300
CELERY_MAX_RETRIES=3
```

### 사용자 정의 설정

1. **환경 변수 파일 생성**:
   ```bash
   cp hybrid_config.env .env
   nano .env  # 필요한 값 수정
   ```

2. **포트 변경** (필요시):
   ```bash
   # .env 파일에서
   APP_PORT=8081
   
   # Procfile.dev에서
   web: uvicorn hybrid_doc_system.api.main:app --host 0.0.0.0 --port 8081 --reload
   ```

---

## 🐛 문제 해결

### 자주 발생하는 문제

#### Q: "WSL 업데이트 필요" 메시지
**A**: PowerShell 관리자 권한으로 실행:
```powershell
wsl --update
wsl --shutdown
```

#### Q: "Redis 연결 실패"
**A**: Redis 서비스 상태 확인:
```bash
sudo service redis-server status
sudo service redis-server start
redis-cli ping
```

#### Q: "ModuleNotFoundError: pkg_resources"
**A**: setuptools 설치:
```bash
pip install setuptools>=65.0.0 wheel>=0.37.0
```

#### Q: "Permission denied: setup_python_env.sh"
**A**: 실행 권한 부여:
```bash
chmod +x setup_python_env.sh
chmod +x start_hybrid_system.sh
```

#### Q: "Port 8080 already in use"
**A**: 포트 사용 중인 프로세스 확인:
```bash
# WSL2에서
sudo lsof -i :8080
# 또는 Windows에서
netstat -ano | findstr :8080
```

### 로그 확인

#### Celery Worker 로그
```bash
# Worker 상세 로그
celery -A hybrid_doc_system.worker.celery_app worker -l debug
```

#### FastAPI 로그
```bash
# 개발 모드 상세 로그
uvicorn hybrid_doc_system.api.main:app --host 0.0.0.0 --port 8080 --reload --log-level debug
```

---

## 🔧 고급 사용법

### 개별 서비스 실행

#### FastAPI만 실행
```bash
source venv/bin/activate
uvicorn hybrid_doc_system.api.main:app --host 0.0.0.0 --port 8080 --reload
```

#### Celery Worker만 실행
```bash
source venv/bin/activate
celery -A hybrid_doc_system.worker.celery_app worker -l info -P solo --concurrency=2
```

### 테스트 실행

#### PDF 업로드 테스트
```bash
# Swagger UI 사용 (권장)
# http://localhost:8080/docs → /upload 엔드포인트

# 또는 curl 사용
curl -X POST "http://localhost:8080/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@sample.pdf"
```

#### Unit Test 실행
```bash
source venv/bin/activate
pytest -v
```

---

## 📈 성능 최적화

### Celery Worker 튜닝
```bash
# 동시 작업 수 증가
celery -A hybrid_doc_system.worker.celery_app worker -l info -P solo --concurrency=4

# 메모리 누수 방지
celery -A hybrid_doc_system.worker.celery_app worker -l info -P solo --max-tasks-per-child=50
```

### Redis 메모리 최적화
```bash
# Redis 설정 확인
redis-cli config get maxmemory
redis-cli config get maxmemory-policy

# 메모리 제한 설정 (예: 512MB)
redis-cli config set maxmemory 512mb
redis-cli config set maxmemory-policy allkeys-lru
```

---

## 🚀 프로덕션 배포

### 서비스 등록 (systemd)

#### 1. 서비스 파일 생성
```bash
sudo nano /etc/systemd/system/hvdc-hybrid.service
```

```ini
[Unit]
Description=HVDC Hybrid System
After=network.target redis.service

[Service]
Type=forking
User=your-username
WorkingDirectory=/mnt/c/Users/SAMSUNG/Downloads/HVDC_Invoice-20251015T070213Z-1-001/HVDC_Invoice/HVDC_Invoice_Audit
ExecStart=/bin/bash start_hybrid_system.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 2. 서비스 활성화
```bash
sudo systemctl daemon-reload
sudo systemctl enable hvdc-hybrid
sudo systemctl start hvdc-hybrid
sudo systemctl status hvdc-hybrid
```

---

## 📞 지원 및 문의

### 문서
- **시스템 아키텍처**: `Documentation/SYSTEM_ARCHITECTURE.md`
- **사용자 가이드**: `Documentation/USER_GUIDE.md`
- **설정 가이드**: `Documentation/CONFIGURATION_GUIDE.md`

### 로그 위치
- **애플리케이션 로그**: 터미널 출력
- **Redis 로그**: `/var/log/redis/redis-server.log`
- **시스템 로그**: `journalctl -u hvdc-hybrid`

### 기술 지원
- **프로젝트**: HVDC Invoice Audit
- **시스템**: Hybrid Document Processing
- **AI 지원**: MACHO-GPT v3.4-mini

---

## 🎉 완료!

시스템이 정상적으로 실행되면:

1. ✅ **FastAPI Docs**: http://localhost:8080/docs
2. ✅ **Health Check**: `{"status":"ok","workers":1}`
3. ✅ **Redis**: `redis-cli ping` → `PONG`
4. ✅ **Celery Worker**: 로그에서 `ready` 상태 확인

**다음 단계**: PDF 업로드 테스트 및 HVDC 시스템과 통합 테스트 진행

---

**작성일**: 2025-10-15  
**작성자**: MACHO-GPT v3.4-mini  
**버전**: v1.0










