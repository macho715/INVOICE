#!/usr/bin/env python3
"""
HVDC 통합 워크플로우 시스템
NetworkX 그래프 생성 + 실시간 상태 추적 + 다중 포맷 출력

기능:
- Untitled-2.py의 그래프 구조 + 검증 로직
- WorkflowTracker 상태 관리 통합
- 실시간 상태를 그래프 색상/스타일로 반영
- PNG/SVG/DOT + 인터랙티브 HTML 출력
- Assumption 기반 검증 (ELC 없이 진행 가능)

Author: MACHO-GPT v3.4-mini
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# NetworkX 및 그래프 라이브러리
import networkx as nx
try:
    import pydot
    PYDOT_AVAILABLE = True
except ImportError:
    PYDOT_AVAILABLE = False
    print("[WARN] pydot 미설치. PNG/SVG 출력 불가. pip install pydot")

# WorkflowTracker 통합 (로컬 정의)
try:
    from workflow_tracker import WorkflowTracker, DocumentStatus, RoleType
except ImportError:
    # 로컬 정의 (workflow_tracker.py가 없는 경우)
    from enum import Enum
    from dataclasses import dataclass
    from datetime import datetime
    from typing import Dict, List, Optional
    
    class DocumentStatus(Enum):
        NOT_PROVIDED = "NOT_PROVIDED"
        PROVIDED = "PROVIDED"
        IN_REVIEW = "IN_REVIEW"
        APPROVED = "APPROVED"
        SUBMITTED = "SUBMITTED"
        REJECTED = "REJECTED"
    
    class RoleType(Enum):
        VESSEL = "Vessel/LCT"
        MAMMOET = "Mammoet"
        ARIES = "Aries"
        SAMSUNG = "Samsung"
        HM = "HM/MWS"
    
    @dataclass
    class Document:
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
    
    class WorkflowTracker:
        def __init__(self, project_id: str):
            self.project_id = project_id
            self.documents: Dict[str, Document] = {}
            self._initialize_documents()
        
        def _initialize_documents(self):
            # 기본 문서 구조 생성
            pass
        
        def update_document_status(self, doc_name: str, status: DocumentStatus, 
                                 file_path: Optional[str] = None, notes: str = ""):
            if doc_name in self.documents:
                self.documents[doc_name].status = status
                self.documents[doc_name].file_path = file_path
                self.documents[doc_name].notes = notes
                return True
            return False
        
        def get_missing_documents(self) -> List[str]:
            return [name for name, doc in self.documents.items() 
                   if doc.status == DocumentStatus.NOT_PROVIDED]
        
        def check_atlp_readiness(self) -> tuple:
            return False, []
        
        def get_workflow_status(self):
            return type('WorkflowStatus', (), {
                'total_documents': len(self.documents),
                'completed_documents': sum(1 for doc in self.documents.values() 
                                        if doc.status in [DocumentStatus.APPROVED, DocumentStatus.SUBMITTED]),
                'pending_documents': sum(1 for doc in self.documents.values() 
                                      if doc.status in [DocumentStatus.PROVIDED, DocumentStatus.IN_REVIEW]),
                'overdue_documents': 0,
                'atlp_ready': False,
                'overall_progress': 0.0
            })()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------- 도메인 모델 (Untitled-2.py에서 가져옴) ----------
@dataclass(frozen=True)
class Role:
    key: str
    label: str

@dataclass(frozen=True)
class Artifact:
    key: str
    label: str
    required: bool = True

@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    what: str
    kind: str  # 'provide' | 'consume' | 'produce' | 'submit' | 'optional' | 'extended'
    required: bool = True

# ---------- 상태별 색상 매핑 ----------
STATUS_COLORS = {
    DocumentStatus.NOT_PROVIDED: "#ff4444",    # 빨강
    DocumentStatus.PROVIDED: "#ffaa00",          # 노랑
    DocumentStatus.IN_REVIEW: "#ff8800",        # 주황
    DocumentStatus.APPROVED: "#44ff44",         # 초록
    DocumentStatus.SUBMITTED: "#4444ff",       # 파랑
    DocumentStatus.REJECTED: "#ff44ff"          # 보라
}

STATUS_STYLES = {
    DocumentStatus.NOT_PROVIDED: "dashed",
    DocumentStatus.PROVIDED: "solid",
    DocumentStatus.IN_REVIEW: "solid",
    DocumentStatus.APPROVED: "bold",
    DocumentStatus.SUBMITTED: "bold",
    DocumentStatus.REJECTED: "dashed"
}

class IntegratedWorkflowSystem:
    """
    통합 워크플로우 시스템
    
    NetworkX 그래프 생성 + WorkflowTracker 상태 관리 + 다중 포맷 출력
    """
    
    def __init__(self, project_id: str = "HVDC_2025"):
        self.project_id = project_id
        self.tracker = WorkflowTracker(project_id)
        self.graph = None
        
        # Untitled-2.py에서 가져온 데이터 구조
        self.roles = [
            Role("vessel", "Vessel/LCT (선장/운항)"),
            Role("mammoet", "Mammoet (방법서/시퀀스)"),
            Role("aries", "Aries (설계/검증)"),
            Role("samsung", "Samsung (코디네이션)"),
            Role("hm", "HM/MWS (검토/승인)"),
        ]
        
        self.artifacts = [
            Artifact("elc", "ELC (FWD/AFT Draft · Trim · GM)", True),
            Artifact("tank", "Ballast Tank Arrangement & Capacity", True),
            Artifact("seq", "Sequence of Loading (단계/접촉/밸러스트)", True),
            Artifact("ms", "Method Statement (Ballasting Seq 포함)", True),
            Artifact("fsc", "Final Sailing Condition", False),
            Artifact("sb", "Stability Booklet/기본도면", False),
            Artifact("pl", "Packing List", False),
            Artifact("str_bridge", "Steel Bridge Strength (결과)", True),
            Artifact("str_bow", "Bow Deck Strength (결과)", True),
            Artifact("intact", "Intact Stability per Step (결과)", True),
            Artifact("tyre7", "7-타이어 스케치 계산 + ETA (결과)", True),
            Artifact("cover", "Cover Note & Bundle", True),
            Artifact("atlp", "ATLP/MWS 제출", True),
        ]
        
        self.edges = [
            # 제공(입력)
            Edge("vessel", "elc", "ELC 수치(드래프트/트림/GM)", "provide", True),
            Edge("vessel", "tank", "탱크 배치/용량", "provide", True),
            Edge("vessel", "sb", "안정성 북릿/기본도면", "provide", False),
            Edge("mammoet", "seq", "SPMT 단계/접촉/밸러스트 표", "provide", True),
            Edge("mammoet", "ms", "방법서/볼라스트 시퀀스", "provide", True),
            Edge("mammoet", "fsc", "Final Sailing Condition", "provide", False),
            Edge("mammoet", "pl", "PL (권장)", "provide", False),
            
            # Aries가 입력 소비
            Edge("elc", "aries", "ELC 입력", "consume", True),
            Edge("tank", "aries", "탱크정보 입력", "consume", True),
            Edge("seq", "aries", "시퀀스 입력", "consume", True),
            
            # Aries 산출
            Edge("aries", "str_bridge", "링크스팬 강도 결과", "produce", True),
            Edge("aries", "str_bow", "Bow Deck 강도 결과", "produce", True),
            Edge("aries", "intact", "단계별 안정성 결과", "produce", True),
            Edge("aries", "tyre7", "7-타이어 스케치/ETA", "produce", True),
            
            # 패키징/제출
            Edge("str_bridge", "samsung", "Aries 산출 전달", "provide", True),
            Edge("str_bow", "samsung", "Aries 산출 전달", "provide", True),
            Edge("intact", "samsung", "Aries 산출 전달", "provide", True),
            Edge("tyre7", "samsung", "Aries 산출 전달", "provide", True),
            Edge("ms", "samsung", "MS 포함", "provide", True),
            Edge("elc", "samsung", "ELC 포함", "provide", True),
            Edge("tank", "samsung", "탱크 포함", "provide", True),
            Edge("sb", "samsung", "기본도면 포함(권장)", "provide", False),
            Edge("pl", "samsung", "PL 포함(권장)", "provide", False),
            Edge("fsc", "samsung", "FSC 포함(권장)", "provide", False),
            
            Edge("samsung", "cover", "커버노트/번들링", "produce", True),
            Edge("cover", "atlp", "ATLP 패키지", "submit", True),
            Edge("atlp", "hm", "제출", "submit", True),
            
            # 확장 범위: Aries가 시퀀스/밸러스트 플랜까지 설계
            Edge("aries", "seq", "추가계약 시 시퀀스 설계", "extended", False),
        ]
        
        # Assumption 기반 검증 설정
        self.assumptions = {
            "elc_absent": {
                "description": "ELC 없이 Aries 계산 가능 (Trim≈0, Present Condition 가정)",
                "enables": ["str_bridge", "str_bow", "intact", "tyre7"],
                "requires": ["tank", "seq"]
            }
        }
    
    def build_graph(self) -> nx.DiGraph:
        """NetworkX 그래프 구성 (상태 반영)"""
        G = nx.DiGraph()
        
        # 노드 추가 (역할)
        for role in self.roles:
            G.add_node(role.key, 
                      kind="role", 
                      label=role.label, 
                      shape="box",
                      fillcolor="#f7f7ff",
                      color="#445")
        
        # 노드 추가 (문서/산출물) - 상태별 색상 적용
        for artifact in self.artifacts:
            # WorkflowTracker에서 상태 가져오기
            status = self.tracker.documents.get(artifact.key, {}).get('status', DocumentStatus.NOT_PROVIDED)
            if hasattr(status, 'value'):
                status = DocumentStatus(status.value) if isinstance(status.value, str) else status
            
            color = STATUS_COLORS.get(status, "#cccccc")
            style = STATUS_STYLES.get(status, "solid")
            
            G.add_node(artifact.key,
                      kind="artifact",
                      label=artifact.label,
                      shape="ellipse",
                      required=artifact.required,
                      status=status.value if hasattr(status, 'value') else str(status),
                      fillcolor=color,
                      color=color,
                      style=style)
        
        # 엣지 추가
        for edge in self.edges:
            # 상태에 따른 엣지 스타일 결정
            edge_style = "solid" if edge.required else "dashed"
            edge_color = {
                "provide": "#2e7d32",
                "consume": "#1565c0", 
                "produce": "#6a1b9a",
                "submit": "#4e342e",
                "extended": "#d68400"
            }.get(edge.kind, "#333333")
            
            G.add_edge(edge.src, edge.dst,
                      what=edge.what,
                      kind=edge.kind,
                      required=edge.required,
                      color=edge_color,
                      style=edge_style)
        
        self.graph = G
        return G
    
    def validate_with_assumptions(self, provided_docs: List[str]) -> Dict[str, any]:
        """Assumption 기반 검증 로직"""
        provided_set = set(provided_docs)
        results = {}
        
        # 기본 검증 (Untitled-2.py 로직)
        min_required = {
            "for_review": {"tank", "seq"},
            "for_approval": {"elc", "tank", "seq", "ms"}
        }
        
        can_review = min_required["for_review"].issubset(provided_set)
        can_approval = min_required["for_approval"].issubset(provided_set)
        
        # Assumption 검증
        elc_absent = "elc" not in provided_set
        if elc_absent and self.assumptions["elc_absent"]["requires"]:
            assumption_met = set(self.assumptions["elc_absent"]["requires"]).issubset(provided_set)
            if assumption_met:
                can_review = True
                results["assumption_elc_absent"] = {
                    "enabled": True,
                    "description": self.assumptions["elc_absent"]["description"],
                    "enables": self.assumptions["elc_absent"]["enables"]
                }
        
        results.update({
            "FOR_REVIEW": can_review,
            "FOR_APPROVAL": can_approval,
            "MISSING_FOR_REVIEW": sorted(min_required["for_review"] - provided_set),
            "MISSING_FOR_APPROVAL": sorted(min_required["for_approval"] - provided_set),
            "PROVIDED_DOCS": sorted(provided_set),
            "NOTE": "ELC 미제공 시 Aries는 Trim≈0 / Present Condition 가정으로 7-타이어 계산 가능(단, 승인본은 ELC 필수)."
        })
        
        return results
    
    def export_graph_files(self, basename: str = "integrated_workflow") -> Dict[str, str]:
        """다중 포맷 그래프 파일 생성"""
        if not self.graph:
            self.build_graph()
        
        results = {}
        
        # DOT 파일 생성
        dot_content = self._to_dot()
        dot_file = f"{basename}.dot"
        with open(dot_file, 'w', encoding='utf-8') as f:
            f.write(dot_content)
        results["dot"] = dot_file
        
        # PNG/SVG 생성 (pydot 사용)
        if PYDOT_AVAILABLE:
            try:
                pdG = self._to_pydot()
                png_file = f"{basename}.png"
                svg_file = f"{basename}.svg"
                pdG.write_png(png_file)
                pdG.write_svg(svg_file)
                results["png"] = png_file
                results["svg"] = svg_file
                logger.info(f"[OK] 저장: {png_file} / {svg_file}")
            except Exception as e:
                logger.warning(f"[WARN] PNG/SVG 렌더 실패: {e}")
        
        # HTML 생성 (상태 정보 포함)
        html_file = f"{basename}.html"
        self._generate_interactive_html(html_file)
        results["html"] = html_file
        
        # JSON 상태 데이터
        json_file = f"{basename}_status.json"
        self._export_status_json(json_file)
        results["json"] = json_file
        
        return results
    
    def _to_dot(self) -> str:
        """DOT 형식으로 그래프 변환"""
        lines = ['digraph G {', '  rankdir=LR;', '  node [fontname="Arial", fontsize="10"];']
        
        # 노드 정의
        for node, data in self.graph.nodes(data=True):
            label = data.get('label', node).replace('"', '\\"')
            shape = data.get('shape', 'ellipse')
            fillcolor = data.get('fillcolor', '#ffffff')
            color = data.get('color', '#000000')
            style = data.get('style', 'solid')
            
            if data.get('kind') == 'role':
                lines.append(f'  {node} [label="{label}", shape={shape}, style="filled", fillcolor="{fillcolor}", color="{color}"];')
            else:
                status = data.get('status', 'NOT_PROVIDED')
                lines.append(f'  {node} [label="{label}\\n({status})", shape={shape}, style="filled", fillcolor="{fillcolor}", color="{color}"];')
        
        # 엣지 정의
        for u, v, data in self.graph.edges(data=True):
            label = data.get('what', '').replace('"', '\\"')
            color = data.get('color', '#333333')
            style = data.get('style', 'solid')
            lines.append(f'  {u} -> {v} [label="{label}", color="{color}", style="{style}"];')
        
        lines.append('}')
        return '\n'.join(lines)
    
    def _to_pydot(self):
        """Pydot 객체로 변환"""
        if not PYDOT_AVAILABLE:
            raise ImportError("pydot 미설치")
        
        pdG = pydot.Dot(graph_type='digraph', rankdir="LR")
        
        # 노드 추가
        for node, data in self.graph.nodes(data=True):
            label = data.get('label', node)
            shape = data.get('shape', 'ellipse')
            fillcolor = data.get('fillcolor', '#ffffff')
            color = data.get('color', '#000000')
            style = data.get('style', 'solid')
            
            pydot_node = pydot.Node(
                node,
                label=label,
                shape=shape,
                style="filled",
                fillcolor=fillcolor,
                color=color,
                fontname="Arial",
                fontsize="10"
            )
            pdG.add_node(pydot_node)
        
        # 엣지 추가
        for u, v, data in self.graph.edges(data=True):
            label = data.get('what', '')
            color = data.get('color', '#333333')
            style = data.get('style', 'solid')
            
            pydot_edge = pydot.Edge(
                u, v,
                label=label,
                color=color,
                style=style,
                fontname="Arial",
                fontsize="9",
                penwidth="2"
            )
            pdG.add_edge(pydot_edge)
        
        return pdG
    
    def _generate_interactive_html(self, filename: str):
        """상태 정보가 포함된 인터랙티브 HTML 생성"""
        status = self.tracker.get_workflow_status()
        missing_docs = self.tracker.get_missing_documents()
        atlp_ready, atlp_missing = self.tracker.check_atlp_readiness()
        
        html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HVDC 통합 워크플로우 시스템</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .status-panel {{
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #dee2e6;
        }}
        .status-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .status-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .status-card.warning {{ border-left-color: #ffc107; }}
        .status-card.danger {{ border-left-color: #dc3545; }}
        .status-card.success {{ border-left-color: #28a745; }}
        .diagram-container {{
            padding: 30px;
            background: #f8f9fa;
        }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚢 HVDC 통합 워크플로우 시스템</h1>
            <p>NetworkX + WorkflowTracker + 실시간 상태 추적</p>
        </div>
        
        <div class="status-panel">
            <h3>📊 현재 상태</h3>
            <div class="status-grid">
                <div class="status-card {'success' if status.overall_progress > 50 else 'warning' if status.overall_progress > 25 else 'danger'}">
                    <strong>전체 진행률</strong><br>
                    {status.overall_progress:.1f}% ({status.completed_documents}/{status.total_documents})
                </div>
                <div class="status-card {'success' if atlp_ready else 'danger'}">
                    <strong>ATLP 준비도</strong><br>
                    {'✅ 준비완료' if atlp_ready else '❌ 미완료'}
                </div>
                <div class="status-card {'warning' if status.pending_documents > 0 else 'success'}">
                    <strong>진행중 문서</strong><br>
                    {status.pending_documents}개
                </div>
                <div class="status-card {'danger' if status.overdue_documents > 0 else 'success'}">
                    <strong>지연 문서</strong><br>
                    {status.overdue_documents}개
                </div>
            </div>
            
            {f'<div class="alert alert-warning"><strong>⚠️ 누락 문서:</strong> {", ".join(missing_docs[:5])}{"..." if len(missing_docs) > 5 else ""}</div>' if missing_docs else '<div class="alert alert-success"><strong>✅ 모든 필수 문서 제공됨</strong></div>'}
        </div>
        
        <div class="diagram-container">
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff4444;"></div>
                    <span>미제공 (NOT_PROVIDED)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ffaa00;"></div>
                    <span>제공됨 (PROVIDED)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff8800;"></div>
                    <span>검토중 (IN_REVIEW)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #44ff44;"></div>
                    <span>승인됨 (APPROVED)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #4444ff;"></div>
                    <span>제출됨 (SUBMITTED)</span>
                </div>
            </div>
            
            <div class="mermaid" id="mermaid-diagram">
{self._generate_mermaid_with_status()}
            </div>
        </div>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'base',
            themeVariables: {{
                primaryColor: '#f7f7ff',
                primaryTextColor: '#2c3e50',
                primaryBorderColor: '#445',
                lineColor: '#374',
                secondaryColor: '#f8fff7',
                tertiaryColor: '#ffffff'
            }},
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }}
        }});
    </script>
</body>
</html>"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"인터랙티브 HTML 생성: {filename}")
    
    def _generate_mermaid_with_status(self) -> str:
        """상태 정보가 포함된 Mermaid 다이어그램 생성"""
        lines = [
            "graph LR",
            "  %% Roles",
            "  Aries([Aries<br/>설계/검증])",
            "  Vessel([Vessel/LCT<br/>선장/운항])",
            "  Mammoet([Mammoet<br/>방법서/시퀀스])",
            "  Samsung([Samsung<br/>코디네이션])",
            "  HM([HM/MWS<br/>검토/승인])",
            "",
            "  %% Artifacts with Status"
        ]
        
        # 상태별 색상 적용
        for artifact in self.artifacts:
            status = self.tracker.documents.get(artifact.key, {}).get('status', DocumentStatus.NOT_PROVIDED)
            if hasattr(status, 'value'):
                status = DocumentStatus(status.value) if isinstance(status.value, str) else status
            
            color = STATUS_COLORS.get(status, "#cccccc")
            status_text = status.value if hasattr(status, 'value') else str(status)
            
            lines.append(f"  {artifact.key}{{{artifact.label}<br/>({status_text})}}")
        
        lines.extend([
            "",
            "  %% Provides with Status Colors",
            "  Vessel -->|제공(필수)| ELC",
            "  Vessel -->|제공(필수)| Tank", 
            "  Vessel -->|제공(권장)| SB",
            "  Mammoet -->|제공(필수)| Seq",
            "  Mammoet -->|제공(필수)| MS",
            "  Mammoet -->|제공(권장)| Fsc",
            "  Mammoet -->|제공(권장)| PL",
            "",
            "  %% Aries consumes -> produces",
            "  ELC --> Aries",
            "  Tank --> Aries", 
            "  Seq --> Aries",
            "  Aries --> StrBridge",
            "  Aries --> StrBow",
            "  Aries --> Intact",
            "  Aries --> Tyre7",
            "",
            "  %% Samsung packages & submits",
            "  StrBridge --> Samsung",
            "  StrBow --> Samsung",
            "  Intact --> Samsung",
            "  Tyre7 --> Samsung",
            "  MS --> Samsung",
            "  ELC --> Samsung",
            "  Tank --> Samsung",
            "  SB --> Samsung",
            "  PL --> Samsung",
            "  Fsc --> Samsung",
            "",
            "  Samsung --> Cover --> ATLP --> HM",
            "",
            "  %% Optional 확장범위",
            "  Aries -.추가계약(7~10d).-> Seq",
            "",
            "  %% Status-based styling",
            "  classDef notProvided fill:#ff4444,stroke:#ff0000,color:#fff",
            "  classDef provided fill:#ffaa00,stroke:#ff8800,color:#000", 
            "  classDef inReview fill:#ff8800,stroke:#ff6600,color:#000",
            "  classDef approved fill:#44ff44,stroke:#00aa00,color:#000",
            "  classDef submitted fill:#4444ff,stroke:#0000ff,color:#fff",
            "  classDef role fill:#f7f7ff,stroke:#445,stroke-width:2px"
        ])
        
        # 상태별 클래스 적용
        for artifact in self.artifacts:
            status = self.tracker.documents.get(artifact.key, {}).get('status', DocumentStatus.NOT_PROVIDED)
            if hasattr(status, 'value'):
                status = DocumentStatus(status.value) if isinstance(status.value, str) else status
            
            status_class = {
                DocumentStatus.NOT_PROVIDED: "notProvided",
                DocumentStatus.PROVIDED: "provided",
                DocumentStatus.IN_REVIEW: "inReview", 
                DocumentStatus.APPROVED: "approved",
                DocumentStatus.SUBMITTED: "submitted"
            }.get(status, "notProvided")
            
            lines.append(f"  class {artifact.key} {status_class}")
        
        lines.extend([
            "  class Aries,Vessel,Mammoet,Samsung,HM role"
        ])
        
        return "\n".join(lines)
    
    def _export_status_json(self, filename: str):
        """상태 데이터 JSON 내보내기"""
        status_data = {
            "project_id": self.project_id,
            "timestamp": datetime.now().isoformat(),
            "workflow_status": asdict(self.tracker.get_workflow_status()),
            "documents": {},
            "assumptions": self.assumptions,
            "validation": self.validate_with_assumptions(
                [doc for doc, data in self.tracker.documents.items() 
                 if data.status != DocumentStatus.NOT_PROVIDED]
            )
        }
        
        # 문서 상태 추가
        for name, doc in self.tracker.documents.items():
            status_data["documents"][name] = {
                "name": doc.name,
                "description": doc.description,
                "status": doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
                "provider": doc.provider.value if hasattr(doc.provider, 'value') else str(doc.provider),
                "consumer": doc.consumer.value if doc.consumer and hasattr(doc.consumer, 'value') else str(doc.consumer) if doc.consumer else None,
                "file_path": doc.file_path,
                "created_date": doc.created_date.isoformat() if doc.created_date else None,
                "notes": doc.notes
            }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"상태 JSON 내보내기: {filename}")
    
    def generate_comprehensive_report(self) -> str:
        """종합 리포트 생성"""
        status = self.tracker.get_workflow_status()
        missing_docs = self.tracker.get_missing_documents()
        atlp_ready, atlp_missing = self.tracker.check_atlp_readiness()
        
        # Assumption 기반 검증
        provided_docs = [doc for doc, data in self.tracker.documents.items() 
                       if data.status != DocumentStatus.NOT_PROVIDED]
        validation = self.validate_with_assumptions(provided_docs)
        
        report = f"""
# HVDC 통합 워크플로우 시스템 리포트
**프로젝트:** {self.project_id}  
**생성일:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 전체 상태
- **전체 문서:** {status.total_documents}개
- **완료:** {status.completed_documents}개 ({status.overall_progress:.1f}%)
- **진행중:** {status.pending_documents}개
- **지연:** {status.overdue_documents}개
- **ATLP 준비도:** {'✅ 준비완료' if atlp_ready else '❌ 미완료'}

## 🔍 Assumption 기반 검증
- **검토 가능:** {'✅ 가능' if validation['FOR_REVIEW'] else '❌ 불가능'}
- **승인 가능:** {'✅ 가능' if validation['FOR_APPROVAL'] else '❌ 불가능'}
- **제공된 문서:** {', '.join(validation['PROVIDED_DOCS'])}
- **검토 누락:** {', '.join(validation['MISSING_FOR_REVIEW'])}
- **승인 누락:** {', '.join(validation['MISSING_FOR_APPROVAL'])}

## 🚨 누락 문서
"""
        if missing_docs:
            for doc in missing_docs:
                doc_info = self.tracker.documents[doc]
                report += f"- **{doc}**: {doc_info.description} (제공자: {doc_info.provider.value})\n"
        else:
            report += "- 모든 필수 문서가 제공되었습니다.\n"
        
        if not atlp_ready:
            report += f"\n## ⚠️ ATLP 제출 대기 문서\n"
            for doc in atlp_missing:
                report += f"- **{doc}**: {self.tracker.documents[doc].description}\n"
        
        # Assumption 정보
        if validation.get('assumption_elc_absent', {}).get('enabled'):
            report += f"\n## 💡 Assumption 활성화\n"
            report += f"- **ELC 없이 진행 가능**: {validation['assumption_elc_absent']['description']}\n"
            report += f"- **활성화된 산출물**: {', '.join(validation['assumption_elc_absent']['enables'])}\n"
        
        report += f"\n## 📝 참고사항\n{validation.get('NOTE', '')}"
        
        return report

def main():
    """메인 실행 함수"""
    print("🚢 HVDC 통합 워크플로우 시스템 시작")
    
    # 통합 시스템 초기화
    system = IntegratedWorkflowSystem("HVDC_2025_001")
    
    # 예시: 일부 문서 상태 업데이트
    system.tracker.update_document_status("ELC", DocumentStatus.PROVIDED, 
                                         file_path="/documents/ELC_v1.0.pdf", 
                                         notes="Vessel에서 제공됨")
    system.tracker.update_document_status("Tank", DocumentStatus.PROVIDED,
                                         file_path="/documents/Tank_Arrangement.pdf")
    system.tracker.update_document_status("Seq", DocumentStatus.PROVIDED,
                                         file_path="/documents/Sequence_Loading.pdf")
    system.tracker.update_document_status("MS", DocumentStatus.PROVIDED,
                                         file_path="/documents/Method_Statement.pdf")
    
    # 그래프 구성
    graph = system.build_graph()
    print(f"그래프 구성 완료: {len(graph.nodes)}개 노드, {len(graph.edges)}개 엣지")
    
    # 다중 포맷 출력
    print("\n📁 다중 포맷 파일 생성 중...")
    files = system.export_graph_files("hvdc_integrated_workflow")
    for format_type, filepath in files.items():
        print(f"✅ {format_type.upper()}: {filepath}")
    
    # 종합 리포트 생성
    report = system.generate_comprehensive_report()
    print("\n📊 종합 리포트:")
    print(report)
    
    # Assumption 검증 예시
    print("\n🔍 Assumption 검증:")
    provided = ["tank", "seq", "ms", "sb", "pl"]  # ELC 없는 케이스
    validation = system.validate_with_assumptions(provided)
    for key, value in validation.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
