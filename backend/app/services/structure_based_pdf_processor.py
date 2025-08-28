#!/usr/bin/env python3
"""
🏗️ 구조 기반 PDF 처리기
포괄적 구조 분석을 기반으로 정확한 문제 추출을 수행하는 시스템
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

from .comprehensive_pdf_analyzer import ComprehensivePDFAnalyzer

class StructureBasedPDFProcessor:
    """구조 기반 PDF 처리 - 완전한 구조 파악 후 정확한 추출"""
    
    def __init__(self, openai_client: openai.AsyncOpenAI):
        self.openai_client = openai_client
        self.analyzer = ComprehensivePDFAnalyzer(openai_client)
        
        # PDF 규칙
        self.PDF_RULES = {
            "total_questions": 60,
            "choice_markers": ["①", "②", "③", "④"],
            "subjects": {
                "1-20": "정보시스템 기반 기술", 
                "21-40": "프로그래밍 언어 활용",
                "41-60": "데이터베이스 활용"
            }
        }
    
    async def process_pdf_structure_based(self, pdf_path: str, upload_id: int) -> Dict[str, Any]:
        """구조 기반 PDF 처리 메인 함수"""
        
        print("🏗️ 구조 기반 PDF 처리 시작")
        print("=" * 60)
        
        try:
            # === 1단계: 포괄적 구조 분석 ===
            print("🔍 1단계: 포괄적 구조 분석")
            structure_analysis = await self.analyzer.analyze_pdf_comprehensive(pdf_path, upload_id)
            
            if not structure_analysis["success"]:
                return {"success": False, "error": "구조 분석 실패"}
            
            # === 2단계: 구조 기반 문제 추출 ===
            print("📝 2단계: 구조 기반 문제 추출")
            extracted_questions = await self._extract_questions_from_structure(
                structure_analysis["reconstructed_questions"]
            )
            
            # === 3단계: 시각 요소 처리 및 통합 ===
            print("🖼️ 3단계: 시각 요소 처리 및 통합")
            enhanced_questions = await self._integrate_visual_elements(
                extracted_questions, structure_analysis["visual_elements"], upload_id
            )
            
            # === 4단계: 정답 매칭 ===
            print("🎯 4단계: 정답 매칭")
            final_questions = await self._match_answers(enhanced_questions, pdf_path)
            
            # === 5단계: 품질 검증 ===
            print("✅ 5단계: 품질 검증")
            validation_result = self._validate_extraction_quality(final_questions)
            
            return {
                "success": True,
                "questions": final_questions,
                "structure_analysis": structure_analysis,
                "validation_result": validation_result,
                "processing_method": "structure_based_comprehensive",
                "total_questions": len(final_questions)
            }
            
        except Exception as e:
            print(f"❌ 구조 기반 처리 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def _extract_questions_from_structure(self, reconstructed_questions: List[Dict]) -> List[Dict]:
        """구조 분석 결과에서 문제 추출"""
        
        extracted = []
        
        for question_data in reconstructed_questions:
            q_num = question_data["question_number"]
            
            # 기본 문제 구조
            question = {
                "question_number": q_num,
                "question_text": question_data["question_text"],
                "choices": question_data["choices"],
                "page_number": question_data["page_number"],
                "correct_answer": None,  # 나중에 매칭
                
                # 구조 기반 메타데이터
                "has_table": question_data["has_table"],
                "has_image": question_data["has_image"],
                "has_code": question_data["has_code"],
                "cross_page_resolved": question_data.get("cross_page_resolved", False),
                "visual_elements": question_data["visual_elements"],
                
                # 추출 방법 정보
                "extraction_method": "structure_based",
                "structure_confidence": "high"
            }
            
            # 선택지 개수 확인
            if len(question["choices"]) < 4:
                print(f"   ⚠️ 문제 {q_num}번: 선택지 {len(question['choices'])}개 (4개 미만)")
            
            extracted.append(question)
        
        print(f"   📋 구조 기반 추출: {len(extracted)}개 문제")
        return extracted
    
    async def _integrate_visual_elements(self, questions: List[Dict], 
                                        visual_elements: Dict, upload_id: int) -> List[Dict]:
        """시각 요소를 문제에 통합"""
        
        assets_dir = Path(f"assets/upload_{upload_id}")
        
        for question in questions:
            q_num = question["question_number"]
            q_visuals = question["visual_elements"]
            
            # 표 요소 처리
            if q_visuals["tables"]:
                question["table_data"] = await self._process_table_for_question(
                    q_visuals["tables"], assets_dir, q_num
                )
            
            # 다이어그램 처리
            if q_visuals["diagrams"]:
                question["diagram_files"] = await self._save_diagrams_for_question(
                    q_visuals["diagrams"], assets_dir, q_num
                )
            
            # 코드 이미지 처리
            if q_visuals["code_images"]:
                question["code_content"] = await self._extract_code_from_images(
                    q_visuals["code_images"], q_num
                )
            
            # 선택지 이미지 처리
            if q_visuals["choice_images"]:
                question["choice_image_files"] = await self._save_choice_images(
                    q_visuals["choice_images"], assets_dir, q_num
                )
        
        print(f"   🖼️ 시각 요소 통합: 완료")
        return questions
    
    async def _process_table_for_question(self, table_data: List[Dict], 
                                         assets_dir: Path, q_num: int) -> Dict:
        """문제의 표 데이터 처리"""
        
        if not table_data:
            return None
        
        table_info = table_data[0]  # 첫 번째 표 사용
        
        # 표 구조를 마크다운 형식으로 변환
        markdown_table = self._convert_table_to_markdown(table_info["table_structure"])
        
        # 표 이미지도 저장
        table_image_path = await self._capture_table_image(table_info, assets_dir, q_num)
        
        return {
            "markdown_format": markdown_table,
            "image_path": table_image_path,
            "cell_count": table_info["cell_count"],
            "rows": table_info["estimated_rows"]
        }
    
    def _convert_table_to_markdown(self, table_structure: List[List[Dict]]) -> str:
        """표 구조를 마크다운으로 변환"""
        
        if not table_structure:
            return ""
        
        markdown_lines = []
        
        for i, row in enumerate(table_structure):
            # 셀 텍스트 추출
            cell_texts = [cell["text"] for cell in row]
            
            # 마크다운 행 생성
            markdown_row = "| " + " | ".join(cell_texts) + " |"
            markdown_lines.append(markdown_row)
            
            # 헤더 구분선 (첫 번째 행 후)
            if i == 0:
                separator = "| " + " | ".join(["---"] * len(cell_texts)) + " |"
                markdown_lines.append(separator)
        
        return "\n".join(markdown_lines)
    
    async def _capture_table_image(self, table_info: Dict, assets_dir: Path, q_num: int) -> str:
        """표 영역 이미지 캡처"""
        
        # 표 셀들의 bounding box 계산
        all_cells = table_info["raw_cells"]
        if not all_cells:
            return None
        
        # 전체 표 영역 계산
        min_x = min(cell["bbox"][0] for cell in all_cells)
        min_y = min(cell["bbox"][1] for cell in all_cells)
        max_x = max(cell["bbox"][2] for cell in all_cells)
        max_y = max(cell["bbox"][3] for cell in all_cells)
        
        table_bbox = (min_x, min_y, max_x, max_y)
        
        # 이미지 파일명
        table_image_name = f"q{q_num}_table.png"
        table_image_path = assets_dir / table_image_name
        
        # TODO: 실제 PDF에서 해당 영역 이미지 추출
        # 현재는 경로만 반환
        return str(table_image_path)
    
    async def _save_diagrams_for_question(self, diagrams: List[Dict], 
                                         assets_dir: Path, q_num: int) -> List[str]:
        """문제의 다이어그램 저장"""
        
        saved_files = []
        
        for i, diagram in enumerate(diagrams):
            img_info = diagram["image_info"]
            
            # 파일명 생성
            diagram_name = f"q{q_num}_diagram_{i+1}.png"
            diagram_path = assets_dir / diagram_name
            
            # 이미지 파일 복사 또는 이동
            if "file_path" in img_info:
                import shutil
                try:
                    shutil.copy2(img_info["file_path"], diagram_path)
                    saved_files.append(str(diagram_path))
                except Exception as e:
                    print(f"   ⚠️ 다이어그램 저장 실패 Q{q_num}: {e}")
        
        return saved_files
    
    async def _extract_code_from_images(self, code_images: List[Dict], q_num: int) -> Dict:
        """코드 이미지에서 코드 내용 추출"""
        
        if not code_images:
            return None
        
        # 첫 번째 코드 이미지 처리
        code_image = code_images[0]
        img_info = code_image["image_info"]
        
        # OpenAI Vision으로 코드 추출
        try:
            if "file_path" in img_info:
                with open(img_info["file_path"], "rb") as f:
                    image_data = f.read()
                
                base64_image = base64.b64encode(image_data).decode('utf-8')
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "이 이미지에서 프로그래밍 코드를 정확히 추출해주세요. 들여쓰기와 구문을 그대로 유지해주세요."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=1000,
                    temperature=0.1
                )
                
                code_text = response.choices[0].message.content
                
                return {
                    "code_text": code_text,
                    "language": self._detect_programming_language(code_text),
                    "image_path": img_info["file_path"]
                }
                
        except Exception as e:
            print(f"   ⚠️ 코드 추출 실패 Q{q_num}: {e}")
        
        return None
    
    def _detect_programming_language(self, code_text: str) -> str:
        """코드에서 프로그래밍 언어 감지"""
        
        if "public class" in code_text or "System.out.println" in code_text:
            return "java"
        elif "#include" in code_text or "printf" in code_text:
            return "c"
        elif "def " in code_text or "import " in code_text:
            return "python"
        elif "function" in code_text or "var " in code_text:
            return "javascript"
        else:
            return "unknown"
    
    async def _save_choice_images(self, choice_images: List[Dict], 
                                 assets_dir: Path, q_num: int) -> List[str]:
        """선택지 이미지 저장"""
        
        saved_files = []
        
        for i, choice_img in enumerate(choice_images):
            img_info = choice_img["image_info"]
            
            choice_name = f"q{q_num}_choice_{i+1}.png"
            choice_path = assets_dir / choice_name
            
            if "file_path" in img_info:
                import shutil
                try:
                    shutil.copy2(img_info["file_path"], choice_path)
                    saved_files.append(str(choice_path))
                except Exception as e:
                    print(f"   ⚠️ 선택지 이미지 저장 실패 Q{q_num}: {e}")
        
        return saved_files
    
    async def _match_answers(self, questions: List[Dict], pdf_path: str) -> List[Dict]:
        """정답 매칭"""
        
        # PDF에서 정답표 추출
        answers = await self._extract_answer_sheet(pdf_path)
        
        for question in questions:
            q_num = question["question_number"]
            if q_num in answers:
                question["correct_answer"] = answers[q_num]
            else:
                question["correct_answer"] = None
                print(f"   ⚠️ 문제 {q_num}번: 정답 매칭 실패")
        
        return questions
    
    async def _extract_answer_sheet(self, pdf_path: str) -> Dict[int, str]:
        """PDF에서 정답표 추출"""
        
        doc = fitz.open(pdf_path)
        answers = {}
        
        # 뒷부분 페이지에서 정답표 찾기
        for page_num in range(len(doc) - 4, len(doc)):  # 마지막 4페이지
            if page_num < 0:
                continue
                
            page = doc[page_num]
            text = page.get_text()
            
            if "정답" in text and "해설" in text:
                # 정답 패턴 추출
                pattern = r'(\d{1,2})\s*[:\-\.]\s*([①②③④⑤])'
                matches = re.findall(pattern, text)
                
                for match in matches:
                    q_num = int(match[0])
                    answer = match[1]
                    answers[q_num] = answer
        
        doc.close()
        print(f"   🎯 정답 매칭: {len(answers)}개 정답 추출")
        return answers
    
    def _validate_extraction_quality(self, questions: List[Dict]) -> Dict[str, Any]:
        """추출 품질 검증"""
        
        validation = {
            "total_questions": len(questions),
            "questions_with_4_choices": 0,
            "questions_with_answers": 0,
            "questions_with_visuals": 0,
            "cross_page_resolved": 0,
            "quality_issues": []
        }
        
        for question in questions:
            q_num = question["question_number"]
            
            # 선택지 개수 검증
            if len(question["choices"]) == 4:
                validation["questions_with_4_choices"] += 1
            else:
                validation["quality_issues"].append(f"Q{q_num}: {len(question['choices'])}개 선택지")
            
            # 정답 존재 검증
            if question.get("correct_answer"):
                validation["questions_with_answers"] += 1
            
            # 시각 요소 검증
            if (question.get("has_table") or question.get("has_image") or 
                question.get("has_code")):
                validation["questions_with_visuals"] += 1
            
            # 크로스 페이지 해결 검증
            if question.get("cross_page_resolved"):
                validation["cross_page_resolved"] += 1
        
        # 품질 점수 계산
        completion_rate = validation["questions_with_4_choices"] / max(validation["total_questions"], 1)
        answer_rate = validation["questions_with_answers"] / max(validation["total_questions"], 1)
        
        validation["quality_score"] = (completion_rate + answer_rate) / 2
        validation["extraction_quality"] = "high" if validation["quality_score"] > 0.9 else "medium"
        
        print(f"   ✅ 품질 검증: {validation['quality_score']:.2f} ({validation['extraction_quality']})")
        return validation