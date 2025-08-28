"""
향상된 PDF 처리 파이프라인 (병렬 처리 지원)
사용자 요구사항: PDF → 문서분석 → 페이지별분류 → OCR → 문제단위정리
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from services.claude_service import claude_service
from services.pdf_layout_analyzer import PDFLayoutAnalyzer
import PyPDF2
import logging
from datetime import datetime
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import math

logger = logging.getLogger(__name__)

class EnhancedPDFProcessor:
    def __init__(self):
        self.max_parallel_workers = 3  # 병렬 처리 최대 워커 수
        self.chunk_size_threshold = 10  # 페이지 수가 이 값을 초과하면 병렬 처리 (더 작게 조정)
        self.executor = ThreadPoolExecutor(max_workers=self.max_parallel_workers)
        self.layout_analyzer = PDFLayoutAnalyzer()  # 레이아웃 분석기 추가
    
    async def process_pdf_with_enhanced_pipeline(self, upload_id: int, file_path: str, file_type: str, db: Session) -> Dict[str, Any]:
        """향상된 PDF 처리 파이프라인"""
        try:
            print(f"[시작] Enhanced PDF Pipeline 시작 - Upload {upload_id}")
            await self._log_progress(upload_id, "[시작] 향상된 PDF 처리 파이프라인 시작", db)
            
            # 0단계: PDF 레이아웃 분석 (새로 추가)
            print("[Step 0] PDF 레이아웃 분석 중...")
            await self._create_ai_task(upload_id, "pdf_layout_analysis", "processing", db)
            
            layout_analysis = await self._analyze_pdf_layout(file_path, db)
            if not layout_analysis.get("success"):
                await self._update_ai_task(upload_id, "pdf_layout_analysis", "failed", layout_analysis, db)
                return {"error": "PDF 레이아웃 분석 실패"}
            
            await self._update_ai_task(upload_id, "pdf_layout_analysis", "completed", layout_analysis, db)
            print(f"[성공] 레이아웃 분석 완료 - {layout_analysis.get('identified_questions', 0)}개 문제 구조 식별")
            
            # 1단계: PDF 구조 분석 (OCR 전 단계)
            print("[Step 1] PDF 구조 및 문서 타입 분석 중...")
            await self._create_ai_task(upload_id, "pdf_structure_analysis", "processing", db)
            
            structure_analysis = await self._analyze_pdf_structure(file_path, db)
            if not structure_analysis.get("success"):
                await self._update_ai_task(upload_id, "pdf_structure_analysis", "failed", structure_analysis, db)
                return {"error": "PDF 구조 분석 실패"}
            
            await self._update_ai_task(upload_id, "pdf_structure_analysis", "completed", structure_analysis, db)
            print(f"[성공] PDF 구조 분석 완료 - 문서 타입: {structure_analysis.get('document_type')}")
            
            # 2단계: 페이지별 콘텐츠 분류
            print("[Step 2] 페이지별 콘텐츠 분류 중...")
            await self._create_ai_task(upload_id, "page_classification", "processing", db)
            
            page_classification = await self._classify_pages_by_content(file_path, structure_analysis, db)
            if not page_classification.get("success"):
                await self._update_ai_task(upload_id, "page_classification", "failed", page_classification, db)
                return {"error": "페이지 분류 실패"}
                
            await self._update_ai_task(upload_id, "page_classification", "completed", page_classification, db)
            print(f"[성공] 페이지 분류 완료 - 문제 페이지: {len(page_classification.get('question_pages', []))}개")
            
            # 3단계: 레이아웃 기반 구조적 OCR 처리 (개선됨)
            print("[Step 3] 레이아웃 기반 구조적 OCR 처리 중...")
            await self._create_ai_task(upload_id, "structured_ocr", "processing", db)
            
            ocr_results = await self._structured_ocr_processing(file_path, layout_analysis, page_classification, db)
            if not ocr_results.get("success"):
                await self._update_ai_task(upload_id, "structured_ocr", "failed", ocr_results, db)
                return {"error": "구조적 OCR 처리 실패"}
                
            await self._update_ai_task(upload_id, "structured_ocr", "completed", ocr_results, db)
            print(f"[성공] 구조적 OCR 완료 - {len(ocr_results.get('structured_questions', []))}개 구조화된 문제")
            
            # 4단계: 문제 단위별 정리 및 추출 (병렬 처리 지원)
            total_cost = 0.0
            processed_questions = []
            processed_materials = []
            
            if file_type in ["questions", "both"] and ocr_results.get('structured_questions'):
                print("[Step 4] 구조화된 문제 데이터 처리 중...")
                await self._create_ai_task(upload_id, "structured_question_processing", "processing", db)
                
                # 구조화된 문제 데이터에서 직접 처리
                structured_questions = ocr_results.get('structured_questions', [])
                
                # 병렬 처리 여부 결정
                use_parallel = len(structured_questions) > 10
                
                if use_parallel:
                    print(f"[알림] 대용량 문서 감지 - 병렬 처리 모드 활성화 ({len(structured_questions)}개 문제)")
                    question_extraction = await self._process_structured_questions_parallel(
                        structured_questions, upload_id, db
                    )
                else:
                    print(f"[알림] 표준 처리 모드 활성화 ({len(structured_questions)}개 문제)")
                    question_extraction = await self._process_structured_questions_standard(
                        structured_questions, db
                    )
                
                if question_extraction.get("success"):
                    questions = question_extraction.get("questions", [])
                    processed_questions = await self._save_questions_to_db(questions, upload_id, db)
                    await self._update_ai_task(upload_id, "structured_question_processing", "completed", 
                                              {"count": len(questions), "parallel": use_parallel}, db)
                    total_cost += question_extraction.get("cost", 0)
                    print(f"[성공] 문제 추출 완료 - {len(questions)}개 문제 (병렬처리: {use_parallel})")
                else:
                    await self._update_ai_task(upload_id, "structured_question_processing", "failed", question_extraction, db)
            
            # 5단계: 이론/학습자료 처리
            if file_type in ["study_material", "both"] and ocr_results.get('theory_text'):
                print("[Step 5] 이론/학습자료 처리 중...")
                await self._create_ai_task(upload_id, "theory_material_processing", "processing", db)
                
                materials_result = await self._process_theory_materials(
                    ocr_results.get('theory_text', ''), 
                    page_classification.get('theory_pages', []), 
                    db
                )
                
                if materials_result.get("success"):
                    materials = materials_result.get("materials", [])
                    processed_materials = await self._save_materials_to_db(materials, upload_id, db)
                    await self._update_ai_task(upload_id, "theory_material_processing", "completed", 
                                              {"count": len(materials)}, db)
                    total_cost += materials_result.get("cost", 0)
                    print(f"[성공] 학습자료 처리 완료 - {len(materials)}개 자료")
                else:
                    await self._update_ai_task(upload_id, "theory_material_processing", "failed", materials_result, db)
            
            # 6단계: 품질 검증
            print("[Step 6] 품질 검증 중...")
            await self._create_ai_task(upload_id, "enhanced_quality_verification", "processing", db)
            
            quality_result = await self._enhanced_quality_verification(
                processed_questions, processed_materials, page_classification, db
            )
            await self._update_ai_task(upload_id, "enhanced_quality_verification", "completed", quality_result, db)
            total_cost += quality_result.get("cost", 0)
            
            # 최종 상태 업데이트
            db.execute(
                text("UPDATE pdf_uploads SET processing_status = 'completed', processed_date = CURRENT_TIMESTAMP WHERE id = :id"),
                {"id": upload_id}
            )
            db.commit()
            
            result = {
                "success": True,
                "upload_id": upload_id,
                "questions_count": len(processed_questions),
                "materials_count": len(processed_materials),
                "total_cost": total_cost,
                "quality_score": quality_result.get("quality_score", 0),
                "pipeline_version": "enhanced_v2",
                "processing_method": "PDF→분석→분류→OCR→정리"
            }
            
            print(f"[완료] 향상된 PDF 처리 완료! 문제: {len(processed_questions)}개, 자료: {len(processed_materials)}개")
            return result
            
        except Exception as e:
            logger.error(f"Enhanced PDF processing error: {e}")
            db.execute(
                text("UPDATE pdf_uploads SET processing_status = 'failed' WHERE id = :id"),
                {"id": upload_id}
            )
            db.commit()
            return {"error": str(e)}
    
    async def _analyze_pdf_structure(self, file_path: str, db: Session) -> Dict[str, Any]:
        """PDF 구조 분석 (OCR 전 단계)"""
        try:
            # PDF 메타데이터 및 기본 정보 추출
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                # 첫 3페이지의 간단한 텍스트 샘플 추출
                sample_text = ""
                for i in range(min(3, total_pages)):
                    page = pdf_reader.pages[i]
                    page_text = page.extract_text()
                    sample_text += f"[Page {i+1}]\n{page_text[:1000]}\n\n"
            
            # Claude에 문서 타입 분석 요청
            agent = await self._get_agent("document_analysis", db)
            if not agent:
                return {"error": "Document analysis agent not found"}
            
            prompt = f"""다음 PDF 문서의 구조를 분석해주세요 (총 {total_pages} 페이지):

{sample_text}

다음 정보를 JSON 형식으로 제공해주세요:
{{
    "document_type": "문제집/교재/혼합",
    "estimated_question_pages": "문제가 있을 것으로 예상되는 페이지 범위",
    "estimated_theory_pages": "이론/설명이 있을 것으로 예상되는 페이지 범위", 
    "has_answer_section": true/false,
    "content_structure": "문서의 전체 구조 설명",
    "processing_strategy": "이 문서에 최적화된 처리 전략"
}}"""

            response = await claude_service.call_claude_api_direct(prompt, agent, db, max_tokens=2000)
            
            if response.get("success"):
                content = response["content"]
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    analysis["success"] = True
                    analysis["total_pages"] = total_pages
                    analysis["cost"] = self._calculate_cost(response.get("usage", {}))
                    return analysis
            
            return {"error": "Failed to analyze PDF structure"}
            
        except Exception as e:
            logger.error(f"PDF structure analysis error: {e}")
            return {"error": str(e)}
    
    async def _classify_pages_by_content(self, file_path: str, structure_analysis: Dict, db: Session) -> Dict[str, Any]:
        """콘텐츠 블록 기반 분류 (페이지 간 연속성 고려)"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                # 전체 페이지 텍스트 추출 및 연속성 분석
                page_texts = []
                for i in range(total_pages):
                    page = pdf_reader.pages[i]
                    page_text = page.extract_text()
                    page_texts.append({
                        "page_number": i + 1,
                        "text": page_text,
                        "text_length": len(page_text)
                    })
                
                # 콘텐츠 블록 기반 분류 (연속성 고려)
                content_blocks = self._identify_content_blocks_with_continuity(page_texts)
                
                # 결과 정리
                question_pages = []
                theory_pages = []
                answer_pages = []
                
                for block in content_blocks:
                    if block["type"] == "questions":
                        question_pages.extend(block["pages"])
                    elif block["type"] == "theory":
                        theory_pages.extend(block["pages"])
                    elif block["type"] == "answers":
                        answer_pages.extend(block["pages"])
                
                # 중복 제거 및 정렬
                question_pages = sorted(list(set(question_pages)))
                theory_pages = sorted(list(set(theory_pages)))
                answer_pages = sorted(list(set(answer_pages)))
                
                return {
                    "success": True,
                    "total_pages": total_pages,
                    "question_pages": question_pages,
                    "theory_pages": theory_pages,
                    "answer_pages": answer_pages,
                    "content_blocks": content_blocks,
                    "continuity_analysis": "페이지 간 연속성 분석 완료"
                }
                
        except Exception as e:
            logger.error(f"Content block classification error: {e}")
            return {"error": str(e)}
    
    def _identify_content_blocks_with_continuity(self, page_texts: List[Dict]) -> List[Dict]:
        """페이지 간 연속성을 고려한 콘텐츠 블록 식별"""
        content_blocks = []
        current_block = None
        
        for page_data in page_texts:
            page_num = page_data["page_number"]
            text = page_data["text"]
            
            # 현재 페이지 타입 분석
            page_type = self._classify_page_content(text)
            continuity_info = self._analyze_page_continuity(text, page_texts, page_num - 1)
            
            # 새로운 블록 시작 조건
            should_start_new_block = (
                current_block is None or  # 첫 번째 페이지
                current_block["type"] != page_type or  # 타입이 변경됨
                not continuity_info["continues_from_previous"]  # 이전 페이지와 연속성 없음
            )
            
            if should_start_new_block:
                # 현재 블록 완료
                if current_block:
                    content_blocks.append(current_block)
                
                # 새 블록 시작
                current_block = {
                    "type": page_type,
                    "pages": [page_num],
                    "start_page": page_num,
                    "text_preview": text[:200],
                    "continuity_info": [continuity_info]
                }
            else:
                # 현재 블록에 페이지 추가
                current_block["pages"].append(page_num)
                current_block["continuity_info"].append(continuity_info)
        
        # 마지막 블록 추가
        if current_block:
            content_blocks.append(current_block)
        
        return content_blocks
    
    def _analyze_page_continuity(self, current_text: str, all_pages: List[Dict], current_index: int) -> Dict:
        """페이지 간 연속성 분석"""
        continuity_info = {
            "continues_from_previous": False,
            "continues_to_next": False,
            "incomplete_question": False,
            "incomplete_theory": False,
            "cross_page_elements": []
        }
        
        # 이전 페이지와의 연속성 확인
        if current_index > 0:
            prev_text = all_pages[current_index - 1]["text"]
            continuity_info["continues_from_previous"] = self._check_text_continuity(prev_text, current_text)
        
        # 다음 페이지와의 연속성 확인
        if current_index < len(all_pages) - 1:
            next_text = all_pages[current_index + 1]["text"]
            continuity_info["continues_to_next"] = self._check_text_continuity(current_text, next_text)
        
        # 미완성 요소 탐지
        continuity_info["incomplete_question"] = self._detect_incomplete_question(current_text)
        continuity_info["incomplete_theory"] = self._detect_incomplete_theory(current_text)
        
        # 페이지 간 요소 탐지
        continuity_info["cross_page_elements"] = self._detect_cross_page_elements(current_text)
        
        return continuity_info
    
    def _check_text_continuity(self, text1: str, text2: str) -> bool:
        """두 텍스트 간 연속성 확인"""
        # 연속성 패턴들
        continuity_patterns = [
            # 문장이 중간에 끊어짐
            (r'[^\.!?]\s*$', r'^\s*[a-zA-Z가-힣]'),
            # 문제 번호 연속성
            (r'(\d+)\.\s*[^\n]*$', r'^\s*(\d+)\.\s*'),
            # 선택지 연속성
            (r'[①②③④]\s*[^\n]*$', r'^\s*[①②③④]'),
            # 표나 그림 참조
            (r'다음.*?표|그림.*?참조', r'^\s*[표그림]'),
        ]
        
        text1_end = text1.strip()[-100:] if len(text1) > 100 else text1.strip()
        text2_start = text2.strip()[:100] if len(text2) > 100 else text2.strip()
        
        for pattern1, pattern2 in continuity_patterns:
            if re.search(pattern1, text1_end) and re.search(pattern2, text2_start):
                return True
        
        return False
    
    def _detect_incomplete_question(self, text: str) -> bool:
        """미완성 문제 탐지"""
        incomplete_patterns = [
            r'\d+\.\s[^\?]*$',  # 문제 번호 있지만 물음표 없음
            r'다음.*중.*$',  # "다음 중"으로 끝남
            r'[①②③④]\s*[^①②③④]*$',  # 선택지가 일부만 있음
            r'그림.*참조.*$',  # 그림 참조로 끝남
        ]
        
        return any(re.search(pattern, text.strip()) for pattern in incomplete_patterns)
    
    def _detect_incomplete_theory(self, text: str) -> bool:
        """미완성 이론/설명 탐지"""
        incomplete_patterns = [
            r'다음과\s*같다?\s*$',  # "다음과 같다"로 끝남
            r'예를\s*들면?\s*$',  # "예를 들면"으로 끝남
            r'즉,?\s*$',  # "즉,"으로 끝남
            r'따라서\s*$',  # "따라서"로 끝남
        ]
        
        return any(re.search(pattern, text.strip()) for pattern in incomplete_patterns)
    
    def _detect_cross_page_elements(self, text: str) -> List[str]:
        """페이지 간 요소 탐지"""
        cross_page_elements = []
        
        # 그림/표 참조
        if re.search(r'그림\s*\d+|표\s*\d+', text):
            cross_page_elements.append("figure_reference")
        
        # 계속됨 표시
        if re.search(r'계속|다음\s*페이지|이어서', text):
            cross_page_elements.append("continuation_marker")
        
        # 미완성 수식
        if re.search(r'=\s*$|\+\s*$|-\s*$', text):
            cross_page_elements.append("incomplete_formula")
        
        return cross_page_elements
    
    def _classify_page_content(self, text: str) -> str:
        """개별 페이지 콘텐츠 타입 분류"""
        # 문제 패턴 탐지
        question_patterns = [
            r'\d+\.\s[^\n]*\?',  # "1. 문제내용?"
            r'[①②③④]',  # 객관식 선택지
            r'다음.*중.*것은',  # "다음 중 옳은 것은"
            r'정답:\s*[①②③④\d]'  # 정답 표시
        ]
        
        # 이론/설명 패턴 탐지
        theory_patterns = [
            r'정의:',
            r'특징:',
            r'개념',
            r'원리',
            r'방법론'
        ]
        
        # 답안 페이지 패턴
        answer_patterns = [
            r'정답\s*및?\s*해설',
            r'^정답',
            r'해답',
            r'[①②③④]\s*[①②③④]\s*[①②③④]'  # 연속된 답안
        ]
        
        question_score = sum(1 for pattern in question_patterns if re.search(pattern, text))
        theory_score = sum(1 for pattern in theory_patterns if re.search(pattern, text))
        answer_score = sum(1 for pattern in answer_patterns if re.search(pattern, text))
        
        if answer_score >= 2:
            return "answers"
        elif question_score >= 2:
            return "questions"
        elif theory_score >= 1:
            return "theory"
        else:
            return "mixed"
    
    async def _selective_ocr_processing(self, file_path: str, page_classification: Dict, db: Session) -> Dict[str, Any]:
        """콘텐츠 블록 기반 OCR 처리 (연속성 보장)"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                question_text = ""
                theory_text = ""
                
                # 콘텐츠 블록별 OCR 처리 (연속성 보장)
                content_blocks = page_classification.get("content_blocks", [])
                
                for block in content_blocks:
                    block_text = self._extract_continuous_text_from_block(pdf_reader, block)
                    
                    if block["type"] == "questions":
                        question_text += f"\n=== 문제 블록 (페이지 {block['pages'][0]}-{block['pages'][-1]}) ===\n"
                        question_text += block_text + "\n"
                    elif block["type"] == "theory":
                        theory_text += f"\n=== 이론 블록 (페이지 {block['pages'][0]}-{block['pages'][-1]}) ===\n"
                        theory_text += block_text + "\n"
                
                # 페이지 간 경계에서 잘린 내용 복구
                question_text = self._restore_cross_page_content(question_text, page_classification)
                theory_text = self._restore_cross_page_content(theory_text, page_classification)
                
                return {
                    "success": True,
                    "question_text": question_text,
                    "theory_text": theory_text,
                    "processed_text": question_text + theory_text,
                    "content_blocks_processed": len(content_blocks),
                    "continuity_preserved": True
                }
                
        except Exception as e:
            logger.error(f"Content block OCR error: {e}")
            return {"error": str(e)}
    
    def _extract_continuous_text_from_block(self, pdf_reader, block: Dict) -> str:
        """블록에서 연속성을 유지한 텍스트 추출"""
        continuous_text = ""
        
        for i, page_num in enumerate(block["pages"]):
            page = pdf_reader.pages[page_num - 1]
            page_text = page.extract_text()
            
            if i == 0:
                # 첫 번째 페이지
                continuous_text += page_text
            else:
                # 연속된 페이지 - 연결 처리
                continuity_info = block["continuity_info"][i] if i < len(block["continuity_info"]) else {}
                
                if continuity_info.get("continues_from_previous", False):
                    # 연속성이 있는 경우 - 자연스럽게 연결
                    continuous_text = continuous_text.rstrip() + " " + page_text.lstrip()
                else:
                    # 연속성이 없는 경우 - 페이지 구분자 추가
                    continuous_text += f"\n--- 페이지 {page_num} ---\n" + page_text
        
        return continuous_text
    
    def _restore_cross_page_content(self, text: str, page_classification: Dict) -> str:
        """페이지 간 잘린 내용 복구"""
        restored_text = text
        
        # 흔히 잘리는 패턴들을 복구
        restore_patterns = [
            # 문제 번호와 내용이 분리된 경우
            (r'(\d+)\.\s*\n=== [^=]+ ===\n([가-힣A-Za-z])', r'\1. \2'),
            # 선택지가 분리된 경우  
            (r'([①②③④])\s*\n=== [^=]+ ===\n([가-힣A-Za-z])', r'\1 \2'),
            # 문장이 중간에 끊어진 경우
            (r'([가-힣A-Za-z])\s*\n=== [^=]+ ===\n([가-힣A-Za-z])', r'\1 \2'),
        ]
        
        for pattern, replacement in restore_patterns:
            restored_text = re.sub(pattern, replacement, restored_text, flags=re.MULTILINE)
        
        return restored_text
    
    def _extract_questions_with_enhanced_regex(self, text: str) -> List[Dict]:
        """향상된 정규식 기반 문제 추출 - 60문제 완전 추출 최적화"""
        questions = []
        
        try:
            print(f"[향상추출] 개선된 정규식 추출 시작 - {len(text)} 문자")
            
            # 1. 문제 단위로 분할 (개선된 패턴)
            question_patterns = [
                r'(?=(?:^|\n)\s*(\d{1,2})\.\s+[가-힣A-Za-z])',  # 1. 다음... 패턴
                r'(?=(?:^|\n)\s*(\d{1,2})\)\s+[가-힣A-Za-z])',  # 1) 다음... 패턴  
                r'(?=(?:^|\n)\s*문제\s*(\d{1,2})\s*[:\.])',     # 문제 1: 패턴
            ]
            
            best_split = []
            best_pattern = None
            
            for pattern in question_patterns:
                try:
                    splits = re.split(pattern, text, flags=re.MULTILINE)
                    # 숫자가 섞인 경우 정리
                    clean_splits = []
                    for i, split in enumerate(splits):
                        if split and not split.isdigit():  # 숫자만 있는 부분 제외
                            clean_splits.append(split.strip())
                    
                    if len(clean_splits) > len(best_split):
                        best_split = clean_splits
                        best_pattern = pattern
                        
                except Exception as e:
                    continue
            
            if not best_split:
                print("[향상추출] 문제 분할 실패")
                return []
            
            print(f"[향상추출] 문제 분할 성공 - {len(best_split)}개 블록 ({best_pattern})")
            
            # 2. 각 블록에서 문제 정보 추출
            for i, block in enumerate(best_split):
                if not block or len(block.strip()) < 10:
                    continue
                
                # 문제 번호 추출
                question_number = self._extract_question_number_enhanced(block)
                if question_number == 0:
                    continue
                
                # 문제 텍스트 추출
                question_text = self._extract_question_text_enhanced(block)
                if not question_text:
                    continue
                
                # 선택지 추출 (개선된 방식)
                options = self._extract_options_enhanced(block)
                
                # 지문 추출
                passage = self._extract_passage_enhanced(block)
                
                question_data = {
                    "question_number": question_number,
                    "passage": passage,
                    "question_text": question_text,
                    "options": options,
                    "correct_answer": None,
                    "explanation": None
                }
                
                questions.append(question_data)
                print(f"[향상추출] 문제 {question_number}: 텍스트 {len(question_text)}자, 선택지 {len(options)}개")
            
            print(f"[향상추출] 최종 추출: {len(questions)}개 문제")
            return questions
            
        except Exception as e:
            print(f"[향상추출] 오류: {e}")
            return []
    
    def _extract_question_number_enhanced(self, text: str) -> int:
        """개선된 문제 번호 추출"""
        patterns = [
            r'(?:^|\n)\s*(\d{1,2})\.\s+',
            r'(?:^|\n)\s*(\d{1,2})\)\s+',
            r'(?:^|\n)\s*문제\s*(\d{1,2})\s*[:\.]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                num = int(match.group(1))
                if 1 <= num <= 60:
                    return num
        return 0
    
    def _extract_question_text_enhanced(self, text: str) -> str:
        """개선된 문제 텍스트 추출"""
        # 문제 번호 제거 후 선택지 전까지의 텍스트
        text = re.sub(r'(?:^|\n)\s*\d{1,2}[\.\)]\s*', '', text, count=1)
        text = re.sub(r'(?:^|\n)\s*문제\s*\d{1,2}\s*[:\.]', '', text, count=1)
        
        # 선택지 패턴 전까지
        option_start = re.search(r'[①②③④⑤]|[ABCDE]\s*[\.\)]|^\s*\d+\s*[\.\)]', text, re.MULTILINE)
        if option_start:
            question_text = text[:option_start.start()].strip()
        else:
            question_text = text.strip()
        
        # 너무 긴 경우 적절히 자르기
        if len(question_text) > 500:
            question_text = question_text[:500] + "..."
        
        return question_text
    
    def _extract_options_enhanced(self, text: str) -> List[str]:
        """개선된 선택지 추출"""
        options = []
        
        # 다양한 선택지 패턴들
        patterns = [
            r'[①②③④⑤]\s*([^\n①②③④⑤]+)',
            r'[ABCDE]\s*[\.\)]\s*([^\nABCDE]+)',
            r'^\s*(\d+)\s*[\.\)]\s*([^\n\d]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        option_text = match[-1].strip()
                    else:
                        option_text = match.strip()
                    
                    if option_text and len(option_text) > 1:
                        # 중복 제거
                        if option_text not in options:
                            options.append(option_text)
                
                if len(options) >= 2:  # 최소 2개 이상이면 성공
                    break
        
        return options[:6]  # 최대 6개까지
    
    def _extract_passage_enhanced(self, text: str) -> str:
        """개선된 지문 추출"""
        passage_patterns = [
            r'다음\s*(글|문|지문|자료|표|그림|코드).*?[을를]\s*(읽고|보고|참고하여)',
            r'아래\s*(글|문|지문|자료|표|그림|코드).*?[을를]\s*(읽고|보고|참고하여)', 
            r'다음.*?[은는이가]\s*주어졌을\s*때',
            r'<그림\s*\d+>',
            r'<표\s*\d+>',
            r'다음\s*프로그램',
            r'다음\s*코드',
            r'(class\s+\w+|def\s+\w+|import\s+\w+|#include|int\s+main)',
        ]
        
        for pattern in passage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 지문으로 추정되는 부분을 더 넓게 추출
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 200)
                return text[start:end].strip()
        
        return None
    
    def _improve_ocr_text(self, text: str) -> str:
        """OCR 텍스트 품질 개선 및 문제 인식률 향상"""
        try:
            print(f"[전처리] OCR 텍스트 개선 시작 - {len(text)} 문자")
            
            # 1. 기본 정리
            improved_text = text.strip()
            
            # 2. 잘못된 줄바꿈 복구 (문제 번호 패턴 기준)
            # "1 ." -> "1." 형태 수정
            improved_text = re.sub(r'(\d+)\s+\.', r'\1.', improved_text)
            
            # 3. 문제 번호와 내용 사이 공백 정규화
            improved_text = re.sub(r'(\d+)\.\s*\n\s*', r'\1. ', improved_text)
            
            # 4. 선택지 패턴 정리
            # "① " -> "① " (공백 정규화)
            improved_text = re.sub(r'([①②③④⑤])\s*', r'\1 ', improved_text)
            improved_text = re.sub(r'([ABCDE])\s*\.\s*', r'\1. ', improved_text)
            
            # 5. 문제 간 경계 명확화 (문제 번호 앞에 줄바꿈 추가)
            improved_text = re.sub(r'(?<!\n)(\d+\.\s+[가-힣A-Za-z])', r'\n\1', improved_text)
            
            # 6. 중복 공백/줄바꿈 정리
            improved_text = re.sub(r'\n\s*\n\s*\n', '\n\n', improved_text)
            improved_text = re.sub(r'[ \t]+', ' ', improved_text)
            
            # 7. 특수 문자 정리 (OCR 오류로 생긴 이상한 문자들)
            improved_text = re.sub(r'[^\w\s가-힣①②③④⑤\.\(\)#<>/\-\+\*=:;,\?!\"\'%]', '', improved_text)
            
            print(f"[전처리] OCR 텍스트 개선 완료 - {len(improved_text)} 문자")
            
            # 8. 개선 후 문제 개수 미리 확인
            question_count = len(re.findall(r'(?:^|\n)\s*(\d{1,2})\.\s+', improved_text, re.MULTILINE))
            print(f"[전처리] 발견된 문제 번호: {question_count}개")
            
            return improved_text
            
        except Exception as e:
            print(f"[전처리] OCR 텍스트 개선 오류: {e}")
            return text  # 오류 시 원본 반환
    
    async def _fallback_to_ocr_processing(self, file_path: str, page_classification: Dict, db: Session) -> Dict[str, Any]:
        """레이아웃 분석 실패 시 기존 OCR 방식으로 fallback"""
        try:
            print("[Fallback] 기존 OCR 방식으로 문제 추출 시작...")
            
            # 1. OCR 텍스트 추출
            ocr_result = await self._selective_ocr_processing(file_path, page_classification, db)
            if not ocr_result.get("success"):
                return {"error": "OCR 처리 실패", "fallback_failed": True}
            
            question_text = ocr_result.get("question_text", "")
            if not question_text or len(question_text.strip()) < 100:
                return {"error": "추출된 문제 텍스트 부족", "fallback_failed": True}
            
            print(f"[Fallback] OCR 텍스트 추출 완료 - {len(question_text)} 문자")
            
            # OCR 텍스트 전처리 및 개선
            question_text = self._improve_ocr_text(question_text)
            
            # 2. 페이지 정보 추출 (기본값 설정)
            question_pages = []
            content_blocks = page_classification.get("content_blocks", [])
            for block in content_blocks:
                if block.get("type") == "questions":
                    question_pages.extend(block.get("pages", []))
            
            if not question_pages:
                # 기본적으로 모든 페이지를 문제 페이지로 간주
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    question_pages = list(range(1, len(pdf_reader.pages) + 1))
            
            print(f"[Fallback] 문제 페이지 범위: {min(question_pages)}-{max(question_pages)}")
            
            # 3. 기존의 검증된 문제 추출 방식 사용
            extraction_result = await self._extract_questions_by_units(question_text, question_pages, db)
            
            if not extraction_result.get("success"):
                print("[Fallback] 단위별 추출 실패, 정규식 방식 시도...")
                # 정규식 기반 추출 시도 (개선된 버전)
                regex_questions = self._extract_questions_with_enhanced_regex(question_text)
                if regex_questions:
                    extraction_result = {
                        "success": True,
                        "questions": regex_questions,
                        "total_questions": len(regex_questions),
                        "cost": 0,
                        "method": "regex_fallback"
                    }
            
            if extraction_result.get("success"):
                questions = extraction_result.get("questions", [])
                print(f"[Fallback 성공] {len(questions)}개 문제 추출됨")
                
                # 최종 결과 포맷 맞추기 (메인 파이프라인 호환)
                return {
                    "success": True,
                    "structured_questions": questions,  # 메인 파이프라인이 기대하는 키
                    "total_questions": len(questions),
                    "questions": questions,  # 기존 키도 유지
                    "cost": extraction_result.get("cost", 0),
                    "processing_method": "ocr_fallback",
                    "fallback_used": True,
                    "layout_based": False  # fallback이므로 false
                }
            else:
                return {"error": "Fallback 문제 추출 실패", "fallback_failed": True}
                
        except Exception as e:
            logger.error(f"Fallback OCR 오류: {e}")
            return {"error": f"Fallback 처리 오류: {str(e)}", "fallback_failed": True}
    
    async def _extract_questions_by_units(self, question_text: str, question_pages: List[int], db: Session) -> Dict[str, Any]:
        """문제 단위별 정리 및 추출"""
        try:
            agent = await self._get_agent("question_extraction", db)
            if not agent:
                return {"error": "Question extraction agent not found"}
            
            # 1단계: 문서 구조 분석 - 실제 문제/이론 개수 파악
            print("[구조분석] 문서 구조 분석 시작...")
            structure_analysis = await self._analyze_document_structure(question_text, db)
            
            if not structure_analysis.get("success"):
                print("[경고] 문서 구조 분석 실패, 기본 방식으로 진행")
                question_units = self._split_text_by_question_units(question_text)
            else:
                structure_info = structure_analysis["structure"]
                # 2단계: 구조 정보를 바탕으로 지능적 블록 생성
                question_units = self._create_intelligent_blocks(question_text, structure_info)
            
            all_questions = []
            total_cost = 0
            
            for unit_idx, unit in enumerate(question_units):
                print(f"[처리중] 문제 단위 {unit_idx + 1}/{len(question_units)} 처리 중...")
                
                enhanced_prompt = f"""다음은 정보처리산업기사 필기시험 문제 텍스트입니다. 이 텍스트에서 완전한 객관식 문제들을 추출하여 JSON 배열로 반환해주세요.

CRITICAL 요구사항:
1. 지문과 문제를 명확히 분리하세요
2. 지문(passage): 문제를 풀기 위해 주어진 설명, 표, 그림, 코드 등
3. 문제(question_text): 실제 질문 ("다음 중 옳은 것은?", "결과는?" 등)
4. 선택지(options): 모든 보기를 정확히 추출 (개수 제한 없음)
5. 지문이 없는 단순한 문제는 passage를 null로 설정

=== 문제 단위 텍스트 ===
{unit}

=== 필수 출력 형식 ===
반드시 다음 형식으로만 응답하세요:

[
  {{
    "passage": "문제 해결을 위한 지문/설명/코드/표 (없으면 null)",
    "question_text": "실제 질문 내용",
    "options": ["선택지1", "선택지2", "선택지3", "선택지4"],
    "correct_answer": "1",
    "question_number": 1
  }},
  {{
    "question_text": "두 번째 문제의 질문 내용",
    "options": ["선택지1", "선택지2", "선택지3", "선택지4"],
    "correct_answer": "2", 
    "question_number": 2
  }}
]

=== 추출 지침 ===
1. 문제 번호(1., 2., 3. 등)가 있는 모든 문제를 찾으세요
2. 각 문제의 완전한 질문 부분을 question_text에 넣으세요
3. 선택지(①②③④ 또는 1)2)3)4))는 options 배열에 넣으세요
4. 정답이 있으면 correct_answer에 넣고, 없으면 null로 하세요

=== 중요 ===
- 선택지만 있는 배열 ["선택지1", "선택지2"] 같은 형식으로 반환하지 마세요
- 반드시 question_text, options, correct_answer, question_number 키가 모두 있는 완전한 객체를 반환하세요"""

                response = await claude_service.call_claude_api_direct(enhanced_prompt, agent, db, max_tokens=8000)
                
                if response.get("success"):
                    content = response["content"]
                    
                    # 더 강력한 JSON 추출 로직
                    unit_questions = self._extract_questions_from_response(content, unit_idx + 1)
                    if unit_questions:
                        all_questions.extend(unit_questions)
                        print(f"[성공] 단위 {unit_idx + 1}: {len(unit_questions)}개 문제 추출")
                    else:
                        print(f"[실패] 단위 {unit_idx + 1}: 문제 추출 실패")
                    
                    total_cost += self._calculate_cost(response.get("usage", {}))
                
                await asyncio.sleep(1)  # API 호출 간격
            
            print(f"[완료] 문제 단위별 추출 완료: {len(all_questions)}개 문제")
            
            return {
                "success": True,
                "questions": all_questions,
                "count": len(all_questions),
                "units_processed": len(question_units),
                "cost": total_cost
            }
            
        except Exception as e:
            logger.error(f"Question unit extraction error: {e}")
            return {"error": str(e)}
    
    async def _analyze_document_structure(self, text: str, db: Session) -> Dict[str, Any]:
        """문서 구조 분석 - 실제 문제/이론 개수 파악"""
        try:
            agent = await self._get_agent("content_analyzer", db)
            if not agent:
                return {"error": "Content analyzer agent not found"}
            
            analysis_prompt = f"""다음 문서를 분석하여 실제 문제와 이론의 개수를 정확히 파악해주세요.

=== 분석 대상 텍스트 ===
{text[:4000]}... (총 {len(text)} 문자)

=== 분석 요청 사항 ===
1. 문제 번호가 있는 객관식 문제가 총 몇 개인지 정확히 세어주세요
2. 이론 설명 섹션이 몇 개인지 파악해주세요  
3. 각 문제의 대략적인 위치(시작 문자열)를 찾아주세요
4. 이론 섹션의 대략적인 위치를 찾아주세요

=== 출력 형식 (JSON) ===
{{
    "total_questions": 실제_문제_개수,
    "total_theories": 이론_섹션_개수,
    "question_locations": [
        {{"question_number": 1, "start_text": "1. 문제 시작 부분..."}},
        {{"question_number": 2, "start_text": "2. 문제 시작 부분..."}}
    ],
    "theory_locations": [
        {{"theory_index": 1, "title": "이론 제목", "start_text": "이론 시작 부분..."}}
    ],
    "document_structure": "questions_only|theory_only|mixed",
    "estimated_processing_blocks": 권장_분할_블록_수
}}"""

            response = await claude_service.call_claude_api_direct(analysis_prompt, agent, db, max_tokens=4000)
            
            if response.get("success"):
                content = response["content"]
                
                # JSON 추출 시도
                structure_info = self._extract_structure_from_response(content)
                if structure_info:
                    print(f"[완료] 문서 구조 분석 완료:")
                    print(f"  - 총 문제 수: {structure_info.get('total_questions', 0)}개")
                    print(f"  - 총 이론 수: {structure_info.get('total_theories', 0)}개")
                    print(f"  - 문서 유형: {structure_info.get('document_structure', 'unknown')}")
                    print(f"  - 권장 분할 블록: {structure_info.get('estimated_processing_blocks', 1)}개")
                    
                    return {
                        "success": True,
                        "structure": structure_info
                    }
                else:
                    print("[실패] 문서 구조 분석 결과 파싱 실패")
                    return {"error": "Structure analysis parsing failed"}
            else:
                return {"error": "Structure analysis failed"}
                
        except Exception as e:
            logger.error(f"Document structure analysis error: {e}")
            return {"error": str(e)}
    
    def _extract_structure_from_response(self, content: str) -> Dict:
        """구조 분석 응답에서 정보 추출"""
        try:
            # JSON 추출 시도
            json_match = re.search(r'\{[\s\S]*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            # 백업: 텍스트에서 직접 추출
            structure = {}
            
            # 문제 개수 찾기
            question_match = re.search(r'"?total_questions"?\s*:\s*(\d+)', content)
            if question_match:
                structure["total_questions"] = int(question_match.group(1))
            
            # 이론 개수 찾기  
            theory_match = re.search(r'"?total_theories"?\s*:\s*(\d+)', content)
            if theory_match:
                structure["total_theories"] = int(theory_match.group(1))
            
            # 문서 구조 타입 찾기
            structure_match = re.search(r'"?document_structure"?\s*:\s*"?([^",\s]+)', content)
            if structure_match:
                structure["document_structure"] = structure_match.group(1)
            
            return structure if structure else None
            
        except Exception as e:
            print(f"구조 분석 파싱 오류: {e}")
            return None
    
    def _create_intelligent_blocks(self, text: str, structure_info: Dict) -> List[str]:
        """구조 분석 결과를 바탕으로 지능적 블록 생성"""
        total_questions = structure_info.get("total_questions", 0)
        total_theories = structure_info.get("total_theories", 0)
        
        if total_questions == 0:
            print("[경고] 문제가 없는 문서로 판단됨")
            return [text]
        
        # 문제 수에 따른 블록 크기 결정
        if total_questions <= 10:
            questions_per_block = total_questions  # 한 번에 처리
        elif total_questions <= 30:
            questions_per_block = 5  # 5문제씩
        else:
            questions_per_block = 3  # 3문제씩
        
        print(f"[블록생성] 지능적 블록 생성: {total_questions}문제 → {questions_per_block}문제씩 분할")
        
        # 실제 문제 패턴으로 분할
        question_pattern = r'(?=\d+\.\s)'
        parts = re.split(question_pattern, text)
        
        # 유효한 문제 부분만 선별
        valid_questions = []
        for part in parts:
            if part.strip() and re.match(r'\d+\.', part.strip()):
                valid_questions.append(part.strip())
        
        print(f"[발견] 실제 발견된 문제: {len(valid_questions)}개")
        
        # 블록으로 그룹핑
        blocks = []
        current_block = ""
        questions_in_block = 0
        
        for question in valid_questions:
            if questions_in_block >= questions_per_block and current_block:
                blocks.append(current_block)
                current_block = question
                questions_in_block = 1
            else:
                if current_block:
                    current_block += "\n\n" + question
                else:
                    current_block = question
                questions_in_block += 1
        
        # 마지막 블록 추가
        if current_block:
            blocks.append(current_block)
        
        print(f"[블록] 최종 생성된 블록: {len(blocks)}개")
        
        return blocks if blocks else [text]
    
    def _split_text_by_question_units(self, text: str) -> List[str]:
        """기본 텍스트 분할 방식 (구조 분석 실패시 백업) - 60문제 완전 추출 최적화"""
        # 1. 문제 번호 패턴으로 개별 문제 분리 (개선된 패턴)
        question_patterns = [
            r'(?=(?:^|\n)\s*(\d{1,2})\.\s+)',  # 1-60번 문제 (줄 시작)
            r'(?=(?:^|\n)\s*(\d{1,2})\)\s+)',  # 1) 형태
            r'(?=(?:^|\n)\s*문제\s*(\d{1,2})\s*[:\.])'  # 문제 1: 형태
        ]
        
        # 여러 패턴으로 시도해서 가장 많이 찾는 패턴 사용
        best_split = []
        for pattern in question_patterns:
            try:
                split_result = re.split(pattern, text)
                if len(split_result) > len(best_split):
                    best_split = split_result
            except:
                continue
        
        individual_questions = best_split if best_split else [text]
        
        valid_questions = []
        for question in individual_questions:
            if question.strip() and len(question.strip()) > 20:  # 더 짧은 문제도 포함
                valid_questions.append(question.strip())
        
        print(f"[분할] 개별 문제 분리: {len(valid_questions)}개 발견")
        
        # 2. 더 작은 블록으로 묶기 (2-3문제씩으로 줄임)
        final_units = []
        current_block = ""
        questions_in_block = 0
        max_questions_per_block = 3  # 5에서 3으로 줄임
        max_block_size = 2500  # 4000에서 2500으로 줄임
        
        for question in valid_questions:
            potential_size = len(current_block) + len(question)
            
            # 블록 크기 조건을 더 엄격하게
            if potential_size < max_block_size and questions_in_block < max_questions_per_block:
                current_block += ("\n\n" if current_block else "") + question
                questions_in_block += 1
            else:
                if current_block:
                    final_units.append(current_block)
                    print(f"  블록 {len(final_units)}: {questions_in_block}문제, {len(current_block)}자")
                current_block = question
                questions_in_block = 1
        
        if current_block:
            final_units.append(current_block)
            print(f"  블록 {len(final_units)}: {questions_in_block}문제, {len(current_block)}자")
        
        print(f"[블록] 기본 방식 최종 블록 수: {len(final_units)}개 (평균 {len(valid_questions)/len(final_units) if final_units else 0:.1f}문제/블록)")
        
        # 3. 너무 큰 블록이 있으면 추가로 분할
        refined_units = []
        for unit in final_units:
            if len(unit) > max_block_size:
                # 큰 블록을 중간에서 분할
                mid_point = len(unit) // 2
                # 문제 경계에서 분할하도록 조정
                split_point = unit.rfind('\n\n', 0, mid_point)
                if split_point > 0:
                    refined_units.append(unit[:split_point])
                    refined_units.append(unit[split_point:])
                    print(f"  [분할] 큰 블록을 2개로 분할")
                else:
                    refined_units.append(unit)
            else:
                refined_units.append(unit)
        
        print(f"[블록] 최종 블록 수: {len(refined_units)}개")
        return refined_units if refined_units else [text]
    
    def _extract_questions_from_response(self, content: str, unit_idx: int) -> List[Dict]:
        """Claude 응답에서 문제를 더 안전하게 추출 - 개선된 버전"""
        questions = []
        
        try:
            print(f"[응답] 단위 {unit_idx} 응답 길이: {len(content)} 문자")
            
            # 방법 0: 정규식 기반 직접 추출 (가장 안전한 방법)
            regex_questions = self._extract_questions_with_regex_v2(content)
            if regex_questions:
                print(f"[성공] 단위 {unit_idx}: 정규식으로 {len(regex_questions)}개 문제 직접 추출")
                return regex_questions
            
            # JSON 배열 찾기
            json_matches = re.findall(r'\[[\s\S]*?\]', content, re.DOTALL)
            if json_matches:
                print(f"[JSON] 단위 {unit_idx} 발견된 JSON 배열 (첫 300자): {json_matches[0][:300]}...")
            
            # 방법 1: 표준 JSON 배열 추출 (가장 정확한 방법)
            json_matches = re.findall(r'\[[\s\S]*?\]', content, re.DOTALL)
            for json_match in json_matches:
                try:
                    print(f"[디버그] 단위 {unit_idx} 원본 JSON (첫 500자): {json_match[:500]}...")
                    
                    # 간단한 JSON 정리만 수행
                    cleaned_json = json_match.strip()
                    # 가장 기본적인 정리만
                    cleaned_json = re.sub(r',\s*([}\]])', r'\1', cleaned_json)  # 끝 쉼표만 제거
                    
                    print(f"[디버그] 단위 {unit_idx} 정리된 JSON (첫 500자): {cleaned_json[:500]}...")
                    
                    parsed_data = json.loads(cleaned_json)
                    
                    # 다양한 형태의 응답 처리
                    questions = []
                    if isinstance(parsed_data, list):
                        questions = parsed_data
                    elif isinstance(parsed_data, dict):
                        # "problems", "questions" 등의 키 확인
                        for key in ["problems", "questions", "items", "data"]:
                            if key in parsed_data and isinstance(parsed_data[key], list):
                                questions = parsed_data[key]
                                break
                    
                    if questions:
                        print(f"[성공] 단위 {unit_idx}: 방법1(JSON 배열)로 {len(questions)}개 추출")
                        print(f"[디버그] 첫 번째 문제 객체: {questions[0] if questions else 'None'}")
                        
                        validated_questions = self._validate_and_clean_questions(questions)
                        if validated_questions:
                            print(f"[완료] 단위 {unit_idx}: 검증 후 {len(validated_questions)}개 문제 확정")
                            return validated_questions
                        else:
                            print(f"[실패] 단위 {unit_idx}: 검증 과정에서 모든 문제가 제거됨")
                except json.JSONDecodeError as e:
                    print(f"[경고] 단위 {unit_idx} JSON 배열 파싱 오류: {e}")
                    print(f"[경고] 오류 위치: {e.pos if hasattr(e, 'pos') else 'Unknown'}")
                    continue
            
            # 방법 2: 개별 JSON 객체 추출 및 재구성
            question_objects = []
            # 더 정확한 JSON 객체 패턴 (중첩 괄호 고려)
            json_pattern = r'\{(?:[^{}]*|\{[^{}]*\})*\}'
            question_patterns = re.findall(json_pattern, content, re.DOTALL)
            
            for q_text in question_patterns:
                try:
                    cleaned_json = self._clean_json_string_advanced(q_text)
                    question_obj = json.loads(cleaned_json)
                    
                    # 필수 필드 확인 및 기본값 설정
                    if isinstance(question_obj, dict) and question_obj.get("question_text"):
                        validated_question = self._validate_question_object(question_obj)
                        if validated_question:
                            question_objects.append(validated_question)
                except Exception as e:
                    print(f"[경고] 단위 {unit_idx} 개별 JSON 객체 파싱 오류: {e}")
                    continue
            
            if question_objects:
                print(f"[성공] 단위 {unit_idx}: 방법2(개별 객체)로 {len(question_objects)}개 추출")
                return question_objects
            
            # 방법 3: 정규식을 이용한 구조화된 텍스트 파싱
            regex_questions = self._extract_questions_with_regex(content)
            if regex_questions:
                print(f"[성공] 단위 {unit_idx}: 방법3(정규식)으로 {len(regex_questions)}개 추출")
                return regex_questions
            
            # 방법 4: 간단한 텍스트 파싱 (최후의 수단)
            simple_questions = self._extract_questions_simple_parsing(content)
            if simple_questions:
                print(f"[성공] 단위 {unit_idx}: 방법4(단순 파싱)으로 {len(simple_questions)}개 추출")
                return simple_questions
                
        except Exception as e:
            print(f"[실패] 단위 {unit_idx} 전체 추출 과정 실패: {e}")
        
        print(f"[실패] 단위 {unit_idx}: 모든 추출 방법 실패")
        return []
    
    def _clean_json_string(self, json_str: str) -> str:
        """JSON 문자열 정리"""
        # 흔한 JSON 오류들 수정
        cleaned = json_str.strip()
        
        # 끝에 있는 쉼표 제거
        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
        
        # 제어 문자 제거/변환
        cleaned = cleaned.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        
        # 따옴표 이스케이프 처리
        cleaned = re.sub(r'([^\\])"([^":\[\],{}]*)"(\s*[,}\]])', r'\1"\2"\3', cleaned)
        
        return cleaned
    
    def _clean_json_string_advanced(self, json_str: str) -> str:
        """고급 JSON 문자열 정리 - 개선된 버전"""
        try:
            cleaned = json_str.strip()
            
            # 1. 일반적인 JSON 정리
            cleaned = re.sub(r'\s+', ' ', cleaned)  # 공백 정리
            cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)  # 끝 쉼표 제거
            
            # 2. 문자열 내 따옴표 문제 해결
            # "text": "문제 내용 "여기"에 있음" → "text": "문제 내용 \"여기\"에 있음"
            def fix_quotes_in_values(match):
                key_part = match.group(1)
                value_part = match.group(2)
                # 값 안의 따옴표를 이스케이프
                fixed_value = value_part.replace('"', '\\"')
                return f'{key_part}"{fixed_value}"'
            
            # 키:값 패턴에서 값 부분의 따옴표 수정
            cleaned = re.sub(r'("[^"]*":\s*")(.*?)("(?:\s*[,}\]]))', fix_quotes_in_values, cleaned)
            
            # 3. 객체 간 누락된 쉼표 추가
            cleaned = re.sub(r'}\s*{', '}, {', cleaned)
            cleaned = re.sub(r']\s*\[', '], [', cleaned)
            
            # 4. 키 이름 따옴표 누락 수정
            cleaned = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', cleaned)
            
            return cleaned
            
        except Exception as e:
            print(f"[JSON정리오류] {e}")
            return json_str
        
        return cleaned
    
    def _validate_and_clean_questions(self, questions: List[Dict]) -> List[Dict]:
        """문제 목록 검증 및 정리"""
        validated = []
        
        for i, q in enumerate(questions):
            if isinstance(q, dict):
                print(f"[검증중] 문제 {i+1} 키: {list(q.keys())}")
                validated_q = self._validate_question_object(q)
                if validated_q:
                    validated.append(validated_q)
                    print(f"[검증성공] 문제 {i+1} 통과")
                else:
                    print(f"[검증실패] 문제 {i+1} 제거됨")
        
        print(f"[검증완료] 총 {len(questions)}개 중 {len(validated)}개 문제 통과")
        return validated
    
    def _validate_question_object(self, question: Dict) -> Dict:
        """개별 문제 객체 검증 및 기본값 설정"""        
        # 다양한 키 이름으로 question_text 찾기
        question_text = None
        for key in ["question_text", "question", "text", "problem", "content"]:
            if question.get(key):
                question_text = question[key]
                break
        
        if not question_text:
            print(f"[검증실패] 문제 텍스트 누락")
            print(f"  - 문제 객체 타입: {type(question)}")
            if isinstance(question, dict):
                print(f"  - 사용 가능한 키: {list(question.keys())}")
                print(f"  - 전체 내용 (첫 200자): {str(question)[:200]}...")
            else:
                print(f"  - 값: {question}")
            return None
        
        # 기본 구조 보장
        validated = {
            "question_number": question.get("question_number", 0),
            "question_text": str(question_text).strip(),
            "options": question.get("options", []),
            "correct_answer": question.get("correct_answer"),
            "topic_category": question.get("topic_category", "일반"),
            "difficulty_level": question.get("difficulty_level", "중급"),
            "explanation": question.get("explanation"),
            "contains_image": question.get("contains_image", False)
        }
        
        # options가 문자열인 경우 리스트로 변환
        if isinstance(validated["options"], str):
            options_text = validated["options"]
            # 선택지 패턴으로 분할
            option_matches = re.findall(r'[①②③④⑤]\s*([^\n①②③④⑤]+)', options_text)
            if option_matches:
                validated["options"] = [opt.strip() for opt in option_matches]
            else:
                validated["options"] = []
        
        return validated
    
    def _extract_questions_with_regex_v2(self, content: str) -> List[Dict]:
        """강화된 정규식 기반 문제 추출"""
        questions = []
        
        try:
            # 1. JSON 형식의 문제들 먼저 추출
            json_patterns = [
                # 표준 JSON 형식
                r'"question_text":\s*"([^"]+)"[\s\S]*?"options":\s*\[([^\]]+)\]',
                # 단순한 형식
                r'문제\s*[:：]\s*"([^"]+)"[\s\S]*?선택지\s*[:：]\s*\[([^\]]+)\]',
                # 번호 형식
                r'(\d+)\.\s*([^"]+?)(?=선택지|옵션|①|A\.)[\s\S]*?\[([^\]]+)\]'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                if matches:
                    print(f"[JSON추출] {len(matches)}개 구조화된 문제 발견")
                    
                    for i, match in enumerate(matches):
                        try:
                            if len(match) == 2:  # question_text, options
                                question_text, options_str = match
                            else:  # question_num, question_text, options
                                question_text, options_str = match[1], match[2]
                            
                            # 선택지 추출 - 다양한 형식 지원
                            options = []
                            option_extraction_patterns = [
                                r'"([^"]+)"',  # 따옴표로 둘러싸인 것
                                r"'([^']+)'",  # 작은따옴표
                                r'([^,\[\]]+)',  # 쉼표로 구분된 것
                            ]
                            
                            for opt_pattern in option_extraction_patterns:
                                option_matches = re.findall(opt_pattern, options_str)
                                if option_matches:
                                    filtered_options = [opt.strip() for opt in option_matches 
                                                      if opt.strip() and len(opt.strip()) > 1]
                                    if len(filtered_options) >= 3:
                                        options = filtered_options[:5]
                                        break
                            
                            if question_text and len(options) >= 3:
                                questions.append({
                                    "question_text": question_text.strip(),
                                    "options": options,
                                    "correct_answer": None,
                                    "question_number": i + 1
                                })
                        except Exception as e:
                            print(f"[JSON추출오류] 문제 {i}: {e}")
                            continue
                    
                    if questions:
                        print(f"[JSON추출완료] {len(questions)}개 문제 추출 성공")
                        return questions
            
            # 2. JSON 형식이 실패한 경우 대안 방법 사용
            print("[JSON추출실패] 대안 방법으로 전환")
            return self._extract_questions_with_regex_fallback(content)
            
        except Exception as e:
            print(f"[정규식오류] {e}")
            return self._extract_questions_with_regex_fallback(content)
    
    def _extract_questions_with_regex_fallback(self, content: str) -> List[Dict]:
        """정규식 대안 방법 - 강화된 패턴"""
        questions = []
        
        try:
            print("[대안추출] 텍스트 직접 분석 시작")
            
            # 1. 전체 문제 개수 먼저 파악
            all_question_numbers = re.findall(r'(?:^|\n)(\d+)\.\s', content, re.MULTILINE)
            total_expected = len(set(all_question_numbers))
            print(f"[대안추출] 예상 문제 수: {total_expected}개")
            
            # 2. 강화된 문제 분할 - 더 정확한 패턴
            question_blocks = re.split(r'(?=(?:^|\n)(\d+)\.\s)', content, flags=re.MULTILINE)
            valid_blocks = []
            
            for i in range(1, len(question_blocks), 2):  # 홀수 인덱스가 실제 문제 번호
                if i + 1 < len(question_blocks):
                    question_num = question_blocks[i]
                    question_content = question_blocks[i + 1]
                    valid_blocks.append((int(question_num), question_content))
            
            print(f"[대안추출] {len(valid_blocks)}개 문제 블록 발견")
            
            for question_num, block in valid_blocks:
                try:
                    # 3. 문제 텍스트 추출 - 개선된 패턴
                    question_text_patterns = [
                        r'^(.+?)(?=\s*[①②③④⑤ⅠⅡⅢⅣⅤabcdABCD]\s*\.|\s*A\s*\.|$)',  # 선택지 전까지
                        r'^(.+?)(?=\s*\d+\s*[\.\)]\s*|\s*[①②③④⑤]\s*)',  # 숫자 선택지나 원형 선택지 전까지  
                        r'^(.+?)(?=\s*정답\s*[:：]|\s*해설\s*[:：]|$)'  # 정답/해설 전까지
                    ]
                    
                    question_text = ""
                    for pattern in question_text_patterns:
                        match = re.search(pattern, block.strip(), re.DOTALL | re.MULTILINE)
                        if match and match.group(1).strip():
                            question_text = match.group(1).strip()
                            break
                    
                    if not question_text:
                        print(f"[경고] 문제 {question_num}: 문제 텍스트 추출 실패")
                        continue
                    
                    # 4. 선택지 추출 - 다양한 형식과 특수문자 지원
                    options = []
                    option_patterns = [
                        # 원형 숫자 선택지 (①, ②, ③, ④) - 더 포괄적
                        r'[①②③④⑤]\s*(.+?)(?=\s*[①②③④⑤]|$)',
                        # 로마자/문자 선택지 with 특수 처리
                        r'[ⅠⅡⅢⅣⅤabcdABCD]\s*[\.\)]\s*(.+?)(?=\s*[ⅠⅡⅢⅣⅤabcdABCD][\.\)]|$)',
                        # 숫자 선택지 (1. 2. 3. 4.)
                        r'(?:^|\n)\s*([1-5])[\.\)]\s*(.+?)(?=\s*[1-5][\.\)]|$)',
                        # A. B. C. D. 형식 - 특수문자 포함
                        r'(?:^|\n)\s*([A-E])[\.\)]\s*(.+?)(?=\s*[A-E][\.\)]|$)'
                    ]
                    
                    for pattern_idx, pattern in enumerate(option_patterns):
                        option_matches = re.findall(pattern, block, re.MULTILINE | re.DOTALL)
                        if option_matches:
                            if pattern_idx >= 2:  # 숫자나 문자 패턴인 경우
                                # 튜플에서 두 번째 요소(실제 선택지 텍스트) 추출
                                filtered_options = []
                                for match in option_matches:
                                    if isinstance(match, tuple) and len(match) == 2:
                                        option_text = match[1].strip()
                                    else:
                                        option_text = str(match).strip()
                                    
                                    # 특수문자와 백슬래시 정리
                                    option_text = self._clean_option_text(option_text)
                                    if option_text and len(option_text) > 1:
                                        filtered_options.append(option_text)
                            else:
                                # 원형이나 로마자 패턴
                                filtered_options = []
                                for match in option_matches:
                                    option_text = str(match).strip()
                                    option_text = self._clean_option_text(option_text)
                                    if option_text and len(option_text) > 1:
                                        filtered_options.append(option_text)
                            
                            if len(filtered_options) >= 2:  # 최소 2개 선택지 (더 유연하게)
                                options = filtered_options  # 개수 제한 제거
                                print(f"[대안추출] 문제 {question_num}: {len(options)}개 선택지 추출 (패턴 {pattern_idx})")
                                break
                    
                    # 5. 정답 추출 (가능한 경우)
                    correct_answer = None
                    answer_patterns = [
                        r'정답\s*[:：]\s*([①②③④⑤ⅠⅡⅢⅣⅤabcdABCD1-5])',
                        r'답\s*[:：]\s*([①②③④⑤ⅠⅡⅢⅣⅤabcdABCD1-5])',
                        r'\(정답\s*[:：]?\s*([①②③④⑤ⅠⅡⅢⅣⅤabcdABCD1-5])\)'
                    ]
                    
                    for pattern in answer_patterns:
                        answer_match = re.search(pattern, block)
                        if answer_match:
                            correct_answer = answer_match.group(1)
                            break
                    
                    # 6. 유효한 문제만 추가 (조건 완화)
                    if question_text and len(options) >= 2:  # 3개에서 2개로 완화
                        # 문제 텍스트 정리
                        question_text = re.sub(r'\s+', ' ', question_text).strip()
                        question_text = re.sub(r'^다음\s+중\s*', '', question_text)
                        
                        # 표/그림/코드 언급이 있으면 특별 표시
                        if any(keyword in question_text for keyword in ['표', '그림', '코드', '다음과 같은', '아래']):
                            question_text = f"[표/그림/코드 포함] {question_text}"
                        
                        questions.append({
                            "question_number": question_num,
                            "passage": None,  # 정규식 추출에서는 지문 분리 불가
                            "question_text": question_text,
                            "options": options,
                            "correct_answer": correct_answer,
                            "topic_category": "일반",
                            "difficulty_level": "중급"
                        })
                        print(f"[성공] 문제 {question_num} 추출 완료 (선택지 {len(options)}개)")
                    else:
                        print(f"[실패] 문제 {question_num}: 텍스트='{question_text[:30] if question_text else 'None'}...', 선택지={len(options)}개")
                
                except Exception as e:
                    print(f"[오류] 문제 {question_num} 처리 중 오류: {e}")
                    continue
            
            print(f"[대안추출] 최종 {len(questions)}개 문제 추출 완료")
            
            # 7. 중복 문제 제거
            unique_questions = self._remove_duplicate_questions(questions)
            if len(unique_questions) != len(questions):
                print(f"[중복제거] {len(questions) - len(unique_questions)}개 중복 문제 제거됨")
            
            return unique_questions
            
        except Exception as e:
            print(f"[대안추출오류] {e}")
            return []
    
    def _remove_duplicate_questions(self, questions: List[Dict]) -> List[Dict]:
        """중복 문제 제거"""
        unique_questions = []
        seen_questions = set()
        
        for question in questions:
            # 문제 텍스트의 핵심 부분으로 중복 체크
            question_key = question.get("question_text", "").strip()[:50]  # 첫 50자로 비교
            question_key = re.sub(r'\s+', ' ', question_key.lower())
            
            if question_key not in seen_questions and question_key:
                seen_questions.add(question_key)
                unique_questions.append(question)
        
        return unique_questions
    
    def _extract_questions_with_regex(self, content: str) -> List[Dict]:
        """정규식을 이용한 구조화된 문제 추출"""
        questions = []
        
        try:
            # 문제 번호 패턴으로 분할
            question_blocks = re.split(r'(?=\d+\.\s)', content)
            
            for block in question_blocks:
                if not block.strip():
                    continue
                
                # 문제 번호 추출
                num_match = re.match(r'(\d+)\.\s*', block)
                if not num_match:
                    continue
                
                question_num = int(num_match.group(1))
                
                # 문제 텍스트 추출
                question_text_match = re.search(r'\d+\.\s*(.+?)(?=[①②③④⑤]|$)', block, re.DOTALL)
                if not question_text_match:
                    continue
                
                question_text = question_text_match.group(1).strip()
                
                # 선택지 추출
                options = []
                option_matches = re.findall(r'[①②③④⑤]\s*([^\n①②③④⑤]+)', block)
                options = [opt.strip() for opt in option_matches]
                
                # 정답 추출
                correct_answer = None
                answer_match = re.search(r'정답\s*[:：]\s*([①②③④⑤\d]+)', block)
                if answer_match:
                    correct_answer = answer_match.group(1)
                
                # 해설 추출
                explanation = None
                explanation_match = re.search(r'해설\s*[:：]\s*(.+?)(?=\n\n|\n\d+\.|$)', block, re.DOTALL)
                if explanation_match:
                    explanation = explanation_match.group(1).strip()
                
                question_obj = {
                    "question_number": question_num,
                    "question_text": question_text,
                    "options": options,
                    "correct_answer": correct_answer,
                    "topic_category": "일반",
                    "difficulty_level": "중급", 
                    "explanation": explanation,
                    "contains_image": "그림" in block or "도표" in block or "표" in block
                }
                
                questions.append(question_obj)
                
        except Exception as e:
            print(f"정규식 추출 오류: {e}")
        
        return questions
    
    def _extract_questions_simple_parsing(self, content: str) -> List[Dict]:
        """간단한 텍스트 파싱 (최후의 수단)"""
        questions = []
        
        try:
            # 숫자로 시작하는 라인 찾기
            lines = content.split('\n')
            current_question = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 문제 번호 패턴
                if re.match(r'\d+\.\s', line):
                    if current_question:
                        questions.append(current_question)
                    
                    num_match = re.match(r'(\d+)\.\s*(.+)', line)
                    if num_match:
                        current_question = {
                            "question_number": int(num_match.group(1)),
                            "question_text": num_match.group(2),
                            "options": [],
                            "correct_answer": None,
                            "topic_category": "일반",
                            "difficulty_level": "중급",
                            "explanation": None,
                            "contains_image": False
                        }
                
                # 선택지 패턴
                elif re.match(r'[①②③④⑤]\s', line) and current_question:
                    option_text = re.sub(r'^[①②③④⑤]\s*', '', line)
                    current_question["options"].append(option_text)
                
                # 정답 패턴
                elif "정답" in line and current_question:
                    answer_match = re.search(r'정답\s*[:：]\s*([①②③④⑤\d]+)', line)
                    if answer_match:
                        current_question["correct_answer"] = answer_match.group(1)
            
            # 마지막 문제 추가
            if current_question:
                questions.append(current_question)
                
        except Exception as e:
            print(f"간단 파싱 오류: {e}")
        
        return questions
    
    def _extract_questions_from_text(self, content: str) -> List[Dict]:
        """텍스트에서 직접 문제 정보 추출 (JSON 파싱 실패시 백업)"""
        questions = []
        
        try:
            # 문제 번호 패턴으로 분할
            question_parts = re.split(r'(?=\d+\.)', content)
            
            for part in question_parts:
                if not part.strip():
                    continue
                
                # 문제 번호 추출
                num_match = re.search(r'^(\d+)\.', part)
                if not num_match:
                    continue
                
                question_num = int(num_match.group(1))
                
                # 문제 텍스트 추출 (간단한 버전)
                question_text = re.search(r'\d+\.\s*(.+?)(?=\[|$)', part, re.DOTALL)
                if not question_text:
                    continue
                
                question_obj = {
                    "question_number": question_num,
                    "question_text": question_text.group(1).strip(),
                    "options": [],
                    "correct_answer": None,
                    "topic_category": "일반",
                    "difficulty_level": "중급",
                    "explanation": None
                }
                
                # 선택지 추출 시도
                options = re.findall(r'[①②③④]\s*([^\n①②③④]+)', part)
                if options:
                    question_obj["options"] = [opt.strip() for opt in options]
                
                questions.append(question_obj)
        
        except Exception as e:
            print(f"텍스트 직접 추출 오류: {e}")
        
        return questions
    
    async def _process_theory_materials(self, theory_text: str, theory_pages: List[int], db: Session) -> Dict[str, Any]:
        """이론/학습자료 처리"""
        try:
            agent = await self._get_agent("study_material_generation", db)
            if not agent:
                return {"error": "Study material generation agent not found"}
            
            prompt = f"""다음 이론/교재 텍스트를 기반으로 체계적인 학습자료를 생성해주세요:

{theory_text[:4000]}

JSON 배열 형식으로 학습자료를 생성해주세요:
[
    {{
        "title": "학습자료 제목",
        "content": "상세한 학습 내용",
        "content_type": "개념정리/요약/예제",
        "difficulty_level": "초급/중급/고급",
        "keywords": ["키워드1", "키워드2"],
        "page_reference": {theory_pages}
    }}
]"""

            response = await claude_service.call_claude_api_direct(prompt, agent, db, max_tokens=6000)
            
            if response.get("success"):
                content = response["content"]
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    materials = json.loads(json_match.group())
                    return {
                        "success": True,
                        "materials": materials,
                        "count": len(materials),
                        "cost": self._calculate_cost(response.get("usage", {}))
                    }
            
            return {"error": "Failed to process theory materials"}
            
        except Exception as e:
            logger.error(f"Theory material processing error: {e}")
            return {"error": str(e)}
    
    async def _enhanced_quality_verification(self, questions: List, materials: List, page_classification: Dict, db: Session) -> Dict[str, Any]:
        """향상된 품질 검증"""
        try:
            agent = await self._get_agent("quality_verification", db)
            if not agent:
                return {"success": True, "quality_score": 80, "feedback": "품질 검증 에이전트 없음", "cost": 0}
            
            prompt = f"""다음 향상된 PDF 처리 결과의 품질을 검증해주세요:

처리 방법: PDF → 구조분석 → 페이지분류 → 선택적OCR → 문제단위정리
총 페이지: {page_classification.get('total_pages', 0)}
문제 페이지: {len(page_classification.get('question_pages', []))}
이론 페이지: {len(page_classification.get('theory_pages', []))}
추출된 문제: {len(questions)}
생성된 학습자료: {len(materials)}

JSON 형식으로 평가 결과를 제공해주세요:
{{
    "quality_score": 0-100점,
    "extraction_accuracy": 0-100점,
    "classification_accuracy": 0-100점,
    "completeness": 0-100점,
    "feedback": "종합 평가",
    "recommendations": ["개선사항1", "개선사항2"]
}}"""

            response = await claude_service.call_claude_api_direct(prompt, agent, db, max_tokens=1000)
            
            if response.get("success"):
                content = response["content"]
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    quality_result = json.loads(json_match.group())
                    quality_result["success"] = True
                    quality_result["cost"] = self._calculate_cost(response.get("usage", {}))
                    return quality_result
            
            return {"success": True, "quality_score": 85, "feedback": "향상된 파이프라인 처리 완료", "cost": 0}
            
        except Exception as e:
            logger.error(f"Enhanced quality verification error: {e}")
            return {"success": True, "quality_score": 75, "feedback": f"검증 오류: {str(e)}", "cost": 0}
    
    async def _get_agent(self, agent_type: str, db: Session) -> Optional[Dict]:
        """AI 에이전트 조회"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_agents WHERE agent_type = ? AND is_active = 1 LIMIT 1", (agent_type,))
            agent_row = cursor.fetchone()
            conn.close()
            
            if not agent_row:
                return None
            
            return {
                "model_name": agent_row[4],
                "system_prompt": agent_row[9] or '',
                "max_tokens": agent_row[7] or 4000,
                "temperature": agent_row[8] or 0.7
            }
        except Exception as e:
            logger.error(f"Agent retrieval error: {e}")
            return None
    
    async def _save_questions_to_db(self, questions: List[Dict], upload_id: int, db: Session) -> List[Dict]:
        """문제를 데이터베이스에 저장"""
        saved_questions = []
        
        # upload_id로부터 certificate_id 가져오기
        upload_record = db.execute(
            text("SELECT certificate_id FROM pdf_uploads WHERE id = :upload_id"),
            {"upload_id": upload_id}
        ).fetchone()
        
        if not upload_record:
            print(f"[오류] upload_id {upload_id}에 해당하는 업로드 레코드를 찾을 수 없습니다")
            return []
        
        certificate_id = upload_record.certificate_id
        print(f"[알림] certificate_id {certificate_id} 확인됨")
        
        for i, question in enumerate(questions):
            try:
                result = db.execute(
                    text("""
                        INSERT INTO extracted_questions 
                        (pdf_upload_id, certificate_id, question_number, question_text, passage, options, correct_answer, topic_category, difficulty_level, explanation)
                        VALUES (:pdf_id, :cert_id, :q_num, :q_text, :passage, :options, :answer, :category, :difficulty, :explanation)
                    """),
                    {
                        "pdf_id": upload_id,
                        "cert_id": certificate_id,
                        "q_num": question.get("question_number", i + 1),
                        "q_text": question.get("question_text", ""),
                        "passage": question.get("passage", None),
                        "options": json.dumps(question.get("options", []), ensure_ascii=False),
                        "answer": question.get("correct_answer", ""),
                        "category": question.get("topic_category", "일반"),
                        "difficulty": question.get("difficulty_level", "중급"),
                        "explanation": question.get("explanation", "")
                    }
                )
                db.flush()
                
                saved_questions.append({
                    "id": result.lastrowid,
                    "question_text": question.get("question_text", ""),
                    "topic_category": question.get("topic_category", "일반")
                })
                
            except Exception as e:
                logger.error(f"Error saving question {i}: {e}")
                continue
        
        db.commit()
        return saved_questions
    
    async def _save_materials_to_db(self, materials: List[Dict], upload_id: int, db: Session) -> List[Dict]:
        """학습자료를 데이터베이스에 저장"""
        saved_materials = []
        
        for i, material in enumerate(materials):
            try:
                result = db.execute(
                    text("""
                        INSERT INTO study_materials 
                        (pdf_upload_id, title, content, content_type, difficulty_level, keywords, chapter_number, section_number)
                        VALUES (:pdf_id, :title, :content, :content_type, :difficulty, :keywords, :chapter, :section)
                    """),
                    {
                        "pdf_id": upload_id,
                        "title": material.get("title", f"학습자료 {i+1}"),
                        "content": material.get("content", ""),
                        "content_type": material.get("content_type", "개념정리"),
                        "difficulty": material.get("difficulty_level", "중급"),
                        "keywords": json.dumps(material.get("keywords", []), ensure_ascii=False),
                        "chapter": 1,
                        "section": i + 1
                    }
                )
                db.flush()
                
                saved_materials.append({
                    "id": result.lastrowid,
                    "title": material.get("title", f"학습자료 {i+1}"),
                    "content_type": material.get("content_type", "개념정리")
                })
                
            except Exception as e:
                logger.error(f"Error saving material {i}: {e}")
                continue
        
        db.commit()
        return saved_materials
    
    def _calculate_cost(self, usage: Dict[str, Any]) -> float:
        """토큰 사용량 기반 비용 계산"""
        if not usage:
            return 0.0
        
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        
        # Claude 3.5 Sonnet 가격 (2024 기준)
        input_cost_per_token = 0.000003
        output_cost_per_token = 0.000015
        
        return (input_tokens * input_cost_per_token) + (output_tokens * output_cost_per_token)
    
    async def _create_ai_task(self, upload_id: int, agent_type: str, status: str, db: Session):
        """AI 작업 생성"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ai_tasks (file_upload_id, task_type, status, started_at, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (upload_id, agent_type, status))
            
            conn.commit()
            conn.close()
            logger.info(f"Created AI task: {agent_type} for upload {upload_id}")
        except Exception as e:
            logger.error(f"Error creating AI task: {e}")
    
    def _serialize_for_json(self, obj):
        """JSON 직렬화를 위한 객체 변환"""
        if hasattr(obj, '__dict__'):
            # dataclass나 custom 객체를 dict로 변환
            result = {}
            for key, value in obj.__dict__.items():
                if isinstance(value, (list, tuple)):
                    result[key] = [self._serialize_for_json(item) for item in value]
                elif hasattr(value, '__dict__'):
                    result[key] = self._serialize_for_json(value)
                else:
                    result[key] = value
            return result
        else:
            return obj
    
    async def _update_ai_task(self, upload_id: int, agent_type: str, status: str, result_data: Dict, db: Session):
        """AI 작업 상태 업데이트"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # 직렬화 가능한 형태로 변환
            serializable_data = self._serialize_for_json(result_data)
            
            cursor.execute("""
                UPDATE ai_tasks 
                SET status = ?, 
                    output_data = ?,
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE file_upload_id = ? AND task_type = ?
            """, (status, json.dumps(serializable_data, ensure_ascii=False), upload_id, agent_type))
            
            conn.commit()
            conn.close()
            logger.info(f"Updated AI task: {agent_type} for upload {upload_id} - {status}")
        except Exception as e:
            logger.error(f"Error updating AI task: {e}")
    
    async def _log_progress(self, upload_id: int, message: str, db: Session):
        """진행 상황 로그"""
        try:
            print(f"[로그] Upload {upload_id}: {message}")
        except Exception as e:
            logger.error(f"Error logging progress: {e}")
    
    # =============================================================================
    # 병렬 처리 메서드들
    # =============================================================================
    
    def _should_use_parallel_processing(self, text: str, page_classification: Dict) -> bool:
        """병렬 처리 필요 여부 결정"""
        text_length = len(text)
        total_pages = len(page_classification.get('question_pages', []))
        
        # 60문제 이상 있을 가능성이 높은 경우 병렬 처리 활성화
        # 문제 패턴 개수 확인
        question_patterns = len(re.findall(r'(?:^|\n)(\d+)\.\s', text, re.MULTILINE))
        
        # 조건 완화: 더 작은 문서도 병렬 처리
        use_parallel = (
            total_pages > 5 or  # 5페이지 이상
            text_length > 20000 or  # 20KB 이상
            question_patterns > 20  # 20문제 이상 예상
        )
        
        print(f"[병렬처리판단] 페이지:{total_pages}, 텍스트길이:{text_length}, 예상문제:{question_patterns}, 병렬처리:{use_parallel}")
        return use_parallel
    
    async def _extract_questions_parallel(self, question_text: str, question_pages: List[int], 
                                        upload_id: int, db: Session) -> Dict[str, Any]:
        """병렬 처리로 문제 추출"""
        try:
            print(f"[병렬처리] 시작 - 페이지 {len(question_pages)}개, 텍스트 {len(question_text)} 문자")
            
            # 1단계: 텍스트를 청크로 분할
            chunks = self._create_parallel_chunks(question_text, question_pages)
            print(f"[병렬처리] {len(chunks)}개 청크로 분할 완료")
            
            # 2단계: 각 청크를 병렬로 처리
            all_questions = []
            total_cost = 0
            
            # 청크별 병렬 처리 태스크 생성
            tasks = []
            for i, chunk in enumerate(chunks):
                task = self._process_chunk_async(chunk, i, upload_id, db)
                tasks.append(task)
            
            # 병렬 실행
            print(f"[병렬처리] {len(tasks)}개 태스크 병렬 실행 시작...")
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 3단계: 결과 통합
            successful_chunks = 0
            for i, result in enumerate(chunk_results):
                if isinstance(result, Exception):
                    print(f"[병렬처리] 청크 {i} 실패: {result}")
                    continue
                
                if result.get("success"):
                    chunk_questions = result.get("questions", [])
                    all_questions.extend(chunk_questions)
                    total_cost += result.get("cost", 0)
                    successful_chunks += 1
                    print(f"[병렬처리] 청크 {i} 성공: {len(chunk_questions)}개 문제")
                else:
                    print(f"[병렬처리] 청크 {i} 실패: {result.get('error', 'Unknown error')}")
            
            print(f"[병렬처리] 완료 - 성공한 청크: {successful_chunks}/{len(chunks)}, 총 문제: {len(all_questions)}개")
            
            return {
                "success": True,
                "questions": all_questions,
                "cost": total_cost,
                "parallel_processing": True,
                "chunks_processed": successful_chunks,
                "total_chunks": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Parallel processing error: {e}")
            return {"error": f"병렬 처리 실패: {str(e)}"}
    
    def _create_parallel_chunks(self, text: str, question_pages: List[int]) -> List[Dict]:
        """병렬 처리를 위한 청크 생성 - 60문제 완전 추출 최적화"""
        chunks = []
        
        # 1. 먼저 전체 문제 개수 파악
        all_question_numbers = re.findall(r'(?:^|\n)(\d+)\.\s', text, re.MULTILINE)
        total_questions = len(set(all_question_numbers))
        print(f"[청크생성] 전체 예상 문제 수: {total_questions}개")
        
        # 2. 문제 기반으로 청크 분할 (더 세밀하게)
        question_units = self._split_text_by_question_units(text)
        print(f"[청크생성] {len(question_units)}개 문제 단위 발견")
        
        # 3. 최적화된 청크 크기 결정
        if total_questions > 50:  # 50문제 이상인 경우
            # 더 많은 청크로 분할하여 각 청크에서 놓치는 문제 최소화
            target_chunks = min(6, math.ceil(total_questions / 12))  # 청크당 10-15개 문제
        else:
            target_chunks = min(4, math.ceil(total_questions / 10))  # 청크당 8-12개 문제
        
        print(f"[청크생성] 목표 청크 수: {target_chunks}개")
        
        if len(question_units) <= target_chunks:
            # 문제 단위가 목표 청크 수보다 적으면 각각을 청크로
            for i, unit in enumerate(question_units):
                if unit.strip():  # 빈 텍스트 제외
                    chunks.append({
                        "chunk_id": i,
                        "text": unit,
                        "pages": question_pages,
                        "unit_type": "single_unit",
                        "expected_questions": self._count_questions_in_text(unit)
                    })
        else:
            # 문제 단위가 많으면 균등하게 분배
            units_per_chunk = math.ceil(len(question_units) / target_chunks)
            
            for i in range(0, len(question_units), units_per_chunk):
                chunk_units = question_units[i:i + units_per_chunk]
                chunk_text = "\n\n".join([unit for unit in chunk_units if unit.strip()])
                
                if chunk_text.strip():  # 빈 텍스트 제외
                    chunks.append({
                        "chunk_id": len(chunks),
                        "text": chunk_text,
                        "pages": question_pages,
                        "unit_type": "multiple_units",
                        "unit_count": len(chunk_units),
                        "expected_questions": self._count_questions_in_text(chunk_text)
                    })
        
        print(f"[청크생성] {len(chunks)}개 청크 생성 완료")
        for chunk in chunks:
            print(f"  청크 {chunk['chunk_id']}: {chunk['expected_questions']}개 문제 예상")
        return chunks
    
    def _count_questions_in_text(self, text: str) -> int:
        """텍스트에서 문제 개수 추정"""
        question_numbers = re.findall(r'(?:^|\n)(\d+)\.\s', text, re.MULTILINE)
        return len(set(question_numbers))
    
    def _clean_option_text(self, text: str) -> str:
        """선택지 텍스트 정리 - 특수문자 및 백슬래시 처리"""
        if not text:
            return ""
        
        # 1. 다중 백슬래시 정리
        text = re.sub(r'\\{2,}', '', text)  # 2개 이상의 백슬래시 제거
        text = re.sub(r'\\(?=["\'])', '', text)  # 따옴표 앞의 백슬래시 제거
        
        # 2. 불필요한 공백 정리
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # 3. 빈 선택지나 의미없는 문자 제거
        meaningless_patterns = [
            r'^[,\s]*$',  # 쉼표와 공백만
            r'^[\\\s]*$',  # 백슬래시와 공백만
            r'^["\'\s]*$',  # 따옴표와 공백만
        ]
        
        for pattern in meaningless_patterns:
            if re.match(pattern, text):
                return ""
        
        # 4. JavaScript 코드나 특수한 경우 처리
        if 'alert(' in text or 'prompt(' in text:
            # JavaScript 함수 호출 형태로 정리
            text = re.sub(r'[\\"\s]+', '', text)  # 불필요한 백슬래시, 따옴표, 공백 제거
            if text.endswith(',') or text.endswith(')'):
                pass  # 의미있는 구문은 유지
        
        return text
    
    async def _process_chunk_async(self, chunk: Dict, chunk_idx: int, upload_id: int, db: Session) -> Dict[str, Any]:
        """단일 청크 비동기 처리"""
        try:
            chunk_text = chunk["text"]
            print(f"[청크{chunk_idx}] 처리 시작 - {len(chunk_text)} 문자")
            
            # AI 에이전트 가져오기
            agent = await self._get_agent("question_extraction", db)
            if not agent:
                return {"error": f"청크 {chunk_idx}: Question extraction agent not found"}
            
            # Claude API 호출
            prompt = f"""다음은 정보처리산업기사 필기시험 문제 텍스트입니다. 이 텍스트에서 완전한 객관식 문제들을 추출하여 JSON 배열로 반환해주세요.

CRITICAL 요구사항:
1. 지문과 문제를 명확히 분리하세요
2. 지문(passage): 문제를 풀기 위해 주어진 설명, 표, 그림, 코드 등
3. 문제(question_text): 실제 질문 ("다음 중 옳은 것은?", "결과는?" 등)
4. 선택지(options): 모든 보기를 정확히 추출 (개수 제한 없음)
5. 지문이 없는 단순한 문제는 passage를 null로 설정
6. 각 문제의 실제 번호를 question_number에 정확히 기록하세요

=== 처리할 텍스트 ===
{chunk_text}

=== 필수 출력 형식 ===
반드시 다음 형식으로만 응답하세요:

[
  {{
    "passage": "문제 해결을 위한 지문/설명/코드/표 (없으면 null)",
    "question_text": "실제 질문 내용",
    "options": ["선택지1", "선택지2", "선택지3", "선택지4"],
    "correct_answer": "1",
    "question_number": 1
  }},
  {{
    "question_text": "두 번째 문제의 질문 내용",
    "options": ["선택지1", "선택지2", "선택지3", "선택지4"],
    "correct_answer": "2", 
    "question_number": 2
  }}
]

=== 추출 지침 ===
1. 문제 번호(1., 2., 3. 등)가 있는 모든 문제를 찾으세요
2. 각 문제의 완전한 질문 부분을 question_text에 넣으세요
3. 선택지(①②③④ 또는 1)2)3)4))는 options 배열에 넣으세요
4. 정답이 있으면 correct_answer에 넣고, 없으면 null로 하세요

=== 중요 ===
- 선택지만 있는 배열 ["선택지1", "선택지2"] 같은 형식으로 반환하지 마세요
- 반드시 question_text, options, correct_answer, question_number 키가 모두 있는 완전한 객체를 반환하세요"""

            response = await claude_service.call_claude_api(prompt, agent['model'])
            
            if response.get("success"):
                content = response['response']
                cost = response.get('cost', 0)
                
                # 문제 추출
                questions = self._extract_questions_from_response(content, chunk_idx)
                
                print(f"[청크{chunk_idx}] 완료 - {len(questions)}개 문제 추출 (비용: ${cost:.4f})")
                
                return {
                    "success": True,
                    "questions": questions,
                    "cost": cost,
                    "chunk_id": chunk_idx
                }
            else:
                error_msg = response.get('error', 'Unknown API error')
                print(f"[청크{chunk_idx}] API 호출 실패: {error_msg}")
                return {"error": f"청크 {chunk_idx} API 실패: {error_msg}"}
                
        except Exception as e:
            print(f"[청크{chunk_idx}] 예외 발생: {e}")
            return {"error": f"청크 {chunk_idx} 처리 실패: {str(e)}"}

    # =============================================================================
    # 레이아웃 분석 및 구조적 OCR 처리 메서드들
    # =============================================================================
    
    async def _analyze_pdf_layout(self, file_path: str, db: Session) -> Dict[str, Any]:
        """PDF 레이아웃 분석"""
        try:
            print(f"[레이아웃 분석] 시작: {file_path}")
            
            # 레이아웃 분석기 실행
            layout_result = self.layout_analyzer.analyze_pdf_layout(file_path)
            
            if layout_result.get("success"):
                print(f"[성공] 레이아웃 분석 - {layout_result.get('identified_questions', 0)}개 문제 구조 식별")
                return layout_result
            else:
                print(f"[실패] 레이아웃 분석 - {layout_result.get('error')}")
                return layout_result
                
        except Exception as e:
            logger.error(f"Layout analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _structured_ocr_processing(self, file_path: str, layout_analysis: Dict, page_classification: Dict, db: Session) -> Dict[str, Any]:
        """구조적 OCR 처리 - 레이아웃 분석 결과를 활용 (Fallback 강화)"""
        try:
            print(f"[구조적 OCR] 시작 - 레이아웃 분석 결과 활용")
            
            # 레이아웃 분석 결과에서 구조화된 문제 추출
            structured_questions = self.layout_analyzer.extract_structured_questions(file_path)
            
            # 결과 품질 검증
            quality_check_passed = (
                structured_questions and 
                len(structured_questions) >= 5 and  # 최소 5개 이상
                self._check_question_quality(structured_questions)
            )
            
            if not quality_check_passed:
                print(f"[경고] 레이아웃 분석 품질 미달 ({len(structured_questions) if structured_questions else 0}개) - 기존 방식으로 fallback")
                return await self._fallback_to_ocr_processing(file_path, page_classification, db)
            
            # 구조화된 문제들을 정제 및 검증
            validated_questions = []
            for question_data in structured_questions:
                if self._validate_structured_question(question_data):
                    validated_questions.append(question_data)
            
            # 최종 품질 검증
            if len(validated_questions) < len(structured_questions) * 0.7:  # 70% 이하 통과율이면 fallback
                print(f"[경고] 검증 통과율 낮음 ({len(validated_questions)}/{len(structured_questions)}) - 기존 방식으로 fallback")
                return await self._fallback_to_ocr_processing(file_path, page_classification, db)
            
            result = {
                "success": True,
                "structured_questions": validated_questions,
                "layout_based": True,
                "total_extracted": len(validated_questions)
            }
            
            print(f"[성공] 구조적 OCR - {len(validated_questions)}개 검증된 문제")
            return result
            
        except Exception as e:
            logger.error(f"Structured OCR error: {e}")
            print(f"[경고] 구조적 OCR 오류 발생 - 기존 방식으로 fallback")
            return await self._fallback_to_ocr_processing(file_path, page_classification, db)
    
    def _check_question_quality(self, questions: List[Dict]) -> bool:
        """문제 품질 검증 (디버깅 포함)"""
        if not questions:
            print(f"[품질검증] 실패: 문제 없음")
            return False
            
        # 문제 텍스트가 너무 짧거나 이상한 경우 감지
        text_lengths = [len(q.get('question_text', '')) for q in questions]
        avg_length = sum(text_lengths) / len(questions) if text_lengths else 0
        print(f"[품질검증] 평균 문제 텍스트 길이: {avg_length:.1f}자")
        
        if avg_length < 10:  # 평균 10자 미만이면 문제
            print(f"[품질검증] 실패: 평균 텍스트 길이가 너무 짧음 ({avg_length:.1f}자)")
            return False
            
        # 선택지가 모두 비정상적으로 많거나 적은 경우
        option_counts = [len(q.get('options', [])) for q in questions if q.get('options')]
        if option_counts:
            avg_options = sum(option_counts) / len(option_counts)
            print(f"[품질검증] 평균 선택지 개수: {avg_options:.1f}개")
            
            if avg_options > 20:  # 평균 20개 초과
                print(f"[품질검증] 실패: 선택지가 너무 많음 (평균 {avg_options:.1f}개)")
                return False
            elif avg_options < 2:  # 평균 2개 미만
                print(f"[품질검증] 실패: 선택지가 너무 적음 (평균 {avg_options:.1f}개)")
                return False
        else:
            print(f"[품질검증] 경고: 선택지가 있는 문제가 없음")
            
        print(f"[품질검증] 성공: {len(questions)}개 문제, 평균 길이 {avg_length:.1f}자")
        return True
    
    def _validate_structured_question(self, question_data: Dict) -> bool:
        """구조화된 문제 데이터 검증"""
        try:
            # 필수 필드 확인
            if not question_data.get("question_number"):
                return False
            if not question_data.get("question_text"):
                return False
                
            # 문제 텍스트 길이 확인 (너무 짧거나 긴 경우 제외)
            question_text = question_data.get("question_text", "").strip()
            if len(question_text) < 10 or len(question_text) > 1000:
                return False
                
            # 선택지가 있는 경우 최소 2개 이상
            options = question_data.get("options", [])
            if options and len(options) < 2:
                return False
                
            return True
            
        except Exception:
            return False
    
    async def _process_structured_questions_standard(self, structured_questions: List[Dict], db: Session) -> Dict[str, Any]:
        """구조화된 문제 표준 처리"""
        try:
            processed_questions = []
            
            for question_data in structured_questions:
                # 기본 형식으로 변환
                processed_question = {
                    "question_number": question_data.get("question_number"),
                    "passage": question_data.get("passage"),
                    "question_text": question_data.get("question_text"),
                    "options": json.dumps(question_data.get("options", []), ensure_ascii=False) if question_data.get("options") else None,
                    "correct_answer": None,  # 정답은 AI가 분석해야 함
                    "explanation": None,
                    "difficulty": "medium",
                    "question_type": "multiple_choice" if question_data.get("options") else "essay",
                    "page_range": question_data.get("page_range")
                }
                processed_questions.append(processed_question)
            
            return {
                "success": True,
                "questions": processed_questions,
                "cost": 0.0  # 구조 분석에서는 AI 비용 없음
            }
            
        except Exception as e:
            logger.error(f"Structured questions processing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_structured_questions_parallel(self, structured_questions: List[Dict], upload_id: int, db: Session) -> Dict[str, Any]:
        """구조화된 문제 병렬 처리 - AI 분석으로 정답/해설 추가"""
        try:
            # 청크로 분할
            chunk_size = 5  # 한 번에 5개씩 처리
            chunks = []
            
            for i in range(0, len(structured_questions), chunk_size):
                chunk = structured_questions[i:i + chunk_size]
                chunks.append(chunk)
            
            print(f"[병렬 처리] {len(structured_questions)}개 문제를 {len(chunks)}개 청크로 분할")
            
            # 병렬로 AI 분석 수행
            tasks = []
            for chunk_idx, chunk in enumerate(chunks):
                task = self._analyze_structured_questions_chunk(chunk, chunk_idx, db)
                tasks.append(task)
            
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 통합
            all_questions = []
            total_cost = 0.0
            
            for chunk_result in chunk_results:
                if isinstance(chunk_result, Exception):
                    print(f"[오류] 청크 처리 중 예외 발생: {chunk_result}")
                    continue
                    
                if chunk_result.get("success"):
                    all_questions.extend(chunk_result.get("questions", []))
                    total_cost += chunk_result.get("cost", 0)
            
            return {
                "success": True,
                "questions": all_questions,
                "cost": total_cost
            }
            
        except Exception as e:
            logger.error(f"Parallel structured processing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_structured_questions_chunk(self, chunk: List[Dict], chunk_idx: int, db: Session) -> Dict[str, Any]:
        """구조화된 문제 청크 AI 분석"""
        try:
            print(f"[청크 {chunk_idx}] AI 분석 시작 - {len(chunk)}개 문제")
            
            # AI에게 정답과 해설 분석 요청
            prompt = """다음은 구조화된 문제 데이터입니다. 각 문제에 대해 정답과 해설을 분석하여 완전한 문제 형태로 만들어주세요.

응답 형식:
```json
[
  {
    "question_number": 문제번호,
    "passage": "지문 (있는 경우)",
    "question_text": "문제 텍스트",
    "options": ["선택지1", "선택지2", "선택지3", "선택지4"],
    "correct_answer": "정답",
    "explanation": "해설",
    "difficulty": "easy|medium|hard",
    "question_type": "multiple_choice|true_false|essay"
  }
]
```

분석할 문제들:
"""
            
            for question in chunk:
                prompt += f"\n문제 {question.get('question_number')}: {question.get('question_text')}\n"
                if question.get('passage'):
                    prompt += f"지문: {question.get('passage')}\n"
                if question.get('options'):
                    prompt += f"선택지: {question.get('options')}\n"
                prompt += "---\n"
            
            # AI 호출 (call_claude_api_direct 사용)
            agent = await self._get_agent("question_extraction", db)
            if not agent:
                return {"success": False, "error": "Agent not found"}
            
            response = await claude_service.call_claude_api_direct(prompt, agent, db, max_tokens=4000)
            
            if response.get("success"):
                # 응답에서 문제 추출
                questions = self._extract_questions_from_response(response.get("content", ""), chunk_idx)
                cost = self._calculate_cost(response.get("usage", {}))
                
                print(f"[청크 {chunk_idx}] 완료 - {len(questions)}개 문제 분석 (비용: ${cost:.4f})")
                
                return {
                    "success": True,
                    "questions": questions,
                    "cost": cost
                }
            else:
                return {"success": False, "error": response.get("error")}
                
        except Exception as e:
            logger.error(f"Structured chunk analysis error: {e}")
            return {"success": False, "error": str(e)}

# 전역 인스턴스
enhanced_pdf_processor = EnhancedPDFProcessor()