# 유틸리티 스크립트

파이프라인 유틸리티 및 헬퍼 스크립트입니다.

## 스크립트 목록

### `check_header_report.py`
헤더 순서 비교 보고서 내용 확인

### `check_stage1_result.py`
Stage 1 실행 결과 확인

### `extract_header_order.py`
헤더 순서 추출 및 비교 보고서 생성

### `read_header_order.py`
최종 헤더 순서 읽기

### `cleanup_scripts.py`
스크립트 정리 도구 (legacy 파일 이동 등)

## 사용법

각 스크립트는 독립적으로 실행 가능합니다:

```bash
python scripts/utils/check_stage1_result.py
python scripts/utils/extract_header_order.py
python scripts/utils/read_header_order.py
```

