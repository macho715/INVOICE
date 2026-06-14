# OFCO Invoice Parser (v0.9)

## Files
- `ofco_parser.py` — Regex-first OFCO invoice parser (표 행 파싱 + 18규칙 매핑 + EA/Rate/Amount 추출).
- `OFCO-INV-0001178.parsed.json` — 샘플 PDF 파싱 결과(있을 경우).
- `README.md` — 사용 방법.

## Quick Start
```bash
# 1) Python 3.9+ 권장
python ofco_parser.py "/path/to/OFCO-INV-0001178_Samsung.pdf" --out "./parsed.json"

# 2) 출력 확인
type ./parsed.json  # Windows
cat ./parsed.json   # Linux/Mac
```

## Notes
- 표 꼬리 패턴: `5% 1.00 490.13 LS 490.13 24.51 514.64` 형태 파싱 지원
- 검증: EA×Rate≈Amount(±0.01 또는 ±2%), Σ라인 vs Total(±2%)
- 매핑: SAFEEN/ADP/CC/FW/BA/5000 IG FW/Handling/Port Charge/PTW/Manpower/Crane/Forklift/MGO/Consumables/Gate Pass/Storage/Waste/Pilotage 등