# 헤더 탐지 안정화 가이드 (v4.0.53)

## 변경 요약
- `HeaderDetectionResult` 도입으로 탐지 점수와 경고를 함께 확인할 수 있습니다.
- `DataSynchronizerV30`는 수동 지정 → 휴리스틱 → 벤더 기본값 순으로 헤더 후보를 검증합니다.
- `case_number` 시맨틱 키를 이용한 기본 검증이 실패하면 자동으로 다음 후보를 시도합니다.
- 벤더를 판별하지 못한 경우 기본 헤더 위치를 강제로 사용하지 않습니다.

## 수동 헤더 행 지정
```bash
python scripts/stage1_sync_sorted/data_synchronizer_v30.py \
  --master /path/to/master.xlsx \
  --warehouse /path/to/warehouse.xlsx \
  --header-override Warehouse:Sheet1=2 \
  --header-override *=summary=0
```
- 형식: `<파일라벨>:<시트명>=<0-based 행번호>`
- `*`는 와일드카드로 사용 가능합니다.
- 여러 시트에 대해 반복 지정할 수 있습니다.

## 운영 팁
- 로그에서 `LOW_CONFIDENCE` 경고가 보이면 벤더 기본값이나 수동 값을 함께 확인하세요.
- 새 테스트(`tests/test_header_detection_strategy.py`)를 통해 주요 시나리오가 검증됩니다.
- 기존 파이프라인 호출부 수정 없이도 자동으로 개선된 로직을 사용합니다.
