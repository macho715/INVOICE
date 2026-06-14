
import sys
from pathlib import Path
sys.path.insert(0, str(Path(".") / "PDF"))

try:
    from parsers.dsv_pdf_parser import DSVPDFParser
    print("✅ 강화된 PDF 파서 임포트 성공")
    
    parser = DSVPDFParser()
    print("✅ 파서 초기화 성공")
    
    with open("test_sample.txt", "w", encoding="utf-8") as f:
        f.write("DEC NO: BOE123456789\nMBL NO: DSVU1234567\nCONTAINER: TGBU1234567")
    
    result = parser.parse_pdf("test_sample.txt", "BOE")
    
    if result.get("data"):
        print("✅ 파싱 테스트 성공")
        data = result["data"]
        print(f"   DEC NO: {data.get(\"dec_no\")}")
        print(f"   MBL NO: {data.get(\"mbl_no\")}")
        print(f"   Containers: {data.get(\"containers\")}")
    else:
        print("❌ 파싱 실패")
        
    import os
    os.remove("test_sample.txt")
    print("🎉 강화된 파서 동작 확인 완료!")
    
except Exception as e:
    print(f"❌ 오류: {e}")

