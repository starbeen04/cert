# OCR 처리 서비스
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import pytesseract
    from PIL import Image
    import pdf2image
    import PyPDF2
except ImportError as e:
    print(f"OCR dependencies not installed: {e}")

class OCRService:
    def __init__(self):
        # Tesseract 경로 설정 (Windows의 경우)
        if os.name == 'nt':  # Windows
            tesseract_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', ''))
            ]
            
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """PDF에서 텍스트 추출 (텍스트 레이어가 있는 경우)"""
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
    
    def convert_pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """PDF를 이미지로 변환"""
        try:
            images = pdf2image.convert_from_path(pdf_path, dpi=300)
            return images
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            return []
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """이미지에서 OCR로 텍스트 추출"""
        try:
            # 한국어 + 영어 인식
            text = pytesseract.image_to_string(image, lang='kor+eng')
            return text
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return ""
    
    def process_pdf(self, pdf_path: str, file_type: str = "questions") -> Dict[str, Any]:
        """PDF 전체 처리 - 텍스트 추출 및 구조화"""
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
            # 1단계: 텍스트 레이어에서 텍스트 추출 시도
            text_layers = self.extract_text_from_pdf(pdf_path)
            
            # 2단계: 이미지로 변환하여 OCR 처리
            images = self.convert_pdf_to_images(pdf_path)
            result["total_pages"] = len(images)
            
            # 각 페이지 처리
            for page_num, image in enumerate(images, 1):
                page_data = {
                    "page_number": page_num,
                    "text_from_layer": text_layers[page_num-1] if page_num-1 < len(text_layers) else "",
                    "text_from_ocr": "",
                    "combined_text": "",
                    "has_images": True,  # OCR이 필요하다는 것은 이미지가 있다는 의미
                }
                
                # OCR 처리
                ocr_text = self.extract_text_from_image(image)
                page_data["text_from_ocr"] = ocr_text
                
                # 텍스트 결합 (텍스트 레이어 우선, OCR로 보완)
                combined_text = page_data["text_from_layer"]
                if not combined_text.strip() or len(combined_text) < 100:
                    combined_text = ocr_text
                elif ocr_text and len(ocr_text) > len(combined_text):
                    combined_text = ocr_text
                
                page_data["combined_text"] = combined_text
                result["pages"].append(page_data)
            
            # 3단계: 파일 유형에 따른 구조화 처리
            if file_type in ["questions", "both"]:
                result["extracted_questions"] = self.extract_questions(result["pages"])
            
            if file_type in ["study_material", "both"]:
                result["study_materials"] = self.extract_study_materials(result["pages"])
            
            result["success"] = True
            
        except Exception as e:
            result["processing_errors"].append(f"전체 처리 오류: {str(e)}")
            print(f"Error processing PDF: {e}")
        
        return result
    
    def extract_questions(self, pages: List[Dict]) -> List[Dict]:
        """페이지에서 문제 추출"""
        questions = []
        question_patterns = [
            r'(\d+)\.\s*(.+?)(?=\d+\.\s|$)',  # 1. 문제내용
            r'문제\s*(\d+)[\.:\s]*(.+?)(?=문제\s*\d+|$)',  # 문제 1. 내용
            r'(\d+)\)\s*(.+?)(?=\d+\)\s|$)',  # 1) 문제내용
        ]
        
        for page in pages:
            text = page["combined_text"]
            if not text:
                continue
                
            # 문제 번호 패턴으로 문제 추출
            for pattern in question_patterns:
                matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
                
                for match in matches:
                    if len(match) >= 2:
                        question_num = match[0]
                        question_text = match[1].strip()
                        
                        if len(question_text) > 10:  # 너무 짧은 것 제외
                            question_data = {
                                "question_number": int(question_num) if question_num.isdigit() else 0,
                                "page_number": page["page_number"],
                                "question_text": question_text,
                                "options": self.extract_options(question_text),
                                "has_image": page["has_images"],
                                "difficulty_level": self.estimate_difficulty(question_text),
                                "topic_category": self.extract_topic(question_text)
                            }
                            questions.append(question_data)
        
        return questions
    
    def extract_options(self, question_text: str) -> List[str]:
        """문제에서 선택지 추출"""
        option_patterns = [
            r'[①②③④⑤]\s*([^\n①②③④⑤]+)',
            r'[1-5][\.)\s]\s*([^\n1-5\.]+)',
            r'[가나다라마]\.\s*([^\n가나다라마]+)',
        ]
        
        options = []
        for pattern in option_patterns:
            matches = re.findall(pattern, question_text)
            if matches and len(matches) >= 3:  # 최소 3개 이상의 선택지
                options = [opt.strip() for opt in matches]
                break
        
        return options
    
    def estimate_difficulty(self, question_text: str) -> int:
        """문제 난이도 추정 (1-5)"""
        # 간단한 휴리스틱으로 난이도 추정
        if len(question_text) > 500:
            return 4  # 긴 문제는 어려움
        elif any(word in question_text for word in ['분석', '설계', '구현', '평가']):
            return 3  # 고차원적 사고 필요
        elif any(word in question_text for word in ['정의', '개념', '특징']):
            return 2  # 기본 개념
        else:
            return 2  # 기본값
    
    def extract_topic(self, question_text: str) -> str:
        """문제에서 토픽 카테고리 추출"""
        topic_keywords = {
            "데이터베이스": ["데이터베이스", "DB", "SQL", "테이블", "관계", "정규화"],
            "네트워크": ["네트워크", "TCP", "IP", "HTTP", "프로토콜", "라우터"],
            "프로그래밍": ["프로그래밍", "알고리즘", "자료구조", "함수", "변수"],
            "보안": ["보안", "암호화", "해킹", "방화벽", "인증"],
            "시스템": ["운영체제", "시스템", "프로세스", "메모리", "CPU"],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in question_text for keyword in keywords):
                return topic
        
        return "기타"
    
    def extract_study_materials(self, pages: List[Dict]) -> List[Dict]:
        """페이지에서 학습 자료 추출"""
        materials = []
        
        for page in pages:
            text = page["combined_text"]
            if not text or len(text.strip()) < 50:
                continue
            
            # 제목 추출 (큰 글씨, 볼드체 등의 패턴)
            title_patterns = [
                r'^(.+?)(?:\n|$)',  # 첫 줄을 제목으로
                r'제\s*(\d+)\s*장\s*(.+?)(?:\n|$)',  # 제 1장 형태
                r'(\d+)\.\s*([^\n]+)',  # 1. 제목 형태
            ]
            
            title = f"페이지 {page['page_number']} 학습자료"
            for pattern in title_patterns:
                match = re.search(pattern, text)
                if match:
                    title = match.group(1) if len(match.groups()) == 1 else match.group(2)
                    title = title.strip()
                    break
            
            material_data = {
                "page_number": page["page_number"],
                "title": title,
                "content": text,
                "content_type": "theory",
                "chapter_number": self.extract_chapter_number(text),
                "section_number": page["page_number"]
            }
            
            materials.append(material_data)
        
        return materials
    
    def extract_chapter_number(self, text: str) -> Optional[int]:
        """텍스트에서 장 번호 추출"""
        pattern = r'제\s*(\d+)\s*장'
        match = re.search(pattern, text)
        return int(match.group(1)) if match else None

# 글로벌 OCR 서비스 인스턴스
ocr_service = OCRService()