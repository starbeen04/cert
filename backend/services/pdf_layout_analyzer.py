"""
PDF 레이아웃 분석기 - 문제와 선택지 구조적 분리
"""

import re
import PyPDF2
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TextElement:
    """텍스트 요소 구조"""
    content: str
    type: str  # question, option, passage, theory
    page_num: int
    position: Dict[str, float]  # x, y, width, height
    confidence: float

@dataclass
class QuestionStructure:
    """문제 구조"""
    question_number: int
    passage: Optional[str] = None
    question_text: str = ""
    options: List[str] = None
    page_range: Tuple[int, int] = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = []

class PDFLayoutAnalyzer:
    """PDF 레이아웃 분석 및 구조 인식"""
    
    def __init__(self):
        # 문제 패턴들 (1-60번 문제 완전 인식)
        self.question_patterns = [
            r'^\s*(\d{1,2})\.\s+',  # "1. ", "10. " 등
            r'^\s*(\d{1,2})\)\s+',  # "1) ", "10) " 등  
            r'^\s*문제\s*(\d{1,2})\s*[:\.]',  # "문제 1:", "문제 10." 등
            r'(?:^|\n)\s*(\d{1,2})\s*[\.\)]\s*[^0-9]',  # 줄 시작의 숫자 패턴
        ]
        
        # 선택지 패턴들 (더 다양한 형태 지원)
        self.option_patterns = [
            r'^\s*[①②③④⑤]\s+([^\n①②③④⑤]+)',
            r'^\s*[ABCDE]\s*[\.\)]\s+([^\nABCDE]+)',
            r'^\s*\(\s*(\d+)\s*\)\s+([^\n\(\)]+)',
            r'^\s*(\d+)\s*[\.\)]\s+([^\n\d]+)',  # 숫자 선택지
        ]
        
        # 지문 패턴들 (확장된 패턴)
        self.passage_patterns = [
            r'다음\s*(글|문|지문|자료|표|그림|코드).*?[을를]\s*(읽고|보고|참고하여)',
            r'아래\s*(글|문|지문|자료|표|그림|코드).*?[을를]\s*(읽고|보고|참고하여)', 
            r'다음.*?[은는이가]\s*주어졌을\s*때',
            r'<그림\s*\d+>',
            r'<표\s*\d+>',
            r'다음\s*프로그램',
            r'다음\s*코드',
            r'주어진\s*(프로그램|코드|함수)',
            r'다음\s*(그림|표|도표).*?보고',
            # 코드/프로그램 블록 패턴
            r'(class\s+\w+|def\s+\w+|import\s+\w+|#include|int\s+main)',
        ]
        
    def analyze_pdf_layout(self, file_path: str) -> Dict[str, Any]:
        """PDF 레이아웃 분석 수행"""
        try:
            print(f"[레이아웃 분석] PDF 파일 분석 시작: {file_path}")
            
            # 1. PDF 텍스트 추출
            raw_pages = self._extract_pdf_text(file_path)
            if not raw_pages:
                return {"success": False, "error": "PDF 텍스트 추출 실패"}
            
            # 2. 페이지별 레이아웃 분석
            layout_analysis = self._analyze_page_layouts(raw_pages)
            
            # 3. 문제 구조 인식 및 분리
            question_structures = self._identify_question_structures(layout_analysis)
            
            # 4. 연속성 분석 (페이지 경계 처리)
            merged_structures = self._handle_cross_page_continuity(question_structures)
            
            result = {
                "success": True,
                "total_pages": len(raw_pages),
                "identified_questions": len(merged_structures),
                "question_structures": merged_structures,
                "layout_analysis": layout_analysis
            }
            
            print(f"[성공] 레이아웃 분석 완료 - {len(merged_structures)}개 문제 구조 식별")
            return result
            
        except Exception as e:
            logger.error(f"PDF 레이아웃 분석 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_pdf_text(self, file_path: str) -> List[Dict[str, Any]]:
        """PDF에서 텍스트 추출"""
        pages = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text.strip():
                        pages.append({
                            "page_num": page_num + 1,
                            "raw_text": text,
                            "text_length": len(text)
                        })
                        
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 오류: {e}")
            
        return pages
    
    def _analyze_page_layouts(self, raw_pages: List[Dict]) -> List[Dict[str, Any]]:
        """페이지별 레이아웃 분석"""
        layout_analysis = []
        
        for page_data in raw_pages:
            page_num = page_data["page_num"]
            text = page_data["raw_text"]
            
            # 텍스트 요소 식별
            elements = self._identify_text_elements(text, page_num)
            
            # 페이지 타입 결정
            page_type = self._determine_page_type(elements)
            
            layout_analysis.append({
                "page_num": page_num,
                "page_type": page_type,
                "elements": elements,
                "raw_text": text
            })
            
            print(f"[페이지 {page_num}] 타입: {page_type}, 요소: {len(elements)}개")
            
        return layout_analysis
    
    def _identify_text_elements(self, text: str, page_num: int) -> List[TextElement]:
        """텍스트에서 구조적 요소 식별 (개선됨)"""
        elements = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 3:  # 너무 짧은 라인 제외
                continue
            
            element_type = "text"
            confidence = 0.5
            
            # 문제 패턴 매칭 (더 엄격하게)
            for pattern in self.question_patterns:
                if re.search(pattern, line):
                    # 문제로 인식하되, 최소 길이 조건 추가
                    if len(line) > 10:  # 최소 10자 이상
                        element_type = "question"
                        confidence = 0.9
                        break
            
            if element_type == "text":
                # 선택지 패턴 매칭 (더 엄격하게)  
                for pattern in self.option_patterns:
                    match = re.search(pattern, line)
                    if match and len(line) > 5:  # 최소 5자 이상
                        element_type = "option"
                        confidence = 0.8
                        break
            
            if element_type == "text":
                # 지문 패턴 매칭
                for pattern in self.passage_patterns:
                    if re.search(pattern, line) and len(line) > 10:  # 최소 10자 이상
                        element_type = "passage"
                        confidence = 0.7
                        break
            
            # 유효한 요소만 추가 (한 글자나 기호만 있는 것 제외)
            if len(line) >= 3 and not re.match(r'^[.。,，\s]+$', line):
                elements.append(TextElement(
                    content=line,
                    type=element_type,
                    page_num=page_num,
                    position={"line": i},
                    confidence=confidence
                ))
        
        return elements
    
    def _determine_page_type(self, elements: List[TextElement]) -> str:
        """페이지 타입 결정"""
        question_count = sum(1 for e in elements if e.type == "question")
        option_count = sum(1 for e in elements if e.type == "option")
        passage_count = sum(1 for e in elements if e.type == "passage")
        
        if question_count > 0 and option_count > 0:
            return "question_page"
        elif question_count > 0:
            return "question_incomplete"
        elif option_count > 0:
            return "option_only"
        elif passage_count > 0:
            return "passage_page"
        else:
            return "theory_page"
    
    def _identify_question_structures(self, layout_analysis: List[Dict]) -> List[QuestionStructure]:
        """문제 구조 식별 및 구성 (개선됨)"""
        question_structures = []
        current_question = None
        pending_passages = []  # 문제 전에 나타난 지문들
        
        for page_data in layout_analysis:
            elements = page_data["elements"]
            
            for element in elements:
                if element.type == "question":
                    # 새 문제 시작
                    if current_question:
                        # 이전 문제에 누락된 선택지 검증 및 보완
                        if not current_question.options:
                            self._find_missing_options_for_question(current_question, layout_analysis)
                        question_structures.append(current_question)
                    
                    # 문제 번호 추출
                    question_num = self._extract_question_number(element.content)
                    question_text = self._clean_question_text(element.content)
                    
                    current_question = QuestionStructure(
                        question_number=question_num,
                        question_text=question_text,
                        page_range=(element.page_num, element.page_num)
                    )
                    
                    # 이전에 수집된 지문들을 이 문제에 연결
                    if pending_passages:
                        current_question.passage = "\n".join(pending_passages)
                        pending_passages = []
                    
                elif element.type == "passage":
                    if current_question:
                        # 현재 문제에 지문 추가
                        if not current_question.passage:
                            current_question.passage = element.content
                        else:
                            current_question.passage += "\n" + element.content
                    else:
                        # 문제가 아직 없으면 임시 저장
                        pending_passages.append(element.content)
                        
                elif element.type == "option" and current_question:
                    # 선택지 추가
                    option_text = self._clean_option_text(element.content)
                    if option_text:  # 빈 선택지 제외
                        current_question.options.append(option_text)
                        current_question.page_range = (
                            current_question.page_range[0], 
                            element.page_num
                        )
        
        # 마지막 문제 추가 및 검증
        if current_question:
            if not current_question.options:
                self._find_missing_options_for_question(current_question, layout_analysis)
            question_structures.append(current_question)
        
        # 최종 검증 및 정리
        validated_structures = self._validate_and_clean_structures(question_structures)
            
        return validated_structures
    
    def _clean_question_text(self, text: str) -> str:
        """문제 텍스트 정리"""
        # 문제 번호 제거
        text = re.sub(r'^\s*\d+\s*[\.\)]\s*', '', text)
        text = re.sub(r'^\s*문제\s*\d+\s*[:\.]\s*', '', text)
        return text.strip()
    
    def _clean_option_text(self, text: str) -> str:
        """선택지 텍스트 정리"""
        # 선택지 기호 제거
        text = re.sub(r'^\s*[①②③④⑤ABCDE]\s*[\.\)]\s*', '', text)
        text = re.sub(r'^\s*\(\s*\d+\s*\)\s*', '', text)
        text = re.sub(r'^\s*\d+\s*[\.\)]\s*', '', text)
        return text.strip()
    
    def _find_missing_options_for_question(self, question: QuestionStructure, layout_analysis: List[Dict]):
        """문제에 누락된 선택지 찾기 (개선됨)"""
        question_num = question.question_number
        
        for page_data in layout_analysis:
            page_text = page_data["raw_text"]
            
            # 해당 문제 번호 위치부터 다음 문제까지의 텍스트 추출
            # 더 포괄적인 패턴으로 문제 블록 찾기
            patterns_to_try = [
                rf'{question_num}\.\s*(.+?)(?=^\s*{question_num+1}\.|\Z)',  # 다음 문제까지
                rf'{question_num}\.\s*(.+?)(?=\n\s*\d+\.|\Z)',              # 다음 번호까지
                rf'{question_num}\.\s*(.+?)(?=\n\n|\Z)',                    # 빈 줄까지
            ]
            
            question_block = None
            for pattern in patterns_to_try:
                match = re.search(pattern, page_text, re.MULTILINE | re.DOTALL)
                if match:
                    question_block = match.group(1)
                    break
            
            if question_block:
                
                # 다양한 선택지 패턴으로 검색
                all_option_patterns = [
                    r'[①②③④⑤]\s*([^\n①②③④⑤]+)',        # ①만 있는 형태
                    r'[①②③④⑤]\s+([^\n①②③④⑤]+)',        # ① 텍스트 형태
                    r'[ABCDE]\s*[\.\)]\s*([^\nABCDE]+)',  # A. 형태
                    r'\(\s*(\d+)\s*\)\s*([^\n\(\)]+)',    # (1) 형태
                    r'(\d+)\s*[\.\)]\s*([^\n\d]+)',       # 1. 형태
                ]
                
                found_options = []
                for pattern in all_option_patterns:
                    matches = re.findall(pattern, question_block, re.MULTILINE)
                    for match in matches:
                        if isinstance(match, tuple):
                            option_text = match[-1]  # 마지막 그룹이 텍스트
                        else:
                            option_text = match
                        
                        option_text = option_text.strip()
                        if option_text and len(option_text) > 1:  # 너무 짧은 텍스트 제외
                            found_options.append(option_text)
                
                # 중복 제거 및 추가
                actually_added = 0
                for option_text in found_options:
                    existing_options = [opt for opt in question.options]
                    
                    if option_text not in existing_options and len(option_text) >= 1:
                        question.options.append(option_text)
                        actually_added += 1
                
                if found_options:
                    print(f"[성공] 문제 {question_num}에서 {actually_added}개 선택지 추가됨")
                else:
                    print(f"[경고] 문제 {question_num} 선택지를 찾을 수 없음")
    
    def _validate_and_clean_structures(self, structures: List[QuestionStructure]) -> List[QuestionStructure]:
        """문제 구조 검증 및 정리"""
        validated = []
        
        for structure in structures:
            # 기본 검증
            if not structure.question_number or not structure.question_text:
                continue
                
            # 문제 텍스트가 너무 짧은 경우 제외
            if len(structure.question_text.strip()) < 5:
                continue
                
            # 선택지가 있는데 너무 적은 경우
            if structure.options and len(structure.options) < 2:
                # 선택지 다시 찾기 시도
                structure.options = []  # 리셋하고 다시 찾기
                
            validated.append(structure)
        
        return validated
    
    def _extract_question_number(self, question_text: str) -> int:
        """문제 번호 추출 (개선됨)"""
        patterns = [
            r'^\s*(\d{1,2})\.',  # "1.", "10." 등
            r'^\s*(\d{1,2})\)',  # "1)", "10)" 등
            r'^\s*문제\s*(\d{1,2})',  # "문제 1", "문제 10" 등
            r'(?:^|\s)(\d{1,2})\s*[\.\)]\s*[가-힣]',  # 숫자 뒤에 한글이 오는 패턴
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question_text)
            if match:
                num = int(match.group(1))
                if 1 <= num <= 60:  # 1-60번 범위 내만 허용
                    return num
                
        return 0
    
    def _handle_cross_page_continuity(self, structures: List[QuestionStructure]) -> List[QuestionStructure]:
        """페이지 경계 연속성 처리"""
        merged_structures = []
        
        for structure in structures:
            # 선택지가 없는 문제 - 다음 구조와 병합 검토
            if not structure.options and merged_structures:
                # 이전 문제의 선택지가 될 수 있는지 확인
                prev_structure = merged_structures[-1]
                if not prev_structure.options:
                    # 이전 문제도 선택지가 없으면 현재 문제의 선택지일 가능성
                    continue
            
            merged_structures.append(structure)
            
        return merged_structures
    
    def extract_structured_questions(self, file_path: str) -> List[Dict[str, Any]]:
        """구조화된 문제 추출"""
        layout_result = self.analyze_pdf_layout(file_path)
        
        if not layout_result.get("success"):
            return []
        
        structured_questions = []
        question_structures = layout_result.get("question_structures", [])
        
        for structure in question_structures:
            if structure.question_number > 0:  # 유효한 문제만
                question_dict = {
                    "question_number": structure.question_number,
                    "passage": structure.passage,
                    "question_text": structure.question_text,
                    "options": structure.options,
                    "page_range": f"{structure.page_range[0]}-{structure.page_range[1]}" if structure.page_range else None
                }
                structured_questions.append(question_dict)
        
        print(f"[최종] 구조화된 문제 {len(structured_questions)}개 추출 완료")
        return structured_questions