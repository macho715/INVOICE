#!/usr/bin/env python3
"""
OFCO Invoice PDF 전처리 스크립트

목적:
- OCR 정확도 향상을 위한 이미지 전처리
- OFCO 인보이스 특유의 레이아웃 최적화
- 금액 필드 가독성 향상

전처리 기법:
1. 이미지 대비 강화 (Adaptive Histogram Equalization)
2. 노이즈 제거 (Bilateral Filter)
3. 테이블 경계선 복원 (Morphological Operations)
4. 텍스트 선명화 (Sharpening)
5. 통화 기호 정규화 (AED/USD)

Usage:
    python step00_ofco_pdf_preprocessor.py --input OFCO-INV-0001178.pdf --output OFCO-INV-0001178_preprocessed.pdf
    python step00_ofco_pdf_preprocessor.py --input-dir ./invoices --output-dir ./preprocessed --enhance-mode aggressive

Options:
    --input: 입력 PDF 파일 경로
    --output: 출력 PDF 파일 경로
    --input-dir: 입력 디렉토리 (배치 처리)
    --output-dir: 출력 디렉토리 (배치 처리)
    --enhance-mode: 강화 모드 (mild, moderate, aggressive) (기본값: moderate)
    --dpi: 이미지 변환 DPI (기본값: 300)
"""

import sys
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[WARNING] OpenCV(cv2)를 설치하세요: pip install opencv-python")

try:
    from pdf2image import convert_from_path
    from PIL import Image
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("[WARNING] pdf2image와 Pillow를 설치하세요: pip install pdf2image Pillow")

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("[WARNING] reportlab를 설치하세요: pip install reportlab")


class OFCOPDFPreprocessor:
    """OFCO Invoice PDF 전처리 클래스"""
    
    ENHANCE_PARAMS = {
        'mild': {
            'clahe_clip': 2.0,
            'clahe_grid': 8,
            'bilateral_d': 5,
            'bilateral_sigma_color': 50,
            'bilateral_sigma_space': 50,
            'sharpen_amount': 1.0,
            'morphology_kernel': 2
        },
        'moderate': {
            'clahe_clip': 3.0,
            'clahe_grid': 8,
            'bilateral_d': 7,
            'bilateral_sigma_color': 75,
            'bilateral_sigma_space': 75,
            'sharpen_amount': 1.5,
            'morphology_kernel': 3
        },
        'aggressive': {
            'clahe_clip': 4.0,
            'clahe_grid': 8,
            'bilateral_d': 9,
            'bilateral_sigma_color': 100,
            'bilateral_sigma_space': 100,
            'sharpen_amount': 2.0,
            'morphology_kernel': 4
        }
    }
    
    def __init__(self, enhance_mode: str = 'moderate'):
        """
        초기화
        
        Args:
            enhance_mode: 강화 모드 ('mild', 'moderate', 'aggressive')
        """
        if not CV2_AVAILABLE or not PDF2IMAGE_AVAILABLE or not REPORTLAB_AVAILABLE:
            raise RuntimeError("필수 라이브러리가 설치되지 않았습니다. 설치 가이드를 참고하세요.")
        
        self.enhance_mode = enhance_mode
        self.params = self.ENHANCE_PARAMS.get(enhance_mode, self.ENHANCE_PARAMS['moderate'])
        print(f"[INFO] 전처리 모드: {enhance_mode}")
        print(f"[INFO] 파라미터: {self.params}")
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        대비 강화 (CLAHE - Contrast Limited Adaptive Histogram Equalization)
        
        Args:
            image: 입력 이미지 (grayscale)
        
        Returns:
            대비 강화된 이미지
        """
        clahe = cv2.createCLAHE(
            clipLimit=self.params['clahe_clip'],
            tileGridSize=(self.params['clahe_grid'], self.params['clahe_grid'])
        )
        enhanced = clahe.apply(image)
        return enhanced
    
    def reduce_noise(self, image: np.ndarray) -> np.ndarray:
        """
        노이즈 제거 (Bilateral Filter)
        
        Args:
            image: 입력 이미지
        
        Returns:
            노이즈 제거된 이미지
        """
        denoised = cv2.bilateralFilter(
            image,
            d=self.params['bilateral_d'],
            sigmaColor=self.params['bilateral_sigma_color'],
            sigmaSpace=self.params['bilateral_sigma_space']
        )
        return denoised
    
    def sharpen_text(self, image: np.ndarray) -> np.ndarray:
        """
        텍스트 선명화 (Unsharp Masking)
        
        Args:
            image: 입력 이미지
        
        Returns:
            선명화된 이미지
        """
        # Gaussian blur
        blurred = cv2.GaussianBlur(image, (0, 0), 3)
        
        # Unsharp mask: original + amount * (original - blurred)
        sharpened = cv2.addWeighted(
            image, 1.0 + self.params['sharpen_amount'],
            blurred, -self.params['sharpen_amount'],
            0
        )
        
        return sharpened
    
    def enhance_table_lines(self, image: np.ndarray) -> np.ndarray:
        """
        테이블 경계선 복원 (Morphological Operations)
        
        Args:
            image: 입력 이미지 (grayscale)
        
        Returns:
            경계선 강화된 이미지
        """
        # 이진화
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 수평선 추출
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_h)
        
        # 수직선 추출
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_v)
        
        # 선 결합
        table_mask = cv2.add(horizontal_lines, vertical_lines)
        
        # 원본 이미지에 테이블 선 강화
        kernel = np.ones((self.params['morphology_kernel'], self.params['morphology_kernel']), np.uint8)
        table_mask = cv2.dilate(table_mask, kernel, iterations=1)
        
        # 원본과 결합
        enhanced = cv2.bitwise_and(image, cv2.bitwise_not(table_mask))
        enhanced = cv2.add(enhanced, table_mask)
        
        return enhanced
    
    def normalize_currency_symbols(self, image: np.ndarray) -> np.ndarray:
        """
        통화 기호 영역 강화 (AED/USD 텍스트 영역)
        
        Note: 실제 구현은 OCR로 통화 기호를 찾아 해당 영역을 강화하는 방식.
              여기서는 간단히 전체 이미지에 대한 처리로 대체.
        
        Args:
            image: 입력 이미지
        
        Returns:
            통화 기호 영역 강화된 이미지
        """
        # 향후 구현: pytesseract로 'AED', 'USD' 영역 찾아 강화
        # 현재는 전체 이미지 처리로 대체
        return image
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        전체 전처리 파이프라인
        
        Args:
            image: 입력 이미지 (BGR)
        
        Returns:
            전처리된 이미지 (BGR)
        """
        print("[INFO] 전처리 단계 시작...")
        
        # 1. 그레이스케일 변환
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 2. 대비 강화
        print("  [1/5] 대비 강화...")
        enhanced_contrast = self.enhance_contrast(gray)
        
        # 3. 노이즈 제거
        print("  [2/5] 노이즈 제거...")
        denoised = self.reduce_noise(enhanced_contrast)
        
        # 4. 테이블 경계선 복원
        print("  [3/5] 테이블 경계선 복원...")
        enhanced_lines = self.enhance_table_lines(denoised)
        
        # 5. 텍스트 선명화
        print("  [4/5] 텍스트 선명화...")
        sharpened = self.sharpen_text(enhanced_lines)
        
        # 6. 통화 기호 정규화 (현재는 생략)
        print("  [5/5] 통화 기호 정규화...")
        normalized = self.normalize_currency_symbols(sharpened)
        
        # BGR로 변환 (저장을 위해)
        if len(normalized.shape) == 2:
            result = cv2.cvtColor(normalized, cv2.COLOR_GRAY2BGR)
        else:
            result = normalized
        
        print("[OK] 전처리 완료")
        return result
    
    def process_pdf(
        self,
        input_pdf: str,
        output_pdf: str,
        dpi: int = 300
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        PDF 파일 전처리
        
        Args:
            input_pdf: 입력 PDF 경로
            output_pdf: 출력 PDF 경로
            dpi: 이미지 변환 DPI
        
        Returns:
            (성공 여부, 통계 정보)
        """
        stats = {
            'input_pdf': input_pdf,
            'output_pdf': output_pdf,
            'pages_processed': 0,
            'success': False,
            'errors': []
        }
        
        try:
            input_path = Path(input_pdf)
            output_path = Path(output_pdf)
            
            if not input_path.exists():
                raise FileNotFoundError(f"입력 PDF를 찾을 수 없습니다: {input_pdf}")
            
            print(f"[INFO] 입력 PDF: {input_path}")
            print(f"[INFO] 출력 PDF: {output_path}")
            print(f"[INFO] DPI: {dpi}")
            
            # PDF를 이미지로 변환
            print(f"\n[Step 1/3] PDF → 이미지 변환 (DPI {dpi})...")
            images = convert_from_path(str(input_path), dpi=dpi)
            print(f"[OK] {len(images)} 페이지 변환 완료")
            
            # 각 페이지 전처리
            print(f"\n[Step 2/3] 이미지 전처리...")
            processed_images = []
            
            for i, pil_image in enumerate(images, 1):
                print(f"\n페이지 {i}/{len(images)} 처리 중...")
                
                # PIL → OpenCV
                opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                
                # 전처리
                processed = self.preprocess_image(opencv_image)
                
                # OpenCV → PIL
                processed_pil = Image.fromarray(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))
                processed_images.append(processed_pil)
                
                stats['pages_processed'] += 1
            
            # 이미지를 PDF로 저장
            print(f"\n[Step 3/3] 이미지 → PDF 저장...")
            
            if processed_images:
                # 첫 페이지를 PDF로 저장, 나머지는 append
                processed_images[0].save(
                    str(output_path),
                    save_all=True,
                    append_images=processed_images[1:] if len(processed_images) > 1 else [],
                    resolution=dpi
                )
                print(f"[OK] PDF 저장 완료: {output_path}")
            else:
                raise Exception("전처리된 이미지가 없습니다")
            
            stats['success'] = True
            
            # 통계 출력
            print(f"\n{'='*80}")
            print(f"전처리 완료!")
            print(f"{'='*80}")
            print(f"입력 파일: {input_path}")
            print(f"출력 파일: {output_path}")
            print(f"처리된 페이지: {stats['pages_processed']}")
            print(f"전처리 모드: {self.enhance_mode}")
            
            return True, stats
            
        except FileNotFoundError as e:
            error_msg = f"파일을 찾을 수 없습니다: {e}"
            print(f"\n[ERROR] {error_msg}")
            stats['errors'].append(error_msg)
            return False, stats
        
        except Exception as e:
            error_msg = f"전처리 중 오류 발생: {type(e).__name__} - {e}"
            print(f"\n[ERROR] {error_msg}")
            stats['errors'].append(error_msg)
            return False, stats
    
    def process_directory(
        self,
        input_dir: str,
        output_dir: str,
        dpi: int = 300,
        pattern: str = "*.pdf"
    ) -> Tuple[int, int, List[str]]:
        """
        디렉토리 내 모든 PDF 파일 배치 처리
        
        Args:
            input_dir: 입력 디렉토리
            output_dir: 출력 디렉토리
            dpi: 이미지 변환 DPI
            pattern: 파일 패턴 (기본값: *.pdf)
        
        Returns:
            (성공 개수, 실패 개수, 오류 목록)
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            raise FileNotFoundError(f"입력 디렉토리를 찾을 수 없습니다: {input_dir}")
        
        # 출력 디렉토리 생성
        output_path.mkdir(parents=True, exist_ok=True)
        
        # PDF 파일 목록
        pdf_files = list(input_path.glob(pattern))
        
        print(f"[INFO] 입력 디렉토리: {input_path}")
        print(f"[INFO] 출력 디렉토리: {output_path}")
        print(f"[INFO] 발견된 PDF 파일: {len(pdf_files)}개")
        
        success_count = 0
        failure_count = 0
        errors = []
        
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n{'='*80}")
            print(f"파일 {i}/{len(pdf_files)}: {pdf_file.name}")
            print(f"{'='*80}")
            
            output_file = output_path / f"{pdf_file.stem}_preprocessed.pdf"
            
            success, stats = self.process_pdf(
                str(pdf_file),
                str(output_file),
                dpi=dpi
            )
            
            if success:
                success_count += 1
            else:
                failure_count += 1
                errors.extend(stats.get('errors', []))
        
        print(f"\n{'='*80}")
        print(f"배치 처리 완료!")
        print(f"{'='*80}")
        print(f"전체 파일: {len(pdf_files)}개")
        print(f"성공: {success_count}개")
        print(f"실패: {failure_count}개")
        
        if errors:
            print(f"\n오류 목록:")
            for error in errors:
                print(f"  - {error}")
        
        return success_count, failure_count, errors


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='OFCO Invoice PDF 전처리 스크립트 v1.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 단일 파일 전처리
  python step00_ofco_pdf_preprocessor.py --input OFCO-INV-0001178.pdf --output OFCO-INV-0001178_preprocessed.pdf
  
  # 배치 처리
  python step00_ofco_pdf_preprocessor.py --input-dir ./invoices --output-dir ./preprocessed
  
  # 강화 모드 설정
  python step00_ofco_pdf_preprocessor.py --input invoice.pdf --output invoice_enhanced.pdf --enhance-mode aggressive
  
  # 고해상도 처리
  python step00_ofco_pdf_preprocessor.py --input invoice.pdf --output invoice_hires.pdf --dpi 600

필수 라이브러리:
  pip install opencv-python pdf2image Pillow reportlab
        """
    )
    
    # 단일 파일 모드
    parser.add_argument('--input', type=str,
                        help='입력 PDF 파일 경로')
    parser.add_argument('--output', type=str,
                        help='출력 PDF 파일 경로')
    
    # 배치 모드
    parser.add_argument('--input-dir', type=str,
                        help='입력 디렉토리 (배치 처리)')
    parser.add_argument('--output-dir', type=str,
                        help='출력 디렉토리 (배치 처리)')
    
    # 공통 옵션
    parser.add_argument('--enhance-mode', type=str, default='moderate',
                        choices=['mild', 'moderate', 'aggressive'],
                        help='강화 모드 (기본값: moderate)')
    parser.add_argument('--dpi', type=int, default=300,
                        help='이미지 변환 DPI (기본값: 300)')
    parser.add_argument('--pattern', type=str, default='*.pdf',
                        help='배치 처리 파일 패턴 (기본값: *.pdf)')
    
    args = parser.parse_args()
    
    # 입력 검증
    if not args.input and not args.input_dir:
        parser.error("--input 또는 --input-dir 중 하나는 필수입니다")
    
    if args.input and not args.output:
        parser.error("--input을 사용할 때는 --output도 필수입니다")
    
    if args.input_dir and not args.output_dir:
        parser.error("--input-dir를 사용할 때는 --output-dir도 필수입니다")
    
    print("="*80)
    print("OFCO Invoice PDF 전처리 스크립트")
    print("="*80)
    print()
    
    # 전처리기 초기화
    try:
        preprocessor = OFCOPDFPreprocessor(enhance_mode=args.enhance_mode)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    
    # 단일 파일 처리
    if args.input:
        success, stats = preprocessor.process_pdf(
            args.input,
            args.output,
            dpi=args.dpi
        )
        
        if success:
            print(f"\n[SUCCESS] 전처리가 완료되었습니다!")
            sys.exit(0)
        else:
            print(f"\n[FAILURE] 전처리 중 오류가 발생했습니다.")
            sys.exit(1)
    
    # 배치 처리
    elif args.input_dir:
        success_count, failure_count, errors = preprocessor.process_directory(
            args.input_dir,
            args.output_dir,
            dpi=args.dpi,
            pattern=args.pattern
        )
        
        if failure_count == 0:
            print(f"\n[SUCCESS] 모든 파일 전처리 완료!")
            sys.exit(0)
        else:
            print(f"\n[PARTIAL SUCCESS] 일부 파일 전처리 실패 ({failure_count}/{success_count + failure_count})")
            sys.exit(1)


if __name__ == '__main__':
    main()
