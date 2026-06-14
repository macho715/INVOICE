# ✅ WSL2 Hybrid System 설치 체크리스트

**프로젝트**: HVDC Invoice Audit - WSL2 Hybrid System  
**작성일**: 2025-10-15  

---

## 📋 사전 준비 확인

- [ ] Windows 10/11 (Build 19041 이상)
- [ ] WSL2 설치됨
- [ ] 관리자 권한 있음
- [ ] 인터넷 연결 가능

---

## 🚀 설치 단계 (4단계)

### ✅ Step 1: WSL2 업데이트

**실행 위치**: PowerShell (관리자 권한)

```powershell
wsl --update
wsl --shutdown
wsl
```

**확인 방법**:
```bash
wsl --version
# WSL 버전: 2.x.x 이상 확인
```

- [ ] WSL2 업데이트 완료
- [ ] WSL2 재시작 완료
- [ ] WSL2 터미널 접속 성공

---

### ✅ Step 2: Redis 설치

**실행 위치**: WSL2 터미널

```bash
# 패키지 목록 업데이트
sudo apt update

# Redis 설치
sudo apt install -y redis-server

# Redis 서비스 시작
sudo service redis-server start

# 연결 확인
redis-cli ping
```

**예상 출력**: `PONG`

- [ ] Redis 설치 완료
- [ ] Redis 서비스 시작 성공
- [ ] `redis-cli ping` → `PONG` 출력 확인

**문제 발생 시**: `REDIS_INSTALLATION_GUIDE.md` 참조

---

### ✅ Step 3: Python 환경 구축

**실행 위치**: WSL2 터미널

```bash
# 프로젝트 디렉토리로 이동
cd /mnt/c/Users/SAMSUNG/Downloads/HVDC_Invoice-20251015T070213Z-1-001/HVDC_Invoice/HVDC_Invoice_Audit

# 스크립트 실행 권한 부여
chmod +x setup_python_env.sh

# Python 환경 구축 실행
bash setup_python_env.sh
```

**예상 소요 시간**: 3-5분

**확인 방법**:
```bash
source venv/bin/activate
python --version  # Python 3.8+ 확인
pip list | grep -E "(fastapi|celery|redis|honcho)"
```

- [ ] 가상 환경 생성 완료
- [ ] 48개 패키지 설치 완료
- [ ] FastAPI, Celery, Redis, Honcho 설치 확인

**문제 발생 시**: `QUICK_START_GUIDE.md` → 문제 해결 섹션 참조

---

### ✅ Step 4: 시스템 시작

**실행 위치**: WSL2 터미널

```bash
# 실행 권한 부여 (필요시)
chmod +x start_hybrid_system.sh

# Hybrid System 시작
bash start_hybrid_system.sh
```

**예상 출력**:
```
🚀 Hybrid System 시작 중...
✅ Redis: PONG
✅ venv 활성화 완료
🔧 Honcho 시작 (FastAPI + Celery Worker)...
[web.1] Uvicorn: http://0.0.0.0:8080
[worker.1] Celery: concurrency=2 (solo)
```

- [ ] FastAPI 서비스 시작 (`[web.1]` 로그 확인)
- [ ] Celery Worker 시작 (`[worker.1]` 로그 확인)
- [ ] 오류 메시지 없음

---

## 🔍 시스템 검증

### 1. FastAPI Swagger UI 확인

**브라우저에서 접속**: http://localhost:8080/docs

- [ ] Swagger UI 페이지 표시됨
- [ ] `/upload`, `/health`, `/status/{task_id}` 엔드포인트 확인

### 2. Health Check API 테스트

**새 터미널에서 실행**:
```bash
curl http://localhost:8080/health
```

**예상 응답**:
```json
{
  "status": "ok",
  "broker": "redis",
  "workers": 1,
  "version": "1.0.0"
}
```

- [ ] Health Check API 정상 응답
- [ ] `"status": "ok"` 확인
- [ ] `"workers": 1` 이상 확인

### 3. Redis 연결 확인

**새 WSL2 터미널에서 실행**:
```bash
redis-cli ping
redis-cli info stats
```

- [ ] `PONG` 출력
- [ ] Redis 통계 정보 표시

### 4. Celery Worker 상태 확인

**Honcho 실행 중인 터미널에서 로그 확인**:
```
[worker.1] [2025-10-15 14:00:00,000: INFO/MainProcess] celery@hostname ready.
[worker.1] [2025-10-15 14:00:00,000: INFO/MainProcess] registered tasks: parse_pdf
```

- [ ] `celery@hostname ready` 메시지 확인
- [ ] `registered tasks` 목록 표시

---

## 📁 생성된 파일 확인

프로젝트 디렉토리에 다음 파일들이 존재하는지 확인:

- [ ] `setup_python_env.sh` (2,510 bytes)
- [ ] `start_hybrid_system.sh` (1,048 bytes, 경로 업데이트됨)
- [ ] `hybrid_config.env` (1,485 bytes)
- [ ] `QUICK_START_GUIDE.md` (8,601 bytes)
- [ ] `WSL2_HYBRID_SYSTEM_SETUP_COMPLETE_REPORT.md` (10,543 bytes)
- [ ] `SETUP_CHECKLIST.md` (본 파일)
- [ ] `venv/` (디렉토리, 48개 패키지 설치됨)
- [ ] `requirements_hybrid.txt` (honcho==2.0.0 포함)

---

## 🎯 추가 테스트 (선택적)

### PDF 업로드 테스트

1. **샘플 PDF 준비** (아무 PDF 파일)
2. **Swagger UI 접속**: http://localhost:8080/docs
3. **`/upload` 엔드포인트 클릭**
4. **Try it out → Choose File → PDF 선택 → Execute**
5. **응답 확인**:
   ```json
   {
     "task_id": "abc-123-xyz",
     "status": "processing",
     "message": "PDF processing started"
   }
   ```

- [ ] PDF 업로드 성공
- [ ] `task_id` 반환됨
- [ ] `/status/{task_id}`로 진행 상태 확인 가능

---

## 🐛 문제 해결

### 문제 1: "WSL 업데이트 필요" 메시지

**해결**:
```powershell
wsl --update
wsl --shutdown
wsl
```

### 문제 2: "Redis 연결 실패"

**해결**:
```bash
sudo service redis-server status
sudo service redis-server restart
redis-cli ping
```

### 문제 3: "ModuleNotFoundError: pkg_resources"

**해결**:
```bash
source venv/bin/activate
pip install setuptools>=65.0.0 wheel>=0.37.0
pip install -r requirements_hybrid.txt
```

### 문제 4: "Permission denied: setup_python_env.sh"

**해결**:
```bash
chmod +x setup_python_env.sh
chmod +x start_hybrid_system.sh
```

### 문제 5: "Port 8080 already in use"

**해결**:
```bash
# WSL2에서
sudo lsof -i :8080
# PID 확인 후 종료
kill -9 <PID>
```

---

## 📚 참조 문서

| 문서 | 설명 |
|------|------|
| `QUICK_START_GUIDE.md` | 상세 실행 가이드 (필독) |
| `WSL2_HYBRID_SYSTEM_SETUP_COMPLETE_REPORT.md` | 완료 보고서 |
| `REDIS_INSTALLATION_GUIDE.md` | Redis 설치 상세 가이드 |
| `Documentation/SYSTEM_ARCHITECTURE.md` | 시스템 아키텍처 |
| `Documentation/USER_GUIDE.md` | 사용자 가이드 |

---

## 🎉 완료!

모든 체크리스트를 완료하셨다면, WSL2 Hybrid System이 정상적으로 가동 중입니다!

### 다음 단계

1. **PDF 업로드 테스트** (Swagger UI 사용)
2. **HVDC 시스템 통합** (USE_HYBRID=true)
3. **성능 벤치마크** (Legacy vs Hybrid 비교)
4. **프로덕션 배포** (systemd 서비스 등록)

---

**작성일**: 2025-10-15  
**프로젝트**: HVDC Invoice Audit  
**버전**: v1.0










