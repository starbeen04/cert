#!/usr/bin/env python3
"""
🔍 포괄적 PDF 구조 분석기
PDF의 모든 정보를 추출하여 구조 기반으로 문제를 정확히 파악하는 시스템
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

@dataclass
class TextBlock:
    """텍스트 블록 정보"""
    text: str
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    font_name: str
    font_size: float
    font_flags: int
    page_number: int
    block_type: str  # question_number, question_text, choice, etc.

@dataclass
class ImageElement:
    """이미지/다이어그램 요소"""
    bbox: Tuple[float, float, float, float]
    page_number: int
    image_data: bytes
    element_type: str  # table, diagram, chart, etc.
    associated_question: Optional[int] = None

@dataclass 
class PageLayout:
    """페이지 레이아웃 정보"""
    page_number: int
    page_width: float
    page_height: float
    text_blocks: List[TextBlock]
    images: List[ImageElement]
    layout_regions: Dict[str, Any]  # header, footer, content areas

class ComprehensivePDFAnalyzer:
    """포괄적 PDF 구조 분석 및 정보 추출"""
    
    def __init__(self, openai_client: openai.AsyncOpenAI):
        self.openai_client = openai_client
        
        # 문제 패턴 정규식
        self.question_patterns = [
            r'^(\d{1,2})\.?\s*',  # "1. " 형태
            r'^문제\s*(\d{1,2})',  # "문제 1" 형태
            r'^(\d{1,2})\)',      # "1)" 형태
        ]
        
        # 선택지 패턴
        self.choice_patterns = [
            r'^[①②③④⑤]\s*',      # 원 숫자
            r'^[⓵⓶⓷⓸⓹]\s*',      # 검은 원 숫자
            r'^[1-5]\.\s*',        # "1. " 형태
            r'^[1-5]\)\s*',        # "1)" 형태
            r'^[가나다라마]\.\s*',  # 한글 순서
        ]
    
    async def analyze_pdf_comprehensive(self, pdf_path: str, upload_id: int) -> Dict[str, Any]:
        """PDF 포괄적 구조 분석 - 모든 정보 추출"""
        
        print("🔍 포괄적 PDF 구조 분석 시작")
        print("=" * 60)
        
        # 1단계: 전체 PDF 구조 추출
        print("📋 1단계: 전체 PDF 구조 정보 추출")
        full_structure = await self._extract_full_pdf_structure(pdf_path, upload_id)
        
        # 2단계: 페이지별 레이아웃 분석
        print("🏗️ 2단계: 페이지별 레이아웃 분석")
        layout_analysis = await self._analyze_page_layouts(full_structure)
        
        # 3단계: 문제 경계 및 구조 파악
        print("📝 3단계: 문제 경계 및 구조 파악")
        question_structure = await self._identify_question_boundaries(layout_analysis)
        
        # 4단계: 표/이미지/다이어그램 추출
        print("🖼️ 4단계: 표/이미지/다이어그램 추출")
        visual_elements = await self._extract_visual_elements(full_structure, question_structure)
        
        # 5단계: 크로스 페이지 연결 분석
        print("🔗 5단계: 크로스 페이지 연결 분석")
        cross_page_analysis = await self._analyze_cross_page_connections(question_structure)
        
        # 6단계: 구조 기반 문제 재구성
        print("🔧 6단계: 구조 기반 문제 재구성")
        reconstructed_questions = await self._reconstruct_questions_from_structure(
            question_structure, visual_elements, cross_page_analysis
        )
        
        return {
            "success": True,
            "full_structure": full_structure,
            "layout_analysis": layout_analysis,
            "question_structure": question_structure,
            "visual_elements": visual_elements,
            "cross_page_analysis": cross_page_analysis,
            "reconstructed_questions": reconstructed_questions,
            "analysis_method": "comprehensive_structure_based"
        }
    
    async def _extract_full_pdf_structure(self, pdf_path: str, upload_id: int) -> Dict[str, Any]:
        """1단계: PDF 전체 구조 정보 추출"""
        
        doc = fitz.open(pdf_path)
        assets_dir = Path(f"assets/upload_{upload_id}")
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        structure_data = {
            "total_pages": len(doc),
            "pages": [],
            "fonts_used": set(),
            "color_schemes": set(),
            "asset_paths": {}
        }
        
        print(f"   📖 총 {len(doc)} 페이지 분석 시작")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # 페이지 기본 정보
            page_info = {
                "page_number": page_num + 1,
                "width": page.rect.width,
                "height": page.rect.height,
                "text_blocks": [],
                "images": [],
                "drawings": [],
                "annotations": []
            }
            
            # === 텍스트 블록 정보 추출 (위치, 폰트, 크기 포함) ===
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if "lines" in block:  # 텍스트 블록
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_block = {
                                "text": span["text"].strip(),
                                "bbox": span["bbox"],  # (x0, y0, x1, y1)
                                "font": span["font"],
                                "size": span["size"],
                                "flags": span["flags"],  # bold, italic 등
                                "color": span["color"],
                                "origin": span["origin"]  # (x, y) 시작점
                            }
                            
                            if text_block["text"]:  # 빈 텍스트 제외
                                page_info["text_blocks"].append(text_block)
                                structure_data["fonts_used"].add(span["font"])
                                structure_data["color_schemes"].add(span["color"])
            
            # === 이미지 추출 ===
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                if pix.n - pix.alpha < 4:  # 컬러 또는 그레이스케일
                    img_bbox = page.get_image_bbox(img)
                    
                    # 이미지 저장
                    img_filename = f"page_{page_num+1}_img_{img_index}.png"
                    img_path = assets_dir / img_filename
                    pix.save(str(img_path))
                    
                    page_info["images"].append({
                        "bbox": img_bbox,
                        "file_path": str(img_path),
                        "xref": xref,
                        "width": pix.width,
                        "height": pix.height
                    })
                
                pix = None
            
            # === 그래픽 요소 (선, 도형 등) ===
            drawings = page.get_drawings()
            for drawing in drawings:
                page_info["drawings"].append({
                    "type": drawing.get("type"),
                    "bbox": drawing.get("rect"),
                    "stroke_color": drawing.get("color"),
                    "stroke_width": drawing.get("width"),
                    "fill_color": drawing.get("fill")
                })
            
            structure_data["pages"].append(page_info)
            print(f"   📄 페이지 {page_num+1}: 텍스트블록 {len(page_info['text_blocks'])}개, 이미지 {len(page_info['images'])}개, 그래픽 {len(page_info['drawings'])}개")
        
        doc.close()
        
        # 폰트와 색상 정보 정리
        structure_data["fonts_used"] = list(structure_data["fonts_used"])
        structure_data["color_schemes"] = list(structure_data["color_schemes"])
        
        print(f"   📊 사용된 폰트: {len(structure_data['fonts_used'])}개")
        print(f"   🎨 색상 스키마: {len(structure_data['color_schemes'])}개")
        
        return structure_data
    
    async def _analyze_page_layouts(self, structure_data: Dict[str, Any]) -> Dict[str, Any]:
        """2단계: 페이지별 레이아웃 분석"""
        
        layouts = []
        
        for page_info in structure_data["pages"]:
            page_num = page_info["page_number"]
            width = page_info["width"]
            height = page_info["height"]
            
            # 텍스트 블록을 Y좌표로 정렬 (위에서 아래로)
            text_blocks = sorted(page_info["text_blocks"], key=lambda b: b["bbox"][1])
            
            # 레이아웃 영역 분석
            layout_regions = self._identify_layout_regions(text_blocks, width, height)
            
            # 텍스트 블록 분류
            classified_blocks = self._classify_text_blocks(text_blocks)
            
            page_layout = {
                "page_number": page_num,
                "dimensions": {"width": width, "height": height},
                "layout_regions": layout_regions,
                "classified_blocks": classified_blocks,
                "images": page_info["images"],
                "drawings": page_info["drawings"]
            }
            
            layouts.append(page_layout)
            print(f"   📐 페이지 {page_num} 레이아웃: {len(layout_regions)}개 영역, {len(classified_blocks)}개 분류")
        
        return {"page_layouts": layouts}
    
    def _identify_layout_regions(self, text_blocks: List[Dict], width: float, height: float) -> Dict[str, Any]:
        """페이지 레이아웃 영역 식별"""
        
        if not text_blocks:
            return {"header": None, "footer": None, "content": None}
        
        # Y좌표 분석으로 header, content, footer 구분
        y_coords = [block["bbox"][1] for block in text_blocks]
        min_y, max_y = min(y_coords), max(y_coords)
        
        header_threshold = height * 0.1  # 상위 10%
        footer_threshold = height * 0.9  # 하위 10%
        
        header_blocks = [b for b in text_blocks if b["bbox"][1] < header_threshold]
        footer_blocks = [b for b in text_blocks if b["bbox"][3] > footer_threshold]
        content_blocks = [b for b in text_blocks if header_threshold <= b["bbox"][1] <= footer_threshold]
        
        return {
            "header": header_blocks,
            "footer": footer_blocks,  
            "content": content_blocks,
            "content_area": {
                "x0": 0, "y0": header_threshold,
                "x1": width, "y1": footer_threshold
            }
        }
    
    def _classify_text_blocks(self, text_blocks: List[Dict]) -> Dict[str, List]:
        """텍스트 블록을 용도별로 분류"""
        
        classified = {
            "question_numbers": [],
            "question_texts": [],
            "choices": [],
            "table_cells": [],
            "code_blocks": [],
            "general_text": []
        }
        
        for block in text_blocks:
            text = block["text"]
            font_size = block["size"]
            
            # 문제 번호 패턴 검사
            if any(re.match(pattern, text) for pattern in self.question_patterns):
                classified["question_numbers"].append(block)
            # 선택지 패턴 검사
            elif any(re.match(pattern, text) for pattern in self.choice_patterns):
                classified["choices"].append(block)
            # 표 셀 (정렬된 텍스트, 숫자 위주)
            elif self._looks_like_table_cell(text, block):
                classified["table_cells"].append(block)
            # 코드 블록 (고정폭 폰트, 들여쓰기)
            elif self._looks_like_code(text, block):
                classified["code_blocks"].append(block)
            # 문제 텍스트 (중간 크기 폰트)
            elif font_size > 10:
                classified["question_texts"].append(block)
            else:
                classified["general_text"].append(block)
        
        return classified
    
    def _looks_like_table_cell(self, text: str, block: Dict) -> bool:
        """표 셀인지 판별"""
        # 짧은 텍스트, 숫자나 간단한 단어
        if len(text) < 20 and (text.isdigit() or 
                               re.match(r'^[A-Za-z0-9가-힣]{1,10}$', text) or
                               '|' in text):
            return True
        return False
    
    def _looks_like_code(self, text: str, block: Dict) -> bool:
        """코드 블록인지 판별"""
        code_indicators = [
            'public', 'class', 'void', 'int', 'String',
            'if', 'for', 'while', 'return', '{', '}',
            'System.out.println', '#include', 'def', 'import'
        ]
        
        return any(indicator in text for indicator in code_indicators)
    
    async def _identify_question_boundaries(self, layout_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """3단계: 문제 경계 및 구조 파악"""
        
        question_boundaries = []
        
        for page_layout in layout_analysis["page_layouts"]:
            page_num = page_layout["page_number"]
            classified_blocks = page_layout["classified_blocks"]
            
            # 문제 번호를 기준으로 문제 경계 설정
            question_numbers = classified_blocks["question_numbers"]
            
            for i, q_num_block in enumerate(question_numbers):
                question_number = self._extract_question_number(q_num_block["text"])
                
                if question_number:
                    # 다음 문제 번호까지의 영역 계산
                    start_y = q_num_block["bbox"][1]
                    
                    if i + 1 < len(question_numbers):
                        end_y = question_numbers[i + 1]["bbox"][1]
                    else:
                        # 마지막 문제인 경우 페이지 끝까지
                        end_y = page_layout["dimensions"]["height"] * 0.9
                    
                    # 해당 영역의 모든 요소 수집
                    question_elements = self._collect_question_elements(
                        page_layout, start_y, end_y, question_number
                    )
                    
                    question_boundaries.append({
                        "question_number": question_number,
                        "page_number": page_num,
                        "boundary": {"start_y": start_y, "end_y": end_y},
                        "elements": question_elements
                    })
        
        print(f"   📍 문제 경계 파악: {len(question_boundaries)}개 문제 영역 식별")
        return {"question_boundaries": question_boundaries}
    
    def _extract_question_number(self, text: str) -> Optional[int]:
        """텍스트에서 문제 번호 추출"""
        for pattern in self.question_patterns:
            match = re.match(pattern, text.strip())
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None
    
    def _collect_question_elements(self, page_layout: Dict, start_y: float, end_y: float, 
                                   question_num: int) -> Dict[str, List]:
        """문제 영역 내의 모든 요소 수집"""
        
        elements = {
            "question_text": [],
            "choices": [],
            "images": [],
            "tables": [],
            "code": []
        }
        
        # 텍스트 요소들
        for category, blocks in page_layout["classified_blocks"].items():
            for block in blocks:
                bbox = block["bbox"]
                if start_y <= bbox[1] <= end_y:
                    if category == "choices":
                        elements["choices"].append(block)
                    elif category == "question_texts":
                        elements["question_text"].append(block)
                    elif category == "table_cells":
                        elements["tables"].append(block)
                    elif category == "code_blocks":
                        elements["code"].append(block)
        
        # 이미지 요소들
        for img in page_layout["images"]:
            img_bbox = img["bbox"]
            if start_y <= img_bbox[1] <= end_y:
                elements["images"].append(img)
        
        return elements
    
    async def _extract_visual_elements(self, structure_data: Dict, question_structure: Dict) -> Dict[str, Any]:
        """4단계: 표/이미지/다이어그램 추출 및 분류"""
        
        visual_elements = {
            "tables": [],
            "diagrams": [],
            "code_images": [],
            "choice_images": []
        }
        
        for question in question_structure["question_boundaries"]:
            q_num = question["question_number"]
            elements = question["elements"]
            
            # 표 요소 처리
            if elements["tables"]:
                table_data = await self._process_table_elements(elements["tables"], q_num)
                if table_data:
                    visual_elements["tables"].append(table_data)
            
            # 이미지 요소 처리 
            if elements["images"]:
                for img in elements["images"]:
                    img_type = await self._classify_image_type(img, elements)
                    visual_elements[img_type].append({
                        "question_number": q_num,
                        "image_info": img,
                        "classification": img_type
                    })
        
        print(f"   🖼️ 시각 요소 추출: 표 {len(visual_elements['tables'])}개, 다이어그램 {len(visual_elements['diagrams'])}개")
        return visual_elements
    
    async def _process_table_elements(self, table_blocks: List[Dict], question_num: int) -> Optional[Dict]:
        """표 요소들을 분석하여 구조화된 표 데이터 생성"""
        
        if not table_blocks:
            return None
        
        # 표 셀들을 위치별로 정렬
        sorted_cells = sorted(table_blocks, key=lambda cell: (cell["bbox"][1], cell["bbox"][0]))
        
        # 행과 열 구조 파악
        rows = self._group_table_cells_by_rows(sorted_cells)
        
        return {
            "question_number": question_num,
            "table_structure": rows,
            "cell_count": len(table_blocks),
            "estimated_rows": len(rows),
            "raw_cells": table_blocks
        }
    
    def _group_table_cells_by_rows(self, cells: List[Dict]) -> List[List[Dict]]:
        """표 셀들을 행별로 그룹화"""
        
        if not cells:
            return []
        
        rows = []
        current_row = [cells[0]]
        current_y = cells[0]["bbox"][1]
        
        for cell in cells[1:]:
            cell_y = cell["bbox"][1]
            
            # Y좌표 차이가 작으면 같은 행
            if abs(cell_y - current_y) < 10:  # 10pt 허용 오차
                current_row.append(cell)
            else:
                # 새로운 행 시작
                rows.append(current_row)
                current_row = [cell]
                current_y = cell_y
        
        rows.append(current_row)  # 마지막 행 추가
        return rows
    
    async def _classify_image_type(self, img_info: Dict, elements: Dict) -> str:
        """이미지 타입 분류"""
        
        # 크기 기반 분류
        bbox = img_info["bbox"]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        area = width * height
        
        # 작은 이미지는 선택지 이미지일 가능성
        if area < 5000:  # 작은 이미지
            return "choice_images"
        
        # 코드와 함께 있으면 코드 관련 이미지
        if elements.get("code"):
            return "code_images"
        
        # 기본적으로 다이어그램으로 분류
        return "diagrams"
    
    async def _analyze_cross_page_connections(self, question_structure: Dict) -> Dict[str, Any]:
        """5단계: 크로스 페이지 연결 분석"""
        
        cross_page_issues = []
        questions = question_structure["question_boundaries"]
        
        for i, question in enumerate(questions):
            q_num = question["question_number"]
            page_num = question["page_number"]
            elements = question["elements"]
            
            # 선택지 부족 검사
            choice_count = len(elements["choices"])
            if choice_count < 4:  # 일반적으로 4개 선택지 필요
                # 다음 페이지에서 나머지 선택지 찾기
                next_page_choices = self._find_choices_on_next_page(
                    q_num, page_num, questions
                )
                
                if next_page_choices:
                    cross_page_issues.append({
                        "question_number": q_num,
                        "issue_type": "incomplete_choices",
                        "current_page": page_num,
                        "current_choices": choice_count,
                        "next_page_choices": next_page_choices
                    })
        
        print(f"   🔗 크로스 페이지 연결: {len(cross_page_issues)}개 문제 감지")
        return {"cross_page_issues": cross_page_issues}
    
    def _find_choices_on_next_page(self, q_num: int, current_page: int, 
                                   all_questions: List[Dict]) -> List[Dict]:
        """다음 페이지에서 해당 문제의 나머지 선택지 찾기"""
        
        next_page_questions = [q for q in all_questions if q["page_number"] == current_page + 1]
        
        if not next_page_questions:
            return []
        
        # 다음 페이지 첫 번째 영역의 선택지들 중에서 연속되는 것들 찾기
        first_question = next_page_questions[0]
        choices = first_question["elements"]["choices"]
        
        # 선택지 마커 분석하여 연속성 확인
        return self._filter_continuing_choices(choices)
    
    def _filter_continuing_choices(self, choices: List[Dict]) -> List[Dict]:
        """연속되는 선택지들만 필터링"""
        
        continuing_choices = []
        expected_markers = ["③", "④", "⑤"]  # ①②가 이전 페이지에 있었다고 가정
        
        for choice in choices:
            text = choice["text"]
            if any(marker in text for marker in expected_markers):
                continuing_choices.append(choice)
        
        return continuing_choices
    
    async def _reconstruct_questions_from_structure(self, question_structure: Dict, 
                                                     visual_elements: Dict, 
                                                     cross_page_analysis: Dict) -> List[Dict]:
        """6단계: 구조 기반 문제 재구성"""
        
        reconstructed = []
        questions = question_structure["question_boundaries"]
        cross_page_issues = cross_page_analysis["cross_page_issues"]
        
        for question in questions:
            q_num = question["question_number"]
            elements = question["elements"]
            
            # 기본 문제 구조
            question_data = {
                "question_number": q_num,
                "question_text": self._combine_question_text(elements["question_text"]),
                "choices": self._format_choices(elements["choices"]),
                "page_number": question["page_number"],
                "has_table": len(elements["tables"]) > 0,
                "has_image": len(elements["images"]) > 0,
                "has_code": len(elements["code"]) > 0
            }
            
            # 크로스 페이지 이슈 해결
            cross_page_issue = next((issue for issue in cross_page_issues 
                                   if issue["question_number"] == q_num), None)
            
            if cross_page_issue:
                question_data["choices"].extend(
                    self._format_choices(cross_page_issue["next_page_choices"])
                )
                question_data["cross_page_resolved"] = True
            
            # 시각 요소 연결
            question_data["visual_elements"] = self._get_visual_elements_for_question(
                q_num, visual_elements
            )
            
            reconstructed.append(question_data)
        
        print(f"   🔧 구조 기반 재구성: {len(reconstructed)}개 문제 완료")
        return reconstructed
    
    def _combine_question_text(self, text_blocks: List[Dict]) -> str:
        """문제 텍스트 블록들을 결합"""
        if not text_blocks:
            return ""
        
        # Y좌표로 정렬하여 순서대로 결합
        sorted_blocks = sorted(text_blocks, key=lambda b: b["bbox"][1])
        return " ".join(block["text"] for block in sorted_blocks)
    
    def _format_choices(self, choice_blocks: List[Dict]) -> List[Dict]:
        """선택지 블록들을 포맷"""
        formatted = []
        
        for block in choice_blocks:
            text = block["text"]
            
            # 선택지 마커 추출
            marker = None
            for pattern in self.choice_patterns:
                match = re.match(pattern, text)
                if match:
                    marker = match.group(0).strip()
                    text = re.sub(pattern, "", text).strip()
                    break
            
            if marker:
                formatted.append({
                    "marker": marker,
                    "content": text,
                    "bbox": block["bbox"]
                })
        
        return formatted
    
    def _get_visual_elements_for_question(self, q_num: int, visual_elements: Dict) -> Dict:
        """특정 문제의 시각 요소들 가져오기"""
        
        question_visuals = {
            "tables": [],
            "diagrams": [],
            "code_images": [],
            "choice_images": []
        }
        
        for element_type, elements in visual_elements.items():
            for element in elements:
                if element.get("question_number") == q_num:
                    question_visuals[element_type].append(element)
        
        return question_visuals