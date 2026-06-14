#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrainingDataGenerator 테스트
TDD Red-Green-Refactor 사이클
"""

import pytest
import json
from pathlib import Path
from training_data_generator import TrainingDataGenerator


class TestTrainingDataGenerator:
    """TrainingDataGenerator 클래스 테스트"""
    
    def test_should_initialize_with_empty_samples(self):
        """초기화 시 빈 샘플 리스트를 가져야 함"""
        generator = TrainingDataGenerator()
        
        assert len(generator.samples) == 0
        assert isinstance(generator.samples, list)
    
    def test_should_add_positive_sample(self):
        """Positive sample 추가 기능"""
        generator = TrainingDataGenerator()
        
        generator.add_positive_sample(
            origin_invoice="DSV Mussafah Yard",
            dest_invoice="Mirfa PMO Site",
            vehicle_invoice="40T Flatbed",
            origin_lane="DSV MUSSAFAH YARD",
            dest_lane="MIRFA SITE",
            vehicle_lane="FLATBED"
        )
        
        assert len(generator.samples) == 1
        assert generator.samples[0]['label'] == 1  # Positive
        assert generator.samples[0]['origin_invoice'] == "DSV Mussafah Yard"
    
    def test_should_add_negative_sample(self):
        """Negative sample 추가 기능"""
        generator = TrainingDataGenerator()
        
        generator.add_negative_sample(
            origin_invoice="DSV Mussafah Yard",
            dest_invoice="Jebel Ali Port",
            vehicle_invoice="Flatbed",
            origin_lane="DSV MUSSAFAH YARD",
            dest_lane="MIRFA SITE",
            vehicle_lane="FLATBED"
        )
        
        assert len(generator.samples) == 1
        assert generator.samples[0]['label'] == 0  # Negative
    
    def test_should_add_metadata_to_sample(self):
        """샘플에 메타데이터 추가 기능"""
        generator = TrainingDataGenerator()
        
        metadata = {'auditor': 'John', 'date': '2024-10-13'}
        
        generator.add_positive_sample(
            origin_invoice="Test Origin",
            dest_invoice="Test Dest",
            vehicle_invoice="Test Vehicle",
            origin_lane="LANE ORIGIN",
            dest_lane="LANE DEST",
            vehicle_lane="LANE VEHICLE",
            metadata=metadata
        )
        
        assert generator.samples[0]['metadata'] == metadata
    
    def test_should_save_to_json(self, tmp_path):
        """JSON 파일로 저장 기능"""
        generator = TrainingDataGenerator()
        
        generator.add_positive_sample(
            origin_invoice="Test",
            dest_invoice="Test",
            vehicle_invoice="Test",
            origin_lane="TEST",
            dest_lane="TEST",
            vehicle_lane="TEST"
        )
        
        output_file = tmp_path / "test_data.json"
        generator.save_to_json(str(output_file))
        
        assert output_file.exists()
        
        # 저장된 내용 확인
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['label'] == 1
    
    def test_should_load_from_json(self, tmp_path):
        """JSON 파일에서 로드 기능"""
        # 테스트 데이터 준비
        test_data = [
            {
                'origin_invoice': 'Test',
                'dest_invoice': 'Test',
                'vehicle_invoice': 'Test',
                'origin_lane': 'TEST',
                'dest_lane': 'TEST',
                'vehicle_lane': 'TEST',
                'label': 1
            }
        ]
        
        input_file = tmp_path / "input_data.json"
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # 로드
        generator = TrainingDataGenerator()
        generator.load_from_json(str(input_file))
        
        assert len(generator.samples) == 1
        assert generator.samples[0]['label'] == 1
    
    def test_should_get_sample_count(self):
        """샘플 개수 조회 기능"""
        generator = TrainingDataGenerator()
        
        generator.add_positive_sample(
            "O1", "D1", "V1", "LO1", "LD1", "LV1"
        )
        generator.add_negative_sample(
            "O2", "D2", "V2", "LO2", "LD2", "LV2"
        )
        
        assert generator.get_sample_count() == 2
        assert generator.get_positive_count() == 1
        assert generator.get_negative_count() == 1
    
    def test_should_generate_negative_samples_automatically(self):
        """자동 Negative sample 생성 기능"""
        generator = TrainingDataGenerator()
        
        # ApprovedLaneMap 시뮬레이션
        approved_lanes = [
            {
                'origin': 'DSV MUSSAFAH YARD',
                'destination': 'MIRFA SITE',
                'vehicle': 'FLATBED',
                'unit': 'per truck'
            },
            {
                'origin': 'M44 WAREHOUSE',
                'destination': 'SHUWEIHAT SITE',
                'vehicle': 'TRAILER',
                'unit': 'per truck'
            },
            {
                'origin': 'JEBEL ALI PORT',
                'destination': 'ABU DHABI SITE',
                'vehicle': 'LOW BED',
                'unit': 'per truck'
            }
        ]
        
        # 자동 Negative sample 생성 (10개)
        generator.generate_negative_samples_auto(approved_lanes, n_samples=10)
        
        assert generator.get_sample_count() == 10
        assert generator.get_negative_count() == 10
        
        # 잘못된 매칭인지 확인 (origin과 destination이 다른 레인에서 가져와야 함)
        for sample in generator.samples:
            assert sample['label'] == 0
            # 원본 레인에 존재하지 않는 조합이어야 함
            matching_lane = [
                lane for lane in approved_lanes
                if (lane['origin'] == sample['origin_lane'] and
                    lane['destination'] == sample['dest_lane'])
            ]
            assert len(matching_lane) == 0  # 매칭되는 레인이 없어야 함

