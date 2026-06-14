
---
## Build Modes & Troubleshooting

- **FAST (onedir, dev 용)**  
  `build.bat`  또는  `.uild.ps1`
- **ONEFILE (배포 용)**  
  `build.bat ONEFILE=1`  또는  `.uild.ps1 -OneFile`
- **Venv 문제시**  
  `build.bat NO_VENV=1`  (시스템 Python 사용)

본 스크립트는 `torch/matplotlib/scipy/pytest/jupyter` 등 **대형·불필요 패키지**를
사전 **제외**하여 빌드 시간을 단축합니다.