#!/usr/bin/env python3
"""
🚀 통합 PDF 처리 시스템: 페이지 경계를 무시한 전체적 접근 방식
기존 페이지별 처리의 문제점들을 해결하는 새로운 아키텍처
"""

import re
import json
import base64
from PIL import Image
import io
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import fitz  # PyMuPDF
import openai
from datetime import datetime
import numpy as np

class UnifiedPDFProcessor:
    """통합 PDF 처리 시스템 - 페이지 경계 무시하고 전체적으로 처리"""
    
    def __init__(self, openai_client: openai.AsyncOpenAI):
        self.openai_client = openai_client
        
        # PDF 전체 규칙
        self.PDF_RULES = {
            "total_questions": 60,
            "questions_per_page": 15,  # 평균적으로
            "choice_markers": ["①", "②", "③", "④"],
            "subjects": {
                "1-20": "정보시스템 기반 기술", 
                "21-40": "프로그래밍 언어 활용",
                "41-60": "데이터베이스 활용"
            }
        }
    
    async def process_pdf_unified(self, pdf_path: str, upload_id: int) -> Dict[str, Any]:
        """통합 처리 메인 함수"""
        
        print("🚀 통합 PDF 처리 시스템 시작")
        print("=" * 60)
        
        try:
            # === 1단계: 전체 PDF 컨텍스트 구축 ===
            print("📋 1단계: 전체 PDF 컨텍스트 구축")
            full_context = await self._build_full_pdf_context(pdf_path, upload_id)
            
            # === 2단계: 크로스 페이지 인식 처리 ===
            print("🔗 2단계: 크로스 페이지 연결 처리")
            connected_content = await self._process_cross_page_connections(full_context)
            
            # === 3단계: 통합 문제 추출 ===
            print("📝 3단계: 통합 문제 추출")
            unified_questions = await self._extract_questions_unified(connected_content)
            
            # === 4단계: 특수 요소 통합 처리 ===
            print("🎨 4단계: 특수 요소 통합 처리")
            enhanced_questions = await self._process_special_elements_unified(unified_questions, full_context)
            
            # === 5단계: 최종 검증 및 정리 ===
            print("✅ 5단계: 최종 검증 및 정리")
            final_questions = self._finalize_and_validate(enhanced_questions)
            
            print(f"✅ 통합 처리 완료: {len(final_questions)}개 문제 추출")
            
            return {
                "success": True,
                "questions": final_questions,
                "total_questions": len(final_questions),
                "processing_method": "unified_processing",
                "context_data": full_context
            }
            
        except Exception as e:
            print(f"❌ 통합 처리 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def _build_full_pdf_context(self, pdf_path: str, upload_id: int) -> Dict[str, Any]:
        """1단계: 전체 PDF 컨텍스트 구축 - 페이지 경계 정보 포함"""
        
        assets_dir = Path(f"assets/upload_{upload_id}")
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        doc = fitz.open(pdf_path)
        
        # 전체 PDF를 하나의 큰 이미지로 연결 (세로 방향)
        combined_image = self._create_combined_image(doc, assets_dir)
        
        # 페이지별 정보도 함께 저장 (위치 참조용)
        page_boundaries = []
        current_height = 0
        
        pages_info = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # 페이지 이미지 생성
            mat = fitz.Matrix(3.0, 3.0)  # 300dpi
            pix = page.get_pixmap(matrix=mat)
            img_path = assets_dir / f"page_{page_num + 1}.png"
            pix.save(str(img_path))
            
            # 페이지 경계 정보
            page_height = pix.height
            page_boundaries.append({
                "page_number": page_num + 1,
                "start_y": current_height,
                "end_y": current_height + page_height,
                "height": page_height,
                "image_path": str(img_path)
            })
            current_height += page_height
            
            # 텍스트와 좌표 정보
            text_dict = page.get_text("dict")
            raw_text = page.get_text()
            
            pages_info.append({
                "page_number": page_num + 1,
                "raw_text": raw_text,
                "text_dict": text_dict,
                "image_path": str(img_path),
                "boundary": page_boundaries[-1]
            })
        
        doc.close()
        
        return {
            "combined_image_path": str(assets_dir / "combined_full.png"),
            "page_boundaries": page_boundaries,
            "pages_info": pages_info,
            "total_height": current_height,
            "assets_dir": str(assets_dir)
        }
    
    def _create_combined_image(self, doc: fitz.Document, assets_dir: Path) -> str:
        """모든 페이지를 세로로 연결한 통합 이미지 생성"""
        
        page_images = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            mat = fitz.Matrix(3.0, 3.0)  # 300dpi
            pix = page.get_pixmap(matrix=mat)
            
            # PIL Image로 변환
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            page_images.append(img)
        
        if not page_images:
            return ""
        
        # 모든 이미지의 너비는 같다고 가정하고, 높이를 합쳐서 하나의 긴 이미지 생성
        total_width = page_images[0].width
        total_height = sum(img.height for img in page_images)
        
        combined_image = Image.new('RGB', (total_width, total_height), 'white')
        
        current_y = 0
        for img in page_images:
            combined_image.paste(img, (0, current_y))
            current_y += img.height
        
        # 저장
        combined_path = assets_dir / "combined_full.png"
        combined_image.save(combined_path)
        
        return str(combined_path)
    
    async def _process_cross_page_connections(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """2단계: 크로스 페이지 연결 분석"""
        
        print("   🔗 크로스 페이지 경계 분석 중...")
        
        # 페이지 경계에서 잘린 요소들 탐지
        cross_page_elements = []
        
        for i in range(len(context["page_boundaries"]) - 1):
            current_page = context["page_boundaries"][i]
            next_page = context["page_boundaries"][i + 1]
            
            # 경계 부근의 텍스트 분석
            boundary_analysis = self._analyze_page_boundary(
                context["pages_info"][i], 
                context["pages_info"][i + 1]
            )
            
            if boundary_analysis["has_cross_page_element"]:
                cross_page_elements.append({
                    "from_page": current_page["page_number"],
                    "to_page": next_page["page_number"],
                    "element_type": boundary_analysis["element_type"],
                    "partial_content": boundary_analysis["content"]
                })
        
        print(f"   📊 크로스 페이지 요소 {len(cross_page_elements)}개 발견")
        
        context["cross_page_elements"] = cross_page_elements
        return context
    
    def _analyze_page_boundary(self, current_page: Dict, next_page: Dict) -> Dict[str, Any]:
        """페이지 경계 분석 - 잘린 요소 탐지"""
        
        current_text = current_page["raw_text"]
        next_text = next_page["raw_text"]
        
        # 현재 페이지 끝부분 (마지막 10줄)
        current_lines = current_text.strip().split('\n')[-10:]
        # 다음 페이지 시작부분 (처음 10줄)
        next_lines = next_text.strip().split('\n')[:10]
        
        # 잘린 선택지 패턴 탐지
        choice_patterns = [r'①.*', r'②.*', r'③.*', r'④.*']
        incomplete_choices = []
        
        for line in current_lines:
            for pattern in choice_patterns:
                if re.search(pattern, line) and (len(line) < 20 or line.endswith('...')):
                    incomplete_choices.append(line)
        
        # 다음 페이지에서 연결되는 부분 찾기
        continuation_found = False
        for line in next_lines:
            for pattern in choice_patterns:
                if re.search(pattern, line):
                    continuation_found = True
                    break
        
        # 표 경계 분석
        table_boundary = self._detect_table_boundary(current_lines, next_lines)
        
        if incomplete_choices or table_boundary["has_table_split"]:
            return {
                "has_cross_page_element": True,
                "element_type": "table" if table_boundary["has_table_split"] else "choices",
                "content": {
                    "incomplete_choices": incomplete_choices,
                    "table_info": table_boundary,
                    "continuation_found": continuation_found
                }
            }
        
        return {"has_cross_page_element": False, "element_type": None, "content": None}
    
    def _detect_table_boundary(self, current_lines: List[str], next_lines: List[str]) -> Dict[str, Any]:
        """표 경계 탐지"""
        
        # 표 패턴 (프로세스, 도착시간, 실행시간 등)
        table_keywords = ["프로세스", "도착시간", "실행시간", "P1", "P2", "P3", "|"]
        
        current_has_table = any(keyword in ' '.join(current_lines) for keyword in table_keywords)
        next_has_table = any(keyword in ' '.join(next_lines) for keyword in table_keywords)
        
        # 현재 페이지에는 헤더가 있고 다음 페이지에는 데이터가 있는 경우
        header_pattern = r'프로세스.*도착시간.*실행시간'
        data_pattern = r'P[1-9].*\d+.*\d+'
        
        has_header_current = bool(re.search(header_pattern, ' '.join(current_lines)))
        has_data_next = bool(re.search(data_pattern, ' '.join(next_lines)))
        
        return {
            "has_table_split": (current_has_table and next_has_table) or (has_header_current and has_data_next),
            "header_in_current": has_header_current,
            "data_in_next": has_data_next,
            "keywords_found": [kw for kw in table_keywords if kw in ' '.join(current_lines + next_lines)]
        }
    
    async def _extract_questions_unified(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """3단계: 통합 이미지를 사용한 문제 추출"""
        
        print("   📝 통합 이미지로 전체 문제 추출 중...")
        
        # 통합 이미지를 base64로 인코딩
        with open(context["combined_image_path"], "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 통합 추출 프롬프트 - OCR 정확도 향상 포함
        prompt = """이 PDF 전체 이미지에서 60개의 시험 문제를 모두 추출해 주세요.

**핵심 개선사항:**
- 페이지 경계를 넘나드는 선택지/표/코드를 완전히 추출하세요
- 잘린 내용은 연결해서 완성하세요
- 표의 경우 헤더와 데이터를 모두 포함하세요
- 문제 번호 1번부터 60번까지 모든 문제를 찾아서 추출하세요

**문자 인식 정확도 향상 규칙:**
- 숫자: 2/3, 0/O, 1/l/I, 5/S, 8/B, 6/9 정확히 구분
- 기호: *, +, =, -, /, %, !=, <=, >= 정확히 인식
- 한글: 받침 유무, 모음 구분 (ㅏ/ㅓ, ㅗ/ㅜ) 정확히 인식
- 영문: 대소문자, 변수명, 함수명 정확히 복사
- 괄호: (), {}, [], <> 형태 정확히 구분
- 선택지: ①②③④ 마커 정확히 인식

**표/코드/이미지 처리:**
- 표: 마크다운 형식으로 정확한 구조 유지
- 코드: 들여쓰기와 문법 정확히 보존
- 선택지: 중복 없이 완전한 내용으로 추출

JSON 형식으로 응답하세요 (백틱 없이 직접):

{
  "questions": [
    {
      "question_number": 1,
      "question_text": "문제 내용",
      "choices": [
        {"marker": "①", "content": "선택지 1"},
        {"marker": "②", "content": "선택지 2"},
        {"marker": "③", "content": "선택지 3"},
        {"marker": "④", "content": "선택지 4"}
      ],
      "passage": "보기 내용 (있는 경우)",
      "has_table": false,
      "has_image": false,
      "has_code": false,
      "y_position": 1200
    }
  ]
}"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "PDF 시험 문제 통합 추출 전문가. 페이지 경계를 넘나드는 내용을 완전히 연결하여 추출합니다."
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
                max_tokens=16000,  # 더 큰 응답 허용
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content
            result = self._parse_questions_json(response_text)
            
            if result and "questions" in result:
                questions = result["questions"]
                print(f"   ✅ 통합 추출 완료: {len(questions)}개 문제")
                return questions
            else:
                print("   ❌ JSON 파싱 실패")
                return []
                
        except Exception as e:
            print(f"   ❌ 통합 추출 실패: {e}")
            return []
    
    def _parse_questions_json(self, response_text: str) -> Optional[Dict]:
        """JSON 응답 파싱"""
        try:
            # ```json ... ``` 블록에서 JSON 추출
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text
            
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            return None
    
    async def _process_special_elements_unified(self, questions: List[Dict], context: Dict[str, Any]) -> List[Dict]:
        """4단계: 특수 요소 통합 처리"""
        
        print("   🎨 특수 요소 통합 처리 중...")
        
        special_questions = []
        for question in questions:
            # 표가 있는 문제 처리
            if question.get('has_table'):
                enhanced_q = await self._enhance_table_question(question, context)
                special_questions.append(enhanced_q)
            # 코드가 있는 문제 처리
            elif question.get('has_code'):
                enhanced_q = await self._enhance_code_question(question, context)
                special_questions.append(enhanced_q)
            # 이미지가 있는 문제 처리
            elif question.get('has_image'):
                enhanced_q = await self._enhance_image_question(question, context)
                special_questions.append(enhanced_q)
            else:
                special_questions.append(question)
        
        return special_questions
    
    async def _enhance_table_question(self, question: Dict, context: Dict[str, Any]) -> Dict:
        """표가 있는 문제 개선 처리"""
        
        # 크로스 페이지 표 정보 확인
        table_elements = [elem for elem in context.get("cross_page_elements", []) 
                         if elem["element_type"] == "table"]
        
        if table_elements:
            print(f"      📊 문제 {question.get('question_number')}번: 크로스 페이지 표 처리")
            # 표 데이터를 완전히 재구성
            complete_table = self._reconstruct_table(question, table_elements)
            question["passage"] = complete_table
            
            # 표 이미지도 저장
            table_image_path = await self._extract_table_as_image(question, context)
            if table_image_path:
                question["table_image_path"] = table_image_path
        
        return question
    
    def _reconstruct_table(self, question: Dict, table_elements: List[Dict]) -> str:
        """크로스 페이지 표 재구성"""
        
        passage = question.get("passage", "")
        
        # 표 키워드 기반 재구성
        if "프로세스" in passage and "도착시간" in passage:
            # 스케줄링 표 패턴
            table_data = self._extract_scheduling_table_data(passage, table_elements)
            return self._format_as_markdown_table(table_data)
        
        return passage
    
    def _extract_scheduling_table_data(self, passage: str, table_elements: List[Dict]) -> Dict:
        """스케줄링 표 데이터 추출"""
        
        # 헤더와 데이터 분리
        lines = passage.split('\n')
        header = ["프로세스", "도착시간", "실행시간"]
        
        data_rows = []
        for line in lines:
            if re.search(r'P\d+', line):  # P1, P2, P3 패턴
                parts = re.findall(r'P\d+|\d+', line)
                if len(parts) >= 3:
                    data_rows.append(parts[:3])
        
        # 크로스 페이지에서 누락된 데이터 보완
        for element in table_elements:
            additional_data = element["partial_content"].get("table_info", {})
            # 추가 데이터 처리 로직
        
        return {
            "header": header,
            "rows": data_rows
        }
    
    def _format_as_markdown_table(self, table_data: Dict) -> str:
        """마크다운 표 형식으로 변환"""
        
        if not table_data.get("header") or not table_data.get("rows"):
            return ""
        
        # 헤더
        header_row = " | ".join(table_data["header"])
        separator = " | ".join(["---"] * len(table_data["header"]))
        
        # 데이터 행들
        data_rows = []
        for row in table_data["rows"]:
            data_row = " | ".join(str(cell) for cell in row)
            data_rows.append(data_row)
        
        # 완성된 표
        table = f"| {header_row} |\n| {separator} |\n"
        for data_row in data_rows:
            table += f"| {data_row} |\n"
        
        return table
    
    async def _extract_table_as_image(self, question: Dict, context: Dict[str, Any]) -> Optional[str]:
        """표를 이미지로 추출하여 저장"""
        
        # 문제의 Y 위치를 기반으로 해당 영역의 이미지 추출
        y_position = question.get("y_position", 0)
        
        if y_position > 0:
            # 통합 이미지에서 해당 영역 추출
            full_image = Image.open(context["combined_image_path"])
            
            # 표 영역 추정 (Y 위치 기준으로 위아래 200px 여유)
            crop_area = (0, max(0, y_position - 200), full_image.width, min(full_image.height, y_position + 400))
            table_image = full_image.crop(crop_area)
            
            # 저장
            assets_dir = Path(context["assets_dir"])
            table_path = assets_dir / f"q{question.get('question_number', 'unknown')}_table.png"
            table_image.save(table_path)
            
            return str(table_path)
        
        return None
    
    async def _enhance_code_question(self, question: Dict, context: Dict[str, Any]) -> Dict:
        """코드가 있는 문제 개선 처리"""
        
        print(f"      💻 문제 {question.get('question_number')}번: 코드 블록 처리")
        
        # 코드 이미지 추출
        code_image_path = await self._extract_code_as_image(question, context)
        if code_image_path:
            question["code_image_path"] = code_image_path
        
        return question
    
    async def _extract_code_as_image(self, question: Dict, context: Dict[str, Any]) -> Optional[str]:
        """코드를 이미지로 추출하여 저장"""
        
        # 표와 같은 방식으로 코드 영역 추출
        y_position = question.get("y_position", 0)
        
        if y_position > 0:
            full_image = Image.open(context["combined_image_path"])
            crop_area = (0, max(0, y_position - 100), full_image.width, min(full_image.height, y_position + 300))
            code_image = full_image.crop(crop_area)
            
            assets_dir = Path(context["assets_dir"])
            code_path = assets_dir / f"q{question.get('question_number', 'unknown')}_code.png"
            code_image.save(code_path)
            
            return str(code_path)
        
        return None
    
    async def _enhance_image_question(self, question: Dict, context: Dict[str, Any]) -> Dict:
        """이미지가 있는 문제 개선 처리"""
        
        print(f"      🖼️ 문제 {question.get('question_number')}번: 이미지 처리")
        
        # 다이어그램/그림 이미지 추출
        diagram_image_path = await self._extract_diagram_as_image(question, context)
        if diagram_image_path:
            question["diagram_image_path"] = diagram_image_path
        
        return question
    
    async def _extract_diagram_as_image(self, question: Dict, context: Dict[str, Any]) -> Optional[str]:
        """다이어그램을 이미지로 추출하여 저장"""
        
        y_position = question.get("y_position", 0)
        
        if y_position > 0:
            full_image = Image.open(context["combined_image_path"])
            crop_area = (0, max(0, y_position - 150), full_image.width, min(full_image.height, y_position + 350))
            diagram_image = full_image.crop(crop_area)
            
            assets_dir = Path(context["assets_dir"])
            diagram_path = assets_dir / f"q{question.get('question_number', 'unknown')}_diagram.png"
            diagram_image.save(diagram_path)
            
            return str(diagram_path)
        
        return None
    
    def _finalize_and_validate(self, questions: List[Dict]) -> List[Dict]:
        """5단계: 최종 검증 및 정리"""
        
        print("   ✅ 최종 검증 및 정리 중...")
        
        # 문제 번호 순서대로 정렬
        questions.sort(key=lambda q: q.get("question_number", 999))
        
        # 중복 제거
        seen_numbers = set()
        unique_questions = []
        
        for q in questions:
            q_num = q.get("question_number")
            if q_num and q_num not in seen_numbers:
                seen_numbers.add(q_num)
                unique_questions.append(q)
        
        # 누락된 번호 확인
        expected_numbers = set(range(1, 61))
        found_numbers = {q.get("question_number") for q in unique_questions}
        missing = expected_numbers - found_numbers
        
        if missing:
            print(f"   ⚠️ 누락된 문제: {sorted(missing)}")
        
        print(f"   📊 최종 정리 완료: {len(unique_questions)}개 문제")
        
        return unique_questions