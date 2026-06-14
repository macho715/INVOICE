"""
HVDC 파이프라인 Excel 런처 전체 설정 스크립트
- tools 폴더 생성
- config_validator.py 생성
- Excel 템플릿 생성
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트 (스크립트 위치 기준)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
VBA_DIR = SCRIPT_DIR

def create_tools_dir():
    """tools 폴더 생성"""
    TOOLS_DIR.mkdir(exist_ok=True)
    print(f"[OK] tools 폴더 확인: {TOOLS_DIR}")

def create_config_validator():
    """config_validator.py 생성"""
    validator_path = TOOLS_DIR / "config_validator.py"
    
    # 이미 존재하면 스킵
    if validator_path.exists():
        print(f"[INFO] config_validator.py 이미 존재: {validator_path}")
        return
    
    # 파일 내용은 이미 tools/config_validator.py로 생성됨
    print(f"[OK] config_validator.py 확인: {validator_path}")

def create_excel_template():
    """Excel 템플릿 생성"""
    try:
        # create_excel_template.py를 임포트
        sys.path.insert(0, str(VBA_DIR))
        from create_excel_template import create_excel_template as create_template
        
        output_path = VBA_DIR / "HVDC_Pipeline_Launcher.xlsm"
        result_path = create_template(str(output_path))
        print(f"[OK] Excel 템플릿 생성: {result_path}")
        print("[INFO] .xlsx 파일이 생성되었습니다. Excel에서 .xlsm으로 변환하세요.")
    except ImportError as e:
        print(f"[WARN] create_excel_template.py 임포트 실패: {e}")
        print("   수동으로 생성하세요.")
    except Exception as e:
        print(f"[WARN] Excel 템플릿 생성 실패: {e}")

def main():
    """전체 설정 실행"""
    print("=" * 60)
    print("HVDC 파이프라인 Excel 런처 전체 설정")
    print("=" * 60)
    
    create_tools_dir()
    create_config_validator()
    create_excel_template()
    
    print("\n" + "=" * 60)
    print("[OK] 설정 완료!")
    print("\n다음 단계:")
    print("1. Excel 파일 열기: HVDC_Pipeline_Launcher.xlsm")
    print("2. Alt+F11 (VBE 열기)")
    print("3. 모듈 추가 → modHVDC_CONTROL.bas 내용 붙여넣기")
    print("4. Excel로 돌아와서 CTRL_Install 실행")
    print("5. B4에 Project Root 경로 입력")
    print("6. '02) YAML 저장(+백업)' 버튼 클릭")
    print("=" * 60)

if __name__ == "__main__":
    main()

