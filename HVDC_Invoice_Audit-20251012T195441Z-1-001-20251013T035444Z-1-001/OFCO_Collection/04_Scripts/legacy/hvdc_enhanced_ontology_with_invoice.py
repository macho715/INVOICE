#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HVDC 통합 온톨로지 분석 파이프라인 (인보이스 포함)
=============================================

hvdc_ontology_pipeline.py를 기반으로 인보이스 데이터를 통합하여
완전한 물류-재무 분석을 제공합니다.

주요 기능:
1. 🎯 기존 온톨로지 매핑 룰 활용 (mapping_rules_v2.4.json)
2. 💰 인보이스 데이터 통합 분석
3. 🔗 창고-인보이스 데이터 연관 분석
4. 📊 종합 재무-운영 리포트 생성
5. 🧠 온톨로지 기반 데이터 구조화

작성자: HVDC Analysis Team
최종 수정: 2025-06-22
기반: hvdc_ontology_pipeline.py
"""

import pandas as pd
import numpy as np
import os
import glob
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. ENHANCED ONTOLOGY CONFIGURATION (인보이스 클래스 추가)
# =============================================================================

class EnhancedOntologyMapper:
    """인보이스 클래스를 포함한 향상된 온톨로지 매퍼"""
    
    def __init__(self, mapping_file: str = "mapping_rules_v2.4.json"):
        """매핑 룰 로드 및 인보이스 클래스 확장"""
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                self.mapping_rules = json.load(f)
            print(f"✅ 온톨로지 매핑 룰 로드 완료: {mapping_file}")
        except FileNotFoundError:
            print(f"⚠️ 매핑 룰 파일 없음: {mapping_file}, 기본 매핑 사용")
            self.mapping_rules = self._get_default_mapping()
        
        self.namespace = self.mapping_rules.get("namespace", "http://samsung.com/project-logistics#")
        self.class_mappings = self.mapping_rules.get("class_mappings", {})
        self.property_mappings = self.mapping_rules.get("property_mappings", {})
        
        # 인보이스 관련 클래스 추가
        self._extend_for_invoice()
    
    def _extend_for_invoice(self):
        """인보이스 관련 온톨로지 클래스 확장"""
        invoice_classes = {
            "InvoiceRecord": "InvoiceRecord",
            "ShipmentOperation": "ShipmentOperation", 
            "CostStructure": "CostStructure",
            "FinancialMetrics": "FinancialMetrics",
            "OperationalEfficiency": "OperationalEfficiency"
        }
        
        self.class_mappings.update(invoice_classes)
        
        # 인보이스 속성 매핑 추가
        invoice_properties = {
            "shipment_no": {"predicate": "hasShipmentNumber", "subject_class": "InvoiceRecord"},
            "operation_month": {"predicate": "operationMonth", "subject_class": "InvoiceRecord"},
            "category": {"predicate": "shipmentCategory", "subject_class": "InvoiceRecord"},
            "total_cost": {"predicate": "totalCost", "subject_class": "CostStructure"},
            "handling_in": {"predicate": "handlingInCost", "subject_class": "CostStructure"},
            "handling_out": {"predicate": "handlingOutCost", "subject_class": "CostStructure"},
            "packages_qty": {"predicate": "packageQuantity", "subject_class": "ShipmentOperation"},
            "weight_kg": {"predicate": "weightInKg", "subject_class": "ShipmentOperation"},
            "cbm": {"predicate": "volumeInCBM", "subject_class": "ShipmentOperation"}
        }
        
        self.property_mappings.update(invoice_properties)
        
        print(f"🔗 인보이스 온톨로지 확장 완료: {len(invoice_classes)}개 클래스, {len(invoice_properties)}개 속성")
    
    def _get_default_mapping(self) -> Dict:
        """기본 매핑 룰 (인보이스 포함)"""
        return {
            "namespace": "http://samsung.com/project-logistics#",
            "class_mappings": {
                "TransportEvent": "TransportEvent",
                "StockSnapshot": "StockSnapshot", 
                "DeadStock": "DeadStock",
                "Case": "Case",
                "Warehouse": "Warehouse",
                "Site": "Site",
                "InvoiceRecord": "InvoiceRecord",
                "ShipmentOperation": "ShipmentOperation",
                "CostStructure": "CostStructure"
            },
            "property_mappings": {}
        }
    
    def map_dataframe_columns(self, df: pd.DataFrame, target_class: str) -> pd.DataFrame:
        """데이터프레임 컬럼을 온톨로지 속성에 매핑"""
        mapped_df = df.copy()
        
        # 컬럼명을 온톨로지 속성으로 변환
        column_mapping = {}
        for col in df.columns:
            if col in self.property_mappings:
                prop_info = self.property_mappings[col]
                if prop_info.get("subject_class") == target_class:
                    column_mapping[col] = prop_info["predicate"]
        
        if column_mapping:
            mapped_df = mapped_df.rename(columns=column_mapping)
            print(f"🔗 {target_class} 클래스: {len(column_mapping)}개 속성 매핑 완료")
        
        return mapped_df
    
    def export_to_ttl(self, data_dict: Dict[str, pd.DataFrame], output_file: str):
        """RDF/TTL 형식으로 데이터 출력"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # 네임스페이스 선언
                f.write(f"@prefix ex: <{self.namespace}> .\n")
                f.write("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n")
                
                # 각 클래스별 데이터 출력
                for class_name, df in data_dict.items():
                    if df.empty:
                        continue
                    
                    ontology_class = self.class_mappings.get(class_name, class_name)
                    f.write(f"# {ontology_class} instances\n")
                    
                    for idx, row in df.iterrows():
                        subject_uri = f"ex:{class_name}_{idx}"
                        f.write(f"{subject_uri} a ex:{ontology_class} ;\n")
                        
                        # 속성 출력
                        properties = []
                        for col, value in row.items():
                            if pd.notna(value):
                                prop_name = f"ex:{col}"
                                if isinstance(value, (int, float)):
                                    properties.append(f"    {prop_name} {value}")
                                elif isinstance(value, datetime):
                                    properties.append(f'    {prop_name} "{value.isoformat()}"^^xsd:dateTime')
                                else:
                                    properties.append(f'    {prop_name} "{str(value)}"')
                        
                        f.write(" ;\n".join(properties))
                        f.write(" .\n\n")
            
            print(f"📄 RDF/TTL 출력 완료: {output_file}")
            
        except Exception as e:
            print(f"❌ TTL 출력 실패: {e}")

# =============================================================================
# 2. INVOICE DATA ANALYZER
# =============================================================================

class InvoiceAnalyzer:
    """인보이스 데이터 분석기 (온톨로지 매핑 지원)"""
    
    def __init__(self, ontology_mapper: EnhancedOntologyMapper):
        self.mapper = ontology_mapper
        self.invoice_df = None
        self.processed_data = {}
        
    def load_invoice_data(self, file_path: str = 'data/HVDC WAREHOUSE_INVOICE.xlsx') -> bool:
        """인보이스 데이터 로드"""
        try:
            self.invoice_df = pd.read_excel(file_path)
            print(f"✅ 인보이스 데이터 로드 완료: {len(self.invoice_df)}건")
            
            # 데이터 전처리
            self._preprocess_invoice_data()
            return True
            
        except Exception as e:
            print(f"❌ 인보이스 데이터 로드 실패: {e}")
            return False
    
    def _preprocess_invoice_data(self):
        """인보이스 데이터 전처리"""
        if self.invoice_df is None:
            return
        
        df = self.invoice_df.copy()
        
        # 컬럼명 표준화
        column_mapping = {
            'Shipment No': 'shipment_no',
            'Operation Month': 'operation_month',
            'Category': 'category',
            'pkgs q\'ty': 'packages_qty',
            'Weight (kg)': 'weight_kg',
            'CBM': 'cbm',
            'TOTAL': 'total_cost',
            'Handling In': 'handling_in',
            'Handling out': 'handling_out',
            'Start': 'start_date',
            'Finish': 'finish_date'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df[new_col] = df[old_col]
        
        # HE 패턴 추출
        df['extracted_he_pattern'] = df['shipment_no'].str.extract(r'(HE-\d+)', expand=False)
        
        # 날짜 형식 통일
        date_columns = ['operation_month', 'start_date', 'finish_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        self.invoice_df = df
        print(f"🔄 인보이스 데이터 전처리 완료: {len(df)}건")
    
    def analyze_invoice_operations(self) -> Dict[str, Any]:
        """인보이스 운영 분석 (온톨로지 ShipmentOperation 클래스)"""
        if self.invoice_df is None:
            return {}
        
        df = self.invoice_df.copy()
        
        # 1. 월별 운영 분석
        monthly_ops = df.groupby('operation_month').agg({
            'shipment_no': 'nunique',
            'packages_qty': 'sum',
            'weight_kg': 'sum',
            'cbm': 'sum',
            'total_cost': 'sum',
            'handling_in': 'sum',
            'handling_out': 'sum'
        }).fillna(0)
        
        # 2. 카테고리별 분석
        category_analysis = df.groupby('category').agg({
            'shipment_no': 'nunique',
            'packages_qty': 'sum',
            'weight_kg': 'sum',
            'cbm': 'sum',
            'total_cost': 'sum'
        }).fillna(0)
        
        # 3. HE 패턴 분석
        he_pattern_analysis = df[df['extracted_he_pattern'].notna()].groupby('extracted_he_pattern').agg({
            'shipment_no': 'nunique',
            'packages_qty': 'sum',
            'total_cost': 'sum'
        }).fillna(0)
        
        # 4. 비용 구조 분석 (CostStructure 클래스)
        cost_structure = {
            'total_handling_in': df['handling_in'].sum(),
            'total_handling_out': df['handling_out'].sum(),
            'total_cost': df['total_cost'].sum(),
            'avg_cost_per_shipment': df['total_cost'].sum() / df['shipment_no'].nunique() if df['shipment_no'].nunique() > 0 else 0,
            'avg_cost_per_package': df['total_cost'].sum() / df['packages_qty'].sum() if df['packages_qty'].sum() > 0 else 0
        }
        
        return {
            'monthly_operations': monthly_ops,
            'category_analysis': category_analysis,
            'he_pattern_analysis': he_pattern_analysis,
            'cost_structure': cost_structure,
            'summary': {
                'total_shipments': df['shipment_no'].nunique(),
                'total_packages': df['packages_qty'].sum(),
                'total_weight_kg': df['weight_kg'].sum(),
                'total_cbm': df['cbm'].sum(),
                'total_cost': df['total_cost'].sum(),
                'unique_he_patterns': df['extracted_he_pattern'].nunique()
            }
        }
    
    def create_invoice_ontology_data(self) -> Dict[str, pd.DataFrame]:
        """인보이스 데이터를 온톨로지 클래스별로 구조화"""
        if self.invoice_df is None:
            return {}
        
        df = self.invoice_df.copy()
        ontology_data = {}
        
        # InvoiceRecord 클래스
        invoice_records = df[['shipment_no', 'operation_month', 'category', 'extracted_he_pattern']].copy()
        invoice_records = invoice_records.dropna(subset=['shipment_no'])
        ontology_data['InvoiceRecord'] = self.mapper.map_dataframe_columns(invoice_records, 'InvoiceRecord')
        
        # ShipmentOperation 클래스
        shipment_ops = df[['shipment_no', 'packages_qty', 'weight_kg', 'cbm', 'start_date', 'finish_date']].copy()
        shipment_ops = shipment_ops.dropna(subset=['shipment_no'])
        ontology_data['ShipmentOperation'] = self.mapper.map_dataframe_columns(shipment_ops, 'ShipmentOperation')
        
        # CostStructure 클래스
        cost_structures = df[['shipment_no', 'total_cost', 'handling_in', 'handling_out']].copy()
        cost_structures = cost_structures.dropna(subset=['shipment_no'])
        ontology_data['CostStructure'] = self.mapper.map_dataframe_columns(cost_structures, 'CostStructure')
        
        print(f"🧠 인보이스 온톨로지 데이터 생성 완료: {len(ontology_data)}개 클래스")
        
        return ontology_data

# =============================================================================
# 3. SIMPLIFIED WAREHOUSE ANALYZER (온톨로지 파이프라인 없이)
# =============================================================================

class SimpleWarehouseAnalyzer:
    """간단한 창고 데이터 분석기"""
    
    def __init__(self):
        self.warehouse_data = {}
    
    def load_warehouse_data(self, data_dir: str = "data") -> bool:
        """창고 데이터 로드"""
        try:
            warehouse_files = [
                'HVDC WAREHOUSE_HITACHI(HE).xlsx',
                'HVDC WAREHOUSE_HITACHI(HE-0214,0252)1.xlsx', 
                'HVDC WAREHOUSE_HITACHI(HE_LOCAL).xlsx',
                'HVDC WAREHOUSE_SIMENSE(SIM).xlsx'
            ]
            
            all_cases = []
            monthly_data = []
            
            for filename in warehouse_files:
                file_path = os.path.join(data_dir, filename)
                if os.path.exists(file_path):
                    try:
                        df = pd.read_excel(file_path, sheet_name=0)
                        
                        # Case No 추출
                        if 'Case No.' in df.columns:
                            cases = df['Case No.'].dropna().unique().tolist()
                            all_cases.extend(cases)
                            print(f"✅ {filename}: {len(cases)}개 케이스")
                        
                        # 날짜 컬럼에서 월별 데이터 추출
                        date_columns = [col for col in df.columns if self._is_date_column(df[col])]
                        
                        for _, row in df.iterrows():
                            case_no = row.get('Case No.', 'UNKNOWN')
                            qty = pd.to_numeric(row.get("Q'ty", 1), errors='coerce') or 1
                            
                            for date_col in date_columns:
                                if pd.notna(row[date_col]):
                                    date_val = pd.to_datetime(row[date_col], errors='coerce')
                                    if pd.notna(date_val):
                                        monthly_data.append({
                                            'Case_No': case_no,
                                            'Date': date_val,
                                            'YearMonth': date_val.strftime('%Y-%m'),
                                            'Location': str(date_col),
                                            'Qty': qty,
                                            'Source_File': filename
                                        })
                        
                    except Exception as e:
                        print(f"⚠️ {filename} 로드 실패: {e}")
            
            self.warehouse_data = {
                'cases': all_cases,
                'monthly_data': pd.DataFrame(monthly_data),
                'total_cases': len(all_cases)
            }
            
            print(f"✅ 창고 데이터 로드 완료: {len(all_cases)}개 케이스, {len(monthly_data)}개 이벤트")
            return True
            
        except Exception as e:
            print(f"❌ 창고 데이터 로드 실패: {e}")
            return False
    
    def _is_date_column(self, series: pd.Series) -> bool:
        """컬럼이 날짜 데이터인지 확인"""
        sample_values = series.dropna().head(10)
        if len(sample_values) == 0:
            return False
        
        date_count = 0
        for val in sample_values:
            try:
                pd.to_datetime(val)
                date_count += 1
            except:
                pass
        
        return date_count / len(sample_values) > 0.5
    
    def analyze_warehouse_operations(self) -> Dict[str, Any]:
        """창고 운영 분석"""
        if not self.warehouse_data or self.warehouse_data['monthly_data'].empty:
            return {}
        
        monthly_df = self.warehouse_data['monthly_data']
        
        # 월별 집계
        monthly_summary = monthly_df.groupby('YearMonth').agg({
            'Case_No': 'nunique',
            'Qty': 'sum'
        }).reset_index()
        monthly_summary.columns = ['YearMonth', 'Cases', 'Quantity']
        
        # 위치별 집계
        location_summary = monthly_df.groupby('Location').agg({
            'Case_No': 'nunique',
            'Qty': 'sum'
        }).reset_index()
        location_summary.columns = ['Location', 'Cases', 'Quantity']
        
        return {
            'monthly_summary': monthly_summary,
            'location_summary': location_summary,
            'summary': {
                'total_cases': self.warehouse_data['total_cases'],
                'total_events': len(monthly_df),
                'unique_months': monthly_df['YearMonth'].nunique(),
                'unique_locations': monthly_df['Location'].nunique()
            }
        }

# =============================================================================
# 4. INTEGRATED ANALYZER
# =============================================================================

class IntegratedAnalyzer:
    """통합 분석기 (창고 + 인보이스)"""
    
    def __init__(self):
        self.mapper = EnhancedOntologyMapper("mapping_rules_v2.4.json")
        self.invoice_analyzer = InvoiceAnalyzer(self.mapper)
        self.warehouse_analyzer = SimpleWarehouseAnalyzer()
        self.integrated_results = {}
    
    def load_all_data(self) -> bool:
        """모든 데이터 로드"""
        try:
            # 인보이스 데이터 로드
            if not self.invoice_analyzer.load_invoice_data():
                return False
            
            # 창고 데이터 로드
            if not self.warehouse_analyzer.load_warehouse_data():
                return False
            
            print(f"✅ 통합 데이터 로드 완료")
            return True
            
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            return False
    
    def perform_integrated_analysis(self) -> Dict[str, Any]:
        """통합 분석 수행"""
        print("🔄 통합 분석 수행 중...")
        
        # 1. 인보이스 분석
        invoice_analysis = self.invoice_analyzer.analyze_invoice_operations()
        
        # 2. 창고 분석
        warehouse_analysis = self.warehouse_analyzer.analyze_warehouse_operations()
        
        # 3. 통합 연관 분석
        integration_analysis = self._analyze_integration()
        
        self.integrated_results = {
            'invoice_analysis': invoice_analysis,
            'warehouse_analysis': warehouse_analysis,
            'integration_analysis': integration_analysis,
            'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.integrated_results
    
    def _analyze_integration(self) -> Dict[str, Any]:
        """통합 연관 분석"""
        try:
            # 시간적 중복 분석
            invoice_months = set()
            if 'monthly_operations' in self.invoice_analyzer.analyze_invoice_operations():
                monthly_ops = self.invoice_analyzer.analyze_invoice_operations()['monthly_operations']
                invoice_months = set(monthly_ops.index.strftime('%Y-%m'))
            
            warehouse_months = set()
            warehouse_analysis = self.warehouse_analyzer.analyze_warehouse_operations()
            if 'monthly_summary' in warehouse_analysis:
                warehouse_months = set(warehouse_analysis['monthly_summary']['YearMonth'])
            
            common_months = invoice_months.intersection(warehouse_months)
            
            # HE 패턴 매칭 분석
            invoice_he_patterns = set()
            if self.invoice_analyzer.invoice_df is not None:
                invoice_he_patterns = set(self.invoice_analyzer.invoice_df['extracted_he_pattern'].dropna().unique())
            
            warehouse_cases = self.warehouse_analyzer.warehouse_data.get('cases', [])
            
            # 패턴 매칭 시도
            potential_matches = 0
            for he_pattern in invoice_he_patterns:
                he_number = he_pattern.replace('HE-', '').lstrip('0')
                if he_number:
                    matching_cases = [case for case in warehouse_cases if he_number in str(case)]
                    if matching_cases:
                        potential_matches += 1
            
            return {
                'temporal_analysis': {
                    'invoice_months': len(invoice_months),
                    'warehouse_months': len(warehouse_months),
                    'common_months': len(common_months),
                    'temporal_overlap_rate': len(common_months) / max(len(invoice_months), len(warehouse_months)) * 100 if max(len(invoice_months), len(warehouse_months)) > 0 else 0
                },
                'pattern_analysis': {
                    'invoice_he_patterns': len(invoice_he_patterns),
                    'warehouse_cases': len(warehouse_cases),
                    'potential_matches': potential_matches,
                    'pattern_match_rate': potential_matches / len(invoice_he_patterns) * 100 if invoice_he_patterns else 0
                },
                'data_quality': {
                    'invoice_completeness': len(self.invoice_analyzer.invoice_df) if self.invoice_analyzer.invoice_df is not None else 0,
                    'warehouse_completeness': len(warehouse_cases)
                }
            }
            
        except Exception as e:
            print(f"❌ 통합 분석 실패: {e}")
            return {'error': str(e)}

# =============================================================================
# 5. REPORT GENERATOR
# =============================================================================

def create_comprehensive_report(analyzer: IntegratedAnalyzer, output_filename: str = None):
    """종합 리포트 생성"""
    if not analyzer.integrated_results:
        print("❌ 분석 결과가 없습니다.")
        return
    
    if output_filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'HVDC_통합_온톨로지_인보이스_리포트_{timestamp}.xlsx'
    
    try:
        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            results = analyzer.integrated_results
            
            # 1. 종합요약 시트
            summary_data = []
            
            # 인보이스 요약
            invoice_summary = results['invoice_analysis']['summary']
            summary_data.extend([
                ['📋 인보이스 분석 요약', ''],
                ['총 선적 건수', f"{invoice_summary['total_shipments']:,}건"],
                ['총 패키지 수량', f"{invoice_summary['total_packages']:,}개"],
                ['총 중량', f"{invoice_summary['total_weight_kg']:,.1f}kg"],
                ['총 부피', f"{invoice_summary['total_cbm']:,.2f}CBM"],
                ['총 비용', f"${invoice_summary['total_cost']:,.2f}"],
                ['고유 HE 패턴', f"{invoice_summary['unique_he_patterns']:,}개"],
                ['', ''],
            ])
            
            # 창고 요약
            warehouse_summary = results['warehouse_analysis']['summary']
            summary_data.extend([
                ['🏢 창고 분석 요약', ''],
                ['총 케이스', f"{warehouse_summary['total_cases']:,}개"],
                ['총 이벤트', f"{warehouse_summary['total_events']:,}건"],
                ['운영 월수', f"{warehouse_summary['unique_months']:,}개월"],
                ['운영 위치', f"{warehouse_summary['unique_locations']:,}개소"],
                ['', ''],
            ])
            
            # 통합 분석
            integration = results['integration_analysis']
            temporal = integration.get('temporal_analysis', {})
            pattern = integration.get('pattern_analysis', {})
            
            summary_data.extend([
                ['🔗 통합 분석 결과', ''],
                ['시간적 중복률', f"{temporal.get('temporal_overlap_rate', 0):.1f}%"],
                ['패턴 매칭률', f"{pattern.get('pattern_match_rate', 0):.1f}%"],
                ['공통 운영 월수', f"{temporal.get('common_months', 0):,}개월"],
                ['잠재적 매칭', f"{pattern.get('potential_matches', 0):,}건"],
            ])
            
            summary_df = pd.DataFrame(summary_data, columns=['항목', '값'])
            summary_df.to_excel(writer, sheet_name='📊 종합요약', index=False)
            
            # 2. 인보이스 월별 분석
            if 'monthly_operations' in results['invoice_analysis']:
                monthly_df = results['invoice_analysis']['monthly_operations'].reset_index()
                monthly_df.columns = ['운영월', '선적건수', '패키지수량', '중량(kg)', 'CBM', '총비용', '입고처리비', '출고처리비']
                monthly_df.to_excel(writer, sheet_name='💰 인보이스_월별_분석', index=False)
            
            # 3. 인보이스 카테고리별 분석
            if 'category_analysis' in results['invoice_analysis']:
                category_df = results['invoice_analysis']['category_analysis'].reset_index()
                category_df.columns = ['카테고리', '선적건수', '패키지수량', '중량(kg)', 'CBM', '총비용']
                category_df.to_excel(writer, sheet_name='📦 인보이스_카테고리별', index=False)
            
            # 4. 창고 월별 분석
            if 'monthly_summary' in results['warehouse_analysis']:
                warehouse_monthly_df = results['warehouse_analysis']['monthly_summary']
                warehouse_monthly_df.to_excel(writer, sheet_name='🏢 창고_월별_분석', index=False)
            
            # 5. HE 패턴 분석
            if 'he_pattern_analysis' in results['invoice_analysis']:
                he_pattern_df = results['invoice_analysis']['he_pattern_analysis'].reset_index()
                he_pattern_df.columns = ['HE패턴', '선적건수', '패키지수량', '총비용']
                he_pattern_df.to_excel(writer, sheet_name='🔗 HE패턴_분석', index=False)
        
        print(f"✅ 통합 리포트 생성 완료: {output_filename}")
        return output_filename
        
    except Exception as e:
        print(f"❌ 리포트 생성 실패: {e}")
        return None

# =============================================================================
# 6. MAIN EXECUTION
# =============================================================================

def main():
    """메인 실행 함수"""
    print("🚀 HVDC 통합 온톨로지 인보이스 분석 시스템 시작")
    print("=" * 60)
    
    # 통합 분석기 초기화
    analyzer = IntegratedAnalyzer()
    
    # 데이터 로드
    print("📂 데이터 로드 중...")
    if not analyzer.load_all_data():
        print("❌ 데이터 로드 실패. 프로그램을 종료합니다.")
        return
    
    # 통합 분석 수행
    print("\n🔄 통합 분석 수행 중...")
    results = analyzer.perform_integrated_analysis()
    
    if not results:
        print("❌ 분석 실패. 프로그램을 종료합니다.")
        return
    
    # 결과 출력
    print("\n📊 분석 결과 요약:")
    print("-" * 40)
    
    # 인보이스 요약
    invoice_summary = results['invoice_analysis']['summary']
    print(f"📋 인보이스 분석:")
    print(f"   - 총 선적 건수: {invoice_summary['total_shipments']:,}건")
    print(f"   - 총 패키지: {invoice_summary['total_packages']:,}개")
    print(f"   - 총 비용: ${invoice_summary['total_cost']:,.2f}")
    print(f"   - HE 패턴: {invoice_summary['unique_he_patterns']:,}개")
    
    # 창고 요약
    warehouse_summary = results['warehouse_analysis']['summary']
    print(f"\n🏢 창고 분석:")
    print(f"   - 총 케이스: {warehouse_summary['total_cases']:,}개")
    print(f"   - 총 이벤트: {warehouse_summary['total_events']:,}건")
    print(f"   - 운영 월수: {warehouse_summary['unique_months']:,}개월")
    
    # 통합 분석
    integration = results['integration_analysis']
    temporal = integration.get('temporal_analysis', {})
    pattern = integration.get('pattern_analysis', {})
    
    print(f"\n🔗 통합 분석:")
    print(f"   - 시간적 중복률: {temporal.get('temporal_overlap_rate', 0):.1f}%")
    print(f"   - 패턴 매칭률: {pattern.get('pattern_match_rate', 0):.1f}%")
    
    # 종합 리포트 생성
    print(f"\n📄 종합 리포트 생성 중...")
    output_file = create_comprehensive_report(analyzer)
    
    if output_file:
        print(f"\n🎉 분석 완료!")
        print(f"📁 생성된 파일: {output_file}")
        
        # 온톨로지 데이터 출력
        print(f"\n🧠 온톨로지 데이터 구조화...")
        invoice_ontology = analyzer.invoice_analyzer.create_invoice_ontology_data()
        if invoice_ontology:
            ttl_file = output_file.replace('.xlsx', '_ontology.ttl')
            analyzer.mapper.export_to_ttl(invoice_ontology, ttl_file)
    else:
        print(f"\n❌ 리포트 생성에 실패했습니다.")

if __name__ == "__main__":
    main() 