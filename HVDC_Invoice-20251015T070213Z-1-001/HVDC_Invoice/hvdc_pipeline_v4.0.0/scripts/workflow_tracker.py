#!/usr/bin/env python3
"""
HVDC 워크플로우 추적 시스템
Samsung C&T × ADNOC·DSV Partnership
해상운송 문서 워크플로우 자동 추적 및 상태 관리
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentStatus(Enum):
    """문서 상태 열거형"""
    NOT_PROVIDED = "NOT_PROVIDED"      # 미제공
    PROVIDED = "PROVIDED"              # 제공됨
    IN_REVIEW = "IN_REVIEW"            # 검토중
    APPROVED = "APPROVED"              # 승인됨
    SUBMITTED = "SUBMITTED"           # 제출됨
    REJECTED = "REJECTED"             # 반려됨

class RoleType(Enum):
    """역할 타입"""
    VESSEL = "Vessel/LCT"
    MAMMOET = "Mammoet"
    ARIES = "Aries"
    SAMSUNG = "Samsung"
    HM = "HM/MWS"

@dataclass
class Document:
    """문서 정보"""
    name: str
    description: str
    provider: RoleType
    consumer: Optional[RoleType]
    status: DocumentStatus
    file_path: Optional[str] = None
    created_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    confidence: float = 0.0
    notes: str = ""

@dataclass
class WorkflowStatus:
    """워크플로우 전체 상태"""
    project_id: str
    last_updated: datetime
    total_documents: int
    completed_documents: int
    pending_documents: int
    overdue_documents: int
    atlp_ready: bool
    overall_progress: float

class WorkflowTracker:
    """
    HVDC 워크플로우 추적 시스템
    
    역할별 문서 제공/생성/제출 상태를 추적하고
    누락 문서를 자동 식별하며 ATLP 제출 준비도를 체크
    """
    
    def __init__(self, project_id: str = "HVDC_2025"):
        self.project_id = project_id
        self.documents: Dict[str, Document] = {}
        self.workflow_config = self._load_workflow_config()
        self._initialize_documents()
        
    def _load_workflow_config(self) -> Dict:
        """워크플로우 설정 로드"""
        return {
            "roles": {
                "Vessel": {"priority": 1, "required_docs": ["ELC", "Tank", "SB"]},
                "Mammoet": {"priority": 2, "required_docs": ["Seq", "MS", "Fsc", "PL"]},
                "Aries": {"priority": 3, "generated_docs": ["StrBridge", "StrBow", "Intact", "Tyre7"]},
                "Samsung": {"priority": 4, "packages": True},
                "HM": {"priority": 5, "approval": True}
            },
            "critical_path": [
                "ELC", "Tank", "Seq", "MS", "StrBridge", "StrBow", "Intact", "Tyre7", "Cover", "ATLP"
            ],
            "optional_docs": ["Fsc", "SB", "PL"],
            "sla_hours": {
                "Vessel": 24,
                "Mammoet": 48,
                "Aries": 72,
                "Samsung": 12,
                "HM": 24
            }
        }
    
    def _initialize_documents(self):
        """초기 문서 구조 생성"""
        # Vessel 제공 문서
        self._add_document("ELC", "FWD/AFT Draft·Trim·GM", RoleType.VESSEL, RoleType.ARIES, DocumentStatus.NOT_PROVIDED)
        self._add_document("Tank", "Ballast Tank Arrangement & Capacity", RoleType.VESSEL, RoleType.ARIES, DocumentStatus.NOT_PROVIDED)
        self._add_document("SB", "Stability Booklet 등 기본도면", RoleType.VESSEL, RoleType.SAMSUNG, DocumentStatus.NOT_PROVIDED)
        
        # Mammoet 제공 문서
        self._add_document("Seq", "Sequence of Loading (SPMT 단계/접촉/밸러스트)", RoleType.MAMMOET, RoleType.ARIES, DocumentStatus.NOT_PROVIDED)
        self._add_document("MS", "Method Statement (Ballasting Seq 포함)", RoleType.MAMMOET, RoleType.SAMSUNG, DocumentStatus.NOT_PROVIDED)
        self._add_document("Fsc", "Final Sailing Condition", RoleType.MAMMOET, RoleType.SAMSUNG, DocumentStatus.NOT_PROVIDED)
        self._add_document("PL", "Packing List", RoleType.MAMMOET, RoleType.SAMSUNG, DocumentStatus.NOT_PROVIDED)
        
        # Aries 생성 문서
        self._add_document("StrBridge", "Steel Bridge Strength", RoleType.ARIES, RoleType.SAMSUNG, DocumentStatus.NOT_PROVIDED)
        self._add_document("StrBow", "Bow Deck Strength", RoleType.ARIES, RoleType.SAMSUNG, DocumentStatus.NOT_PROVIDED)
        self._add_document("Intact", "Intact Stability per Step", RoleType.ARIES, RoleType.SAMSUNG, DocumentStatus.NOT_PROVIDED)
        self._add_document("Tyre7", "7-타이어 스케치 계산 + ETA", RoleType.ARIES, RoleType.SAMSUNG, DocumentStatus.NOT_PROVIDED)
        
        # Samsung 패키징
        self._add_document("Cover", "Cover Note & Bundle", RoleType.SAMSUNG, RoleType.HM, DocumentStatus.NOT_PROVIDED)
        self._add_document("ATLP", "ATLP/MWS 제출", RoleType.SAMSUNG, RoleType.HM, DocumentStatus.NOT_PROVIDED)
    
    def _add_document(self, name: str, description: str, provider: RoleType, 
                     consumer: Optional[RoleType], status: DocumentStatus):
        """문서 추가"""
        self.documents[name] = Document(
            name=name,
            description=description,
            provider=provider,
            consumer=consumer,
            status=status,
            created_date=datetime.now() if status != DocumentStatus.NOT_PROVIDED else None
        )
    
    def update_document_status(self, doc_name: str, status: DocumentStatus, 
                             file_path: Optional[str] = None, notes: str = ""):
        """문서 상태 업데이트"""
        if doc_name not in self.documents:
            logger.warning(f"문서 '{doc_name}'을 찾을 수 없습니다.")
            return False
            
        doc = self.documents[doc_name]
        doc.status = status
        doc.file_path = file_path
        doc.notes = notes
        
        if status == DocumentStatus.PROVIDED:
            doc.created_date = datetime.now()
            
        logger.info(f"문서 '{doc_name}' 상태가 '{status.value}'로 업데이트되었습니다.")
        return True
    
    def get_missing_documents(self) -> List[str]:
        """누락된 문서 목록 반환"""
        missing = []
        for name, doc in self.documents.items():
            if doc.status == DocumentStatus.NOT_PROVIDED:
                missing.append(name)
        return missing
    
    def get_role_todos(self, role: RoleType) -> List[Dict]:
        """역할별 TODO 목록 생성"""
        todos = []
        
        for name, doc in self.documents.items():
            if doc.provider == role and doc.status == DocumentStatus.NOT_PROVIDED:
                todos.append({
                    "document": name,
                    "description": doc.description,
                    "priority": "HIGH" if name in self.workflow_config["critical_path"] else "MEDIUM",
                    "due_date": self._calculate_due_date(role),
                    "status": "PENDING"
                })
            elif doc.consumer == role and doc.status == DocumentStatus.PROVIDED:
                todos.append({
                    "document": name,
                    "description": f"{doc.description} 검토/처리",
                    "priority": "HIGH" if name in self.workflow_config["critical_path"] else "MEDIUM",
                    "due_date": self._calculate_due_date(role),
                    "status": "IN_PROGRESS"
                })
        
        return sorted(todos, key=lambda x: (x["priority"], x["due_date"]))
    
    def _calculate_due_date(self, role: RoleType) -> datetime:
        """역할별 마감일 계산"""
        sla_hours = self.workflow_config["sla_hours"].get(role.value.split('/')[0], 48)
        return datetime.now() + timedelta(hours=sla_hours)
    
    def check_atlp_readiness(self) -> Tuple[bool, List[str]]:
        """ATLP 제출 준비도 체크"""
        missing = []
        critical_docs = self.workflow_config["critical_path"]
        
        for doc_name in critical_docs:
            if doc_name in self.documents:
                doc = self.documents[doc_name]
                if doc.status not in [DocumentStatus.APPROVED, DocumentStatus.SUBMITTED]:
                    missing.append(doc_name)
        
        atlp_ready = len(missing) == 0
        return atlp_ready, missing
    
    def get_workflow_status(self) -> WorkflowStatus:
        """워크플로우 전체 상태 반환"""
        total = len(self.documents)
        completed = sum(1 for doc in self.documents.values() 
                       if doc.status in [DocumentStatus.APPROVED, DocumentStatus.SUBMITTED])
        pending = sum(1 for doc in self.documents.values() 
                     if doc.status in [DocumentStatus.PROVIDED, DocumentStatus.IN_REVIEW])
        overdue = sum(1 for doc in self.documents.values() 
                     if doc.due_date and doc.due_date < datetime.now() and doc.status != DocumentStatus.SUBMITTED)
        
        atlp_ready, _ = self.check_atlp_readiness()
        progress = (completed / total) * 100 if total > 0 else 0
        
        return WorkflowStatus(
            project_id=self.project_id,
            last_updated=datetime.now(),
            total_documents=total,
            completed_documents=completed,
            pending_documents=pending,
            overdue_documents=overdue,
            atlp_ready=atlp_ready,
            overall_progress=progress
        )
    
    def generate_status_report(self) -> str:
        """상태 리포트 생성"""
        status = self.get_workflow_status()
        missing_docs = self.get_missing_documents()
        atlp_ready, atlp_missing = self.check_atlp_readiness()
        
        report = f"""
# HVDC 워크플로우 상태 리포트
**프로젝트:** {self.project_id}  
**생성일:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 전체 진행률
- **전체 문서:** {status.total_documents}개
- **완료:** {status.completed_documents}개 ({status.overall_progress:.1f}%)
- **진행중:** {status.pending_documents}개
- **지연:** {status.overdue_documents}개
- **ATLP 준비도:** {'✅ 준비완료' if atlp_ready else '❌ 미완료'}

## 🚨 누락 문서
"""
        if missing_docs:
            for doc in missing_docs:
                doc_info = self.documents[doc]
                report += f"- **{doc}**: {doc_info.description} (제공자: {doc_info.provider.value})\n"
        else:
            report += "- 모든 필수 문서가 제공되었습니다.\n"
        
        if not atlp_ready:
            report += f"\n## ⚠️ ATLP 제출 대기 문서\n"
            for doc in atlp_missing:
                report += f"- **{doc}**: {self.documents[doc].description}\n"
        
        # 역할별 TODO
        report += "\n## 📋 역할별 TODO\n"
        for role in RoleType:
            todos = self.get_role_todos(role)
            if todos:
                report += f"\n### {role.value}\n"
                for todo in todos[:5]:  # 상위 5개만 표시
                    priority_icon = "🔴" if todo["priority"] == "HIGH" else "🟡"
                    report += f"- {priority_icon} {todo['document']}: {todo['description']}\n"
        
        return report
    
    def export_to_json(self, file_path: str):
        """JSON 형태로 내보내기"""
        data = {
            "project_id": self.project_id,
            "last_updated": datetime.now().isoformat(),
            "documents": {name: asdict(doc) for name, doc in self.documents.items()},
            "workflow_status": asdict(self.get_workflow_status())
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"워크플로우 데이터가 {file_path}로 내보내졌습니다.")
    
    def import_from_json(self, file_path: str):
        """JSON 형태로 가져오기"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 문서 데이터 복원
            for name, doc_data in data.get("documents", {}).items():
                if name in self.documents:
                    doc = self.documents[name]
                    doc.status = DocumentStatus(doc_data["status"])
                    doc.file_path = doc_data.get("file_path")
                    doc.notes = doc_data.get("notes", "")
                    if doc_data.get("created_date"):
                        doc.created_date = datetime.fromisoformat(doc_data["created_date"])
            
            logger.info(f"워크플로우 데이터가 {file_path}에서 로드되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"데이터 로드 실패: {e}")
            return False

def main():
    """메인 실행 함수"""
    print("🚢 HVDC 워크플로우 추적 시스템 시작")
    
    # 워크플로우 추적기 초기화
    tracker = WorkflowTracker("HVDC_2025_001")
    
    # 예시: 일부 문서 상태 업데이트
    tracker.update_document_status("ELC", DocumentStatus.PROVIDED, 
                                 file_path="/documents/ELC_v1.0.pdf", 
                                 notes="Vessel에서 제공됨")
    tracker.update_document_status("Tank", DocumentStatus.PROVIDED,
                                 file_path="/documents/Tank_Arrangement.pdf")
    
    # 상태 리포트 생성
    report = tracker.generate_status_report()
    print(report)
    
    # JSON 내보내기
    tracker.export_to_json("hvdc_workflow_status.json")
    
    # 역할별 TODO 확인
    print("\n📋 Samsung TODO:")
    samsung_todos = tracker.get_role_todos(RoleType.SAMSUNG)
    for todo in samsung_todos:
        print(f"- {todo['document']}: {todo['description']}")

if __name__ == "__main__":
    main()
