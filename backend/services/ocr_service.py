# OCR 처리 서비스 (간단한 버전)
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import PyPDF2
except ImportError as e:
    print(f"OCR dependencies not installed: {e}")

class OCRService:
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """PDF에서 텍스트 추출"""
        try:
            texts = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text.strip():
                        texts.append(text)
            return texts
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return []
    
    def process_pdf(self, pdf_path: str, file_type: str = "questions") -> Dict[str, Any]:
        """PDF 전체 처리"""
        result = {
            "success": False,
            "pages": [],
            "extracted_questions": [],
            "study_materials": [],
            "processing_errors": [],
            "total_pages": 0,
            "processed_at": datetime.now().isoformat()
        }
        
        try:
            # 텍스트 추출
            text_layers = self.extract_text_from_pdf(pdf_path)
            result["total_pages"] = len(text_layers)
            
            print(f"Processing {len(text_layers)} pages using text extraction")
            
            # 페이지 처리
            for page_num, text in enumerate(text_layers, 1):
                page_data = {
                    "page_number": page_num,
                    "text_from_layer": text,
                    "text_from_ocr": "",
                    "combined_text": text,
                    "has_images": False,
                }
                result["pages"].append(page_data)
            
            # 전체 텍스트 결합
            all_text = []
            for page in result["pages"]:
                if page["combined_text"]:
                    all_text.append(page["combined_text"])
            
            result["extracted_text"] = "\n\n".join(all_text)
            
            # 파일 유형에 따른 구조화 처리
            if file_type in ["questions", "both"]:
                result["extracted_questions"] = self.extract_questions(result["pages"])
                result["questions"] = result["extracted_questions"]  # AI 프로세서와 호환성
            
            if file_type in ["study_material", "both"]:
                result["study_materials"] = self.extract_study_materials(result["pages"])
            
            result["success"] = True
            
        except Exception as e:
            result["processing_errors"].append(f"처리 오류: {str(e)}")
            print(f"Error processing PDF: {e}")
        
        return result
    
    def extract_questions(self, pages: List[Dict]) -> List[Dict]:
        """페이지에서 문제 추출"""
        questions = []
        question_patterns = [
            r'(\d+)\.\s*(.+?)(?=\d+\.\s|Answer|정답|$)',
            r'(\d+)\)\s*(.+?)(?=\d+\)\s|Answer|정답|$)',
        ]
        
        option_patterns = [
            r'[①②③④⑤]\s*(.+?)(?=[①②③④⑤]|Answer|정답|$)',
            r'[1-5]\)\s*(.+?)(?=[1-5]\)|Answer|정답|$)',
        ]
        
        answer_patterns = [
            r'Answer:\s*(\d+)',
            r'정답:\s*(\d+)',
        ]
        
        for page in pages:
            text = page["combined_text"]
            if not text:
                continue
                
            print(f"Processing page {page['page_number']} with text length: {len(text)}")
            
            for pattern in question_patterns:
                matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
                
                for match in matches:
                    if len(match) >= 2:
                        question_num = match[0]
                        question_text = match[1].strip()
                        
                        if len(question_text) > 10:
                            # 선택지 추출
                            options = []
                            for opt_pattern in option_patterns:
                                opts = re.findall(opt_pattern, question_text)
                                if opts:
                                    options.extend([opt.strip() for opt in opts])
                            
                            # 정답 추출
                            correct_answer = None
                            for ans_pattern in answer_patterns:
                                ans_match = re.search(ans_pattern, text)
                                if ans_match:
                                    correct_answer = ans_match.group(1)
                                    break
                            
                            question_data = {
                                "question_number": int(question_num) if question_num.isdigit() else 0,
                                "question_text": question_text,
                                "options": options,
                                "correct_answer": correct_answer,
                                "page_number": page["page_number"],
                                "difficulty": 3,
                                "topic": "general"
                            }
                            
                            questions.append(question_data)
                            print(f"Extracted question {question_num}: {question_text[:50]}...")
        
        return questions
    
    def extract_study_materials(self, pages: List[Dict]) -> List[Dict]:
        """페이지에서 학습자료 추출"""
        materials = []
        
        for page in pages:
            text = page["combined_text"]
            if not text:
                continue
            
            if len(text.strip()) > 100:
                material_data = {
                    "title": f"Page {page['page_number']} Content",
                    "content": text,
                    "chapter": "",
                    "section": "",
                    "material_type": "theory",
                    "page_number": page["page_number"]
                }
                materials.append(material_data)
        
        return materials

# 전역 인스턴스 생성
ocr_service = OCRService()
