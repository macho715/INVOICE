# ⚠️ 수동 설치 필요 안내

**작성일**: 2025-10-15  
**상태**: WSL2 업데이트 필요  

---

## 🔴 현재 상황

자동 설치를 시도했으나, **WSL2가 설치되지 않았거나 업데이트가 필요한 상태**입니다.

```
오류: "Linux용 Windows 하위 시스템 최신 버전으로 업데이트해야 합니다"
```

---

## ✅ 해결 방법 (3단계)

### 1단계: PowerShell 관리자 권한으로 실행

1. **시작 메뉴** 클릭
2. **"PowerShell"** 검색
3. **우클릭 → "관리자 권한으로 실행"** 선택

### 2단계: WSL2 업데이트 명령 실행

PowerShell 관리자 창에서 다음 명령어를 **순서대로** 실행:

```powershell
# 1. WSL 업데이트
wsl --update

# 2. WSL 종료 (재시작)
wsl --shutdown

# 3. WSL 버전 확인
wsl --version
```

**예상 출력**:
```
WSL 버전: 2.x.x
커널 버전: 5.x.x
```

### 3단계: WSL2 접근 테스트

```powershell
# WSL2 터미널 접속
wsl
```

성공하면 Linux 프롬프트가 표시됩니다:
```bash
user@hostname:~$
```

---

## 🚀 WSL2 설치 후 진행 단계

WSL2가 정상 작동하면, 다음 스크립트들을 **순서대로** 실행하세요:

### A. Redis 설치 (WSL2 터미널)

```bash
# 패키지 업데이트
sudo apt update

# Redis 설치
sudo apt install -y redis-server

# Redis 시작
sudo service redis-server start

# 연결 확인
redis-cli ping  # PONG 출력되어야 함
```

### B. Python 환경 구축 (WSL2 터미널)

```bash
# 프로젝트 디렉토리로 이동
cd /mnt/c/Users/SAMSUNG/Downloads/HVDC_Invoice-20251015T070213Z-1-001/HVDC_Invoice/HVDC_Invoice_Audit

# 실행 권한 부여
chmod +x setup_python_env.sh
chmod +x start_hybrid_system.sh

# Python 환경 구축
bash setup_python_env.sh
```

**예상 소요 시간**: 3-5분

### C. Hybrid System 시작 (WSL2 터미널)

```bash
# 시스템 시작
bash start_hybrid_system.sh
```

**예상 출력**:
```
🚀 Hybrid System 시작 중...
✅ Redis: PONG
✅ venv 활성화 완료
[web.1] Uvicorn: http://0.0.0.0:8080
[worker.1] Celery: concurrency=2 (solo)
```

### D. 시스템 검증

**브라우저 접속**: http://localhost:8080/docs

**Health Check** (새 터미널):
```bash
curl http://localhost:8080/health
```

---

## 📁 준비 완료된 파일

다음 파일들이 이미 생성되어 즉시 사용 가능합니다:

- ✅ `setup_python_env.sh` - Python 환경 자동 구축
- ✅ `start_hybrid_system.sh` - 시스템 시작 스크립트
- ✅ `hybrid_config.env` - 환경 변수 설정
- ✅ `requirements_hybrid.txt` - 패키지 목록 (honcho v2.0.0)
- ✅ `QUICK_START_GUIDE.md` - 상세 가이드
- ✅ `SETUP_CHECKLIST.md` - 체크리스트

---

## 🐛 WSL2 설치 문제 해결

### 문제 1: "wsl 명령을 찾을 수 없음"

**해결**:
1. Windows 10 버전 확인: **설정 → 시스템 → 정보**
2. 필요 버전: **Build 19041 이상**
3. Windows Update 실행

### 문제 2: "가상화가 비활성화됨"

**해결**:
1. BIOS 진입 (재부팅 시 F2/Del 키)
2. Virtualization Technology (VT-x/AMD-V) **활성화**
3. 저장 후 재부팅

### 문제 3: "WSL 기능이 설치되지 않음"

**해결** (PowerShell 관리자):
```powershell
# WSL 기능 활성화
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# 가상 머신 플랫폼 활성화
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 재부팅
Restart-Computer

# 재부팅 후
wsl --set-default-version 2
wsl --install -d Ubuntu
```

---

## 📞 추가 지원

### 공식 문서
- **WSL 설치 가이드**: https://learn.microsoft.com/windows/wsl/install
- **WSL 문제 해결**: https://learn.microsoft.com/windows/wsl/troubleshooting

### 프로젝트 문서
- **`QUICK_START_GUIDE.md`**: 전체 설치 가이드
- **`SETUP_CHECKLIST.md`**: 단계별 체크리스트
- **`REDIS_INSTALLATION_GUIDE.md`**: Redis 상세 가이드

---

## ⏭️ 다음 단계

1. **PowerShell 관리자 권한**으로 `wsl --update` 실행
2. **WSL2 정상 작동** 확인 (`wsl --version`)
3. **위 A-B-C-D 단계** 순서대로 진행
4. **시스템 검증** 완료

---

**작성일**: 2025-10-15  
**프로젝트**: HVDC Invoice Audit  
**상태**: WSL2 수동 설치 필요










