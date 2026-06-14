Python
# Python 3.11 / pandas 2.2 / openpyxl 3.1
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.styles.colors import Color
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter

def apply_professional_excel_style(df: pd.DataFrame, file_path: str, sheet_name: str = "Sheet1", title: str = None):
    """
    Pandas DataFrame을 전문적인 스타일의 Excel 테이블로 저장합니다.

    Args:
        df (pd.DataFrame): 스타일을 적용할 DataFrame.
        file_path (str): 저장할 Excel 파일 경로 (예: "C:/Data/styled_report.xlsx").
        sheet_name (str): 데이터를 작성할 시트 이름.
        title (str, optional): Excel 파일에 추가할 제목. 기본값은 None.
    """
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        # 1. DataFrame을 Excel에 쓰기 (헤더와 인덱스는 나중에 수동으로 추가하여 스타일링)
        # 제목이 있을 경우, DataFrame 시작 행을 조정합니다.
        start_row_data = 1 if title else 0
        df.to_excel(writer, sheet_name=sheet_name, startrow=start_row_data + 1, index=False, header=False)

        # Workbook 및 Sheet 객체 가져오기
        book = writer.book
        sheet = writer.sheets[sheet_name]

        # 2. 제목 추가 및 스타일링
        if title:
            sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=df.shape[1])
            title_cell = sheet.cell(row=1, column=1, value=title)
            title_cell.font = Font(name='Calibri', size=16, bold=True, color='000000')
            title_cell.alignment = Alignment(horizontal='center', vertical='center')

        # 3. 헤더 추가 및 스타일링
        header_row = start_row_data + 1
        header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='002D62', end_color='002D62', fill_type='solid')
        thin_white_border = Border(left=Side(style='thin', color='FFFFFF'),
                                   right=Side(style='thin', color='FFFFFF'),
                                   top=Side(style='thin', color='FFFFFF'),
                                   bottom=Side(style='thin', color='FFFFFF'))

        for col_num, value in enumerate(df.columns, 1):
            cell = sheet.cell(row=header_row, column=col_num, value=value)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin_white_border
            # 컬럼 너비 자동 조정 (데이터 길이에 따라)
            sheet.column_dimensions[get_column_letter(col_num)].width = max(len(str(value)), 10) + 2

        # 4. 인덱스 (첫 번째 열) 스타일링 (필요시)
        # 여기서는 '입고월' 컬럼을 인덱스처럼 스타일링하는 예시를 보여줍니다.
        # df에 인덱스가 포함되어 있다면 df.to_excel(index=True)로 변경하고 해당 컬럼을 스타일링합니다.
        index_col_num = 1 # '입고월'이 첫 번째 컬럼이라고 가정
        index_font = Font(name='Calibri', size=11, bold=True, color='000000')
        index_fill = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')
        
        for row_num in range(header_row + 1, sheet.max_row + 1):
            cell = sheet.cell(row=row_num, column=index_col_num)
            cell.font = index_font
            cell.fill = index_fill
            cell.alignment = Alignment(horizontal='left', vertical='center')
            cell.border = Border(left=Side(style='thin', color='CCCCCC'),
                                right=Side(style='thin', color='CCCCCC'),
                                top=Side(style='thin', color='CCCCCC'),
                                bottom=Side(style='thin', color='CCCCCC'))

        # 5. 데이터 부분 서식 지정 (예: 격자 행 배경색, 숫자 서식)
        data_border = Border(left=Side(style='thin', color='CCCCCC'),
                             right=Side(style='thin', color='CCCCCC'),
                             top=Side(style='thin', color='CCCCCC'),
                             bottom=Side(style='thin', color='CCCCCC'))

        for row_num in range(header_row + 1, sheet.max_row + 1):
            # 격자 행 배경색
            row_fill = PatternFill(start_color='F2F2F2', end_color='F2F2F2', fill_type='solid') if row_num % 2 == 0 else PatternFill(fill_type=None)
            for col_num in range(1, sheet.max_column + 1):
                cell = sheet.cell(row=row_num, column=col_num)
                cell.fill = row_fill
                cell.border = data_border
                # 숫자 서식 (예시: 정수형 데이터에 쉼표 스타일 적용)
                if isinstance(cell.value, (int, float)):
                    cell.number_format = '#,##0' # 정수형
                    if isinstance(cell.value, float) and cell.value % 1 != 0:
                        cell.number_format = '#,##0.00' # 소수점 2자리

        # 6. 필터 추가
        sheet.auto_filter.ref = f"A{header_row}:{get_column_letter(df.shape[1])}{sheet.max_row}"
        
        # 7. 틀 고정 (헤더 행)
        sheet.freeze_panes = sheet.cell(row=header_row + 1, column=1)

    print(f"Excel 파일이 '{file_path}'에 성공적으로 저장되었습니다.")

# 예시 DataFrame (사용자 제공 데이터 기반)
data = {
    '입고월': ['2023-02', '2023-03', '2023-04', '2023-05', '2023-06', '2023-07', '2023-08', '2023-09', '2023-10', '2023-11', '2023-12', '2024-01', '2024-02'],
    '입고_DHL WH': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '출고_DHL WH': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '누적_DHL WH': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '입고_DSV Indoor': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 73, 113],
    '출고_DSV Indoor': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '누적_DSV Indoor': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 73, 186],
    '입고_DSV Al Markaz': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8],
    '출고_DSV Al Markaz': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '누적_DSV Al Markaz': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8],
    '입고_DSV Outdoor': [36, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 68, 80],
    '출고_DSV Outdoor': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '누적_DSV Outdoor': [36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 104, 184],
    '입고_DSV MZP': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '출고_DSV MZP': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '누적_DSV MZP': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '입고_JDN MZD': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '출고_JDN MZD': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '누적_JDN MZD': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '입고_Hauler Indoor': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '출고_Hauler Indoor': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '누적_Hauler Indoor': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '입고_AAA Storage': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '출고_AAA Storage': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '누적_AAA Storage': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '입고_MOSB': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5],
    '출고_MOSB': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '누적_MOSB': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5]
}
df_sample = pd.DataFrame(data)

# 함수 호출 예시
# apply_professional_excel_style(df_sample, "C:/Users/MINKYU CHA/Desktop/창고_월별_입출고_보고서.xlsx", title="창고 월별 입출고 현황")