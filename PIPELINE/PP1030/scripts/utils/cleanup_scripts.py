#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel 색상 검증 스크립트 정리 도구

기존 7개 스크립트를 archive/verify_colors_archive로 이동합니다.
"""

import shutil
from pathlib import Path
from datetime import datetime

def cleanup_old_scripts():
    """기존 스크립트를 아카이브로 이동"""
    
    print("=" * 80)
    print("Excel 색상 검증 스크립트 정리".center(80))
    print("=" * 80)
    
    # 현재 디렉토리
    current_dir = Path(__file__).parent
    archive_dir = current_dir / "archive" / "verify_colors_archive"
    
    # 아카이브 디렉토리 생성
    archive_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[1] 아카이브 디렉토리: {archive_dir}")
    
    # 이동할 파일 목록
    files_to_archive = [
        "verify_excel_colors.py",
        "verify_excel_colors_fast.py",
        "verify_excel_colors_ultra_fast.py",
        "verify_excel_colors_enhanced.py",
        "verify_excel_colors_optimized.py",
        "verify_excel_colors_patched.py",
        "verify_excel_colors_fast_batch.py",
    ]
    
    # 보존할 파일 (이동하지 않음)
    keep_files = [
        "verify_excel_colors_unified.py",  # 통합 스크립트
        "cleanup_old_scripts.py",           # 이 스크립트 자체
    ]
    
    moved_count = 0
    skipped_count = 0
    
    print(f"\n[2] 파일 이동 중...")
    print("-" * 80)
    
    for filename in files_to_archive:
        source_path = current_dir / filename
        
        if not source_path.exists():
            print(f"  ⚠️ 건너뜀 (파일 없음): {filename}")
            skipped_count += 1
            continue
        
        # 백업 파일명에 타임스탬프 추가
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
        dest_path = archive_dir / dest_filename
        
        try:
            shutil.move(str(source_path), str(dest_path))
            print(f"  ✅ 이동 완료: {filename} → {dest_filename}")
            moved_count += 1
        except Exception as e:
            print(f"  ❌ 오류: {filename} - {e}")
            skipped_count += 1
    
    # 요약
    print("\n" + "=" * 80)
    print("정리 완료".center(80))
    print("=" * 80)
    print(f"\n  ✅ 이동된 파일: {moved_count}개")
    print(f"  ⚠️ 건너뛴 파일: {skipped_count}개")
    print(f"\n  아카이브 위치: {archive_dir}")
    
    # 남은 파일 확인
    remaining_scripts = list(current_dir.glob("verify_excel_colors*.py"))
    
    if remaining_scripts:
        print(f"\n[3] 현재 디렉토리 남은 스크립트:")
        print("-" * 80)
        for script in remaining_scripts:
            if script.name in keep_files:
                print(f"  ✅ {script.name} (보존)")
            else:
                print(f"  ⚠️ {script.name} (예상치 못한 파일)")
    
    # 통합 스크립트 확인
    unified_script = current_dir / "verify_excel_colors_unified.py"
    if unified_script.exists():
        print(f"\n[4] 통합 스크립트 확인")
        print("-" * 80)
        print(f"  ✅ {unified_script.name} - 준비 완료")
        print(f"\n  사용법:")
        print(f"    python {unified_script.name} --mode=basic")
        print(f"    python {unified_script.name} --mode=ultra_fast")
        print(f"    python {unified_script.name} --mode=batch")
    else:
        print(f"\n[4] ⚠️ 경고: 통합 스크립트를 찾을 수 없습니다!")
        print(f"  예상 위치: {unified_script}")
    
    # 문서 확인
    readme = current_dir / "README_UNIFIED.md"
    migration = current_dir / "MIGRATION_GUIDE.md"
    
    print(f"\n[5] 문서 확인")
    print("-" * 80)
    if readme.exists():
        print(f"  ✅ {readme.name}")
    else:
        print(f"  ⚠️ {readme.name} - 없음")
    
    if migration.exists():
        print(f"  ✅ {migration.name}")
    else:
        print(f"  ⚠️ {migration.name} - 없음")
    
    print("\n" + "=" * 80)
    print("다음 단계:".center(80))
    print("=" * 80)
    print("""
  1. 통합 스크립트 테스트:
     python verify_excel_colors_unified.py --mode=ultra_fast
  
  2. 기존 명령어 업데이트:
     기존: python verify_excel_colors_optimized.py
     신규: python verify_excel_colors_unified.py --mode=basic
  
  3. 문서 확인:
     - README_UNIFIED.md: 사용 가이드
     - MIGRATION_GUIDE.md: 마이그레이션 가이드
  
  4. CI/CD 파이프라인 업데이트 (해당 시)
    """)
    
    return moved_count, skipped_count

def main():
    """메인 함수"""
    try:
        moved, skipped = cleanup_old_scripts()
        
        if moved > 0:
            print("\n✅ 정리가 성공적으로 완료되었습니다!")
        else:
            print("\n⚠️ 이동된 파일이 없습니다. 이미 정리되었거나 파일이 없을 수 있습니다.")
        
        return 0
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
