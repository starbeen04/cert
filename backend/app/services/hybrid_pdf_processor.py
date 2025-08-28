#!/usr/bin/env python3
"""
🎯 하이브리드 PDF 처리 시스템
- 데이터 타입별 특화 처리 + 개별 처리 정확도 유지 + 크로스 페이지 연결
"""

import re
import json
import base64
from PIL import Image
import io
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
import fitz  # PyMuPDF
import openai
from datetime import datetime
import numpy as np
from dataclasses import dataclass
from enum import Enum

class DataType(Enum):
    """데이터 타입 분류"""
    TEXT_QUESTION = "text_question"      # 순수 텍스트 문제
    TABLE_DATA = "table_data"            # 표 데이터 (스케줄링, 성능 등)
    CODE_BLOCK = "code_block"            # 프로그래밍 코드
    DIAGRAM_IMAGE = "diagram_image"      # 다이어그램, 트리, 그래프
    CHOICE_IMAGE = "choice_image"        # 이미지가 선택지인 경우 (ERD 기호 등)
    MIXED_CONTENT = "mixed_content"      # 텍스트 + 표/이미지 혼합
    PASSAGE_TEXT = "passage_text"        # 긴 지문/보기
    FORMULA_MATH = "formula_math"        # 수식/공식

@dataclass
class ProcessingStrategy:
    """데이터 타입별 처리 전략"""
    data_type: DataType
    extraction_method: str
    accuracy_priority: str
    special_handling: List[str]
    cross_page_sensitive: bool

class HybridPDFProcessor:
    """하이브리드 PDF 처리 시스템 - 데이터 타입별 특화 + 개별 정확도 유지"""
    
    def __init__(self, openai_client: openai.AsyncOpenAI):
        self.openai_client = openai_client
        
        # 데이터 타입별 처리 전략 정의
        self.processing_strategies = {
            DataType.TEXT_QUESTION: ProcessingStrategy(
                data_type=DataType.TEXT_QUESTION,
                extraction_method="vision_ocr_standard",
                accuracy_priority="text_precision",
                special_handling=["korean_text", "choice_markers"],
                cross_page_sensitive=True
            ),
            DataType.TABLE_DATA: ProcessingStrategy(
                data_type=DataType.TABLE_DATA,
                extraction_method="table_structure_analysis",
                accuracy_priority="data_integrity",
                special_handling=["number_precision", "cell_boundary", "header_detection"],
                cross_page_sensitive=True  # 표는 크로스 페이지에 매우 민감
            ),
            DataType.CODE_BLOCK: ProcessingStrategy(
                data_type=DataType.CODE_BLOCK,
                extraction_method="code_syntax_analysis",
                accuracy_priority="syntax_preservation",
                special_handling=["indentation", "keywords", "symbols", "brackets"],
                cross_page_sensitive=True
            ),
            DataType.DIAGRAM_IMAGE: ProcessingStrategy(
                data_type=DataType.DIAGRAM_IMAGE,
                extraction_method="image_extraction",
                accuracy_priority="visual_fidelity",
                special_handling=["image_save", "description_generation"],
                cross_page_sensitive=False  # 다이어그램은 보통 한 페이지 내
            ),
            DataType.CHOICE_IMAGE: ProcessingStrategy(
                data_type=DataType.CHOICE_IMAGE,
                extraction_method="choice_image_analysis",
                accuracy_priority="choice_distinction",
                special_handling=["image_per_choice", "choice_labeling"],
                cross_page_sensitive=False
            ),
            DataType.MIXED_CONTENT: ProcessingStrategy(
                data_type=DataType.MIXED_CONTENT,
                extraction_method="multi_modal_analysis",
                accuracy_priority="content_separation",
                special_handling=["text_image_boundary", "context_preservation"],
                cross_page_sensitive=True
            ),
            DataType.PASSAGE_TEXT: ProcessingStrategy(
                data_type=DataType.PASSAGE_TEXT,
                extraction_method="long_text_analysis",
                accuracy_priority="context_coherence",
                special_handling=["paragraph_structure", "line_breaks"],
                cross_page_sensitive=True
            ),
            DataType.FORMULA_MATH: ProcessingStrategy(
                data_type=DataType.FORMULA_MATH,
                extraction_method="math_formula_extraction",
                accuracy_priority="symbol_accuracy",
                special_handling=["math_symbols", "subscripts", "superscripts"],
                cross_page_sensitive=False
            )
        }
        
        # PDF 규칙
        self.PDF_RULES = {
            "total_questions": 60,
            "choice_markers": ["①", "②", "③", "④"],
            "subjects": {
                "1-20": "정보시스템 기반 기술", 
                "21-40": "프로그래밍 언어 활용",
                "41-60": "데이터베이스 활용"
            },
            # 데이터 타입별 예상 분포
            "data_type_distribution": {
                DataType.TEXT_QUESTION: [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 14, 16, 17, 18, 19, 20, 21, 22, 23, 25, 26, 27, 28, 29, 30, 31, 32, 34, 35, 36, 37, 38, 39, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 57, 58, 59, 60],
                DataType.TABLE_DATA: [6],  # 스케줄링 표
                DataType.CHOICE_IMAGE: [15],  # ERD 기호 선택지
                DataType.CODE_BLOCK: [24, 33, 40],  # Java 코드
                DataType.DIAGRAM_IMAGE: [56],  # 트리 다이어그램
                DataType.MIXED_CONTENT: [13],  # 텍스트 + 이미지
            }
        }
    
    async def process_pdf_hybrid(self, pdf_path: str, upload_id: int) -> Dict[str, Any]:
        """하이브리드 처리 메인 함수"""
        
        print("🎯 하이브리드 PDF 처리 시작 - 데이터 타입별 특화 처리")
        print("=" * 70)
        
        try:
            # === 1단계: PDF 구조 분석 및 데이터 타입 분류 ===
            print("📋 1단계: PDF 구조 분석 및 데이터 타입 분류")
            structure_analysis = await self._analyze_pdf_structure_and_classify(pdf_path, upload_id)
            
            # === 2단계: 크로스 페이지 연결 지도 생성 ===
            print("🔗 2단계: 크로스 페이지 연결 지도 생성")
            cross_page_map = await self._create_cross_page_connection_map(structure_analysis)
            
            # === 3단계: 데이터 타입별 특화 처리 ===
            print("🎨 3단계: 데이터 타입별 특화 처리")
            processed_elements = await self._process_by_data_type(structure_analysis, cross_page_map)
            
            # === 4단계: 개별 처리 결과 통합 ===
            print("🔧 4단계: 개별 처리 결과 통합")
            unified_questions = self._unify_processed_elements(processed_elements)
            
            # === 5단계: 품질 검증 및 최적화 ===
            print("✅ 5단계: 품질 검증 및 최적화")
            final_questions = await self._quality_check_and_optimize(unified_questions, structure_analysis)
            
            print(f"✅ 하이브리드 처리 완료: {len(final_questions)}개 문제 추출")
            
            return {
                "success": True,
                "questions": final_questions,
                "total_questions": len(final_questions),
                "processing_method": "hybrid_specialized",
                "structure_analysis": structure_analysis,
                "cross_page_map": cross_page_map,
                "processing_stats": self._generate_processing_stats(processed_elements)
            }
            
        except Exception as e:
            print(f"❌ 하이브리드 처리 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def _analyze_pdf_structure_and_classify(self, pdf_path: str, upload_id: int) -> Dict[str, Any]:
        """1단계: PDF 구조 분석 및 각 문제의 데이터 타입 분류"""
        
        assets_dir = Path(f"assets/upload_{upload_id}")
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        doc = fitz.open(pdf_path)
        
        # 페이지별 기본 정보 수집
        pages_info = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # 고해상도 이미지 생성 (개별 처리 정확도 유지)
            mat = fitz.Matrix(4.0, 4.0)  # 400dpi for maximum accuracy
            pix = page.get_pixmap(matrix=mat)
            img_path = assets_dir / f"page_{page_num + 1}_hq.png"
            pix.save(str(img_path))
            
            # 텍스트 및 구조 정보
            text_dict = page.get_text("dict")
            raw_text = page.get_text()
            
            pages_info.append({
                "page_number": page_num + 1,
                "raw_text": raw_text,
                "text_dict": text_dict,
                "image_path": str(img_path),
                "blocks": text_dict["blocks"] if "blocks" in text_dict else []
            })
        
        doc.close()
        
        # 각 페이지에서 문제 요소들 감지 및 데이터 타입 분류
        classified_elements = []
        
        for page_info in pages_info:
            page_elements = await self._classify_page_elements(page_info)
            classified_elements.extend(page_elements)
        
        print(f"   📊 분류된 요소: {len(classified_elements)}개")
        
        return {
            "pages_info": pages_info,
            "classified_elements": classified_elements,
            "assets_dir": str(assets_dir)
        }
    
    async def _classify_page_elements(self, page_info: Dict) -> List[Dict[str, Any]]:
        """페이지 내 요소들을 데이터 타입별로 분류"""
        
        elements = []
        raw_text = page_info["raw_text"]
        page_num = page_info["page_number"]
        
        # 문제 번호 패턴 찾기
        question_patterns = re.findall(r'(\d+)\.?\s*([^0-9\n]{10,})', raw_text)
        
        for q_num_str, content_preview in question_patterns:
            try:
                q_num = int(q_num_str)
                if 1 <= q_num <= 60:
                    # 데이터 타입 분류
                    data_type = self._classify_question_data_type(q_num, content_preview, raw_text)
                    
                    elements.append({
                        "question_number": q_num,
                        "page_number": page_num,
                        "data_type": data_type,
                        "content_preview": content_preview[:100],
                        "processing_strategy": self.processing_strategies[data_type],
                        "estimated_position": self._estimate_question_position(q_num_str, raw_text)
                    })
            except ValueError:
                continue
        
        return elements
    
    def _classify_question_data_type(self, q_num: int, content: str, full_text: str) -> DataType:
        """문제 번호와 내용을 기반으로 데이터 타입 분류"""
        
        # 미리 알려진 특수 문제들
        if q_num in self.PDF_RULES["data_type_distribution"].get(DataType.TABLE_DATA, []):
            return DataType.TABLE_DATA
        elif q_num in self.PDF_RULES["data_type_distribution"].get(DataType.CODE_BLOCK, []):
            return DataType.CODE_BLOCK
        elif q_num in self.PDF_RULES["data_type_distribution"].get(DataType.CHOICE_IMAGE, []):
            return DataType.CHOICE_IMAGE
        elif q_num in self.PDF_RULES["data_type_distribution"].get(DataType.DIAGRAM_IMAGE, []):
            return DataType.DIAGRAM_IMAGE
        
        # 내용 기반 자동 분류
        content_lower = content.lower()
        full_text_lower = full_text.lower()
        
        # 표 관련 키워드
        table_keywords = ["프로세스", "도착시간", "실행시간", "스케줄링", "대기시간", "p1", "p2", "p3"]
        if any(keyword in content_lower for keyword in table_keywords):
            return DataType.TABLE_DATA
        
        # 코드 관련 키워드
        code_keywords = ["class", "public", "void", "main", "string", "int", "for", "if", "while", "{", "}", ";"]
        if any(keyword in content_lower for keyword in code_keywords):
            return DataType.CODE_BLOCK
        
        # 수식 관련 키워드
        math_keywords = ["∑", "∏", "∫", "√", "²", "³", "≤", "≥", "≠", "α", "β", "γ"]
        if any(keyword in content for keyword in math_keywords):
            return DataType.FORMULA_MATH
        
        # 긴 지문인지 확인
        if len(content) > 200:
            return DataType.PASSAGE_TEXT
        
        # 기본값: 텍스트 문제
        return DataType.TEXT_QUESTION
    
    def _estimate_question_position(self, q_num_str: str, text: str) -> int:
        """텍스트에서 문제의 대략적인 위치 추정"""
        try:
            pattern = f"{q_num_str}\\."
            match = re.search(pattern, text)
            if match:
                # 텍스트에서의 문자 위치를 Y 좌표로 근사 변환
                char_pos = match.start()
                estimated_y = (char_pos / len(text)) * 3000  # 대략적인 이미지 높이
                return int(estimated_y)
        except:
            pass
        return 0
    
    async def _create_cross_page_connection_map(self, structure_analysis: Dict) -> Dict[str, Any]:
        """2단계: 크로스 페이지 연결이 필요한 요소들 식별"""
        
        elements = structure_analysis["classified_elements"]
        cross_page_connections = []
        
        # 크로스 페이지에 민감한 데이터 타입들 확인
        sensitive_elements = [elem for elem in elements 
                            if elem["processing_strategy"].cross_page_sensitive]
        
        print(f"   🔗 크로스 페이지 민감 요소: {len(sensitive_elements)}개")
        
        # 페이지 경계 근처의 요소들 확인
        pages_info = structure_analysis["pages_info"]
        
        for i in range(len(pages_info) - 1):
            current_page = pages_info[i]
            next_page = pages_info[i + 1]
            
            # 현재 페이지 끝부분과 다음 페이지 시작부분 분석
            connection = await self._analyze_page_boundary_connection(
                current_page, next_page, sensitive_elements
            )
            
            if connection["has_connection"]:
                cross_page_connections.append(connection)
        
        return {
            "connections": cross_page_connections,
            "sensitive_elements": sensitive_elements,
            "total_connections": len(cross_page_connections)
        }
    
    async def _analyze_page_boundary_connection(self, current_page: Dict, next_page: Dict, 
                                             sensitive_elements: List[Dict]) -> Dict[str, Any]:
        """페이지 경계에서 연결이 필요한 요소 분석"""
        
        current_text = current_page["raw_text"]
        next_text = next_page["raw_text"]
        
        # 현재 페이지의 마지막 부분 (하위 20%)
        current_lines = current_text.strip().split('\n')
        boundary_lines = current_lines[-max(5, len(current_lines)//5):]
        
        # 다음 페이지의 시작 부분 (상위 20%)  
        next_lines = next_text.strip().split('\n')
        start_lines = next_lines[:max(5, len(next_lines)//5)]
        
        # 연결 패턴 감지
        connection_patterns = {
            "incomplete_choices": self._detect_incomplete_choices(boundary_lines, start_lines),
            "split_table": self._detect_split_table(boundary_lines, start_lines),
            "continued_code": self._detect_continued_code(boundary_lines, start_lines),
            "split_passage": self._detect_split_passage(boundary_lines, start_lines)
        }
        
        has_connection = any(pattern["detected"] for pattern in connection_patterns.values())
        
        return {
            "has_connection": has_connection,
            "from_page": current_page["page_number"],
            "to_page": next_page["page_number"],
            "connection_type": [k for k, v in connection_patterns.items() if v["detected"]],
            "connection_details": connection_patterns
        }
    
    def _detect_incomplete_choices(self, boundary_lines: List[str], start_lines: List[str]) -> Dict:
        """불완전한 선택지 감지"""
        
        choice_markers = ["①", "②", "③", "④"]
        
        # 경계에서 잘린 선택지 찾기
        incomplete_choices = []
        for line in boundary_lines:
            for marker in choice_markers:
                if marker in line and (len(line) < 30 or "..." in line or line.endswith(marker)):
                    incomplete_choices.append({"marker": marker, "partial_text": line})
        
        # 다음 페이지에서 연결되는 부분 찾기
        continuation_found = False
        for line in start_lines:
            if any(marker in line for marker in choice_markers):
                continuation_found = True
                break
        
        return {
            "detected": len(incomplete_choices) > 0 and continuation_found,
            "incomplete_choices": incomplete_choices,
            "continuation_found": continuation_found
        }
    
    def _detect_split_table(self, boundary_lines: List[str], start_lines: List[str]) -> Dict:
        """분할된 표 감지"""
        
        table_indicators = ["프로세스", "도착시간", "실행시간", "|", "P1", "P2", "P3"]
        
        # 경계에 표 헤더가 있는지 확인
        has_table_header = any(
            any(indicator in line for indicator in table_indicators[:4]) 
            for line in boundary_lines
        )
        
        # 다음 페이지에 표 데이터가 있는지 확인
        has_table_data = any(
            any(indicator in line for indicator in table_indicators[4:]) 
            for line in start_lines
        )
        
        return {
            "detected": has_table_header and has_table_data,
            "header_in_boundary": has_table_header,
            "data_in_start": has_table_data
        }
    
    def _detect_continued_code(self, boundary_lines: List[str], start_lines: List[str]) -> Dict:
        """연속된 코드 블록 감지"""
        
        code_indicators = ["{", "}", "class", "public", "void", ";", "//"]
        
        # 경계에 코드 시작이 있는지
        has_code_start = any(
            any(indicator in line for indicator in code_indicators)
            for line in boundary_lines
        )
        
        # 다음 페이지에 코드 연속이 있는지
        has_code_continuation = any(
            any(indicator in line for indicator in code_indicators)
            for line in start_lines
        )
        
        return {
            "detected": has_code_start and has_code_continuation,
            "code_start": has_code_start,
            "code_continuation": has_code_continuation
        }
    
    def _detect_split_passage(self, boundary_lines: List[str], start_lines: List[str]) -> Dict:
        """분할된 지문 감지"""
        
        # 경계의 마지막 줄이 문장 중간에서 끝나는지 확인
        last_line = boundary_lines[-1] if boundary_lines else ""
        incomplete_sentence = not any(last_line.strip().endswith(punct) for punct in [".", "?", "!", "】", ")"]) and len(last_line.strip()) > 0
        
        # 다음 페이지 첫 줄이 소문자나 연결어로 시작하는지 확인
        first_line = start_lines[0] if start_lines else ""
        sentence_continuation = any(first_line.strip().startswith(cont) for cont in ["그", "이", "그러", "하지만", "또한"])
        
        return {
            "detected": incomplete_sentence and sentence_continuation,
            "incomplete_sentence": incomplete_sentence,
            "sentence_continuation": sentence_continuation
        }
    
    async def _process_by_data_type(self, structure_analysis: Dict, cross_page_map: Dict) -> Dict[str, Any]:
        """3단계: 데이터 타입별 특화 처리"""
        
        elements = structure_analysis["classified_elements"]
        processed_results = {}
        
        # 데이터 타입별로 그룹화
        grouped_by_type = {}
        for element in elements:
            data_type = element["data_type"]
            if data_type not in grouped_by_type:
                grouped_by_type[data_type] = []
            grouped_by_type[data_type].append(element)
        
        print(f"   🎨 데이터 타입별 분포:")
        for data_type, items in grouped_by_type.items():
            print(f"      - {data_type.value}: {len(items)}개")
        
        # 각 데이터 타입별로 특화 처리
        for data_type, items in grouped_by_type.items():
            print(f"   🔄 {data_type.value} 처리 중... ({len(items)}개)")
            
            if data_type == DataType.TEXT_QUESTION:
                results = await self._process_text_questions(items, structure_analysis, cross_page_map)
            elif data_type == DataType.TABLE_DATA:
                results = await self._process_table_data(items, structure_analysis, cross_page_map)
            elif data_type == DataType.CODE_BLOCK:
                results = await self._process_code_blocks(items, structure_analysis, cross_page_map)
            elif data_type == DataType.DIAGRAM_IMAGE:
                results = await self._process_diagram_images(items, structure_analysis, cross_page_map)
            elif data_type == DataType.CHOICE_IMAGE:
                results = await self._process_choice_images(items, structure_analysis, cross_page_map)
            elif data_type == DataType.MIXED_CONTENT:
                results = await self._process_mixed_content(items, structure_analysis, cross_page_map)
            elif data_type == DataType.PASSAGE_TEXT:
                results = await self._process_passage_text(items, structure_analysis, cross_page_map)
            elif data_type == DataType.FORMULA_MATH:
                results = await self._process_formula_math(items, structure_analysis, cross_page_map)
            else:
                results = await self._process_default(items, structure_analysis, cross_page_map)
            
            processed_results[data_type] = results
            print(f"   ✅ {data_type.value} 완료: {len(results)}개 결과")
        
        return processed_results
    
    async def _process_text_questions(self, items: List[Dict], structure_analysis: Dict, cross_page_map: Dict) -> List[Dict]:
        """텍스트 문제 특화 처리 - 높은 OCR 정확도 우선"""
        
        results = []
        pages_info = {p["page_number"]: p for p in structure_analysis["pages_info"]}
        
        for item in items:
            page_num = item["page_number"]
            page_info = pages_info[page_num]
            
            # 크로스 페이지 연결 확인
            cross_page_connection = self._find_cross_page_connection(item, cross_page_map)
            
            # 개별 페이지 고정밀 처리
            result = await self._extract_text_question_precise(page_info, item, cross_page_connection)
            if result:
                results.append(result)
        
        return results
    
    async def _extract_text_question_precise(self, page_info: Dict, item: Dict, cross_page_connection: Optional[Dict]) -> Optional[Dict]:
        """텍스트 문제 정밀 추출"""
        
        with open(page_info["image_path"], "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 텍스트 문제 특화 프롬프트
        prompt = f"""페이지에서 {item['question_number']}번 문제를 정밀하게 추출해 주세요.

**텍스트 문제 전용 처리 규칙:**
- 한글 텍스트 정확도 최우선
- 선택지 마커 ①②③④ 정확 인식
- 받침, 모음 구분 정밀 처리
- 문장 부호, 괄호 정확 보존

{self._get_cross_page_instruction(cross_page_connection)}

JSON 응답:
{{
  "question_number": {item['question_number']},
  "question_text": "문제 내용",
  "choices": [
    {{"marker": "①", "content": "선택지 1"}},
    {{"marker": "②", "content": "선택지 2"}},
    {{"marker": "③", "content": "선택지 3"}},
    {{"marker": "④", "content": "선택지 4"}}
  ],
  "passage": "보기 내용 (있는 경우)"
}}"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "텍스트 문제 전용 OCR 전문가. 한글 텍스트와 선택지 마커의 정확도가 최우선입니다."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000,
                temperature=0.05  # 매우 낮은 온도로 정확도 극대화
            )
            
            response_text = response.choices[0].message.content
            result = self._parse_question_json(response_text)
            
            if result:
                result["data_type"] = DataType.TEXT_QUESTION.value
                result["processing_method"] = "text_specialized"
                return result
                
        except Exception as e:
            print(f"      ❌ 텍스트 문제 {item['question_number']}번 처리 실패: {e}")
        
        return None
    
    async def _process_table_data(self, items: List[Dict], structure_analysis: Dict, cross_page_map: Dict) -> List[Dict]:
        """표 데이터 특화 처리 - 데이터 무결성 + 시각적 보존"""
        
        results = []
        pages_info = {p["page_number"]: p for p in structure_analysis["pages_info"]}
        assets_dir = Path(structure_analysis["assets_dir"])
        
        for item in items:
            page_num = item["page_number"]
            page_info = pages_info[page_num]
            
            # 크로스 페이지 연결 확인 (표는 매우 중요)
            cross_page_connection = self._find_cross_page_connection(item, cross_page_map)
            
            # 표 전용 처리
            result = await self._extract_table_data_specialized(page_info, item, cross_page_connection, assets_dir)
            if result:
                results.append(result)
        
        return results
    
    async def _extract_table_data_specialized(self, page_info: Dict, item: Dict, cross_page_connection: Optional[Dict], assets_dir: Path) -> Optional[Dict]:
        """표 데이터 특화 추출"""
        
        with open(page_info["image_path"], "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 표 데이터 전용 프롬프트
        prompt = f"""페이지에서 {item['question_number']}번 문제의 표 데이터를 완벽하게 추출해 주세요.

**표 데이터 전용 처리 규칙:**
- 숫자 정확도 최우선: 2≠3, 0≠O, 1≠l, 5≠S, 8≠B, 6≠9
- 표 구조 완전 보존: 헤더, 모든 데이터 행 포함
- 셀 경계 정확 인식
- 프로세스명 (P1, P2, P3) 정확 추출
- 시간 데이터 (숫자) 정확 추출

{self._get_cross_page_instruction(cross_page_connection)}

**중요**: 표는 마크다운 형식 + 원본 이미지 둘 다 제공

JSON 응답:
{{
  "question_number": {item['question_number']},
  "question_text": "문제 내용",
  "choices": [
    {{"marker": "①", "content": "선택지 1"}},
    {{"marker": "②", "content": "선택지 2"}},
    {{"marker": "③", "content": "선택지 3"}},
    {{"marker": "④", "content": "선택지 4"}}
  ],
  "table_markdown": "| 프로세스 | 도착시간 | 실행시간 |\\n|---------|--------|--------|\\n| P1 | 0 | 3 |\\n| P2 | 1 | 4 |",
  "table_data": [
    {{"process": "P1", "arrival_time": 0, "execution_time": 3}},
    {{"process": "P2", "arrival_time": 1, "execution_time": 4}}
  ],
  "passage": "표 설명 텍스트",
  "requires_image_extraction": true
}}"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "표 데이터 전용 추출 전문가. 숫자와 표 구조의 정확도가 최우선이며, 절대로 데이터를 추측하거나 생성하지 않습니다."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000,
                temperature=0.01  # 표 데이터는 극도로 낮은 온도
            )
            
            response_text = response.choices[0].message.content
            result = self._parse_question_json(response_text)
            
            if result:
                result["data_type"] = DataType.TABLE_DATA.value
                result["processing_method"] = "table_specialized"
                
                # 표 이미지 별도 추출
                if result.get("requires_image_extraction"):
                    table_image_path = await self._extract_table_image(page_info["image_path"], item, assets_dir)
                    if table_image_path:
                        result["table_image_path"] = table_image_path
                
                return result
                
        except Exception as e:
            print(f"      ❌ 표 데이터 {item['question_number']}번 처리 실패: {e}")
        
        return None
    
    async def _extract_table_image(self, page_image_path: str, item: Dict, assets_dir: Path) -> Optional[str]:
        """표 영역만 별도 이미지로 추출"""
        
        try:
            # 페이지 이미지에서 표 영역 추정하여 crop
            page_image = Image.open(page_image_path)
            
            # 문제 위치 기반으로 표 영역 추정
            estimated_y = item.get("estimated_position", 0)
            if estimated_y > 0:
                # 표 영역 추정 (문제 위치에서 +200~+600픽셀 정도)
                crop_area = (0, max(0, estimated_y), page_image.width, min(page_image.height, estimated_y + 400))
                table_image = page_image.crop(crop_area)
                
                # 저장
                table_path = assets_dir / f"q{item['question_number']}_table.png"
                table_image.save(table_path)
                
                return str(table_path)
        except Exception as e:
            print(f"      ⚠️ 표 이미지 추출 실패: {e}")
        
        return None
    
    async def _process_code_blocks(self, items: List[Dict], structure_analysis: Dict, cross_page_map: Dict) -> List[Dict]:
        """코드 블록 특화 처리 - 문법 보존 + 들여쓰기 정확도"""
        
        results = []
        pages_info = {p["page_number"]: p for p in structure_analysis["pages_info"]}
        assets_dir = Path(structure_analysis["assets_dir"])
        
        for item in items:
            page_num = item["page_number"]
            page_info = pages_info[page_num]
            
            cross_page_connection = self._find_cross_page_connection(item, cross_page_map)
            result = await self._extract_code_block_specialized(page_info, item, cross_page_connection, assets_dir)
            if result:
                results.append(result)
        
        return results
    
    async def _extract_code_block_specialized(self, page_info: Dict, item: Dict, cross_page_connection: Optional[Dict], assets_dir: Path) -> Optional[Dict]:
        """코드 블록 특화 추출"""
        
        with open(page_info["image_path"], "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 코드 블록 전용 프롬프트
        cross_page_instruction = self._get_cross_page_instruction(cross_page_connection)
        
        prompt = f"""페이지에서 {item['question_number']}번 문제의 코드 블록을 완벽하게 추출해 주세요.

**코드 블록 전용 처리 규칙:**
- 문법 정확도 최우선
- 들여쓰기 완전 보존 (공백, 탭 구분)
- 키워드 정확 인식: class, public, void, main, String, int, for, if, while
- 기호 정확 인식: {{}}, (), [], ;, =, !=, <=, >=
- 변수명/함수명 대소문자 정확 보존
- 주석 (// /* */) 정확 인식
- 문자열 따옴표 ("", '', ``) 정확 인식

{cross_page_instruction}

JSON 응답:
{{
  "question_number": {item['question_number']},
  "question_text": "문제 내용",
  "choices": [
    {{"marker": "①", "content": "선택지 1"}},
    {{"marker": "②", "content": "선택지 2"}},
    {{"marker": "③", "content": "선택지 3"}},
    {{"marker": "④", "content": "선택지 4"}}
  ],
  "code_block": {{
    "language": "java",
    "code": "public class Example {{\\n    public static void main(String[] args) {{\\n        int result = 0;\\n        System.out.println(result);\\n    }}\\n}}",
    "line_numbers": true
  }},
  "passage": "코드 설명 텍스트",
  "requires_image_extraction": true
}}"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "코드 블록 전용 추출 전문가. 프로그래밍 문법과 들여쓰기의 정확도가 최우선이며, 코드를 수정하거나 추측하지 않습니다."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000,
                temperature=0.02  # 코드는 매우 낮은 온도
            )
            
            response_text = response.choices[0].message.content
            result = self._parse_question_json(response_text)
            
            if result:
                result["data_type"] = DataType.CODE_BLOCK.value
                result["processing_method"] = "code_specialized"
                
                # 코드 이미지 별도 추출
                if result.get("requires_image_extraction"):
                    code_image_path = await self._extract_code_image(page_info["image_path"], item, assets_dir)
                    if code_image_path:
                        result["code_image_path"] = code_image_path
                
                return result
                
        except Exception as e:
            print(f"      ❌ 코드 블록 {item['question_number']}번 처리 실패: {e}")
        
        return None
    
    async def _extract_code_image(self, page_image_path: str, item: Dict, assets_dir: Path) -> Optional[str]:
        """코드 영역만 별도 이미지로 추출"""
        
        try:
            page_image = Image.open(page_image_path)
            estimated_y = item.get("estimated_position", 0)
            
            if estimated_y > 0:
                # 코드 블록 영역 추정
                crop_area = (0, max(0, estimated_y), page_image.width, min(page_image.height, estimated_y + 500))
                code_image = page_image.crop(crop_area)
                
                code_path = assets_dir / f"q{item['question_number']}_code.png"
                code_image.save(code_path)
                
                return str(code_path)
        except Exception as e:
            print(f"      ⚠️ 코드 이미지 추출 실패: {e}")
        
        return None
    
    async def _process_diagram_images(self, items: List[Dict], structure_analysis: Dict, cross_page_map: Dict) -> List[Dict]:
        """다이어그램 이미지 특화 처리 - 시각적 정보 보존"""
        # 다이어그램은 텍스트로 변환하지 않고 이미지 그대로 보존
        return await self._process_image_based_elements(items, structure_analysis, "diagram")
    
    async def _process_choice_images(self, items: List[Dict], structure_analysis: Dict, cross_page_map: Dict) -> List[Dict]:
        """선택지 이미지 특화 처리 - 각 선택지별 이미지 분리"""
        return await self._process_image_based_elements(items, structure_analysis, "choice_image")
    
    async def _process_image_based_elements(self, items: List[Dict], structure_analysis: Dict, element_type: str) -> List[Dict]:
        """이미지 기반 요소 처리"""
        
        results = []
        pages_info = {p["page_number"]: p for p in structure_analysis["pages_info"]}
        assets_dir = Path(structure_analysis["assets_dir"])
        
        for item in items:
            page_info = pages_info[item["page_number"]]
            
            # 이미지 추출 및 저장
            image_path = await self._extract_element_image(page_info["image_path"], item, assets_dir, element_type)
            
            # 기본 문제 정보 추출
            basic_result = await self._extract_basic_question_info(page_info, item)
            
            if basic_result and image_path:
                basic_result["data_type"] = element_type
                basic_result["image_path"] = image_path
                basic_result["processing_method"] = f"{element_type}_specialized"
                results.append(basic_result)
        
        return results
    
    async def _extract_element_image(self, page_image_path: str, item: Dict, assets_dir: Path, element_type: str) -> Optional[str]:
        """요소별 이미지 추출"""
        
        try:
            page_image = Image.open(page_image_path)
            estimated_y = item.get("estimated_position", 0)
            
            if estimated_y > 0:
                crop_area = (0, max(0, estimated_y - 100), page_image.width, min(page_image.height, estimated_y + 600))
                element_image = page_image.crop(crop_area)
                
                element_path = assets_dir / f"q{item['question_number']}_{element_type}.png"
                element_image.save(element_path)
                
                return str(element_path)
        except Exception as e:
            print(f"      ⚠️ {element_type} 이미지 추출 실패: {e}")
        
        return None
    
    async def _extract_basic_question_info(self, page_info: Dict, item: Dict) -> Optional[Dict]:
        """기본 문제 정보 추출 (이미지 기반 요소용)"""
        
        with open(page_info["image_path"], "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        prompt = f"""페이지에서 {item['question_number']}번 문제의 기본 정보를 추출해 주세요. 
이미지/다이어그램 요소는 별도 처리되므로 텍스트 부분만 정확히 추출하세요.

JSON 응답:
{{
  "question_number": {item['question_number']},
  "question_text": "문제 텍스트 부분만",
  "choices": [
    {{"marker": "①", "content": "선택지 1 (이미지인 경우 '이미지 선택지'로 표시)"}},
    {{"marker": "②", "content": "선택지 2"}},
    {{"marker": "③", "content": "선택지 3"}},
    {{"marker": "④", "content": "선택지 4"}}
  ]
}}"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "이미지 기반 문제의 텍스트 부분만 추출하는 전문가입니다."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}", "detail": "high"}}
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            return self._parse_question_json(response.choices[0].message.content)
            
        except Exception as e:
            print(f"      ❌ 기본 정보 추출 실패: {e}")
        
        return None
    
    async def _process_mixed_content(self, items: List[Dict], structure_analysis: Dict, cross_page_map: Dict) -> List[Dict]:
        """혼합 콘텐츠 처리"""
        # 텍스트와 이미지가 섞인 경우의 특별 처리
        return await self._process_default(items, structure_analysis, cross_page_map)
    
    async def _process_passage_text(self, items: List[Dict], structure_analysis: Dict, cross_page_map: Dict) -> List[Dict]:
        """긴 지문 처리"""
        # 긴 텍스트의 맥락과 구조 보존에 특화
        return await self._process_default(items, structure_analysis, cross_page_map)
    
    async def _process_formula_math(self, items: List[Dict], structure_analysis: Dict, cross_page_map: Dict) -> List[Dict]:
        """수식 처리"""
        # 수학 기호와 수식 구조 정확도에 특화
        return await self._process_default(items, structure_analysis, cross_page_map)
    
    async def _process_default(self, items: List[Dict], structure_analysis: Dict, cross_page_map: Dict) -> List[Dict]:
        """기본 처리 (특화되지 않은 타입들)"""
        
        results = []
        pages_info = {p["page_number"]: p for p in structure_analysis["pages_info"]}
        
        for item in items:
            page_info = pages_info[item["page_number"]]
            result = await self._extract_basic_question_info(page_info, item)
            if result:
                result["data_type"] = item["data_type"].value
                result["processing_method"] = "default"
                results.append(result)
        
        return results
    
    def _find_cross_page_connection(self, item: Dict, cross_page_map: Dict) -> Optional[Dict]:
        """특정 아이템의 크로스 페이지 연결 찾기"""
        
        connections = cross_page_map.get("connections", [])
        item_page = item["page_number"]
        
        for connection in connections:
            if connection["from_page"] == item_page or connection["to_page"] == item_page:
                return connection
        
        return None
    
    def _get_cross_page_instruction(self, connection: Optional[Dict]) -> str:
        """크로스 페이지 연결에 대한 추가 지시사항"""
        
        if not connection:
            return ""
        
        instructions = ["**크로스 페이지 연결 감지됨:**"]
        
        if "incomplete_choices" in connection.get("connection_type", []):
            instructions.append("- 잘린 선택지가 다음 페이지에 연결될 수 있음")
        if "split_table" in connection.get("connection_type", []):
            instructions.append("- 표 데이터가 다음 페이지에 계속될 수 있음")
        if "continued_code" in connection.get("connection_type", []):
            instructions.append("- 코드 블록이 다음 페이지에 계속될 수 있음")
        
        return "\n".join(instructions)
    
    def _parse_question_json(self, response_text: str) -> Optional[Dict]:
        """JSON 응답 파싱"""
        try:
            # ```json ... ``` 블록에서 JSON 추출
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 직접 JSON 찾기
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text
            
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            return None
    
    def _unify_processed_elements(self, processed_results: Dict[str, Any]) -> List[Dict]:
        """4단계: 각 데이터 타입별 처리 결과를 통합"""
        
        all_questions = []
        
        for data_type, results in processed_results.items():
            for result in results:
                all_questions.append(result)
        
        # 문제 번호순으로 정렬
        all_questions.sort(key=lambda q: q.get("question_number", 999))
        
        print(f"   🔧 통합된 문제: {len(all_questions)}개")
        
        return all_questions
    
    async def _quality_check_and_optimize(self, questions: List[Dict], structure_analysis: Dict) -> List[Dict]:
        """5단계: 품질 검증 및 최적화"""
        
        print("   ✅ 품질 검증 시작...")
        
        # 중복 제거
        unique_questions = []
        seen_numbers = set()
        
        for q in questions:
            q_num = q.get("question_number")
            if q_num and q_num not in seen_numbers:
                seen_numbers.add(q_num)
                unique_questions.append(q)
        
        # 누락 확인
        expected_numbers = set(range(1, 61))
        found_numbers = {q.get("question_number") for q in unique_questions}
        missing = expected_numbers - found_numbers
        
        if missing:
            print(f"   ⚠️ 누락된 문제: {sorted(missing)}")
        
        print(f"   📊 최종 품질 검증 완료: {len(unique_questions)}개 문제")
        
        return unique_questions
    
    def _generate_processing_stats(self, processed_results: Dict[str, Any]) -> Dict[str, Any]:
        """처리 통계 생성"""
        
        stats = {
            "data_type_counts": {},
            "total_processed": 0,
            "processing_methods": {}
        }
        
        for data_type, results in processed_results.items():
            type_name = data_type.value if hasattr(data_type, 'value') else str(data_type)
            count = len(results)
            
            stats["data_type_counts"][type_name] = count
            stats["total_processed"] += count
            
            # 처리 방법별 통계
            for result in results:
                method = result.get("processing_method", "unknown")
                if method not in stats["processing_methods"]:
                    stats["processing_methods"][method] = 0
                stats["processing_methods"][method] += 1
        
        return stats