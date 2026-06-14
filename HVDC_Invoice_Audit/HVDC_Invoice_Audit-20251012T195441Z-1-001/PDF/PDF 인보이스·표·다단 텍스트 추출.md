# **PDF 인보이스·표·다단 텍스트 추출: PyMuPDF, pdfplumber, Camelot 등 도구 비교**

로컬 Python 환경에서 **인보이스**, **멀티컬럼(다단) 텍스트 문서**, **표 중심 PDF**를 효과적으로 처리하기 위해 대표적인 오픈소스 PDF 추출 도구들의 특성을 비교합니다. 주요 후보는 **PyMuPDF (fitz)**, **pdfplumber**, **Camelot**, **tabula-py**, **pytesseract** 등입니다. 각각의 도구에 대해 **레이아웃 인식 능력**, **추출 정확도와 누락률**, **속도/리소스 효율**, **문서 유형별 적합도**, **오류 시 폴백 전략**, **사용 예시 코드** 측면에서 살펴보고, 2025년 기준 유지관리 상태까지 고려한 **최적 조합**을 제시합니다.

## **주요 PDF 추출 도구 비교 (장단점)**

각 라이브러리의 강점과 약점을 아래 표로 정리합니다:

| 도구 | 장점 | 단점 |
| :---- | :---- | :---- |
| **PyMuPDF** | 매우 빠른 속도와 가벼운 메모리 사용 (텍스트 추출 속도는 PyPDF2 대비 \~15배, pdfminer.six 대비 \~35배 빠름)[\[1\]](https://www.reddit.com/r/learnpython/comments/11ltkqz/which_is_faster_at_extracting_text_from_a_pdf/#:~:text=%E2%80%A2%20%203y%20ago). 좌표 기반의 정확한 텍스트/이미지 추출 제공. 멀티컬럼 페이지 감지 기능으로 복잡한 레이아웃도 논리 구조 유지 가능[\[2\]](https://medium.com/@pymupdf/extract-text-from-a-multi-column-document-using-pymupdf-in-python-a0395ebc8e28#:~:text=One%20of%20the%20advanced%20features,and%20preserve%20its%20logical%20structure). | 표 추출 전용 기능이 없으며 사용자 구현 필요[\[3\]](https://pradeepundefned.medium.com/a-comparison-of-python-libraries-for-pdf-data-extraction-for-text-images-and-tables-c75e5dbcfef8#:~:text=PyMuPDF%20is%20a%20Python%20binding,documentation%20can%20be%20found%20here). 복잡한 레이아웃에서는 기본 추출 결과의 읽기 순서가 의도와 다를 수 있어 추가 정제가 필요[\[4\]](https://openwebtech.com/battle-of-the-pdf-titans-apache-tika-pymupdf-pdfplumber-pdf2image-and-textract/#:~:text=,text%20extraction%20with%20minimal%20fuss). |
| **pdfplumber** | PDFMiner.six 기반으로 문자 위치를 분석하여 **텍스트 블록을 재구성**, 레이아웃(컬럼, 단락, 들여쓰기 등) 보존이 우수[\[5\]](https://www.pdfplumber.com/how-does-pdfplumber-handle-text-extraction-from-pdfs/#:~:text=PDFPlumber%20offers%20a%20powerful%20solution,friendly%20text%20extraction)[\[6\]](https://www.pdfplumber.com/how-does-pdfplumber-handle-text-extraction-from-pdfs/#:~:text=Column%20Detection%20for%20Multi). **표 추출** 기능 내장 – 테이블을 데이터프레임 형태로 추출 가능. 세부 설정으로 글자 간격, 줄간격 등 튜닝 가능하여 정확도 향상[\[7\]](https://www.pdfplumber.com/how-does-pdfplumber-handle-text-extraction-from-pdfs/#:~:text=Tolerance%20Settings%20for%20Character%20and,Line%20Spacing)[\[8\]](https://www.pdfplumber.com/how-does-pdfplumber-handle-text-extraction-from-pdfs/#:~:text=A%20financial%20statement%20with%20multi,ready%20for%20analysis%20or%20integration). | Pure Python 구현으로 대용량 PDF 처리 시 **속도가 느림**(PyMuPDF 대비 상당히 느림)[\[1\]](https://www.reddit.com/r/learnpython/comments/11ltkqz/which_is_faster_at_extracting_text_from_a_pdf/#:~:text=%E2%80%A2%20%203y%20ago). 기본 추출 텍스트에서 간혹 단어 붙어짐이나 공백 오류 등 **후처리** 필요[\[9\]](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257#:~:text=first_page%20%3D%20pdf.pages,extract_table). |
| **Camelot** | **PDF 테이블 추출 특화** 도구로, 복잡한 표도 구조적으로 **정확히 추출** 가능[\[10\]](https://pradeepundefned.medium.com/a-comparison-of-python-libraries-for-pdf-data-extraction-for-text-images-and-tables-c75e5dbcfef8#:~:text=Camelot%20is%20a%20Python%20library,python%2C%20GhostScript%20%28OS%20level%20installation). **Lattice** 모드(셀 경계 선 이용)와 **Stream** 모드(공백 기반) 두 가지 방법 제공 – 다양한 표 레이아웃에 대응. 추출 결과를 Pandas DataFrame/CSV/HTML 등으로 바로 변환. 설정 파라미터가 풍부해 테이블 감지 실패 시 튜닝을 통해 개선 가능[\[11\]](https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf#:~:text=data%20retains%20the%20information%20and,requires%20a%20Java%20Runtime%20Environment). | **초기 설정 복잡** – OpenCV, Ghostscript 등 추가 설치 필요[\[10\]](https://pradeepundefned.medium.com/a-comparison-of-python-libraries-for-pdf-data-extraction-for-text-images-and-tables-c75e5dbcfef8#:~:text=Camelot%20is%20a%20Python%20library,python%2C%20GhostScript%20%28OS%20level%20installation). 표가 아닌 일반 텍스트 추출에는 부적합. 많은 파라미터로 세밀한 조정이 가능하지만 사용에 학습 곡선이 있음[\[12\]](https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf#:~:text=The%20main%20advantage%20of%20Camelot,you%20can%20improve%20the%20extraction). 또한 Camelot 자체는 최근 업데이트가 드물며(커뮤니티 포크인 pypdf\_table\_extraction 등장) 유지관리 이슈가 조금 있음[\[13\]](https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf#:~:text=aldnav%20Nov%206%2C%202024%20at,14%3A16). |
| **tabula-py** | Java 기반 Tabula의 Python 래퍼로 **표 형태 데이터 추출에 강점**[\[14\]](https://pradeepundefned.medium.com/a-comparison-of-python-libraries-for-pdf-data-extraction-for-text-images-and-tables-c75e5dbcfef8#:~:text=Tabul,for%20extracting%20tables%20from%20PDFs). Camelot 대비 설치가 간단하고 (tabula.read\_pdf() 한 줄로 사용) 기본적인 테이블 추출에 유용. **컬럼 선이 없는 표**도 Stream 방식으로 비교적 잘 추출 (일부 경우 Camelot보다 정확)[\[15\]](https://arxiv.org/html/2410.09871v1#:~:text=Fig,demonstrated%20high%20recall%20scores%20across)[\[16\]](https://arxiv.org/html/2410.09871v1#:~:text=Scientific%20Camelot%200,2974). | **Java 런타임 필요**(환경에 Java 설치되어야 동작)[\[17\]](https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf#:~:text=I%20think%20Camelot%20better%20extracts,requires%20a%20Java%20Runtime%20Environment). 추출 결과 품질은 표 구조에 따라 들쑥날쑥하며, 복잡한 표에서는 실패하거나 데이터 누락 가능[\[18\]](https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf#:~:text=per%20cells%20.%20,a%20Java%20Runtime%20Environment). Camelot처럼 상세 튜닝 옵션이 부족하여 어려운 표에 대한 융통성이 낮음. |
| **pytesseract** (OCR) | 이미지 기반 PDF나 스캔 문서를 **광학 문자 인식(OCR)**하여 텍스트 추출. 오픈소스 Tesseract 엔진으로 다국어 지원. 표 등 레이아웃에 상관없이 **사람이 읽는 수준의 문자열 추출** 가능. | **속도 느림** – 페이지 이미징 및 OCR 처리로 한 페이지당 수 초 이상 소요. 인식 오류 가능성(OCR 에러로 인한 철자 혼동 등) 있고 **레이アウト 정보 유실**: 텍스트 위치나 표 구조를 별도로 복원해야 함. 따라서 디지털 PDF의 대안 폴백 용도로 사용되며, 후처리(예: 좌표 기반 재정렬, 철자 교정)가 필요[\[19\]](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257#:~:text=package%20for%20compatibility%20with%20it,edge%20cases%20like%20handling%20images). |

**비교 요약:** PyMuPDF와 pdfplumber는 **텍스트 전체 추출**에 주로 쓰이며, 전자는 속도와 효율이 뛰어나고 후자는 레이아웃 보존에 강합니다. Camelot과 tabula-py는 **테이블 추출 전문**으로, Camelot은 조정 가능성이 높아 복잡한 표에도 대응하고 tabula-py는 간편하게 표를 뽑아내지만 유연성은 낮습니다. pytesseract는 **OCR 폴백**으로, 디지털 방식으로 읽을 수 없을 때 최후의 수단으로 사용합니다.

각 도구의 **추출 정확도** 측면에서는, **PyMuPDF**가 다양한 문서 유형에서 비교적 높은 F1 점수와 재현율을 보여 **텍스트 누락이 적고 전체적인 신뢰도**가 높다는 연구 결과가 있습니다[\[20\]](https://arxiv.org/html/2410.09871v1#:~:text=pypdfium2%2C%20Unstructured%2C%20Tabula%2C%20Camelot%2C%20as,Our%20findings%20highlight%20the)[\[21\]](https://arxiv.org/html/2410.09871v1#:~:text=Manual%20pdfminer,8507). 반면 **pdfplumber**는 복잡한 레이아웃(특히 과학 문서 등)에서 일부 텍스트를 누락하거나 순서가 흐트러지는 경향이 보고되었으나[\[22\]](https://arxiv.org/html/2410.09871v1#:~:text=Scientific%20pdfminer,9404), 일반적인 재무 보고서 등에서는 거의 모든 내용을 정확히 추출했습니다[\[23\]](https://arxiv.org/html/2410.09871v1#:~:text=Financial%20pdfminer,9354). 표 추출에서는 **문서 종류에 따라** 최적 도구가 달랐는데, 예를 들어 **정부 보고서** 같이 격자 테이블이 많은 경우 Camelot (Lattice)이 최고의 성능을 보였고[\[24\]](https://arxiv.org/html/2410.09871v1#:~:text=and%20consistency%20across%20all%20categories,Table%205), **특허나 학술 논문**처럼 표에 선이 없거나 복잡한 경우 Tabula가 상대적으로 높은 인식율을 보였습니다[\[24\]](https://arxiv.org/html/2410.09871v1#:~:text=and%20consistency%20across%20all%20categories,Table%205). **PyMuPDF**의 표 탐지 능력은 전용 도구보다는 못하지만 모든 종류의 문서에서 **고른 성능을 유지**하는 안정성이 특징입니다[\[15\]](https://arxiv.org/html/2410.09871v1#:~:text=Fig,demonstrated%20high%20recall%20scores%20across)[\[16\]](https://arxiv.org/html/2410.09871v1#:~:text=Scientific%20Camelot%200,2974). **pdfplumber**의 표 추출 기능도 재무제표 등에서는 높은 정확도를 보이며[\[25\]](https://arxiv.org/html/2410.09871v1#:~:text=Financial%20Camelot%200,2186)[\[26\]](https://arxiv.org/html/2410.09871v1#:~:text=Tender%20Camelot%200,5042), **OpenCV** 기반이 아니라서 이미지 노이즈 영향이 없는 장점이 있지만, 복잡한 표 구조 인식력은 Camelot보다 떨어질 때가 있습니다.

## **문서 유형별 추천 조합과 폴백 전략**

다음은 **인보이스**, **표 위주 문서**, **다단 텍스트 보고서** 세 가지 문서 유형에 대한 권장 도구 조합과 처리 흐름입니다 (상황별로 도구를 혼용하여 장점을 살리는 전략):

·       **인보이스 (Invoice)** – **혼합형 문서**: 회사명, 날짜, 금액 등의 텍스트 필드 \+ **행렬 형태의 품목 표**로 구성된 경우가 많습니다.

·       **텍스트 필드 추출:** pdfplumber를 추천합니다. 필드 레이블과 값이 공간적으로 구분되어 있을 때 좌표 기반으로 텍스트를 묶어주므로 주소, 총액 등의 항목을 정확히 얻을 수 있습니다. PyMuPDF도 사용할 수 있으나, PDF 구조상 필드가 칸으로 구획된 게 아니라면 개별 텍스트 블록을 직접 찾아야 해서 pdfplumber의 편의성이 높습니다.

·       **표 추출:** Camelot **Stream 모드**로 품목 리스트 테이블을 추출하는 조합이 효과적입니다[\[18\]](https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf#:~:text=per%20cells%20.%20,a%20Java%20Runtime%20Environment). 인보이스 표는 경계선이 없거나 어긋나는 경우가 많으므로, 우선 Camelot을 flavor="stream"으로 시도하고, 행 병합이나 열 분리가 잘못되었으면 split\_text=True, strip\_text='\\n' 등의 옵션을 조정해볼 수 있습니다. **폴백:** Camelot이 표를 못 찾거나 깨진다면 tabula-py로 재시도하십시오. Tabula도 내부적으로 유사한 방식(stream 기반)으로 동작하므로 대체재가 됩니다. 그래도 안 되면 pdfplumber의 extract\_table 함수를 써서 페이지 내 선분(drawing)을 활용하거나, 최후에는 PyMuPDF로 해당 영역의 텍스트들을 x좌표로 클러스터링하여 수동으로 표를 구성하는 방법이 있습니다.

* **스캔 인보이스 처리:** 인보이스가 스캔 PDF이거나 텍스트가 추출되지 않는 경우, **pytesseract OCR**을 폴백으로 적용합니다[\[19\]](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257#:~:text=package%20for%20compatibility%20with%20it,edge%20cases%20like%20handling%20images). PDF를 이미지로 변환한 후 Tesseract로 인식하며, 인식 결과는 행 단위 문자열이므로, 이후 금액 필드는 숫자 패턴으로 찾고 표는 좌표나 구분자를 기반으로 다시 테이블화하는 **후처리**가 필요합니다. OCR 단계 전후로 데이터가 유실되지 않았는지 검증하는 것도 중요합니다.  
* **표 위주의 문서** – **데이터 테이블 중심 PDF** (예: 재무제표, 보고서 부록의 통계표 등):  
  ·       **표 추출 1차:** **Camelot (Lattice 모드)**를 우선 고려합니다. 표에 명확한 셀 경계선이 있으면 flavor="lattice"로 추출하여 가장 구조적인 결과를 얻을 수 있습니다. 한 페이지에 여러 표가 있을 경우 tables \= camelot.read\_pdf(..., split\_text=True) 등을 활용하면 모든 표를 리스트로 받아 처리할 수 있습니다.  
  ·       **표 추출 2차:** 셀 경계선이 없거나 Camelot이 표 경계를 잘못 인식하는 경우 **tabula-py**로 재시도합니다. Tabula는 자동으로 표 영역을 찾아주기도 하지만, 잘못 탐지되면 area나 columns 파라미터로 표 범위를 지정해 정확도를 높일 수 있습니다. 실험 결과에 따르면 줄이 없는 복잡한 표에서는 Tabula가 Camelot보다 높은 **검출율**을 보인 사례도 있습니다[\[27\]](https://arxiv.org/html/2410.09871v1#:~:text=Fig,Table%205).  
* **추가 폴백:** Camelot/Tabula 모두 실패하는 극단적인 경우(예: 셀 내용에 줄바꿈이 많아 행분리가 안 되는 경우), **pdfplumber**를 이용해 해당 페이지의 모든 텍스트 좌표를 가져와 수작업으로 셀을 구성할 수 있습니다. pdfplumber는 page.extract\_table()로 간단한 표를 뽑거나, 복잡한 경우 page.lines (페이지 내 선 좌표)와 page.chars (개별 문자 정보)로 세밀한 제어가 가능합니다. 최종적으로도 표 데이터가 어긋난다면, **셀 병합/분할 후처리**를 스크립트로 수행하거나 수동 보정해야 합니다. 또한 표가 **여러 페이지에 걸쳐있는 경우** Camelot이나 Tabula는 각각의 페이지별 표로 인식하므로, 추출 후 **다음 페이지 표 머리글을 감안하여 데이터 연결** 작업을 해주어야 합니다.  
* **다단 텍스트 보고서** – **멀티컬럼 구조의 본문이 많은 PDF** (예: 학술지 논문, 잡지 기사, 제품 매뉴얼 등):  
  ·       **텍스트 추출:** **PyMuPDF** \+ 전용 멀티컬럼 유틸리티 또는 **pdfplumber** 튜닝으로 접근합니다. 멀티컬럼 레이아웃의 경우 추출 도구가 한 컬럼의 끝에서 바로 다음 컬럼의 동일한 행을 이어붙이거나, 순서가 뒤섞이는 문제를 주의해야 합니다[\[28\]](https://arxiv.org/html/2410.09871v1#:~:text=2). PyMuPDF는 MuPDF 엔진의 **텍스트 블록 탐지 기능**을 통해 컬럼을 구분하는 스크립트를 제공하며, 이를 활용하면 각 컬럼 별로 텍스트를 따로 추출해 논리 순서를 유지할 수 있습니다[\[2\]](https://medium.com/@pymupdf/extract-text-from-a-multi-column-document-using-pymupdf-in-python-a0395ebc8e28#:~:text=One%20of%20the%20advanced%20features,and%20preserve%20its%20logical%20structure)[\[29\]](https://medium.com/@pymupdf/extract-text-from-a-multi-column-document-using-pymupdf-in-python-a0395ebc8e28#:~:text=import%20pymupdf%20from%20multi_column%20import,column_boxes). pdfplumber도 기본적으로 X 좌표를 분석해 **컬럼을 인식**하므로 텍스트가 섞이지 않지만[\[30\]](https://www.pdfplumber.com/how-does-pdfplumber-handle-text-extraction-from-pdfs/#:~:text=PDFPlumber%20intelligently%20analyzes%20the%20X,preserving%20column%20structure%2C%20PDFPlumber%20ensures), 필요하면 x\_tolerance, y\_tolerance 등을 조정해 컬럼 간 간격을 인지시키는 방법이 있습니다. 추출 후에는 각 컬럼 텍스트를 순서대로 합치는 작업이 필요할 수 있습니다 (예: 좌-\>우 컬럼 순으로).  
  ·       **레이아웃 유지 및 후처리:** 멀티컬럼 문서에서는 쪽글, 캡션 등이 본문 사이에 끼어들어 추출되기도 합니다. pdfplumber나 PyMuPDF 모두 이런 요소를 완벽히 배제하지는 못하므로, 예컨대 **폰트 크기나 위치 기준으로 본문과 주석을 구분**하는 후처리를 고려해야 합니다. 또한 단락이 여러 컬럼에 걸쳐 이어지는 경우, 각 컬럼에서 얻은 텍스트를 적절히 줄바꿈 등으로 연결해 주어야 합니다. **OCR 폴백:** 만약 멀티컬럼 문서가 이미지로만 되어 있다면, 페이지를 좌우 컬럼 단위로 잘라서 pytesseract로 각각 OCR 인식한 후, 결과를 컬럼 순서에 맞게 합치는 전략을 사용할 수 있습니다. 이처럼 복잡한 레이아웃일수록 1차적으로 **디지털 텍스트 추출**을 시도하고, 부득이한 경우에만 OCR을 적용하는 것이 효율적입니다.

위 조합들을 종합하면, **디지털 PDF**의 경우 **“PyMuPDF/pdfplumber \+ Camelot”** 조합이 많은 상황에 안정적입니다. 즉, **텍스트는 PyMuPDF**로 빠르게 뽑고 **표는 Camelot**으로 정교하게 추출하는 방식입니다[\[31\]](https://openwebtech.com/battle-of-the-pdf-titans-apache-tika-pymupdf-pdfplumber-pdf2image-and-textract/#:~:text=)[\[32\]](https://openwebtech.com/battle-of-the-pdf-titans-apache-tika-pymupdf-pdfplumber-pdf2image-and-textract/#:~:text=When%20precision%20matters%2C%20pdfplumber%20steps,get%20exactly%20what%20you%20need). 필요 시 pdfplumber로 보완하여 레이아웃을 검증하고, **OCR (pytesseract)**는 최후의 수단으로만 사용합니다[\[33\]](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257#:~:text=,edge%20cases%20like%20handling%20images). 이러한 하이브리드 파이프라인은 속도와 정확도를 균형 있게 달성하며, 2025년 시점에서도 각 라이브러리의 활발한 유지보수로 신뢰성 있게 운영할 수 있습니다 (PyMuPDF, pdfplumber는 지속 업데이트 중이고 Camelot도 안정 버전으로 널리 사용됨).

## **PDF 추출 파이프라인 예시 코드**

아래는 **인보이스 PDF**를 예로 들어, 위에서 설명한 도구들을 조합하는 **샘플 파이프라인 코드**입니다. PDF에서 텍스트를 추출하고, 표를 별도로 감지하며, 필요시 OCR 폴백을 수행하는 단계를 보여줍니다:

import fitz  \# PyMuPDF  
 import pdfplumber  
 import camelot  
 import tabula  
 from pdf2image import convert\_from\_path  
 import pytesseract

 file\_path \= "invoice.pdf"

 \# 1\. 텍스트 추출: 우선 pdfplumber로 시도  
 text\_pages \= \[\]  
 with pdfplumber.open(file\_path) as pdf:  
 	for page in pdf.pages:  
     	text \= page.extract\_text()  
     	if text:  
             text\_pages.append(text)

 \# 1-2. OCR 폴백: 만약 pdfplumber로 추출한 텍스트가 거의 없으면 (스캔본으로 추정)  
 if len(text\_pages) \== 0 or sum(len(t) for t in text\_pages) \< 10:  
 	text\_pages \= \[\]  \# 초기화  
     pages\_images \= convert\_from\_path(file\_path)	\# PDF 페이지를 PIL 이미지 리스트로 변환  
 	for img in pages\_images:  
     	ocr\_text \= pytesseract.image\_to\_string(img, lang="eng")  \# 필요한 경우 한국어: lang="kor"  
         text\_pages.append(ocr\_text)

 \# 2\. 표 추출: Camelot으로 시도  
 tables\_dfs \= \[\]  
 try:  
 	tables \= camelot.read\_pdf(file\_path, pages="all", flavor="stream")  
 	for t in tables:  
         tables\_dfs.append(t.df)  \# 각 페이지의 표를 DataFrame으로 저장  
 except Exception as e:  
 	\# Camelot 실패 시 tabula-py로 폴백  
 	try:  
     	tables \= tabula.read\_pdf(file\_path, pages="all", multiple\_tables=True)  
         tables\_dfs.extend(tables)  \# tabula 결과는 곧바로 DataFrame 리스트  
 	except Exception as e2:  
         tables\_dfs \= \[\]

 \# 3\. 추출 결과 활용 예시  
 full\_text \= "\\n".join(text\_pages)  
 print("Extracted text sample:", full\_text\[:100\], "...")  \# 추출된 텍스트 일부 출력  
 if tables\_dfs:  
     print("First table preview:")  
     print(tables\_dfs\[0\].head())  \# 첫 번째 표 데이터 미리보기

**코드 설명:** 먼저 pdfplumber로 전체 페이지의 텍스트를 추출하고, 내용이 없으면 pdf2image로 페이지를 이미지화한 뒤 pytesseract로 OCR을 수행합니다. 그 다음 camelot을 이용해 모든 페이지의 표를 추출하며, 오류가 발생하면 tabula-py로 대체합니다. 최종적으로 full\_text 변수에 문서의 전체 텍스트가 저장되고 tables\_dfs 리스트에 각 표의 데이터프레임이 저장됩니다. 실제 활용 시 인보이스의 헤더/필드 정보는 full\_text에서 키워드 검색이나 정규식으로 찾아내고, 표 데이터는 tables\_dfs에서 필요한 부분을 처리하면 됩니다.

※ **추가 참고:** 멀티컬럼 문서를 처리할 때는 위 코드에서 텍스트 추출 부분을 PyMuPDF로 대체하고, fitz.Page.get\_textblocks() 등을 이용해 컬럼별로 텍스트를 나누는 식으로 응용할 수 있습니다. 또한 실무에서는 **예외 상황별로 세분화된 폴백** (예: Camelot의 lattice→stream→tabula 순 시도 등)과 추출 후 **데이터 정합성 검사**(필수 필드 누락 확인 등)를 통해 안정성을 높이는 것이 좋습니다.

결론적으로, 하나의 라이브러리로 모든 PDF를 완벽하게 처리하기는 어렵기 때문에 각 도구의 장점을 살린 **혼합 활용**이 중요합니다. PyMuPDF와 pdfplumber로 텍스트 정확도와 레이아웃을 확보하고, Camelot/tabula로 표 구조를 가져오며, Tesseract로 OCR 폴백을 구현하는 방식이 2025년 현재까지도 가장 실용적이고 유지보수-friendly한 접근입니다[\[34\]](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257#:~:text=Simple%20often%20wins,could%20completely%20change%20the%20results)[\[33\]](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257#:~:text=,edge%20cases%20like%20handling%20images). 이 조합을 통해 인보이스 같은 반구조화 문서부터 복잡한 보고서까지 폭넓게 대응할 수 있습니다.

**Sources:** 주요 내용은 PDF 파싱 도구들의 공식 문서 및 성능 평가 연구[\[20\]](https://arxiv.org/html/2410.09871v1#:~:text=pypdfium2%2C%20Unstructured%2C%20Tabula%2C%20Camelot%2C%20as,Our%20findings%20highlight%20the)[\[24\]](https://arxiv.org/html/2410.09871v1#:~:text=and%20consistency%20across%20all%20categories,Table%205), 개발자 블로그[\[31\]](https://openwebtech.com/battle-of-the-pdf-titans-apache-tika-pymupdf-pdfplumber-pdf2image-and-textract/#:~:text=)[\[2\]](https://medium.com/@pymupdf/extract-text-from-a-multi-column-document-using-pymupdf-in-python-a0395ebc8e28#:~:text=One%20of%20the%20advanced%20features,and%20preserve%20its%20logical%20structure), 기술 미디엄 글[\[35\]](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257#:~:text=textract%20%280,capabilities%2C%20minor%20formatting%20variations)[\[36\]](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257#:~:text=Context%20matters%20more%20than%20raw,Most) 등을 인용하여 작성되었습니다.

---

[\[1\]](https://www.reddit.com/r/learnpython/comments/11ltkqz/which_is_faster_at_extracting_text_from_a_pdf/#:~:text=%E2%80%A2%20%203y%20ago) Which is faster at extracting text from a PDF: PyMuPDF or PyPDF2? : r/learnpython

[https://www.reddit.com/r/learnpython/comments/11ltkqz/which\_is\_faster\_at\_extracting\_text\_from\_a\_pdf/](https://www.reddit.com/r/learnpython/comments/11ltkqz/which_is_faster_at_extracting_text_from_a_pdf/)

[\[2\]](https://medium.com/@pymupdf/extract-text-from-a-multi-column-document-using-pymupdf-in-python-a0395ebc8e28#:~:text=One%20of%20the%20advanced%20features,and%20preserve%20its%20logical%20structure) [\[29\]](https://medium.com/@pymupdf/extract-text-from-a-multi-column-document-using-pymupdf-in-python-a0395ebc8e28#:~:text=import%20pymupdf%20from%20multi_column%20import,column_boxes) Extract Text From a Multi-Column Document | Medium

[https://medium.com/@pymupdf/extract-text-from-a-multi-column-document-using-pymupdf-in-python-a0395ebc8e28](https://medium.com/@pymupdf/extract-text-from-a-multi-column-document-using-pymupdf-in-python-a0395ebc8e28)

[\[3\]](https://pradeepundefned.medium.com/a-comparison-of-python-libraries-for-pdf-data-extraction-for-text-images-and-tables-c75e5dbcfef8#:~:text=PyMuPDF%20is%20a%20Python%20binding,documentation%20can%20be%20found%20here) [\[10\]](https://pradeepundefned.medium.com/a-comparison-of-python-libraries-for-pdf-data-extraction-for-text-images-and-tables-c75e5dbcfef8#:~:text=Camelot%20is%20a%20Python%20library,python%2C%20GhostScript%20%28OS%20level%20installation) [\[14\]](https://pradeepundefned.medium.com/a-comparison-of-python-libraries-for-pdf-data-extraction-for-text-images-and-tables-c75e5dbcfef8#:~:text=Tabul,for%20extracting%20tables%20from%20PDFs) A Comparison of python libraries for PDF Data Extraction for text, images and tables | by Pradeep Bansal | Medium

[https://pradeepundefned.medium.com/a-comparison-of-python-libraries-for-pdf-data-extraction-for-text-images-and-tables-c75e5dbcfef8](https://pradeepundefned.medium.com/a-comparison-of-python-libraries-for-pdf-data-extraction-for-text-images-and-tables-c75e5dbcfef8)

[\[4\]](https://openwebtech.com/battle-of-the-pdf-titans-apache-tika-pymupdf-pdfplumber-pdf2image-and-textract/#:~:text=,text%20extraction%20with%20minimal%20fuss) [\[31\]](https://openwebtech.com/battle-of-the-pdf-titans-apache-tika-pymupdf-pdfplumber-pdf2image-and-textract/#:~:text=) [\[32\]](https://openwebtech.com/battle-of-the-pdf-titans-apache-tika-pymupdf-pdfplumber-pdf2image-and-textract/#:~:text=When%20precision%20matters%2C%20pdfplumber%20steps,get%20exactly%20what%20you%20need) Battle of the PDF Titans: Apache Tika, PyMuPDF, pdfplumber, pdf2image, and Textract \- OpenWeb Technologies

[https://openwebtech.com/battle-of-the-pdf-titans-apache-tika-pymupdf-pdfplumber-pdf2image-and-textract/](https://openwebtech.com/battle-of-the-pdf-titans-apache-tika-pymupdf-pdfplumber-pdf2image-and-textract/)

[\[5\]](https://www.pdfplumber.com/how-does-pdfplumber-handle-text-extraction-from-pdfs/#:~:text=PDFPlumber%20offers%20a%20powerful%20solution,friendly%20text%20extraction) [\[6\]](https://www.pdfplumber.com/how-does-pdfplumber-handle-text-extraction-from-pdfs/#:~:text=Column%20Detection%20for%20Multi) [\[7\]](https://www.pdfplumber.com/how-does-pdfplumber-handle-text-extraction-from-pdfs/#:~:text=Tolerance%20Settings%20for%20Character%20and,Line%20Spacing) [\[8\]](https://www.pdfplumber.com/how-does-pdfplumber-handle-text-extraction-from-pdfs/#:~:text=A%20financial%20statement%20with%20multi,ready%20for%20analysis%20or%20integration) [\[30\]](https://www.pdfplumber.com/how-does-pdfplumber-handle-text-extraction-from-pdfs/#:~:text=PDFPlumber%20intelligently%20analyzes%20the%20X,preserving%20column%20structure%2C%20PDFPlumber%20ensures) How does PDFPlumber handle text extraction from PDFs? \- PDFPlumber

[https://www.pdfplumber.com/how-does-pdfplumber-handle-text-extraction-from-pdfs/](https://www.pdfplumber.com/how-does-pdfplumber-handle-text-extraction-from-pdfs/)

[\[9\]](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257#:~:text=first_page%20%3D%20pdf.pages,extract_table) [\[19\]](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257#:~:text=package%20for%20compatibility%20with%20it,edge%20cases%20like%20handling%20images) [\[33\]](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257#:~:text=,edge%20cases%20like%20handling%20images) [\[34\]](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257#:~:text=Simple%20often%20wins,could%20completely%20change%20the%20results) [\[35\]](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257#:~:text=textract%20%280,capabilities%2C%20minor%20formatting%20variations) [\[36\]](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257#:~:text=Context%20matters%20more%20than%20raw,Most) I Tested 7 Python PDF Extractors So You Don’t Have To (2025 Edition) | by Aman Kumar | Medium

[https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257)

[\[11\]](https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf#:~:text=data%20retains%20the%20information%20and,requires%20a%20Java%20Runtime%20Environment) [\[12\]](https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf#:~:text=The%20main%20advantage%20of%20Camelot,you%20can%20improve%20the%20extraction) [\[13\]](https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf#:~:text=aldnav%20Nov%206%2C%202024%20at,14%3A16) [\[17\]](https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf#:~:text=I%20think%20Camelot%20better%20extracts,requires%20a%20Java%20Runtime%20Environment) [\[18\]](https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf#:~:text=per%20cells%20.%20,a%20Java%20Runtime%20Environment) python \- tabula vs camelot for table extraction from PDF \- Stack Overflow

[https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf](https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf)

[\[15\]](https://arxiv.org/html/2410.09871v1#:~:text=Fig,demonstrated%20high%20recall%20scores%20across) [\[16\]](https://arxiv.org/html/2410.09871v1#:~:text=Scientific%20Camelot%200,2974) [\[20\]](https://arxiv.org/html/2410.09871v1#:~:text=pypdfium2%2C%20Unstructured%2C%20Tabula%2C%20Camelot%2C%20as,Our%20findings%20highlight%20the) [\[21\]](https://arxiv.org/html/2410.09871v1#:~:text=Manual%20pdfminer,8507) [\[22\]](https://arxiv.org/html/2410.09871v1#:~:text=Scientific%20pdfminer,9404) [\[23\]](https://arxiv.org/html/2410.09871v1#:~:text=Financial%20pdfminer,9354) [\[24\]](https://arxiv.org/html/2410.09871v1#:~:text=and%20consistency%20across%20all%20categories,Table%205) [\[25\]](https://arxiv.org/html/2410.09871v1#:~:text=Financial%20Camelot%200,2186) [\[26\]](https://arxiv.org/html/2410.09871v1#:~:text=Tender%20Camelot%200,5042) [\[27\]](https://arxiv.org/html/2410.09871v1#:~:text=Fig,Table%205) [\[28\]](https://arxiv.org/html/2410.09871v1#:~:text=2) A Comparative Study of PDF Parsing Tools Across Diverse Document Categories

[https://arxiv.org/html/2410.09871v1](https://arxiv.org/html/2410.09871v1)

