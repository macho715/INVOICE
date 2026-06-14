

# **파이썬 기반의 안정적인 PDF 데이터 추출 파이프라인 설계: 주요 오픈소스 라이브러리 비교 분석**

## **Executive Summary**

본 보고서는 로컬 파이썬 환경에서 인보이스, 다중 컬럼, 표 중심의 PDF로부터 구조화된 데이터를 안정적으로 추출하기 위한 심층 기술 분석을 제공한다. 주요 오픈소스 라이브러리인 PyMuPDF, pdfplumber, Camelot, Tesseract를 비교 분석한 결과, 모든 시나리오에 완벽하게 부합하는 단일 솔루션은 존재하지 않으며, 문서의 특성(구조, 스캔 여부)과 프로젝트의 우선순위(성능, 정밀도, 개발 속도)에 따라 최적의 도구를 선택해야 한다는 결론에 도달했다.

### **핵심 권장 사항 요약**

* **최고의 성능과 범용 추출 능력:** PyMuPDF는 C언어 기반의 MuPDF에 파이썬 바인딩을 제공하여 압도적인 처리 속도와 강력한 통합 테이블 감지 기능을 포함한 포괄적인 기능을 제공하므로, 범용 추출 엔진으로서 가장 강력한 선택지이다.1  
* **최상의 정밀도와 복잡한 레이아웃 처리:** pdfplumber는 PDF 내부의 모든 문자, 선, 사각형 객체에 대한 세밀한 접근과 시각적 디버깅 기능을 제공한다. 이는 비표준적인 문서 구조를 정밀하게 분석하고 처리해야 하는 고난도 작업에 필수적이다.4  
* **고품질의 테이블 전문 추출:** Camelot은 테이블 데이터 추출에 특화된 라이브러리로, 명확한 경계선이 있는 테이블과 없는 테이블에 각각 최적화된 두 가지 강력한 파싱 전략을 제공하여, 테이블이 핵심인 문서에서 최고의 정확도를 보인다.7  
* **스캔 및 이미지 기반 문서 처리:** 스캔된 문서의 경우, PyMuPDF를 사용하여 페이지를 고해상도 이미지로 변환하고, OpenCV로 전처리한 후 Tesseract OCR 엔진으로 텍스트를 인식하는 하이브리드 파이프라인이 유일하게 신뢰할 수 있는 오픈소스 해결책이다.9

### **전략적 결론**

현대적이고 안정적인 PDF 추출 파이프라인은 각 문서 페이지의 특성을 사전에 분석하여 최적의 도구를 동적으로 선택하는 모듈식 시스템으로 설계되어야 한다. 예를 들어, 텍스트 기반 페이지는 PyMuPDF로 신속하게 처리하고, 스캔된 페이지는 Tesseract OCR 파이프라인으로 전환하는 방식이다. 이러한 하이브리드 아키텍처는 성능과 정확성 사이의 균형을 맞추고, 다양한 유형의 문서에 대한 강건성을 극대화하는 최적의 전략이다.

---

## **Section 1: 범용 PDF 파싱 엔진**

이 섹션에서는 모든 추출 파이프라인의 기초가 되는 두 가지 강력한 범용 PDF 파싱 라이브러리를 분석한다. 이들은 단순한 텍스트 추출을 넘어 문서의 복잡한 구조를 이해하는 데 필수적인 도구이다.

### **1.1. PyMuPDF: 고성능 엔진**

#### **1.1.1. 아키텍처의 우위와 성능**

PyMuPDF의 핵심 경쟁력은 C언어로 작성된 경량 고성능 라이브러리인 MuPDF에 파이썬 바인딩을 제공하는 구조에서 비롯된다.1 이 아키텍처는 순수 파이썬으로 구현된 다른 라이브러리들에 비해 월등한 성능을 보장하는 근본적인 이유이다. 공개된 벤치마크 자료에 따르면, PyMuPDF는 파일 복사, 텍스트 추출, 페이지 렌더링과 같은 핵심 작업에서 PyPDF2나 pdfminer와 같은 경쟁 도구보다 수십 배에서 수백 배 빠른 처리 속도를 기록한다.3 이러한 성능 우위는 대규모 문서를 일괄 처리해야 하는 프로덕션 환경에서 PyMuPDF를 가장 먼저 고려해야 할 이유가 된다.

#### **1.1.2. page.get\_text()를 활용한 다목적 텍스트 추출**

PyMuPDF의 page.get\_text() 메서드는 단순한 텍스트 추출을 넘어, 다양한 플래그를 통해 추출 결과의 구조와 상세 수준을 제어할 수 있는 강력한 기능을 제공한다.

* "text": 가장 기본적인 옵션으로, 줄 바꿈이 포함된 순수 텍스트를 빠르게 추출한다. 단일 컬럼의 간단한 레이아웃을 가진 문서에 적합하다.15  
* "blocks" 및 "words": 텍스트를 단락(block) 또는 단어(word) 단위로 그룹화하여 리스트 형태로 반환한다. 각 요소에는 좌표 정보가 포함되어 있어, 다중 컬럼 문서에서 텍스트의 논리적 읽기 순서를 재구성하는 데 유용하다.15  
* "dict" / "json" 및 "rawdict": 가장 강력하고 상세한 정보를 제공하는 옵션이다. 이 모드는 페이지의 모든 콘텐츠를 블록(blocks) \> 라인(lines) \> 스팬(spans)의 계층적 구조로 반환한다. 각 스팬(span)은 동일한 글꼴, 크기, 색상을 공유하는 텍스트 조각으로, 텍스트 내용뿐만 아니라 정확한 경계 상자(bounding box), 글꼴 이름, 크기, 색상 정보까지 포함한다.10 이 상세 정보는 복잡한 인보이스나 양식의 레이아웃을 프로그래밍 방식으로 완벽하게 복원하는 데 핵심적인 역할을 한다.  
* **LLM을 위한 최신 혁신:** 최근에는 PyMuPDF4LLM이라는 확장 패키지가 등장했다. 이 패키지의 to\_markdown() 함수는 다중 컬럼 레이아웃과 테이블을 자동으로 감지하고 구조를 유지하면서 GitHub 호환 마크다운 형식으로 변환해준다. 이는 RAG(Retrieval-Augmented Generation) 파이프라인에 PDF 콘텐츠를 공급하는 과정을 획기적으로 단순화한다.19

Python

import pymupdf \# fitz 별칭으로도 사용 가능

doc \= pymupdf.open("multi\_column\_report.pdf")  
page \= doc

\# 1\. 기본 텍스트 추출  
plain\_text \= page.get\_text("text")  
print("--- Plain Text \---")  
print(plain\_text\[:300\])

\# 2\. 구조화된 딕셔너리 형태로 추출  
structured\_data \= page.get\_text("dict")  
for block in structured\_data\["blocks"\]:  
    if block\['type'\] \== 0: \# 텍스트 블록  
        for line in block\["lines"\]:  
            for span in line\["spans"\]:  
                \# 텍스트, 좌표, 글꼴, 크기 등 상세 정보 접근 가능  
                print(f"Text: '{span\['text'\]}', Bbox: {span\['bbox'\]}, Font: {span\['font'\]}")

\# 3\. LLM/RAG를 위한 마크다운 변환 (PyMuPDF4LLM 필요)  
\# pip install pymupdf4llm  
import pymupdf4llm  
md\_text \= pymupdf4llm.to\_markdown(doc)  
print("\\n--- Markdown Output \---")  
print(md\_text)

doc.close()

### **1.2. PyMuPDF의 통합 테이블 추출 (page.find\_tables())**

#### **1.2.1. 기능 개요**

버전 1.23부터 도입된 page.find\_tables() 메서드는 PyMuPDF를 단순한 텍스트 파서를 넘어 강력한 테이블 추출 도구로 변모시켰다.21 이 메서드는 페이지 내의 테이블을 자동으로 탐지하고, 각 테이블을 구조화된 Table 객체로 반환한다. 이 객체는 테이블의 경계 상자(.bbox), 개별 셀의 좌표 리스트(.cells), 헤더 정보(.header)와 같은 유용한 속성과 함께, 테이블 내용을 파이썬 리스트로 추출하는 .extract() 메서드 및 판다스 데이터프레임으로 직접 변환하는 .to\_pandas() 메서드를 제공하여 데이터 처리 과정을 크게 간소화한다.23

#### **1.2.2. 복잡한 테이블 처리**

find\_tables()는 병합된 셀이나 경계선이 없는 테이블과 같은 일반적인 문제 상황에 대응하기 위한 전략을 내장하고 있다. 예를 들어, 여러 열이나 행에 걸쳐 병합된 셀이 있는 경우, PyMuPDF는 이를 하위 열/행 구조로 인식하고 해당되지 않는 셀 위치에는 None 값을 채워 넣어 테이블의 전체적인 사각형 구조를 유지한다. 또한, 수직선이 없는 테이블의 경우 vertical\_strategy="text" 옵션을 사용하여 단어들의 수직 정렬을 기반으로 열 경계를 추론할 수 있다.23 이러한 조정 가능한 옵션들은 다양한 형태의 비정형 테이블에 대한 추출 성공률을 높인다.

#### **1.2.3. 실용 예제**

다음 코드는 PDF 파일의 첫 페이지에서 모든 테이블을 찾아 판다스 데이터프레임과 마크다운 형식으로 변환하는 전체 과정을 보여준다.

Python

import pymupdf  
import pandas as pd

doc \= pymupdf.open("financial\_report.pdf")  
page \= doc

\# 페이지에서 테이블 찾기  
found\_tables \= page.find\_tables()

if found\_tables.tables:  
    print(f"Found {len(found\_tables.tables)} table(s) on page {page.number \+ 1}.")  
      
    for i, table in enumerate(found\_tables):  
        print(f"\\n--- Table {i+1} \---")  
          
        \# 1\. 판다스 데이터프레임으로 변환  
        df \= table.to\_pandas()  
        print("Pandas DataFrame:")  
        print(df.head())  
          
        \# 데이터프레임을 CSV 파일로 저장  
        df.to\_csv(f"table\_{i+1}.csv", index=False)  
          
        \# 2\. 마크다운 형식으로 변환  
        md \= table.to\_markdown()  
        print("\\nMarkdown Representation:")  
        print(md)  
else:  
    print("No tables found on this page.")

doc.close()

이처럼 PyMuPDF는 단일 라이브러리 내에서 고성능 텍스트 추출과 정교한 테이블 분석을 모두 수행할 수 있는 올인원 솔루션으로 발전했다. 이는 과거 여러 라이브러리를 조합해야만 가능했던 작업을 단순화하며, 개발 생산성을 크게 향상시킨다.

### **1.3. pdfplumber: 정밀 제어 툴킷**

#### **1.3.1. 핵심 철학 및 객체 접근**

pdfplumber는 pdfminer.six를 기반으로 구축되었으며, 그 설계 철학은 속도보다는 개발자에게 PDF 콘텐츠에 대한 세밀하고 완벽한 제어권을 제공하는 데 중점을 둔다.4 pdfplumber의 가장 큰 장점은 페이지를 구성하는 모든 기본 요소에 직접 접근할 수 있다는 점이다. 개발자는 page.chars, page.lines, page.rects, page.curves 등의 속성을 통해 각 문자와 그 위치, 페이지에 그려진 모든 선과 사각형, 곡선에 대한 정보를 리스트 형태로 얻을 수 있다.5 이처럼 세분화된 데이터는 텍스트 내용뿐만 아니라 시각적 정렬 자체가 중요한 의미를 갖는 인보이스나 양식 같은 문서의 구조를 역공학적으로 분석하는 데 필수적이다.

#### **1.3.2. 좌표계 및 영역 지정 (crop)**

pdfplumber는 페이지의 좌측 상단을 원점 (0, 0)으로 하는 직관적인 좌표계를 사용한다. 여기서 특히 유용한 기능은 page.crop(bounding\_box) 메서드이다. 이 메서드를 사용하면 페이지의 특정 영역(예: 인보이스의 헤더, 품목 테이블, 합계 부분)을 지정하여 해당 영역만을 포함하는 새로운 가상 페이지 객체를 생성할 수 있다.5 이렇게 관심 영역을 먼저 분리하고 나면, 후속 추출 작업의 정확도를 높이고 불필요한 노이즈를 제거할 수 있어 복잡한 문서 처리 시 매우 효과적인 전략이 된다.

### **1.4. pdfplumber의 고급 테이블 파싱과 시각적 디버깅**

#### **1.4.1. 설정 가능한 테이블 추출**

pdfplumber의 테이블 추출 기능(page.extract\_table(), page.extract\_tables())은 table\_settings 딕셔너리를 통해 매우 상세하게 제어할 수 있다.5 예를 들어, 경계선이 없는 테이블의 경우 "vertical\_strategy": "text" 설정을 통해 텍스트의 수직 정렬을 기준으로 열을 구분하도록 지시할 수 있다. 또한, snap\_tolerance나 join\_tolerance 같은 허용 오차 값을 조정하여 미세하게 어긋난 선들을 합치거나 정렬함으로써 테이블 감지 정확도를 미세 조정할 수 있다.5

#### **1.4.2. 핵심 기능: 시각적 디버깅**

pdfplumber를 다른 라이브러리와 차별화하는 가장 강력한 기능은 바로 시각적 디버깅 워크플로우이다. 다른 라이브러리들의 추출 과정이 종종 '블랙박스'처럼 느껴지는 반면, pdfplumber는 개발자가 추출 과정을 직접 눈으로 확인하고 문제를 진단할 수 있게 해준다.

이 워크플로우는 다음과 같은 단계로 진행된다:

1. page.to\_image()를 호출하여 페이지를 이미지 객체로 렌더링한다.  
2. 이 이미지 위에 im.draw\_rects(page.chars)나 im.draw\_lines(page.lines)와 같은 드로잉 메서드를 사용하여 pdfplumber가 인식한 문자, 선, 사각형의 위치를 시각적으로 표시한다.  
3. 특히 테이블 추출 시에는 im.debug\_tablefinder()를 사용하여 라이브러리가 어떻게 셀과 경계선을 감지했는지 직접 확인할 수 있다.5

이 과정을 통해 개발자는 "왜 이 열이 합쳐졌는가?" 또는 "왜 이 행이 누락되었는가?"와 같은 질문에 대한 명확한 답을 얻고, 이를 바탕으로 table\_settings를 반복적으로 수정하며 최적의 추출 결과를 도출할 수 있다.

#### **1.4.3. 활용 사례**

구조가 복잡하고 비정형적인 인보이스에서 테이블을 추출하는 상황을 가정해보자. 초기 extract\_table() 호출이 실패했을 때, 개발자는 시각적 디버깅을 통해 특정 열의 텍스트 정렬이 미세하게 어긋나 있어 감지가 실패했음을 발견할 수 있다. 이 정보를 바탕으로 table\_settings의 snap\_tolerance 값을 약간 높여 재시도함으로써 성공적으로 테이블을 추출할 수 있다. 이처럼 문제 진단과 해결을 위한 직관적인 피드백 루프는 pdfplumber만이 제공하는 독보적인 장점이다.28

Python

import pdfplumber

with pdfplumber.open("complex\_invoice.pdf") as pdf:  
    page \= pdf.pages

    \# 시각적 디버깅을 위한 이미지 생성  
    im \= page.to\_image(resolution=150)

    \# 페이지에서 감지된 모든 수직선과 수평선을 이미지 위에 그리기  
    \# im.draw\_lines(page.lines, stroke="red", stroke\_width=2)  
      
    \# 테이블 파인더가 감지한 셀 경계를 시각화  
    im.debug\_tablefinder()  
      
    \# 디버깅 이미지를 파일로 저장하여 확인  
    im.save("debug\_complex\_invoice.png", format\="PNG")

    \# 디버깅 결과를 바탕으로 테이블 추출 설정 조정  
    table\_settings \= {  
        "vertical\_strategy": "text",  
        "horizontal\_strategy": "lines",  
        "snap\_tolerance": 5,  
    }  
      
    table \= page.extract\_table(table\_settings)  
      
    if table:  
        for row in table:  
            print(row)

이러한 접근 방식은 개발 시간이 더 소요될 수 있지만, 가장 까다로운 문서에 대해서도 가장 높은 수준의 정확성을 달성할 수 있는 신뢰성 있는 경로를 제공한다.

---

## **Section 2: 전문가: Camelot을 이용한 고품질 테이블 추출**

이 섹션에서는 테이블 추출이라는 특정 목적을 위해 제작된 전문 도구인 Camelot에 대해 집중적으로 분석한다. 범용 파서와는 다른 접근 방식을 통해 테이블 데이터 추출의 정확성을 극대화하는 전략을 살펴본다.

### **2.1. 핵심 이분법: Lattice vs. Stream**

Camelot의 강력함은 서로 다른 유형의 테이블을 처리하기 위해 설계된 두 가지 뚜렷한 알고리즘에서 나온다. Camelot은 범용 PDF 파서가 아니며, 명시적으로 텍스트 기반 PDF에서만 작동하고 스캔된 문서는 지원하지 않는다.7

#### **2.1.1. Lattice 모드 (flavor='lattice')**

Lattice 모드는 테이블에 명확한 경계선이 있는 경우에 사용된다. 이 알고리즘은 내부적으로 OpenCV를 사용하여 페이지 이미지에서 수직 및 수평선을 감지하고, 이 선들의 교차점을 기반으로 셀 그리드를 정확하게 재구성한다.31 이 방식은 추측에 의존하지 않고 그래픽 요소를 기반으로 하므로 매우 결정론적(deterministic)이며 높은 정확도를 보인다. 테이블의 선이 배경에 그려진 경우 process\_background=True 옵션을 사용하거나, 미세한 선의 감지 감도를 높이기 위해 line\_scale 파라미터를 조정하는 등의 세부 설정이 가능하다.32

#### **2.1.2. Stream 모드 (flavor='stream')**

Stream 모드는 경계선이 없는 테이블, 즉 텍스트 요소들 사이의 공백(whitespace)을 통해 시각적으로만 테이블 형태를 이루는 경우에 사용된다. 이 알고리즘은 텍스트 단어들의 정렬과 간격을 분석하여 가상의 열과 행 경계를 추론하는 휴리스틱 기반 접근 방식을 사용한다.31 Lattice에 비해 오류의 가능성이 높지만, row\_tol (수직 텍스트 그룹화 허용 오차)과 같은 파라미터를 조정하거나, table\_areas 또는 columns 옵션을 통해 분석할 테이블의 정확한 좌표나 열의 x좌표를 직접 지정하여 알고리즘의 정확도를 크게 향상시킬 수 있다.32

이 두 가지 모드의 존재로 인해 개발자는 처리하려는 PDF 테이블의 시각적 특성에 따라 가장 적합한 추출 전략을 선택할 수 있다. 일반적으로는 먼저 기본값인 Lattice를 시도하고, 결과가 만족스럽지 않거나 테이블에 선이 없는 경우 Stream으로 전환하여 세부 파라미터를 조정하는 방식으로 접근한다.

### **2.2. 성공 측정 및 데이터 워크플로우 통합**

#### **2.2.1. 파싱 리포트**

Camelot의 독특한 기능 중 하나는 추출된 각 테이블에 대해 .parsing\_report를 제공한다는 점이다. 이 리포트에는 'accuracy'(정확도), 'whitespace'(공백 비율)와 같은 정량적 지표가 포함되어 있다.7 개발자는 이 지표를 활용하여 프로그래밍 방식으로 추출 품질을 평가하고, 특정 임계값 이하의 품질을 가진 테이블을 자동으로 필터링하거나 재처리 대상으로 분류할 수 있다. 이는 대규모 문서 처리 시 수동 검증 작업을 줄이는 데 매우 유용하다.

#### **2.2.2. 판다스(Pandas)와의 완벽한 연동**

Camelot은 파이썬 데이터 분석 생태계와의 통합을 최우선으로 고려하여 설계되었다. camelot.read\_pdf()의 반환값인 TableList 객체 내의 각 Table 객체는 .df 속성을 통해 즉시 판다스 데이터프레임으로 접근할 수 있다.7 이 설계 덕분에 개발자는 테이블을 추출한 후 별도의 변환 과정 없이 즉시 판다스의 강력한 데이터 정제, 변환, 분석 기능을 활용할 수 있다.34

#### **2.2.3. 다양한 포맷으로의 내보내기**

추출된 테이블은 .export() 메서드를 통해 CSV, JSON, Excel, HTML 등 다양한 파일 형식으로 손쉽게 저장할 수 있다.7 이는 후속 ETL(Extract, Transform, Load) 파이프라인이나 다른 시스템과의 연동을 매우 편리하게 만든다.

Python

import camelot  
import pandas as pd

\# Lattice 모드를 사용하여 경계선이 있는 테이블 추출  
tables \= camelot.read\_pdf("bordered\_table.pdf", flavor='lattice', pages='1')

if tables.n \> 0:  
    \# 첫 번째 테이블 선택  
    table \= tables  
      
    \# 1\. 파싱 리포트 확인  
    print("Parsing Report:")  
    print(table.parsing\_report)  
      
    \# 2\. 판다스 데이터프레임으로 접근 및 처리  
    df \= table.df  
    print("\\nPandas DataFrame:")  
    print(df.head())  
      
    \# 데이터프레임 후처리 (예: 특정 열을 숫자형으로 변환)  
    \# df \= pd.to\_numeric(df, errors='coerce')  
      
    \# 3\. Excel 파일로 내보내기  
    table.to\_excel("output.xlsx")  
    print("\\nTable exported to output.xlsx")

이러한 특징들은 Camelot이 단순한 추출 도구를 넘어, 데이터 분석 워크플로우의 시작점에 자연스럽게 통합될 수 있는 전문적인 솔루션임을 보여준다. 그러나 Camelot의 이러한 전문성은 동시에 한계를 의미하기도 한다. 테이블 외의 텍스트(예: 제목, 주석, 본문)는 추출할 수 없으므로, 텍스트와 테이블이 혼재된 일반적인 문서를 완벽하게 처리하기 위해서는 다른 범용 라이브러리와의 조합이 필수적이다.37 이 경우, 각 라이브러리가 사용하는 서로 다른 좌표계를 일치시켜 텍스트와 테이블의 순서를 올바르게 재구성하는 추가적인 복잡성이 발생할 수 있다.38

---

## **Section 3: 마지막 과제: Tesseract OCR을 이용한 스캔 문서 처리**

이 섹션에서는 PDF 내에 텍스트 데이터가 존재하지 않는 가장 어려운 과제, 즉 스캔된 문서를 다룬다. PyMuPDF, pdfplumber, Camelot과 같은 라이브러리들은 기본적으로 "네이티브" 또는 "텍스트 기반" PDF에서 작동하며, 이미지로 구성된 스캔 문서의 텍스트를 읽을 수 없다.7 따라서 이 문제를 해결하기 위해서는 Tesseract와 같은 광학 문자 인식(OCR) 엔진을 통합하는 하이브리드 전략이 필수적이다.

### **3.1. 하이브리드 OCR 파이프라인 구축**

스캔된 문서와 텍스트 기반 문서가 혼재된 환경을 안정적으로 처리하기 위한 표준 아키텍처 패턴은 다음과 같은 2단계 접근 방식을 따른다.

1. **페이지 분석 및 분류:** 먼저 PyMuPDF와 같은 빠른 라이브러리를 사용하여 각 페이지에서 텍스트를 추출 시도한다 (page.get\_text()). 반환된 텍스트의 길이가 매우 짧거나 거의 없다면(예: 40자 미만), 해당 페이지는 스캔된 이미지일 가능성이 높다고 판단하고 OCR 처리 대상으로 분류한다.10  
2. **OCR 대체 처리 (Fallback):** 스캔된 것으로 분류된 페이지에 대해서는 다음의 OCR 파이프라인을 실행한다.  
   * **이미지 변환:** PyMuPDF의 page.get\_pixmap(dpi=300)을 사용하여 페이지를 OCR에 적합한 고해상도(최소 300 DPI 권장) 이미지로 메모리 내에서 렌더링한다.10  
   * **OCR 수행:** 생성된 이미지 객체(예: PIL Image)를 pytesseract.image\_to\_string() 함수에 전달하여 텍스트를 인식한다.9

이 방식은 중간에 파일을 디스크에 쓸 필요 없이 모든 과정을 메모리 내에서 처리하므로 효율적이며, 각 페이지의 특성에 맞는 최적의 처리 방식을 동적으로 적용하여 전체 파이프라인의 성능과 정확성을 모두 확보할 수 있다.

Python

import pymupdf  
import pytesseract  
from PIL import Image  
import io

def extract\_text\_from\_pdf(pdf\_path, text\_threshold=40):  
    doc \= pymupdf.open(pdf\_path)  
    full\_text \=

    for page\_num, page in enumerate(doc):  
        \# 1\. 페이지 분석: 텍스트 양 확인  
        text \= page.get\_text("text")  
        if len(text.strip()) \> text\_threshold:  
            \# 텍스트 기반 페이지: PyMuPDF로 직접 추출  
            print(f"Page {page\_num \+ 1} is text-based. Extracting directly.")  
            full\_text.append(text)  
        else:  
            \# 2\. OCR Fallback: 스캔된 페이지로 간주  
            print(f"Page {page\_num \+ 1} is likely scanned. Performing OCR.")  
            \# 고해상도 이미지로 렌더링  
            pix \= page.get\_pixmap(dpi=300)  
            img\_data \= pix.tobytes("png")  
            img \= Image.open(io.BytesIO(img\_data))  
              
            \# Tesseract로 OCR 수행 (한국어+영어)  
            ocr\_text \= pytesseract.image\_to\_string(img, lang='kor+eng')  
            full\_text.append(ocr\_text)

    doc.close()  
    return "\\n".join(full\_text)

\# 사용 예시  
\# result \= extract\_text\_from\_pdf("mixed\_document.pdf")  
\# print(result)

### **3.2. 이미지 전처리를 통한 OCR 정확도 극대화**

Tesseract의 OCR 성능은 입력 이미지의 품질에 절대적으로 의존한다.42 PDF에서 변환된 원본 이미지를 그대로 사용하면 노이즈, 불균일한 조명, 기울어짐 등으로 인해 인식률이 현저히 저하될 수 있다. 따라서 안정적인 결과를 얻기 위해서는 OpenCV와 같은 이미지 처리 라이브러리를 이용한 전처리 과정이 반드시 필요하다.

* **필수 전처리 단계:**  
  * **그레이스케일 변환:** cv2.cvtColor(image, cv2.COLOR\_BGR2GRAY)를 통해 이미지를 흑백으로 변환하여 처리 과정을 단순화하고 노이즈를 줄인다.9  
  * **이진화 (Binarization):** cv2.adaptiveThreshold()를 사용하여 이미지를 선명한 흑과 백으로 구분한다. 문서의 조명이 균일하지 않은 경우가 많으므로, 이미지 전체에 단일 임계값을 적용하는 것보다 각 영역에 맞는 최적의 임계값을 계산하는 적응형 임계값(adaptive thresholding) 방식이 훨씬 효과적이다.11  
  * **노이즈 제거:** cv2.bilateralFilter()와 같은 필터를 적용하여 이미지의 불필요한 점이나 얼룩을 제거하면서도 텍스트의 경계선은 보존한다.9  
  * **기울기 보정 (Deskewing):** 스캔 시 발생한 문서의 기울어짐은 Tesseract의 성능을 크게 저하시키는 주요 요인이다. 이미지의 기울기를 감지하고 수평으로 회전시키는 보정 작업을 수행해야 한다.9  
* Tesseract 설정 최적화:  
  pytesseract를 사용할 때, 처리할 문서의 특성에 맞게 설정을 최적화하는 것이 중요하다. lang 파라미터를 통해 인식할 언어를 명시하고(예: lang='eng+kor'), config 파라미터를 통해 페이지 분할 모드(PSM, Page Segmentation Mode)를 지정할 수 있다. 예를 들어, 문서가 단일 텍스트 블록으로 구성된 경우 \--psm 6 옵션을 사용하면 인식 정확도를 높일 수 있다.9

결론적으로, 신뢰성 있는 OCR 시스템은 단순히 pytesseract.image\_to\_string() 함수를 호출하는 것이 아니라, 페이지 유형 감지, 이미지 렌더링, 정교한 전처리, 최적화된 OCR 호출로 이어지는 체계적인 파이프라인을 구축하는 것을 의미한다. 특히 전처리 단계에 대한 투자는 전체 시스템의 안정성과 정확성을 결정짓는 가장 중요한 요소이다.

한편, 이러한 전통적인 OCR 파이프라인의 복잡성을 해결하기 위해 새로운 패러다임이 등장하고 있다. Donut과 같은 최신 멀티모달 대규모 언어 모델(LLM)은 'OCR-free' 접근 방식을 채택한다.44 이 모델들은 비전 인코더(Swin Transformer 등)와 텍스트 디코더(BART 등)를 결합하여 이미지에서 곧바로 구조화된 텍스트를 생성한다.44 이는 이미지 인식과 언어 이해를 단일 네트워크에서 엔드투엔드로 처리함으로써, 별도의 OCR 엔진이나 복잡한 전처리 규칙의 필요성을 줄여준다. 아직 로컬 환경에 배포하기에는 복잡성이 있지만, 이러한 모델들은 문서 이해 기술의 미래 방향을 제시하며, 현재 Tesseract 기반 파이프라인의 한계를 극복할 잠재력을 보여준다.

---

## **Section 4: 라이브러리별 비교 분석**

이 섹션에서는 앞서 논의된 내용을 종합하여 각 라이브러리의 특징을 다차원적으로 직접 비교하고, 실제 시나리오에 기반한 질적 평가를 통해 각 도구의 실용적인 장단점을 명확히 한다.

### **4.1. 기능 비교 매트릭스**

다음 표는 각 라이브러리의 핵심 속성을 요약하여 한눈에 비교할 수 있도록 정리한 것이다. 이 표는 특정 요구사항에 가장 적합한 도구를 신속하게 선택하기 위한 가이드 역할을 한다.

**Table 4.1: 파이썬 PDF 라이브러리 기능 비교 매트릭스**

| 기능 | PyMuPDF | pdfplumber | Camelot | Tesseract (pytesseract 경유) |
| :---- | :---- | :---- | :---- | :---- |
| **주요 사용 사례** | 속도, 올인원(All-in-one) | 정밀도, 디버깅 | 테이블 추출 | 이미지 OCR |
| **성능** | 매우 우수 | 보통 | 보통 | 느림 (페이지당) |
| **테이블 추출** | 우수 (통합 기능) | 매우 우수 (설정 가능) | 최우수 (특화 기능) | 해당 없음 (후처리 필요) |
| **레이아웃 보존** | 매우 우수 | 최우수 | 해당 없음 (테이블만) | 낮음 (순수 텍스트) |
| **스캔 PDF 지원** | OCR 통합으로 가능 | OCR 통합으로 가능 | 미지원 | 네이티브 (이미지 대상) |
| **주요 의존성** | 없음 (자체 포함) | pdfminer.six | OpenCV, Ghostscript | Tesseract 바이너리 |
| **라이선스** | AGPL / 상업용 | MIT | MIT | Apache 2.0 |

이 표는 각 라이브러리의 기술적 특성뿐만 아니라, 의존성 및 라이선스와 같이 실제 프로젝트 도입 시 반드시 고려해야 할 비기능적 요구사항까지 포함하고 있다. 특히 PyMuPDF의 AGPL 라이선스는 오픈소스 프로젝트가 아닌 상업용 내부 애플리케이션에서 사용할 경우 라이선스 정책을 신중하게 검토해야 함을 시사한다.1

### **4.2. 복잡한 문서에 대한 질적 평가**

정량적 벤치마크를 넘어, 복잡한 실제 인보이스 문서를 예로 들어 각 라이브러리의 접근 방식을 질적으로 비교해 본다.

* **시나리오:** 다중 컬럼 헤더, 수직선이 없고 여러 줄로 된 설명이 포함된 품목 테이블, 그리고 키-값 쌍으로 이루어진 요약 섹션을 포함하는 복잡한 인보이스.  
* **PyMuPDF의 접근 방식:** page.get\_text("dict")를 사용하여 모든 텍스트 블록과 좌표를 얻은 후, 좌표 기반 휴리스틱을 적용하여 헤더와 요약 섹션을 그룹화한다. 품목 테이블은 page.find\_tables(vertical\_strategy="text")를 사용하여 추출을 시도한다. 이 방식은 높은 자동화 수준을 목표로 하지만, 복잡한 구조에서는 정확한 그룹화를 위한 추가적인 코딩이 필요할 수 있다.  
* **pdfplumber의 접근 방식:** page.crop()을 사용하여 헤더, 테이블, 요약 세 영역을 명확하게 분리한다. 테이블 영역에 대해 page.extract\_table()을 vertical\_strategy="text"와 함께 사용하고, 결과가 불완전할 경우 page.to\_image().debug\_tablefinder()를 통해 시각적으로 문제를 진단한다. 진단 결과를 바탕으로 snap\_tolerance와 같은 설정을 미세 조정하여 정확한 결과를 얻을 때까지 반복한다. 이 접근은 개발자의 개입이 더 많이 필요하지만, 가장 신뢰성 높은 결과를 도출할 가능성이 크다.  
* **Camelot의 접근 방식:** 테이블에 선이 없으므로 flavor='stream'을 사용한다. 자동 감지가 실패할 가능성이 높으므로, camelot.plot(kind='text')로 페이지를 시각화하여 테이블의 정확한 좌표(table\_areas)와 각 열의 x좌표(columns)를 수동으로 파악한 후, 이를 read\_pdf 함수의 인자로 전달한다. 이 방식은 테이블 자체에 대해서는 높은 정확도를 보장하지만, 헤더와 요약 같은 비-테이블 영역은 완전히 무시한다.

이 비교를 통해, 가장 복잡하고 비정형적인 문서의 경우, 더 많은 수작업을 요구하더라도 pdfplumber의 시각적 피드백 루프가 정확한 솔루션에 도달하는 가장 확실한 경로를 제공한다는 점이 분명해진다.27

### **4.3. 프로젝트 건전성 및 커뮤니티 활동**

* **PyMuPDF:** 상용 소프트웨어 회사인 Artifex가 적극적으로 유지보수하며, 잦은 릴리스와 상업용 라이선스 및 지원 옵션을 제공한다. GitHub에서 8.2k 이상의 스타를 기록하는 등 매우 활발하고 건강한 프로젝트이다.1  
* **pdfplumber:** 개인 개발자에 의해 주도되지만, 8.9k 이상의 스타를 기록하며 매우 강력한 커뮤니티를 보유하고 있다. GitHub의 이슈와 토론 포럼이 활발하게 운영되며, 꾸준히 업데이트가 이루어지고 있어 신뢰도가 높다.24  
* **Camelot:** 3.5k 이상의 스타를 보유한 인기 있는 프로젝트이지만, 최근 활동은 새로운 기능 개발보다는 기존 기능의 유지보수 및 의존성 업데이트에 집중되는 경향을 보인다. 핵심 기능은 안정적이고 성숙한 상태로 평가된다.51  
* **Tesseract:** 구글의 지원을 받는 매우 오래되고 성숙한 오픈소스 프로젝트로, 방대한 커뮤니티와 오랜 역사를 가지고 있다. 개발은 지속적으로 이루어지고 있다.

---

## **Section 5: 종합 및 전략적 권장 사항**

이 마지막 섹션에서는 기술적 분석을 바탕으로 실제 비즈니스 시나리오에 적용할 수 있는 구체적이고 실행 가능한 전략을 제시한다.

### **5.1. 실제 시나리오별 처방적 툴체인**

#### **5.1.1. 시나리오 A: 대규모 일괄 처리 (예: 일관된 형식의 은행 거래 내역서 10만 건 처리)**

* **권장 사항:** **PyMuPDF 단독 엔진 사용.**  
* **근거:** 이 시나리오의 핵심 요구사항은 압도적인 처리 속도이다. PyMuPDF의 성능은 다른 모든 라이브러리를 능가하며, 구조화된 문서의 텍스트와 테이블을 추출하는 데 필요한 기능이 충분히 내장되어 있다. 다른 라이브러리를 추가하여 발생하는 성능 저하와 복잡성 증가는 불필요하다.

#### **5.1.2. 시나리오 B: 다양하고 복잡한 인보이스의 고정밀 추출 (예: 수천 개 공급업체의 각기 다른 형식의 인보이스 처리)**

* **권장 사항:** **시각적 디버깅을 포함한 pdfplumber 중심의 워크플로우.**  
* **근거:** 핵심 과제는 처리 속도가 아니라 형식의 다양성과 복잡성에 대응하는 것이다. pdfplumber의 세밀한 객체 제어와 시각적 디버깅 기능은 새롭게 접하는 인보이스 템플릿 각각에 대해 강건한 파서를 개발하는 데 필수적이다. 템플릿별 초기 개발 시간은 더 길지만, 그 결과로 만들어진 파서는 변화에 더 탄력적으로 대응할 수 있다.

#### **5.1.3. 시나리오 C: 혼합된 아카이브 디지털화 (예: 최신 디지털 PDF와 오래된 스캔 문서가 섞인 법률 파일 처리)**

* **권장 사항:** **하이브리드 PyMuPDF \+ Tesseract/OpenCV 파이프라인.**  
* **근거:** 이는 가장 강건하고 다재다능한 아키텍처이다. 각 페이지의 특성을 동적으로 판단하여 최적의 도구를 선택함으로써 모든 유형의 문서를 처리할 수 있다.  
* **아키텍처 설계:**  
  1. pymupdf로 문서를 열고 페이지를 순회한다.  
  2. 각 페이지에 대해 page.get\_text()를 실행하고 반환된 텍스트의 길이를 확인한다.  
  3. **텍스트 길이가 임계값 초과 시:** 해당 페이지는 텍스트 기반으로 판단하고, PyMuPDF의 네이티브 함수(get\_text("dict"), find\_tables())를 사용하여 텍스트와 테이블을 처리한다.  
  4. **텍스트 길이가 임계값 이하 시:** 해당 페이지는 스캔된 것으로 간주하고, OCR 파이프라인을 실행한다: page.get\_pixmap()으로 고해상도 이미지를 생성하고, OpenCV로 전처리한 후, pytesseract로 텍스트를 추출한다.  
  5. 모든 페이지에서 추출된 구조화된 결과를 취합하여 최종 결과물을 생성한다.

### **5.2. 미래 전망: 문서 파운데이션 모델의 부상**

본 보고서에서 분석한 라이브러리들은 근본적으로 기하학적 규칙과 좌표에 기반한 파싱 방식을 사용한다. 이는 현재 매우 효과적이지만, 미래에는 새로운 패러다임이 부상할 것으로 예상된다.

**LayoutLM**이나 **Donut**과 같은 레이아웃 인식 트랜스포머 모델은 이러한 규칙 기반 시스템의 한계를 넘어서는 것을 목표로 한다.44 이 모델들의 핵심적인 차이점은 레이아웃과 텍스트 사이의 *의미론적 관계*를 학습한다는 것이다. 예를 들어, 인보이스의 특정 위치에 있는 숫자가 '총액'일 가능성이 높은 이유를 단순히 좌표 규칙 때문이 아니라, 수백만 개의 문서를 학습하며 얻은 맥락적 이해를 통해 파악한다.54

이러한 모델들은 아직 로컬 환경에서 미세 조정하고 배포하기에 복잡성이 높지만, 문서 이해 기술의 미래를 대표한다. 다양한 레이아웃 변형에 대해 규칙 기반 시스템보다 훨씬 유연하게 대처하여 템플릿별로 코드를 작성해야 하는 필요성을 줄여줄 것으로 기대된다. 따라서 현재는 본 보고서에서 제시한 클래식 라이브러리 기반의 파이프라인이 가장 현실적이고 강력한 솔루션이지만, 장기적으로는 AI 기반의 엔드투엔드 문서 이해 모델이 이 분야를 주도하게 될 것이다.

#### **Works cited**

1. pymupdf/PyMuPDF: PyMuPDF is a high performance ... \- GitHub, accessed on October 13, 2025, [https://github.com/pymupdf/PyMuPDF](https://github.com/pymupdf/PyMuPDF)  
2. MuPDF: The ultimate library for managing PDF documents, accessed on October 13, 2025, [https://mupdf.com/](https://mupdf.com/)  
3. Features Comparison \- PyMuPDF documentation, accessed on October 13, 2025, [https://pymupdf.readthedocs.io/en/latest/about.html](https://pymupdf.readthedocs.io/en/latest/about.html)  
4. PDFPlumber – Extract & Process PDF Data Easily, accessed on October 13, 2025, [https://www.pdfplumber.com/](https://www.pdfplumber.com/)  
5. pdfplumber · PyPI, accessed on October 13, 2025, [https://pypi.org/project/pdfplumber/](https://pypi.org/project/pdfplumber/)  
6. Using PDFPlumber for PDF data extraction \- GitHub, accessed on October 13, 2025, [https://github.com/eriston/PDFPlumber-data-extraction](https://github.com/eriston/PDFPlumber-data-extraction)  
7. Camelot Documentation \- Read the Docs, accessed on October 13, 2025, [https://readthedocs.org/projects/camelot-py/downloads/pdf/master/](https://readthedocs.org/projects/camelot-py/downloads/pdf/master/)  
8. Camelot: PDF Table Extraction for Humans — Camelot 1.0.9 ..., accessed on October 13, 2025, [https://camelot-py.readthedocs.io/](https://camelot-py.readthedocs.io/)  
9. Ultimate guide to Python Tesseract \- Nutrient SDK, accessed on October 13, 2025, [https://www.nutrient.io/blog/tesseract-python-guide/](https://www.nutrient.io/blog/tesseract-python-guide/)  
10. How to extract text from a PDF using PyMuPDF and Python \- Nutrient SDK, accessed on October 13, 2025, [https://www.nutrient.io/blog/extract-text-from-pdf-pymupdf/](https://www.nutrient.io/blog/extract-text-from-pdf-pymupdf/)  
11. Preprocessing image for Tesseract OCR with OpenCV \- Stack Overflow, accessed on October 13, 2025, [https://stackoverflow.com/questions/28935983/preprocessing-image-for-tesseract-ocr-with-opencv](https://stackoverflow.com/questions/28935983/preprocessing-image-for-tesseract-ocr-with-opencv)  
12. A Comparison of python libraries for PDF Data Extraction for text, images and tables, accessed on October 13, 2025, [https://pradeepundefned.medium.com/a-comparison-of-python-libraries-for-pdf-data-extraction-for-text-images-and-tables-c75e5dbcfef8](https://pradeepundefned.medium.com/a-comparison-of-python-libraries-for-pdf-data-extraction-for-text-images-and-tables-c75e5dbcfef8)  
13. Which is faster at extracting text from a PDF: PyMuPDF or PyPDF2? : r/learnpython \- Reddit, accessed on October 13, 2025, [https://www.reddit.com/r/learnpython/comments/11ltkqz/which\_is\_faster\_at\_extracting\_text\_from\_a\_pdf/](https://www.reddit.com/r/learnpython/comments/11ltkqz/which_is_faster_at_extracting_text_from_a_pdf/)  
14. Appendix 4: Performance Comparison Methodology \- PyMuPDF documentation, accessed on October 13, 2025, [https://pymupdf.readthedocs.io/en/latest/app4.html](https://pymupdf.readthedocs.io/en/latest/app4.html)  
15. Tutorial \- PyMuPDF documentation, accessed on October 13, 2025, [https://pymupdf.readthedocs.io/en/latest/tutorial.html](https://pymupdf.readthedocs.io/en/latest/tutorial.html)  
16. The Basics \- PyMuPDF documentation, accessed on October 13, 2025, [https://pymupdf.readthedocs.io/en/latest/the-basics.html](https://pymupdf.readthedocs.io/en/latest/the-basics.html)  
17. Text \- PyMuPDF documentation, accessed on October 13, 2025, [https://pymupdf.readthedocs.io/en/latest/recipes-text.html](https://pymupdf.readthedocs.io/en/latest/recipes-text.html)  
18. Text Extraction Using PyMuPDF \- Medium, accessed on October 13, 2025, [https://medium.com/@pymupdf/text-extraction-using-pymupdf-4572b97c6a58](https://medium.com/@pymupdf/text-extraction-using-pymupdf-4572b97c6a58)  
19. PyMuPDF Documentation \- Read the Docs, accessed on October 13, 2025, [https://buildmedia.readthedocs.org/media/pdf/pymupdf/latest/pymupdf.pdf](https://buildmedia.readthedocs.org/media/pdf/pymupdf/latest/pymupdf.pdf)  
20. PyMuPDF4LLM \- PyMuPDF documentation \- Read the Docs, accessed on October 13, 2025, [https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/)  
21. How do I extract a table from a pdf file using pymupdf \[closed\] \- Stack Overflow, accessed on October 13, 2025, [https://stackoverflow.com/questions/56155676/how-do-i-extract-a-table-from-a-pdf-file-using-pymupdf](https://stackoverflow.com/questions/56155676/how-do-i-extract-a-table-from-a-pdf-file-using-pymupdf)  
22. Page \- PyMuPDF documentation, accessed on October 13, 2025, [https://pymupdf.readthedocs.io/en/latest/page.html](https://pymupdf.readthedocs.io/en/latest/page.html)  
23. Extracting Tables from PDFs with PyMuPDF | Artifex, accessed on October 13, 2025, [https://artifex.com/blog/extracting-tables-from-pdfs-with-pymupdf](https://artifex.com/blog/extracting-tables-from-pdfs-with-pymupdf)  
24. jsvine/pdfplumber: Plumb a PDF for detailed information ... \- GitHub, accessed on October 13, 2025, [https://github.com/jsvine/pdfplumber](https://github.com/jsvine/pdfplumber)  
25. pdfplumber \- PyDigger, accessed on October 13, 2025, [https://pydigger.com/pypi/pdfplumber](https://pydigger.com/pypi/pdfplumber)  
26. No Grid Lines? Extract Multi-Page PDF Invoices Easily (Python \+ PDFPlumber/PyMuPDF), accessed on October 13, 2025, [https://www.youtube.com/watch?v=zqHe8Dh\_FNI](https://www.youtube.com/watch?v=zqHe8Dh_FNI)  
27. Python Libraries to Extract Tables From PDF: A Comparison \- Unstract, accessed on October 13, 2025, [https://unstract.com/blog/extract-tables-from-pdf-python/](https://unstract.com/blog/extract-tables-from-pdf-python/)  
28. PDF Processing: PyPDF2 and pdfplumber \- Tutorial | Krython, accessed on October 13, 2025, [https://krython.com/tutorial/python/pdf-processing-pypdf2-and-pdfplumber/](https://krython.com/tutorial/python/pdf-processing-pypdf2-and-pdfplumber/)  
29. What are common use cases for pdfplumber?, accessed on October 13, 2025, [https://www.pdfplumber.com/what-are-common-use-cases-for-pdfplumber/](https://www.pdfplumber.com/what-are-common-use-cases-for-pdfplumber/)  
30. PDF invoices data extraction with pdfplumber in Python \- YouTube, accessed on October 13, 2025, [https://www.youtube.com/watch?v=ZEaEH\_aQcBE](https://www.youtube.com/watch?v=ZEaEH_aQcBE)  
31. How It Works — Camelot 1.0.9 documentation \- Read the Docs, accessed on October 13, 2025, [https://camelot-py.readthedocs.io/en/master/user/how-it-works.html](https://camelot-py.readthedocs.io/en/master/user/how-it-works.html)  
32. Advanced Usage — Camelot 1.0.9 documentation, accessed on October 13, 2025, [https://camelot-py.readthedocs.io/en/master/user/advanced.html](https://camelot-py.readthedocs.io/en/master/user/advanced.html)  
33. API Reference — Camelot 1.0.9 documentation \- Read the Docs, accessed on October 13, 2025, [https://camelot-py.readthedocs.io/en/master/api.html](https://camelot-py.readthedocs.io/en/master/api.html)  
34. How to Extract tabular data from PDF document using Camelot in Python \- Analytics Vidhya, accessed on October 13, 2025, [https://www.analyticsvidhya.com/blog/2020/08/how-to-extract-tabular-data-from-pdf-document-using-camelot-in-python/](https://www.analyticsvidhya.com/blog/2020/08/how-to-extract-tabular-data-from-pdf-document-using-camelot-in-python/)  
35. Extracting and Summarizing Tables from PDFs Using Camelot and Tabulate \- Medium, accessed on October 13, 2025, [https://medium.com/@priti.mohapatra1989/extracting-and-summarizing-tables-from-pdfs-using-camelot-and-tabulate-e620e7924841](https://medium.com/@priti.mohapatra1989/extracting-and-summarizing-tables-from-pdfs-using-camelot-and-tabulate-e620e7924841)  
36. Quickstart — Camelot 1.0.9 documentation \- Read the Docs, accessed on October 13, 2025, [https://camelot-py.readthedocs.io/en/master/user/quickstart.html](https://camelot-py.readthedocs.io/en/master/user/quickstart.html)  
37. How to extract table name along with table using camelot from pdf files using python?, accessed on October 13, 2025, [https://stackoverflow.com/questions/58219098/how-to-extract-table-name-along-with-table-using-camelot-from-pdf-files-using-py](https://stackoverflow.com/questions/58219098/how-to-extract-table-name-along-with-table-using-camelot-from-pdf-files-using-py)  
38. Extracting both tables and text from PDF using camelot : r/learnpython \- Reddit, accessed on October 13, 2025, [https://www.reddit.com/r/learnpython/comments/1gmgmhu/extracting\_both\_tables\_and\_text\_from\_pdf\_using/](https://www.reddit.com/r/learnpython/comments/1gmgmhu/extracting_both_tables_and_text_from_pdf_using/)  
39. OCR \- Optical Character Recognition \- PyMuPDF documentation, accessed on October 13, 2025, [https://pymupdf.readthedocs.io/en/latest/recipes-ocr.html](https://pymupdf.readthedocs.io/en/latest/recipes-ocr.html)  
40. Converting PDFs to Images with PyMuPDF: A Complete Guide \- Artifex Software, accessed on October 13, 2025, [https://artifex.com/blog/converting-pdfs-to-images-with-pymupdf-a-complete-guide](https://artifex.com/blog/converting-pdfs-to-images-with-pymupdf-a-complete-guide)  
41. h/pytesseract: Python-tesseract is an optical character ... \- GitHub, accessed on October 13, 2025, [https://github.com/h/pytesseract](https://github.com/h/pytesseract)  
42. Introduction to Python Pytesseract Package \- GeeksforGeeks, accessed on October 13, 2025, [https://www.geeksforgeeks.org/python/introduction-to-python-pytesseract-package/](https://www.geeksforgeeks.org/python/introduction-to-python-pytesseract-package/)  
43. Python OCR Tutorial: Tesseract, Pytesseract, and OpenCV \- Nanonets, accessed on October 13, 2025, [https://nanonets.com/blog/ocr-with-tesseract/](https://nanonets.com/blog/ocr-with-tesseract/)  
44. Donut \- Hugging Face, accessed on October 13, 2025, [https://huggingface.co/docs/transformers/en/model\_doc/donut](https://huggingface.co/docs/transformers/en/model_doc/donut)  
45. Donut: Document Understanding Transformer \- Kaggle, accessed on October 13, 2025, [https://www.kaggle.com/code/yesdeepakmittal/donut-document-understanding-transformer](https://www.kaggle.com/code/yesdeepakmittal/donut-document-understanding-transformer)  
46. How to use Donut, the document understanding Transformer for document Classification, Parsing and document Question and Answering\! | by Renix Informatics | Medium, accessed on October 13, 2025, [https://medium.com/@renix\_informatics/how-to-use-donut-the-document-understanding-transformer-for-document-classification-parsing-and-fde0c7efa3f3](https://medium.com/@renix_informatics/how-to-use-donut-the-document-understanding-transformer-for-document-classification-parsing-and-fde0c7efa3f3)  
47. Document AI: Fine-tuning Donut for document-parsing using Hugging Face Transformers, accessed on October 13, 2025, [https://www.philschmid.de/fine-tuning-donut](https://www.philschmid.de/fine-tuning-donut)  
48. PyMuPDF \- PyPI, accessed on October 13, 2025, [https://pypi.org/project/PyMuPDF/](https://pypi.org/project/PyMuPDF/)  
49. Comparison with other PDF Table Extraction libraries and tools \- GitHub, accessed on October 13, 2025, [https://github.com/camelot-dev/camelot/wiki/Comparison-with-other-PDF-Table-Extraction-libraries-and-tools](https://github.com/camelot-dev/camelot/wiki/Comparison-with-other-PDF-Table-Extraction-libraries-and-tools)  
50. I Tested 12 “Best-in-Class” PDF Table Extraction Tools, and the Results Were Appalling | by Mark Kramer | Medium, accessed on October 13, 2025, [https://medium.com/@kramermark/i-tested-12-best-in-class-pdf-table-extraction-tools-and-the-results-were-appalling-f8a9991d972e](https://medium.com/@kramermark/i-tested-12-best-in-class-pdf-table-extraction-tools-and-the-results-were-appalling-f8a9991d972e)  
51. camelot-dev/camelot: A Python library to extract tabular ... \- GitHub, accessed on October 13, 2025, [https://github.com/camelot-dev/camelot](https://github.com/camelot-dev/camelot)  
52. Power of LayoutLM for Text Extraction | Nitor Infotech, accessed on October 13, 2025, [https://www.nitorinfotech.com/blog/how-can-layoutlm-transform-text-extraction/](https://www.nitorinfotech.com/blog/how-can-layoutlm-transform-text-extraction/)  
53. Information Extraction Series Part 1 | by Tejpal Kumawat \- Medium, accessed on October 13, 2025, [https://medium.com/@tejpal.abhyuday/layoutlm-with-real-world-application-c6c09f1cc368](https://medium.com/@tejpal.abhyuday/layoutlm-with-real-world-application-c6c09f1cc368)  
54. Your ultimate guide to understanding LayoutLM \- Nanonets, accessed on October 13, 2025, [https://nanonets.com/blog/layoutlm-explained/](https://nanonets.com/blog/layoutlm-explained/)  
55. Comparing AI Extraction Methods: Traditional OCR vs. LLM Parsing \- Airparser, accessed on October 13, 2025, [https://airparser.com/blog/comparing-ai-extraction-methods-traditional-ocr-vs-llm-parsing/](https://airparser.com/blog/comparing-ai-extraction-methods-traditional-ocr-vs-llm-parsing/)