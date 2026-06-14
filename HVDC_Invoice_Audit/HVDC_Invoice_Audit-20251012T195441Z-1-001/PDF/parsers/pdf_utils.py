"""
PDF Utils Module
================

PDF 텍스트 추출을 위한 공통 유틸리티

Author: HVDC Logistics Team
Version: 1.0.0
"""

from typing import List
import re


def try_import(name: str):
    """안전한 모듈 임포트"""
    try:
        return __import__(name)
    except Exception:
        return None


def extract_text_pages(pdf_path: str) -> List[str]:
    """
    PDF에서 페이지별 텍스트 추출

    pdfplumber 우선, 실패/빈 문서면 pytesseract 폴백(선택)
    테스트를 위해 .txt 파일도 지원

    Args:
        pdf_path: PDF 파일 경로

    Returns:
        List[str]: 페이지별 텍스트 리스트
    """
    texts: List[str] = []

    # 테스트용: .txt 파일 직접 읽기
    if pdf_path.endswith(".txt"):
        try:
            with open(pdf_path, "r", encoding="utf-8") as f:
                return [f.read()]
        except Exception:
            return [""]

    # Primary: pdfplumber
    pdfplumber = try_import("pdfplumber")
    if pdfplumber:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for p in pdf.pages:
                    txt = (p.extract_text() or "").strip()
                    texts.append(txt)
        except Exception:
            pass

    # Fallback: OCR if no text or very short content
    if not any(texts) or sum(len(t) for t in texts) < 20:
        # Optional OCR fallback for image-based PDFs
        fitz = try_import("fitz")  # PyMuPDF
        pytesseract = try_import("pytesseract")

        if fitz and pytesseract:
            try:
                doc = fitz.open(pdf_path)
                texts = []
                for p in doc:
                    pix = p.get_pixmap(dpi=200)
                    from PIL import Image
                    import io

                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    texts.append(pytesseract.image_to_string(img))
                doc.close()
            except Exception:
                pass

    # Clean up text formatting
    return [re.sub(r"[ \t]+", " ", t).strip() for t in texts]


def normalize_whitespace(text: str) -> str:
    """텍스트 공백 정규화"""
    return re.sub(r"\s+", " ", text).strip()


def extract_pattern(text: str, pattern: str, flags: int = re.IGNORECASE) -> str:
    """정규식 패턴으로 첫 번째 매치 추출"""
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else ""


def extract_all_patterns(
    text: str, pattern: str, flags: int = re.IGNORECASE
) -> List[str]:
    """정규식 패턴으로 모든 매치 추출"""
    matches = re.findall(pattern, text, flags)
    return [m.strip() if isinstance(m, str) else m for m in matches]
