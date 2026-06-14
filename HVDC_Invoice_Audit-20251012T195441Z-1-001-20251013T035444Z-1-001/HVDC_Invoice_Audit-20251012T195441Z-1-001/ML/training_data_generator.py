#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrainingDataGenerator - ML 학습 데이터 생성기
TDD로 구현됨
"""

import json
import random
from typing import Optional, Dict, List


class TrainingDataGenerator:
    """
    ML 학습 데이터 생성 및 관리 클래스
    
    Features:
    - Positive/Negative sample 추가
    - JSON 저장/로드
    - 샘플 통계 조회
    """
    
    def __init__(self):
        """초기화"""
        self.samples = []
    
    def add_positive_sample(
        self,
        origin_invoice: str,
        dest_invoice: str,
        vehicle_invoice: str,
        origin_lane: str,
        dest_lane: str,
        vehicle_lane: str,
        metadata: Optional[Dict] = None
    ):
        """
        Positive sample 추가 (올바른 매칭)
        
        Args:
            origin_invoice: 송장의 출발지
            dest_invoice: 송장의 목적지
            vehicle_invoice: 송장의 차량 타입
            origin_lane: 레인의 출발지
            dest_lane: 레인의 목적지
            vehicle_lane: 레인의 차량 타입
            metadata: 추가 메타데이터 (optional)
        """
        sample = {
            'origin_invoice': origin_invoice,
            'dest_invoice': dest_invoice,
            'vehicle_invoice': vehicle_invoice,
            'origin_lane': origin_lane,
            'dest_lane': dest_lane,
            'vehicle_lane': vehicle_lane,
            'label': 1  # Positive
        }
        
        if metadata:
            sample['metadata'] = metadata
        
        self.samples.append(sample)
    
    def add_negative_sample(
        self,
        origin_invoice: str,
        dest_invoice: str,
        vehicle_invoice: str,
        origin_lane: str,
        dest_lane: str,
        vehicle_lane: str,
        metadata: Optional[Dict] = None
    ):
        """
        Negative sample 추가 (잘못된 매칭)
        
        Args:
            origin_invoice: 송장의 출발지
            dest_invoice: 송장의 목적지
            vehicle_invoice: 송장의 차량 타입
            origin_lane: 레인의 출발지
            dest_lane: 레인의 목적지
            vehicle_lane: 레인의 차량 타입
            metadata: 추가 메타데이터 (optional)
        """
        sample = {
            'origin_invoice': origin_invoice,
            'dest_invoice': dest_invoice,
            'vehicle_invoice': vehicle_invoice,
            'origin_lane': origin_lane,
            'dest_lane': dest_lane,
            'vehicle_lane': vehicle_lane,
            'label': 0  # Negative
        }
        
        if metadata:
            sample['metadata'] = metadata
        
        self.samples.append(sample)
    
    def save_to_json(self, output_path: str):
        """
        샘플 데이터를 JSON 파일로 저장
        
        Args:
            output_path: 출력 파일 경로
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.samples, f, ensure_ascii=False, indent=2)
    
    def load_from_json(self, input_path: str):
        """
        JSON 파일에서 샘플 데이터 로드
        
        Args:
            input_path: 입력 파일 경로
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            self.samples = json.load(f)
    
    def get_sample_count(self) -> int:
        """전체 샘플 개수"""
        return len(self.samples)
    
    def get_positive_count(self) -> int:
        """Positive 샘플 개수"""
        return sum(1 for s in self.samples if s['label'] == 1)
    
    def get_negative_count(self) -> int:
        """Negative 샘플 개수"""
        return sum(1 for s in self.samples if s['label'] == 0)
    
    def generate_negative_samples_auto(
        self,
        approved_lanes: List[Dict],
        n_samples: int = 100
    ):
        """
        자동으로 Negative sample 생성
        
        전략: ApprovedLaneMap의 레인들을 섞어서
        실제로 존재하지 않는 origin-destination 조합 생성
        
        Args:
            approved_lanes: ApprovedLaneMap 레인 리스트
            n_samples: 생성할 negative sample 개수
        """
        if len(approved_lanes) < 2:
            raise ValueError("최소 2개 이상의 레인이 필요합니다")
        
        generated_count = 0
        max_attempts = n_samples * 10  # 무한 루프 방지
        attempts = 0
        
        while generated_count < n_samples and attempts < max_attempts:
            attempts += 1
            
            # 랜덤하게 2개의 레인 선택
            lane1, lane2 = random.sample(approved_lanes, 2)
            
            # 잘못된 조합 생성 (lane1의 origin + lane2의 destination)
            origin = lane1['origin']
            destination = lane2['destination']
            vehicle = lane1['vehicle']
            
            # 이 조합이 실제로 존재하는지 확인
            is_valid_combination = any(
                lane['origin'] == origin and
                lane['destination'] == destination and
                lane['vehicle'] == vehicle
                for lane in approved_lanes
            )
            
            # 존재하지 않는 조합이면 negative sample로 추가
            if not is_valid_combination:
                self.add_negative_sample(
                    origin_invoice=origin,
                    dest_invoice=destination,
                    vehicle_invoice=vehicle,
                    origin_lane=origin,
                    dest_lane=destination,
                    vehicle_lane=vehicle
                )
                generated_count += 1
        
        if generated_count < n_samples:
            print(f"⚠️  Warning: {n_samples}개 중 {generated_count}개만 생성됨")

