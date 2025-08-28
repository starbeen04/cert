"""
초정밀 PDF 구조 분석기 - 실제 PDF에 맞춘 상세 분석
사용자 요구사항: 훨씬 더 구체적이고 자세한 구조 파악
"""

import asyncio
import json
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import fitz  # PyMuPDF
import openai
from PIL import Image
import io
import base64

class UltraPrecisePDFAnalyzer:
    """초정밀 PDF 구조 분석기 - 실제 PDF 맞춤 상세 분석"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
    
    async def analyze_pdf_structure_ultra_detailed(self, pdf_path: str, upload_id: int, 
                                                  progress_callback=None) -> Dict[str, Any]:
        """향상된 2단계 초정밀 PDF 구조 분석 - 전체 개괄 후 상세 분석"""
        
        def update_progress(percentage, step, description=""):
            if progress_callback:
                progress_callback(percentage, step, description)
            print(f"📊 진행률: [{'█' * (percentage // 10)}{'░' * (10 - percentage // 10)}] {percentage}% - {step}")
            if description:
                print(f"   {description}")
        
        print(f"🚀 향상된 2단계 초정밀 PDF 구조 분석 시작 - Upload {upload_id}")
        print("=" * 70)
        update_progress(0, "분석 준비 중...", "새로운 2단계 전체-상세 분석 방식")
        
        try:
            # === STAGE 1: 전체 PDF 개괄 분석 (0-50%) ===
            update_progress(5, "PDF 기본 정보 추출 중...", "메타데이터, 페이지 수, 텍스트 패턴 분석")
            basic_info = await self._extract_basic_pdf_info(pdf_path)
            
            update_progress(10, "텍스트 기반 사전 분석 중...", "전체 PDF 텍스트에서 문제 패턴 추출")
            cross_page_analysis = await self._analyze_cross_page_issues_from_text(pdf_path)
            basic_info['cross_page_issues'] = cross_page_analysis
            
            # 🆕 1단계: 전체 PDF 한 눈에 보기 (저해상도 전체 개괄)
            update_progress(20, "전체 PDF 개괄 분석 중...", "모든 페이지 저해상도로 전체 구조 파악")
            overview_result = await self._perform_full_pdf_overview(pdf_path, basic_info, upload_id)
            
            if not overview_result.get("success"):
                print("⚠️ 전체 개괄 분석 실패, 기존 방식으로 진행")
                overview_result = {"global_overview": {}, "success": True}
            
            # 🆕 개괄 분석 기반으로 기본 정보 보정
            update_progress(30, "개괄 분석 결과 적용 중...", "전체 파악 결과로 문제 수 및 구조 보정")
            enhanced_basic_info = await self._enhance_basic_info_with_overview(
                basic_info, overview_result, pdf_path
            )
            
            # === STAGE 2: 상세 정밀 분석 (50-100%) ===
            update_progress(50, "초고해상도 이미지 생성 중...", f"12배 확대 이미지 생성 ({enhanced_basic_info['total_pages']}페이지)")
            ultra_high_res_images = await self._create_ultra_high_res_images(pdf_path, upload_id, scale=12.0)
            
            update_progress(65, "개괄 기반 정밀 구조 분석 중...", "전체 파악 결과를 바탕으로 세부 분석")
            detailed_structure = await self._perform_overview_guided_analysis(
                ultra_high_res_images, enhanced_basic_info, overview_result, upload_id
            )
            
            if not detailed_structure.get("success"):
                return detailed_structure
            
            update_progress(80, "특수 요소 정밀 분석 중...", "개괄에서 식별된 특수 요소 집중 분석")
            special_analysis_result = await self._perform_special_elements_analysis(
                pdf_path, detailed_structure, upload_id
            )
            
            update_progress(92, "2단계 분석 결과 통합 중...", "개괄 + 상세 + 특수 요소 분석 종합")
            integrated_structure = await self._integrate_all_analysis_results(
                overview_result, detailed_structure, special_analysis_result, upload_id
            )
            
            update_progress(97, "최종 검증 및 보완 중...", "2단계 분석 결과 교차 검증")
            validated_structure = await self._validate_and_enhance_structure(
                integrated_structure, pdf_path, upload_id
            )
            
            update_progress(100, "2단계 구조 분석 완료!", "전체 개괄 + 상세 정밀 분석 성공 완료")
            print("✅ 향상된 2단계 초정밀 PDF 구조 분석 완료:")
            self._print_detailed_analysis_result(validated_structure)
            
            return validated_structure
            
        except Exception as e:
            print(f"❌ 향상된 2단계 구조 분석 실패: {e}")
            return {"success": False, "error": str(e), "upload_id": upload_id}
    
    def _detect_question_count_from_text(self, pages_text: List[Dict]) -> int:
        """텍스트에서 실제 문제 개수 동적 감지"""
        
        print("🔍 실제 문제 개수 감지 중...")
        
        # 전체 텍스트 합치기
        full_text = ""
        for page_info in pages_text:
            full_text += page_info.get('text', '') + "\n"
        
        # 다양한 문제 번호 패턴 찾기
        question_numbers = set()
        
        # 패턴 1: "문제 1번", "문제 2번" 등
        pattern1 = re.findall(r'문제\s*(\d+)\s*번', full_text)
        for num in pattern1:
            question_numbers.add(int(num))
        
        # 패턴 2: "1.", "2.", "3." 등 (더 유연하게)
        pattern2 = re.findall(r'(?:^|\s)(\d+)\.(?:\s|$)', full_text, re.MULTILINE)
        for num in pattern2:
            if 1 <= int(num) <= 100:  # 1-100 범위만
                question_numbers.add(int(num))
        
        # 패턴 3: "Q1", "Q2", "문1", "문2" 등
        pattern3 = re.findall(r'[QQ문](\d+)', full_text)
        for num in pattern3:
            if 1 <= int(num) <= 100:
                question_numbers.add(int(num))
        
        # 패턴 4: "1)", "2)", "3)" 등 (선택지가 아닌 문제 번호)
        pattern4 = re.findall(r'(?:^|\n)\s*(\d+)\)', full_text, re.MULTILINE)
        for num in pattern4:
            if 1 <= int(num) <= 100:
                question_numbers.add(int(num))
        
        # 패턴 5: "[1]", "[2]", "[3]" 등 
        pattern5 = re.findall(r'\[(\d+)\]', full_text)
        for num in pattern5:
            if 1 <= int(num) <= 100:
                question_numbers.add(int(num))
        
        # 패턴 6: 한자 문제 번호 "一", "二", "三" 등을 숫자로 변환
        chinese_numbers = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
        for chinese, number in chinese_numbers.items():
            if chinese in full_text:
                question_numbers.add(number)
        
        # 연속적인 문제 번호 범위 찾기
        if question_numbers:
            sorted_numbers = sorted(question_numbers)
            max_continuous = self._find_max_continuous_sequence(sorted_numbers)
            max_number = max(sorted_numbers)
            
            # 더 나은 추정치 선택
            final_count = max(max_continuous, max_number)
            
            print(f"   📊 감지된 문제 번호들: {sorted(list(question_numbers))}")
            print(f"   📈 연속적인 문제 수: {max_continuous}")
            print(f"   🔢 최대 문제 번호: {max_number}")
            print(f"   🎯 최종 추정: {final_count}개")
            
            return final_count
        
        # 패턴을 찾지 못한 경우, 선택지 패턴으로 추정
        choice_patterns = len(re.findall(r'[①②③④⑤]', full_text))
        estimated_from_choices = choice_patterns // 4  # 평균 4개 선택지 가정
        
        print(f"   🔍 선택지 패턴으로 추정: {estimated_from_choices}개 문제")
        return max(estimated_from_choices, 20)  # 최소 20개는 보장
    
    def _find_max_continuous_sequence(self, numbers: List[int]) -> int:
        """연속적인 숫자 시퀀스 중 최대 길이 찾기"""
        
        if not numbers:
            return 0
            
        # 1부터 시작하는 연속 시퀀스 찾기
        max_continuous = 0
        current_continuous = 0
        
        for i in range(1, max(numbers) + 1):
            if i in numbers:
                current_continuous += 1
                max_continuous = max(max_continuous, current_continuous)
            else:
                current_continuous = 0
        
        # 연속성이 없으면 최대 번호를 반환
        if max_continuous == 0:
            return max(numbers)
            
        return max_continuous

    async def _extract_basic_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """PDF 기본 정보 추출"""
        
        try:
            doc = fitz.open(pdf_path)
            
            # 메타데이터 추출
            metadata = doc.metadata
            
            # 페이지별 기본 텍스트 추출 (구조 힌트용)
            pages_text = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                pages_text.append({
                    'page_number': page_num + 1,
                    'text_length': len(text),
                    'line_count': len(text.split('\n')),
                    'has_korean': bool(re.search(r'[가-힣]', text)),
                    'has_numbers': bool(re.search(r'\d+', text)),
                    'has_choices': bool(re.search(r'[①②③④⑤]', text)),
                    'sample_text': text[:200].replace('\n', ' ').strip()
                })
            
            doc.close()
            
            # 실제 문제 개수 동적 감지
            detected_question_count = self._detect_question_count_from_text(pages_text)
            
            return {
                'total_pages': len(pages_text),
                'detected_question_count': detected_question_count,  # 동적 감지된 문제 수
                'metadata': metadata,
                'pages_info': pages_text,
                'file_size_mb': Path(pdf_path).stat().st_size / (1024 * 1024)
            }
            
        except Exception as e:
            print(f"⚠️ PDF 기본 정보 추출 실패: {e}")
            return {'total_pages': 0, 'error': str(e)}
    
    async def _analyze_cross_page_issues_from_text(self, pdf_path: str) -> Dict[str, Any]:
        """향상된 텍스트 기반 페이지 경계 문제 사전 분석"""
        
        try:
            doc = fitz.open(pdf_path)
            cross_page_issues = {
                "split_questions": [],
                "incomplete_choices": [],
                "continuation_markers": [],
                "text_code_elements": [],  # 새로운: 텍스트/코드 요소 감지
                "cross_page_tables": [],   # 새로운: 페이지 간 표 분할 
                "text_analysis": [],
                "detailed_issues": []      # 새로운: 상세 이슈 분석
            }
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                lines = text.split('\n')
                
                # 1. 기존 기능 강화 - 페이지 끝에서 끊어지는 문제 감지
                if len(lines) > 0:
                    last_lines = lines[-10:]  # 마지막 10줄로 확장
                    first_lines_next_page = []
                    
                    # 다음 페이지 첫 10줄 가져오기
                    if page_num + 1 < len(doc):
                        next_page = doc.load_page(page_num + 1)
                        next_text = next_page.get_text()
                        first_lines_next_page = next_text.split('\n')[:10]
                    
                    for i, line in enumerate(last_lines):
                        # 문제가 끊어진 경우 더 정밀하게 감지
                        if re.search(r'문제\s*\d+번', line) and i >= len(last_lines) - 3:
                            # 해당 문제의 완성도 체크
                            question_text = line
                            choice_count = len(re.findall(r'[①②③④⑤]', '\n'.join(last_lines[i:])))
                            
                            if choice_count < 2:  # 선택지가 충분하지 않으면 분할 의심
                                cross_page_issues["split_questions"].append({
                                    "page": page_num + 1,
                                    "issue": f"문제가 페이지 {page_num + 1}에서 다음 페이지로 연결",
                                    "question_number": re.search(r'(\d+)', line).group(1) if re.search(r'\d+', line) else "?",
                                    "partial_text": line.strip(),
                                    "choice_count_current": choice_count,
                                    "likely_continues": True
                                })
                        
                        # 선택지 분할 더 정밀하게 감지
                        current_choices = re.findall(r'[①②③④⑤]', line)
                        if current_choices:
                            # 현재 페이지에서 마지막으로 나타난 선택지 번호
                            last_choice_num = max([ord(c) - ord('①') + 1 for c in current_choices])
                            
                            # 다음 페이지에서 연속되는 선택지 확인
                            if first_lines_next_page:
                                next_page_choices = []
                                for next_line in first_lines_next_page:
                                    choices_in_line = re.findall(r'[①②③④⑤]', next_line)
                                    next_page_choices.extend(choices_in_line)
                                
                                if next_page_choices:
                                    next_choice_nums = [ord(c) - ord('①') + 1 for c in next_page_choices]
                                    # 연속성 확인 (현재 페이지 마지막 + 1 = 다음 페이지 첫번째)
                                    if min(next_choice_nums) == last_choice_num + 1:
                                        cross_page_issues["incomplete_choices"].append({
                                            "page": page_num + 1,
                                            "issue": f"선택지가 페이지 {page_num + 1}-{page_num + 2}에 분할",
                                            "current_choices": current_choices,
                                            "current_max": last_choice_num,
                                            "next_page_choices": next_page_choices,
                                            "next_min": min(next_choice_nums),
                                            "is_sequential": True
                                        })
                
                # 2. 새로운 기능: 텍스트/코드 요소 감지 (선택지 내)
                self._detect_text_code_in_choices(text, page_num + 1, cross_page_issues)
                
                # 3. 새로운 기능: 페이지 간 표 분할 감지
                self._detect_cross_page_tables(text, first_lines_next_page, page_num + 1, cross_page_issues)
                
                # 4. 기존 연속 표시 감지 강화
                continuation_patterns = [
                    r'(계속|다음\s*페이지|continued|→|\.{3,}|…)',
                    r'(다음\s*문제\s*계속|이어서|계속해서)',
                    r'(\*\s*계속|\[계속\]|\(계속\))'
                ]
                
                for pattern in continuation_patterns:
                    markers = re.findall(pattern, text, re.IGNORECASE)
                    if markers:
                        cross_page_issues["continuation_markers"].append({
                            "page": page_num + 1,
                            "markers": markers,
                            "pattern_type": pattern
                        })
                
                # 5. 강화된 텍스트 분석
                cross_page_issues["text_analysis"].append({
                    "page": page_num + 1,
                    "has_incomplete_questions": bool(re.search(r'문제\s*\d+번[^①②③④⑤]*$', text)),
                    "has_incomplete_choices": len(re.findall(r'[①②③④⑤]', text)) % 4 != 0 and bool(re.search(r'[①②③④⑤]', text)),
                    "ends_abruptly": bool(re.search(r'[①②③④⑤][^①②③④⑤\n]*$', text)),
                    "has_code_blocks": bool(re.search(r'(class|def|function|public|private|int|string|return)', text)),
                    "has_mathematical_formulas": bool(re.search(r'[∑∏∫√±∞≠≤≥∈∉∪∩]|x\^|[a-z]\s*=\s*[0-9]', text)),
                    "has_english_text": bool(re.search(r'[a-zA-Z]{4,}', text)),
                    "has_tables": bool(re.search(r'\|\s*[가-힣a-zA-Z0-9\s]+\s*\|', text))
                })
            
            doc.close()
            
            # 6. 종합적인 이슈 분석
            self._analyze_comprehensive_issues(cross_page_issues)
            
            return cross_page_issues
            
        except Exception as e:
            print(f"⚠️ 향상된 페이지 경계 분석 실패: {e}")
            return {"error": str(e)}
    
    def _detect_text_code_in_choices(self, text: str, page_num: int, issues: Dict):
        """선택지 내 텍스트/코드 요소 감지"""
        
        lines = text.split('\n')
        for line_idx, line in enumerate(lines):
            # 선택지가 있는 줄 찾기
            if re.search(r'[①②③④⑤]', line):
                # 각 선택지별로 분석
                choices = re.findall(r'[①②③④⑤][^①②③④⑤]*', line)
                
                for choice in choices:
                    choice_num = choice[0]
                    choice_content = choice[1:].strip()
                    
                    detected_elements = []
                    
                    # 코드 요소 감지 (향상됨)
                    if re.search(r'(class|def|function|public|private|int|string|return|printf|cout|System\.out|SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|JOIN)', choice_content):
                        detected_elements.append("프로그래밍/SQL 코드")
                    
                    # 수학 공식 감지
                    if re.search(r'[∑∏∫√±∞≠≤≥∈∉∪∩]|x\^|[a-z]\s*=\s*[0-9]|log|sin|cos|tan', choice_content):
                        detected_elements.append("수학 공식")
                    
                    # 영어 기술 용어 감지
                    if re.search(r'[A-Z]{2,}|[a-z]+[A-Z][a-z]*|algorithm|database|network|server', choice_content):
                        detected_elements.append("영어 기술 용어")
                    
                    # 숫자와 연산 기호 감지 (향상됨)
                    if re.search(r'\d+\s*[+\-*/=<>!]\s*\d+|[0-9]+\.[0-9]+|%|[><]=?|\d+\s*(MB|KB|GB|Hz|GHz|ms|ns)|0x[0-9A-Fa-f]+|\d+bit|\d+byte', choice_content):
                        detected_elements.append("숫자/연산/단위")
                    
                    # 특수 기호 감지
                    if re.search(r'[→←↑↓⟵⟶⟷]|[◆◇■□●○▲△▼▽]', choice_content):
                        detected_elements.append("특수 기호/도형")
                    
                    if detected_elements:
                        issues["text_code_elements"].append({
                            "page": page_num,
                            "line": line_idx + 1,
                            "choice": choice_num,
                            "elements": detected_elements,
                            "content_preview": choice_content[:50] + ("..." if len(choice_content) > 50 else "")
                        })
    
    def _detect_cross_page_tables(self, current_text: str, next_page_lines: List[str], 
                                  page_num: int, issues: Dict):
        """페이지 간 표 분할 감지"""
        
        # 현재 페이지에서 표의 시작/중간/끝 감지
        table_patterns = [
            r'\|[^|]*\|[^|]*\|',  # 기본 표 패턴
            r'┌[─┬]*┐|├[─┼]*┤|└[─┴]*┘',  # 박스 표 패턴
            r'─{3,}|═{3,}',  # 구분선
        ]
        
        current_has_table = False
        table_incomplete = False
        
        for pattern in table_patterns:
            if re.search(pattern, current_text):
                current_has_table = True
                
                # 표가 완전하지 않은지 확인 (헤더만 있고 데이터가 없는 경우)
                lines = current_text.split('\n')
                table_lines = [line for line in lines if re.search(pattern, line)]
                
                if len(table_lines) <= 2:  # 헤더와 구분선만 있는 경우
                    table_incomplete = True
                    break
        
        if current_has_table and table_incomplete and next_page_lines:
            # 다음 페이지에서 표의 연속 확인
            next_page_text = '\n'.join(next_page_lines)
            next_has_table_continuation = False
            
            for pattern in table_patterns:
                if re.search(pattern, next_page_text):
                    next_has_table_continuation = True
                    break
            
            if next_has_table_continuation:
                issues["cross_page_tables"].append({
                    "page": page_num,
                    "issue": f"표가 페이지 {page_num}에서 {page_num + 1}로 분할",
                    "table_type": "데이터 테이블",
                    "current_page_has_header": True,
                    "next_page_has_data": True
                })
    
    def _analyze_comprehensive_issues(self, issues: Dict):
        """종합적인 이슈 분석 및 우선순위 설정"""
        
        total_issues = len(issues["split_questions"]) + len(issues["incomplete_choices"]) + \
                      len(issues["cross_page_tables"]) + len(issues["text_code_elements"])
        
        severity_level = "low"
        if total_issues >= 10:
            severity_level = "high"
        elif total_issues >= 5:
            severity_level = "medium"
        
        issues["detailed_issues"] = {
            "total_cross_page_problems": total_issues,
            "severity_level": severity_level,
            "requires_special_processing": severity_level != "low",
            "processing_recommendations": [
                "페이지 경계를 고려한 문제 재구성" if issues["split_questions"] else None,
                "선택지 완전성 검증 필요" if issues["incomplete_choices"] else None,
                "표 데이터 통합 처리 필요" if issues["cross_page_tables"] else None,
                "선택지 내 코드/수식 특별 처리" if issues["text_code_elements"] else None
            ]
        }
        
        # None 값 제거
        issues["detailed_issues"]["processing_recommendations"] = [
            rec for rec in issues["detailed_issues"]["processing_recommendations"] if rec
        ]
    
    def _format_cross_page_analysis_for_prompt(self, cross_page_issues: Dict) -> str:
        """향상된 페이지 경계 분석 결과를 프롬프트용으로 포맷"""
        
        if not cross_page_issues or "error" in cross_page_issues:
            return "- 페이지 경계 사전 분석 결과 없음"
        
        formatted = []
        
        # 분할된 문제들
        if cross_page_issues.get("split_questions"):
            formatted.append("⚠️ 페이지 간 분할 문제 감지:")
            for issue in cross_page_issues["split_questions"]:
                formatted.append(f"  - 문제 {issue['question_number']}번: {issue['issue']}")
                formatted.append(f"    현재 페이지 선택지 수: {issue['choice_count_current']}개")
        
        # 불완전한 선택지들  
        if cross_page_issues.get("incomplete_choices"):
            formatted.append("⚠️ 선택지 페이지 분할 감지:")
            for issue in cross_page_issues["incomplete_choices"]:
                formatted.append(f"  - {issue['issue']}")
                if issue.get("is_sequential"):
                    formatted.append(f"    연속성 확인됨: {issue['current_max']} → {issue['next_min']}")
        
        # 새로운: 텍스트/코드 요소들
        if cross_page_issues.get("text_code_elements"):
            formatted.append("🔍 선택지 내 특수 요소 감지:")
            choice_elements = {}
            for element in cross_page_issues["text_code_elements"]:
                page = element["page"]
                if page not in choice_elements:
                    choice_elements[page] = []
                choice_elements[page].append(f"선택지 {element['choice']}: {', '.join(element['elements'])}")
            
            for page, elements in choice_elements.items():
                formatted.append(f"  - 페이지 {page}:")
                for elem in elements:
                    formatted.append(f"    • {elem}")
        
        # 새로운: 페이지 간 표 분할
        if cross_page_issues.get("cross_page_tables"):
            formatted.append("📊 페이지 간 표 분할 감지:")
            for table in cross_page_issues["cross_page_tables"]:
                formatted.append(f"  - {table['issue']}")
                formatted.append(f"    표 유형: {table['table_type']}")
        
        # 연속 표시자들
        if cross_page_issues.get("continuation_markers"):
            formatted.append("📍 연속 표시자 감지:")
            for marker_info in cross_page_issues["continuation_markers"]:
                formatted.append(f"  - 페이지 {marker_info['page']}: {marker_info['markers']}")
        
        # 종합 이슈 분석
        if cross_page_issues.get("detailed_issues"):
            details = cross_page_issues["detailed_issues"]
            formatted.append(f"📊 종합 분석: 총 {details['total_cross_page_problems']}개 이슈 ({details['severity_level']} 심각도)")
            if details.get("processing_recommendations"):
                formatted.append("   권장 처리 방식:")
                for rec in details["processing_recommendations"]:
                    formatted.append(f"    • {rec}")
        
        if not formatted:
            formatted.append("✅ 페이지 경계 문제 없음 - 각 페이지가 독립적으로 완성됨")
        
        return "\n".join(formatted)
    
    async def _create_ultra_high_res_images(self, pdf_path: str, upload_id: int, scale: float = 8.0) -> List[Dict]:
        """구조 분석용 페이지 이미지 생성 (가변 해상도)"""
        
        try:
            doc = fitz.open(pdf_path)
            ultra_high_res_images = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # 가변 해상도로 렌더링
                mat = fitz.Matrix(scale, scale)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Base64 인코딩
                img_data = self._optimize_image_size(pix)
                base64_img = base64.b64encode(img_data).decode('utf-8')
                
                ultra_high_res_images.append({
                    'page_number': page_num + 1,
                    'width': pix.width,
                    'height': pix.height,
                    'image_data': base64_img,
                    'format': 'png'
                })
                
                print(f"   📄 {scale}배 해상도 페이지 {page_num + 1} 생성: {pix.width}x{pix.height}")
            
            doc.close()
            return ultra_high_res_images
            
        except Exception as e:
            print(f"❌ 구조 분석용 이미지 생성 실패: {e}")
            return []
    
    async def _perform_full_pdf_overview(self, pdf_path: str, basic_info: Dict, upload_id: int) -> Dict[str, Any]:
        """1단계: 전체 PDF 개괄 분석 - 저해상도로 모든 페이지 한눈에 파악"""
        
        print(f"🌍 전체 PDF 개괄 분석 시작 - Upload {upload_id}")
        
        try:
            # 저해상도 이미지 생성 (빠른 전체 파악용)
            overview_images = await self._create_ultra_high_res_images(pdf_path, upload_id, scale=2.0)
            
            # 전체 개괄 분석 프롬프트
            overview_prompt = self._create_full_overview_prompt(basic_info)
            
            messages = [
                {
                    "role": "system",
                    "content": """당신은 PDF 전체 구조 파악 전문가입니다.

🎯 **핵심 임무**: 전체 PDF를 한눈에 보고 정확한 문제 개수와 구조를 파악하세요.

⚡ **중요 지침**:
- 모든 페이지를 종합적으로 보고 실제 문제 개수를 정확히 세어주세요
- "문제 1번"부터 "문제 N번"까지 연속적으로 찾으세요
- 각 페이지가 어떤 역할인지 정확히 구분하세요 (문제/정답/해설)
- 중복 계산하지 마세요 - 실제 문제 번호만 세어주세요

🚨 **매우 중요 - 선택지 구분**:
- ①②③④⑤ 같은 동그라미 숫자는 선택지입니다! 문제가 아닙니다!
- 1)2)3)4)5) 같은 괄호 숫자도 선택지입니다! 문제가 아닙니다!
- A)B)C)D)E) 같은 알파벳도 선택지입니다! 문제가 아닙니다!
- 선택지를 절대 별개 문제로 카운트하지 마세요!

🔍 **특별 주의사항**:
- 정답만 나열된 페이지는 문제 개수에 포함하지 마세요
- 해설 페이지도 문제 개수에 포함하지 마세요  
- 실제 문제 번호가 적힌 문제만 카운트하세요
- 계층 구조를 정확히 인식하세요: 문제 → 지문 → 선택지들"""
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": overview_prompt}]
                }
            ]
            
            # 모든 페이지 이미지 추가
            for img_data in overview_images:
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_data['image_data']}",
                        "detail": "low"  # 전체 개괄은 저해상도로 빠르게
                    }
                })
            
            # GPT Vision 호출
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=3000,
                temperature=0.1  # 정확성을 위한 낮은 온도
            )
            
            response_text = response.choices[0].message.content
            print(f"🌍 전체 개괄 분석 응답 길이: {len(response_text)}자")
            
            # 결과 파싱
            overview_result = self._parse_overview_response(response_text)
            
            print("✅ 전체 PDF 개괄 분석 완료")
            return {"global_overview": overview_result, "success": True}
            
        except Exception as e:
            print(f"❌ 전체 PDF 개괄 분석 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_full_overview_prompt(self, basic_info: Dict) -> str:
        """전체 PDF 개괄 분석 프롬프트"""
        
        detected_count = basic_info.get('detected_question_count', 0)
        total_pages = basic_info.get('total_pages', 0)
        
        return f"""🌍 전체 PDF 구조 개괄 분석

📋 **기본 정보**:
- 총 페이지: {total_pages}페이지
- 텍스트 기반 예상 문제 수: {detected_count}개

🎯 **분석 목표 (매우 상세히)**:
1. **정확한 총 문제 개수 파악**: "문제 1번"부터 "문제 N번"까지 정확히 몇 개인지
2. **페이지별 문제 범위**: 각 페이지에 몇 번부터 몇 번까지 있는지
3. **페이지 역할 분류**: 문제/정답/해설/표지/기타 정확히 구분
4. **선택지 개수 파악**: 각 문제의 선택지가 몇 개인지 (2개/4개/5개 등)
5. **특수 요소 위치**: 표/이미지/코드/다이어그램이 정확히 몇 번 문제에 있는지
6. **페이지 경계 문제**: 문제나 선택지가 페이지를 넘나드는지 확인

🔍 **정확한 분석 방법**:

**1. 문제 번호 식별 (이것만 진짜 문제):**
- "문제 1번", "문제 2번", "1.", "2.", "Q1", "Q2" 등의 패턴
- 마지막 문제 번호가 실제 총 문제 개수입니다

**2. 선택지 식별 (문제가 아님!):**
- ①, ②, ③, ④, ⑤ (동그라미 숫자)
- 1), 2), 3), 4), 5) (괄호 숫자)
- A), B), C), D), E) (알파벳)
- 이런 것들은 문제가 아니라 선택지입니다!

**3. 계층 구조 인식:**
- 문제 번호 → 문제 지문 → 선택지들
- 선택지는 해당 문제의 하위 항목입니다
- 선택지를 별도 문제로 절대 카운트하지 마세요

**4. 페이지 역할 구분:**
- 정답만 있는 페이지나 해설만 있는 페이지는 구분해주세요

📊 **JSON 출력 형식** (매우 정확하게):
```json
{{
  "actual_total_questions": 실제_문제_개수,
  "last_question_number": 마지막_문제_번호,
  "first_question_number": 첫_문제_번호,
  "page_roles": [
    {{
      "page_number": 1,
      "role": "questions|answers|explanations|cover|other",
      "question_range": "1-12번" (정확한_범위),
      "question_count": 실제_이_페이지_문제_개수,
      "choice_counts": {{"2선택지": 0, "4선택지": 10, "5선택지": 2}},
      "special_elements": {{"tables": [문제번호들], "images": [문제번호들], "codes": [문제번호들], "diagrams": [문제번호들]}},
      "cross_page_issues": ["문제가_넘어가는_경우"],
      "content_summary": "이_페이지의_구체적_내용"
    }}
  ],
  "detailed_question_info": {{
    "questions_with_images": [문제번호들],
    "questions_with_tables": [문제번호들], 
    "questions_with_codes": [문제번호들],
    "questions_with_diagrams": [문제번호들],
    "choice_distribution": {{"2선택지": 개수, "4선택지": 개수, "5선택지": 개수}}
  }},
  "document_structure": {{
    "question_pages": [페이지_번호들],
    "answer_pages": [페이지_번호들],
    "explanation_pages": [페이지_번호들]
  }},
  "verification": {{
    "total_questions_verified": true/false,
    "page_continuity_checked": true/false,
    "special_elements_located": true/false
  }},
  "confidence": 0.0-1.0,
  "notes": "상세한_구조_설명"
}}
```

⚠️ **매우 중요 - 정확한 분석**:
- 추정하지 마세요! 실제로 보이는 문제 번호만 세어주세요
- 정답 페이지의 "1번: ②" 같은 건 문제가 아닙니다
- 해설 페이지의 "문제 1번 해설" 같은 것도 실제 문제가 아닙니다
- 오직 실제 문제 텍스트와 선택지가 있는 것만 문제로 카운트하세요

🚨 **선택지 오인식 방지 - 절대 준수**:
- ①, ②, ③, ④, ⑤ 는 선택지입니다! 문제 번호가 아닙니다!
- 1), 2), 3), 4), 5) 는 선택지입니다! 문제 번호가 아닙니다!
- A), B), C), D), E) 는 선택지입니다! 문제 번호가 아닙니다!
- 이런 것들을 별개 문제로 절대 카운트하지 마세요!

📋 **체계적 분석 방법**:
1. 각 페이지를 차례대로 스캔하면서 "문제 N번" 패턴 찾기
2. 각 문제의 선택지 개수 정확히 세기 (①②③④ 또는 1)2)3)4) 등)
3. 표, 이미지, 코드, 다이어그램이 있는 문제 번호 기록
4. 페이지 끝에서 문제가 중간에 끊어지는지 확인
5. 다음 페이지 시작이 이전 페이지와 연결되는지 확인

🔍 **검증 필수사항**:
- 첫 문제부터 마지막 문제까지 연속성 확인
- 누락된 문제 번호가 있는지 확인
- 각 페이지의 문제 개수 합이 전체와 일치하는지 확인"""
    
    def _parse_overview_response(self, response_text: str) -> Dict:
        """전체 개괄 분석 결과 파싱"""
        
        try:
            # JSON 블록 찾기
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # 첫 번째 { 부터 마지막 } 까지 추출
                start = response_text.find('{')
                end = response_text.rfind('}')
                if start != -1 and end != -1:
                    json_text = response_text[start:end+1]
                else:
                    return self._create_fallback_overview()
            
            # JSON 파싱
            overview_data = json.loads(json_text)
            
            # 결과 요약 출력
            actual_questions = overview_data.get('actual_total_questions', 0)
            confidence = overview_data.get('confidence', 0.0)
            
            print(f"🌍 전체 개괄 분석 결과:")
            print(f"   📊 실제 총 문제 수: {actual_questions}개")
            print(f"   🎯 마지막 문제 번호: {overview_data.get('last_question_number', '?')}번")
            print(f"   🔍 첫 문제 번호: {overview_data.get('first_question_number', '?')}번")
            print(f"   🔍 분석 신뢰도: {confidence*100:.1f}%")
            
            # 상세 정보 출력
            detailed_info = overview_data.get('detailed_question_info', {})
            if detailed_info:
                print(f"   📊 특수 요소:")
                if detailed_info.get('questions_with_tables'):
                    print(f"      📋 표 포함 문제: {detailed_info['questions_with_tables']}")
                if detailed_info.get('questions_with_images'): 
                    print(f"      🖼️ 이미지 포함 문제: {detailed_info['questions_with_images']}")
                if detailed_info.get('questions_with_codes'):
                    print(f"      💻 코드 포함 문제: {detailed_info['questions_with_codes']}")
                if detailed_info.get('questions_with_diagrams'):
                    print(f"      📈 다이어그램 포함 문제: {detailed_info['questions_with_diagrams']}")
                
                choice_dist = detailed_info.get('choice_distribution', {})
                if choice_dist:
                    print(f"   📊 선택지 분포: {choice_dist}")
            
            # 페이지 역할 요약
            page_roles = overview_data.get('page_roles', [])
            question_pages = len([p for p in page_roles if p.get('role') == 'questions'])
            answer_pages = len([p for p in page_roles if p.get('role') == 'answers'])
            explanation_pages = len([p for p in page_roles if p.get('role') == 'explanations'])
            
            print(f"   📄 페이지 구성: 문제 {question_pages}페이지, 정답 {answer_pages}페이지, 해설 {explanation_pages}페이지")
            
            return overview_data
            
        except Exception as e:
            print(f"⚠️ 전체 개괄 분석 파싱 실패: {e}")
            return self._create_fallback_overview()
    
    def _create_fallback_overview(self) -> Dict:
        """개괄 분석 실패시 기본값"""
        return {
            "actual_total_questions": 60,  # 기본값 (일반적인 기출문제 수)
            "last_question_number": 60,
            "first_question_number": 1,
            "page_roles": [
                {"page_number": 1, "role": "questions", "question_count": 12},
                {"page_number": 2, "role": "questions", "question_count": 12},
                {"page_number": 3, "role": "questions", "question_count": 12},
                {"page_number": 4, "role": "questions", "question_count": 12},
                {"page_number": 5, "role": "questions", "question_count": 12}
            ],
            "document_structure": {
                "question_pages": [1, 2, 3, 4, 5],
                "answer_pages": [6],
                "explanation_pages": [7, 8]
            },
            "detailed_question_info": {
                "questions_with_tables": [],
                "questions_with_images": [],
                "questions_with_codes": [],
                "questions_with_diagrams": [],
                "choice_distribution": {"4선택지": 60}
            },
            "confidence": 0.3,
            "notes": "개괄 분석 실패로 표준 구조 기본값 사용"
        }
    
    async def _enhance_basic_info_with_overview(self, basic_info: Dict, overview_result: Dict, pdf_path: str) -> Dict:
        """개괄 분석 결과로 기본 정보 보정"""
        
        enhanced_info = basic_info.copy()
        
        if overview_result.get("success"):
            global_overview = overview_result.get("global_overview", {})
            
            # 실제 문제 개수로 업데이트
            actual_questions = global_overview.get("actual_total_questions", 0)
            if actual_questions > 0:
                enhanced_info['detected_question_count'] = actual_questions
                enhanced_info['overview_corrected_count'] = actual_questions
                print(f"🔧 개괄 분석으로 문제 수 보정: {basic_info.get('detected_question_count', 0)} → {actual_questions}")
            
            # 페이지 역할 정보 추가
            enhanced_info['page_roles'] = global_overview.get("page_roles", [])
            enhanced_info['document_structure'] = global_overview.get("document_structure", {})
            enhanced_info['global_overview'] = global_overview
        
        return enhanced_info
    
    async def _perform_overview_guided_analysis(self, ultra_high_res_images: List[Dict], 
                                               enhanced_basic_info: Dict, overview_result: Dict, 
                                               upload_id: int) -> Dict[str, Any]:
        """개괄 분석 기반 정밀 구조 분석"""
        
        print(f"🔍 개괄 기반 정밀 구조 분석 시작 - Upload {upload_id}")
        
        try:
            # 개괄 분석 정보 활용한 정밀 프롬프트
            guided_prompt = self._create_overview_guided_prompt(enhanced_basic_info, overview_result)
            
            messages = [
                {
                    "role": "system",
                    "content": """당신은 전체 개괄을 바탕으로 정밀 분석하는 전문가입니다.

🎯 **핵심 임무**: 이미 파악된 전체 구조를 바탕으로 각 페이지를 정밀 분석하세요.

⚡ **중요 지침**:
- 전체 개괄에서 파악된 정확한 문제 개수를 기준으로 분석하세요
- 각 페이지의 역할(문제/정답/해설)이 이미 파악되었으므로 이를 확인하고 보완하세요
- 고해상도 이미지로 세부 내용을 정확히 분석하세요
- 특수 요소(표, 이미지, 코드)의 정확한 위치와 내용을 파악하세요"""
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": guided_prompt}]
                }
            ]
            
            # 초고해상도 이미지 추가
            for img_data in ultra_high_res_images:
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_data['image_data']}",
                        "detail": "high"  # 정밀 분석을 위한 고해상도
                    }
                })
            
            # GPT Vision 호출
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=6000,
                temperature=0.05
            )
            
            response_text = response.choices[0].message.content
            print(f"🔍 정밀 구조 분석 응답 길이: {len(response_text)}자")
            
            # 결과 파싱 및 개괄 정보 포함
            detailed_result = self._parse_ultra_detailed_response(response_text, upload_id)
            
            if detailed_result.get('success'):
                detailed_result['basic_info'] = enhanced_basic_info
                detailed_result['guided_by_overview'] = True
            
            print("✅ 개괄 기반 정밀 구조 분석 완료")
            return detailed_result
            
        except Exception as e:
            error_str = str(e)
            print(f"❌ 개괄 기반 정밀 구조 분석 실패: {e}")
            
            # 이미지 크기 관련 에러 처리
            if "400" in error_str or "invalid_request_error" in error_str or "something went wrong" in error_str:
                print("⚠️ 이미지 크기 초과로 인한 API 요청 실패로 추정됩니다.")
                print("🔧 해상도를 낮춰서 다시 시도하거나 이미지 압축을 강화해야 합니다.")
                return {"success": False, "error": "Image size too large for API", "error_type": "image_size_exceeded", "upload_id": upload_id}
            
            return {"success": False, "error": error_str, "upload_id": upload_id}
    
    def _create_overview_guided_prompt(self, enhanced_basic_info: Dict, overview_result: Dict) -> str:
        """개괄 분석 기반 정밀 분석 프롬프트"""
        
        global_overview = overview_result.get("global_overview", {})
        actual_questions = global_overview.get("actual_total_questions", 0)
        page_roles = global_overview.get("page_roles", [])
        
        # 페이지 역할 요약
        page_roles_summary = ""
        for page_role in page_roles[:5]:  # 처음 5페이지만 표시
            page_num = page_role.get("page_number", 0)
            role = page_role.get("role", "unknown")
            question_range = page_role.get("question_range", "없음")
            page_roles_summary += f"- 페이지 {page_num}: {role} ({question_range})\n"
        
        return f"""🔍 전체 개괄 기반 정밀 구조 분석

📋 **전체 개괄 분석 결과 (확정됨)**:
- 실제 총 문제 수: {actual_questions}개
- 마지막 문제 번호: {global_overview.get('last_question_number', '?')}번
- 분석 신뢰도: {global_overview.get('confidence', 0.0)*100:.1f}%

📄 **페이지 역할 (개괄에서 파악됨)**:
{page_roles_summary}

🎯 **정밀 분석 목표**:
1. **개괄 결과 검증**: 위에서 파악된 정보가 고해상도에서도 일치하는지 확인
2. **세부 내용 분석**: 각 문제의 정확한 내용, 선택지, 특수 요소 파악
3. **특수 요소 위치**: 표, 이미지, 코드 블록의 정확한 문제 번호 매칭
4. **품질 검증**: 각 문제의 완성도, 선택지 개수, 페이지 간 연결성 확인

🔍 **페이지 경계 문제 사전 분석 결과** (텍스트 기반):
{self._format_cross_page_analysis_for_prompt(enhanced_basic_info.get('cross_page_issues', {}))}

⚠️ **매우 중요**: 
- 총 문제 수 {actual_questions}개는 이미 확정된 값입니다
- 이 값과 다르게 분석될 경우 고해상도 분석에서 누락이나 오인식을 점검하세요
- 개괄에서 파악된 페이지 역할을 기준으로 정밀 검증하세요

{self._create_detailed_analysis_format_instructions(actual_questions)}"""
    
    def _create_detailed_analysis_format_instructions(self, expected_questions: int) -> str:
        """상세 분석을 위한 JSON 형식 지침"""
        
        return f"""🎯 **JSON 출력 형식** (반드시 이 구조로):
```json
{{
  "analysis_summary": {{
    "document_type": "practice_tests",
    "total_pages": 실제_페이지_수,
    "total_questions": {expected_questions},
    "confidence_score": 0.9-1.0
  }},
  "page_analysis": [
    {{
      "page_number": 1,
      "page_type": "pure_questions|answer_sheet|explanation_sheet",
      "questions_on_page": [실제_문제_번호들],
      "question_density": 실제_문제_개수,
      "special_elements": ["tables", "diagrams", "code_blocks", "images"] 중 해당사항,
      "layout_complexity": "simple|medium|complex",
      "processing_notes": "이 페이지 특이사항"
    }}
  ],
  "question_analysis": {{
    "total_questions": {expected_questions},
    "numbering_pattern": "문제 1번|1.|Q1" 등 실제 패턴,
    "choice_pattern": "①②③④⑤|1)2)3)4)5)" 등 실제 패턴,
    "average_choices_per_question": 평균_선택지_개수
  }},
  "processing_strategy": {{
    "recommended_approach": "페이지별|구조기반",
    "chunk_size_recommendation": "15-20문제씩",
    "special_handling": ["필요한_특수_처리들"]
  }}
}}
```

📊 **검증 체크리스트**:
- [ ] 총 문제 수가 {expected_questions}개인지 확인
- [ ] 모든 페이지의 역할이 개괄 분석과 일치하는지 확인
- [ ] 문제 번호가 1번부터 {expected_questions}번까지 순서대로 있는지 확인
- [ ] 특수 요소가 있는 페이지와 문제 번호가 정확한지 확인

🚨 **선택지 오인식 방지 체크리스트**:
- [ ] ①②③④⑤ 같은 동그라미 숫자가 별개 문제로 카운트되지 않았는지 확인
- [ ] 1)2)3)4)5) 같은 괄호 숫자가 별개 문제로 카운트되지 않았는지 확인
- [ ] 선택지 개수만큼 문제 수가 늘어나지 않았는지 확인
- [ ] 각 문제가 정확히 하나의 문제 번호만 가지는지 확인"""
    
    async def _integrate_all_analysis_results(self, overview_result: Dict, detailed_structure: Dict, 
                                            special_analysis: Dict, upload_id: int) -> Dict[str, Any]:
        """전체 개괄 + 정밀 분석 + 특수 요소 분석 결과 통합"""
        
        print(f"🔧 2단계 분석 결과 통합 중 - Upload {upload_id}")
        
        try:
            # 정밀 분석 결과를 베이스로 사용
            integrated = detailed_structure.copy()
            
            # 개괄 분석 정보 추가
            if overview_result.get("success"):
                global_overview = overview_result.get("global_overview", {})
                integrated['global_overview'] = global_overview
                integrated['two_stage_analysis'] = True
                
                # 개괄 분석의 실제 문제 수로 최종 확정
                actual_questions = global_overview.get("actual_total_questions", 0)
                if actual_questions > 0:
                    integrated['analysis_summary']['total_questions'] = actual_questions
                    print(f"🔧 개괄 분석 기준으로 최종 문제 수 확정: {actual_questions}개")
            
            # 기본 정보의 cross_page_issues를 최상위로 복사
            if detailed_structure.get('basic_info', {}).get('cross_page_issues'):
                integrated['cross_page_issues'] = detailed_structure['basic_info']['cross_page_issues']
            
            # 특수 요소 분석 결과 통합
            special_questions = special_analysis.get('special_analysis', {}).get('special_questions', [])
            if special_questions:
                # 기존 통합 로직 사용
                integrated = await self._integrate_structure_and_special_analysis(
                    integrated, special_analysis, upload_id
                )
            
            print("✅ 2단계 분석 결과 통합 완료")
            return integrated
            
        except Exception as e:
            print(f"❌ 2단계 분석 결과 통합 실패: {e}")
            return detailed_structure
    
    async def _perform_ultra_detailed_analysis(self, page_images: List[Dict], 
                                             basic_info: Dict, upload_id: int) -> Dict[str, Any]:
        """초정밀 구조 분석 실행"""
        
        # 초정밀 분석 프롬프트 생성
        ultra_detailed_prompt = self._create_ultra_detailed_analysis_prompt(basic_info)
        
        try:
            # 시스템 메시지 추가 - 이미지 감지 강화
            system_message = {
                "role": "system",
                "content": """당신은 PDF 내 시각적 요소 감지 전문가입니다.

🎯 **핵심 임무**: 모든 시각적 요소를 빠짐없이 감지하고 각 문제번호와 연결하세요.

⚡ **특별 지침 - 한국어 시험문제 전문 분석**:
- "문제 1번", "1.", "1)" 형식의 문제 번호를 찾으세요
- 각 문제번호 주변의 모든 시각적 요소를 정확히 기록하세요
- 선택지 ①②③④⑤ 내부나 옆에 있는 이미지를 반드시 찾으세요

📸 **이미지 감지 우선순위 (문제번호별)**:
1. **선택지 이미지**: ①, ②, ③, ④, ⑤ 내부 또는 바로 옆의 모든 그래픽 요소
   - 작은 아이콘, 도형, 그래프, 사진까지 모두 포함
   - 수식이 이미지로 처리된 것도 포함
2. **문제 본문 이미지**: 문제 설명에 포함된 다이어그램, 표, 그래프, 코드
3. **참고 자료**: 지문에 포함된 시각적 자료

🔍 **반드시 감지해야 할 요소들**:
- 네트워크 다이어그램 (서버, 클라이언트 연결도)
- 플로차트, 순서도
- 데이터베이스 ER 다이어그램
- 시스템 아키텍처 도표
- 표(테이블) - 특히 스케줄링, 프로세스 테이블
- 코드 블록 (Java, C++, Python 등)
- 수학 공식이나 수식
- 그래프, 차트 (막대, 원, 선 그래프)
- 회로도, 논리게이트
- 화면 캡처, UI 목업
- 기하학적 도형, 패턴

⚠️ **매우 중요**: 
- 작은 이미지라도 반드시 감지하세요
- 텍스트처럼 보여도 그래픽으로 렌더링된 것은 이미지입니다
- 각 문제번호와 해당 이미지의 정확한 매칭이 핵심입니다"""
            }
            
            messages = [
                system_message,
                {"role": "user", "content": [{"type": "text", "text": ultra_detailed_prompt}]}
            ]
            
            # 모든 페이지 이미지를 사용자 메시지에 추가
            for img_data in page_images:
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_data['image_data']}",
                        "detail": "high"  # 초정밀 분석을 위한 고해상도
                    }
                })
            
            # GPT Vision 호출 (더 큰 토큰 허용)
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=6000,  # 상세 분석을 위한 큰 토큰
                temperature=0.05  # 매우 일관된 분석을 위한 낮은 온도
            )
            
            response_text = response.choices[0].message.content
            
            # OpenAI 실제 응답 확인
            print(f"🤖 OpenAI 실제 응답 (첫 500자):\n{response_text[:500]}")
            print(f"📝 전체 응답 길이: {len(response_text)}자")
            print(f"🔍 JSON 블록 찾기: {bool(re.search(r'```json', response_text))}")
            
            # JSON 파싱 및 구조화
            parsed_result = self._parse_ultra_detailed_response(response_text, upload_id)
            
            # basic_info를 파싱 결과에 포함
            if parsed_result.get('success'):
                parsed_result['basic_info'] = basic_info
                
            return parsed_result
            
        except Exception as e:
            print(f"❌ 초정밀 구조 분석 실패: {e}")
            return {"success": False, "error": str(e), "upload_id": upload_id}
    
    def _create_ultra_detailed_analysis_prompt(self, basic_info: Dict) -> str:
        """초정밀 분석을 위한 매우 상세한 프롬프트"""
        
        # 동적으로 감지된 문제 수 사용
        detected_count = basic_info.get('detected_question_count', 0)
        
        pages_hint = ""
        if basic_info.get('pages_info'):
            pages_hint = f"\n📋 **PDF 기본 정보** (예상 문제 수: {detected_count}개):\n"
            for page_info in basic_info['pages_info'][:5]:  # 처음 5페이지만 힌트로 제공
                pages_hint += f"- 페이지 {page_info['page_number']}: {page_info['line_count']}줄, "
                pages_hint += f"한글: {'있음' if page_info['has_korean'] else '없음'}, "
                pages_hint += f"선택지: {'있음' if page_info['has_choices'] else '없음'}\n"
                pages_hint += f"  샘플: \"{page_info['sample_text']}\"\n"
        
        return f"""🔬 당신은 한국어 시험문제 PDF 분석 초전문가입니다.

🎯 **핵심 임무 - 문제별 상세 템플릿 생성**: 
1. 각 문제의 정확한 구조 패턴 분석
2. 문제 지문의 시작/끝 단어, 길이, 특수 요소 파악
3. 선택지의 형식, 개수, 내용 유형 분석
4. 추출 시 사용할 정확한 템플릿 제공

📋 **문제별 상세 분석 요구사항**:
- 문제 번호: "1.", "문제 1번", "1)" 등 정확한 형식
- 지문 시작: "다음 중", "아래의", "다음 설명" 등 시작 패턴  
- 지문 끝: "것은?", "는가?", "하시오." 등 종료 패턴
- 선택지 형식: "①②③④", "1)2)3)4)", "가)나)다)라)" 등
- 특수 요소: 표, 코드, 다이어그램의 정확한 위치와 내용

🔍 **문제 구조 템플릿 예시**:
```
문제 6번 템플릿:
- 번호 형식: "6."
- 지문 시작: "다음 표와 같이"
- 지문 끝: "얼마인가?"
- 지문 길이: 약 45자
- 표 위치: 지문 바로 아래
- 표 내용: | 프로세스 | 도착시간 | 실행시간 | (3열 5행)
- 선택지: ①②③④ (4개, 숫자 형태)
```

{pages_hint}

🔍 **페이지 경계 문제 사전 분석 결과** (텍스트 기반):
{self._format_cross_page_analysis_for_prompt(basic_info.get('cross_page_issues', {}))}

📸 **핵심 임무 - 시각적 요소 정밀 감지**:
- 모든 이미지, 다이어그램, 표, 코드를 문제번호와 정확히 매칭
- 선택지 내부의 작은 이미지도 빠뜨리지 말고 감지
- 특히 ①②③④⑤ 선택지 옆이나 안의 시각적 요소를 정밀 분석

🖼️ **시각적 요소 초정밀 감지 (글자가 아닌 모든 그래픽 요소)**:

**🎯 선택지 내 시각적 요소 감지**:
- ①②③④⑤ 각 선택지를 개별적으로 검사
- 도형으로 된 선택지: 원, 사각형, 삼각형, 다각형, 기하도형
- 그래프로 된 선택지: 막대그래프, 원그래프, 선그래프, 히스토그램
- 다이어그램으로 된 선택지: 네트워크도, 플로차트, 시스템구조도
- 예: "문제 15번의 선택지 ②③이 원과 사각형 도형"

**📊 문제 지문 내 시각적 요소 감지**:
- 표/테이블: 데이터표, 비교표, 스케줄링 테이블, 프로세스 테이블
- 코드 블록: Java, C++, Python, SQL 등 프로그래밍 코드
- 수학 공식: 수식, 계산식, 알고리즘 표현
- 다이어그램: ER다이어그램, 네트워크 구조도, 시스템 아키텍처
- 예: "문제 25번 지문에 데이터베이스 ER다이어그램 포함"

**🔍 긴 지문 및 특수 텍스트 감지**:
- 긴 지문: 5줄 이상의 설명문, 케이스 스터디, 시나리오
- 영어 텍스트: 영문 설명, 기술 용어, 코드 주석
- 수식 표현: 수학적 공식, 논리식, 알고리즘
- 예: "문제 30번에 네트워크 구성 시나리오 긴 지문 포함"

**📍 정확한 위치 및 맥락 정보**:
- 페이지 번호, 문제 번호, 구체적 위치 (상단/중간/하단)
- 선택지인 경우 어떤 번호 선택지인지 명시
- 후속 이미지 캡처를 위한 상세 좌표 정보

📊 **선택지 개수별 상세 분석**:
- 각 문제별로 정확히 몇 개의 선택지가 있는지 카운트
- 2개, 3개, 4개, 5개 선택지별로 문제 번호들을 분류
- 선택지가 이미지인 경우와 텍스트인 경우 구분

🔗 **페이지 경계 문제 면밀 분석**:
- 문제 내용이 두 페이지에 걸쳐 나뉜 경우 (지문이 긴 경우)
- 선택지 일부가 다음 페이지로 넘어간 경우 (몇 번 선택지부터인지)
- 문제와 선택지가 완전히 분리된 경우
- 지문과 문제가 다른 페이지에 있는 경우

⚠️ **매우 중요**: 예상 {detected_count}개는 참고일 뿐입니다. 
- 실제로 "문제 1번"부터 "문제 N번"까지 순서대로 모두 찾아주세요
- 빠진 문제 번호나 중복된 번호가 있는지 확인하세요
- 페이지를 넘나드는 문제는 특별히 표시하세요

📋 **1. 문서 타입 정밀 분석**:
- document_type: "questions_only" | "theory_only" | "mixed" | "answers_explanations" | "practice_tests" | "summary_notes"
- content_complexity: "simple" | "intermediate" | "complex" | "mixed_levels"
- language_type: "korean_only" | "mixed_korean_english" | "technical_terms_heavy"

📊 **2. 페이지별 상세 분석** (각 페이지마다):
**🔍 페이지 타입 정확히 구분하기 (매우 중요)**:
- page_type: 
  - "pure_questions": 문제 번호 + 선택지가 명확히 있는 페이지
  - "answer_sheet": 정답만 나열된 페이지 ("1번: ②", "2번: ④" 형식)
  - "explanation_sheet": 해설만 있는 페이지 ("정답 해설", "풀이 과정" 등)
  - "cover_page": 표지, 시험 안내문
  - "table_of_contents": 목차
  - "theory_explanation": 이론 설명
  - "mixed_content": 문제와 다른 내용이 혼재
  
**✅ 문제 페이지 식별 기준**:
- "문제 1번", "1.", "1)" 등의 문제 번호가 있음
- ①②③④⑤ 또는 1)2)3)4)5) 등의 선택지가 있음
- 문제 텍스트와 선택지가 완전한 세트로 구성됨

**❌ 비문제 페이지 식별 기준**:
- 정답만 나열: "1. ②", "2. ④", "3. ①" 형식으로만 구성
- 해설만 있음: "정답 해설", "풀이", "해답" 등의 제목만 있음
- 표지/안내: "시험 안내", "주의사항", "답안지 작성법" 등
- 빈 페이지: 의미있는 내용이 거의 없음

- question_density: 페이지당 실제 문제 개수 (정답만 있으면 0으로 표시)
- layout_type: "single_column" | "double_column" | "mixed_layout" | "table_heavy" | "image_heavy"
- special_elements: ["tables", "diagrams", "code_blocks", "mathematical_formulas", "images"] 중 해당 요소들

📝 **3. 문제 구조 초정밀 분석** (문제가 있는 경우):
- total_questions: 정확한 문제 개수 (추정이 아닌 실제 카운트)
- numbering_pattern: "1." | "문제 1번" | "Q1" | "1)" | 기타 실제 패턴
- choice_pattern: "①②③④⑤" | "1)2)3)4)5)" | "ABCDE" | "가나다라마" | 기타 실제 패턴
- average_choices_per_question: 실제 평균 선택지 개수
- choice_completeness: 각 문제별 선택지 완성도 분석

🎯 **4. 기본 문제 구조 분석**:
- total_questions: 정확한 문제 개수 (추정이 아닌 실제 카운트)
- numbering_pattern: "1." | "문제 1번" | "Q1" | "1)" | 기타 실제 패턴  
- choice_pattern: "①②③④⑤" | "1)2)3)4)5)" | "ABCDE" | "가나다라마" | 기타 실제 패턴
- average_choices_per_question: 실제 평균 선택지 개수

🔍 **5. 특수 요소가 있는 문제만 선별 분석** (최대 10개만):
특별한 요소(표, 코드, 다이어그램)가 있는 문제만 간단히 분석:
- question_number: 문제 번호
- special_element: "table" | "code" | "diagram" | "image" | "passage"
- page_location: 페이지 번호

📊 **5. 표/그래프/이미지 분석**:
- tables_detected: 발견된 표의 정확한 위치와 내용 (몇 페이지 몇 번 문제)
- images_detected: 이미지의 위치와 용도 (선택지용/설명용/장식용) - 텍스트가 아닌 모든 시각적 요소 포함
- diagrams_detected: 다이어그램의 위치와 유형
- code_blocks_detected: 코드 블록의 위치와 프로그래밍 언어

🔍 **6. 페이지 경계 문제 초정밀 분석** (매우 중요!):

**🚨 선택지 분할 검출**:
- 각 문제의 선택지를 ①②③④⑤ 순서로 확인
- 선택지 일부가 다음 페이지에 있는 경우 정확한 문제 번호와 어떤 선택지부터 넘어가는지 기록
- 예: "문제 17번의 선택지 ③④⑤가 다음 페이지에 있음"

**🔗 문제 내용 분할 검출**:
- 문제 텍스트나 지문이 두 페이지에 걸쳐 나뉜 경우
- 어느 부분에서 페이지가 나뉘는지 구체적으로 기록
- 예: "문제 25번의 지문이 페이지 3-4에 걸쳐 분할됨"

**📊 표/코드 분할 검출**:
- 표나 코드 블록이 페이지 경계에서 잘린 경우
- 테이블 헤더만 있고 데이터가 다음 페이지에 있는 경우
- 코드의 일부만 보이고 나머지가 다음 페이지에 있는 경우

**👁️ 시각적 단서 감지**:
- "계속", "다음 페이지 참조", 화살표 표시 등
- 문제나 선택지가 페이지 하단에서 갑자기 끊어지는 경우
- 페이지 상단에 선택지만 있거나 문제 번호 없이 내용만 있는 경우

**🔍 완성도 검증**:
- 각 문제가 문제번호 + 문제텍스트 + 모든 선택지를 갖추었는지 확인
- 불완전한 문제들을 구체적으로 나열
- 예: "문제 17번: 선택지 ③④ 누락", "문제 25번: 지문 후반부 누락"

⚙️ **7. 처리 전략 도출**:
- recommended_chunk_strategy: 이 PDF에 최적화된 청크 전략
- special_processing_needed: 특별히 주의해야 할 처리 요소들
- extraction_order: 권장 추출 순서
- potential_challenges: 예상되는 처리 어려움과 해결책

🎯 **JSON 출력 형식** (반드시 이 구조로):
```json
{{
  "analysis_summary": {{
    "document_type": "실제_분석_결과",
    "total_pages": 실제_페이지_수,
    "total_questions": 정확한_문제_개수,
    "confidence_score": 0.0-1.0
  }},
  "page_analysis": [
    {{
      "page_number": 1,
      "page_type": "실제_페이지_타입",
      "questions_on_page": [실제_문제_번호들],
      "question_density": 실제_문제_개수,
      "special_elements": ["실제_발견된_요소들"],
      "layout_complexity": "simple|medium|complex",
      "processing_notes": "이 페이지 특별 처리 사항"
    }}
  ],
  "question_analysis": {{
    "total_questions": 실제_문제_개수,
    "numbering_pattern": "실제_패턴",
    "choice_pattern": "실제_선택지_패턴",
    "average_choices_per_question": 실제_평균_선택지_개수,
    "detailed_question_templates": [
      {{
        "question_number": 문제번호,
        "number_format": "6.", 
        "text_start_pattern": "다음 표와 같이",
        "text_end_pattern": "얼마인가?",
        "text_length": 약_45자,
        "choice_format": "①②③④",
        "choice_count": 4,
        "special_elements": {{
          "has_table": true,
          "table_position": "지문_바로_아래",
          "table_structure": "| 프로세스 | 도착시간 | 실행시간 | (3열_5행)",
          "has_code": false,
          "has_diagram": false
        }},
        "extraction_template": {{
          "question_start_marker": "6. 다음 표와 같이",
          "question_end_marker": "얼마인가?",
          "choice_start_marker": "①",
          "table_extraction_needed": true,
          "table_format": "markdown"
        }}
      }}
    ],
    "special_questions": [
      {{
        "question_number": 문제번호,
        "special_element": "table|code|diagram|image|passage",
        "page_location": 페이지_번호,
        "brief_description": "간단한 설명"
      }}
    ]
  }},
  "special_elements": {{
    "tables": [
      {{
        "location": "페이지X_문제Y",
        "table_type": "데이터표|비교표|계산표",
        "complexity": "simple|complex",
        "data_completeness": "header_only|partial_data|complete_data"
      }}
    ],
    "visual_elements_detailed": {{
      "diagram_in_choices": [
        {{
          "question": 25,
          "page": 3,
          "location": "선택지 ①②③④ 모두 다이어그램",
          "diagram_type": "네트워크|플로차트|ER다이어그램|시스템구조"
        }}
      ],
      "graph_in_choices": [
        {{
          "question": 35,
          "page": 5, 
          "location": "선택지 전체가 그래프",
          "graph_type": "막대|원|선|산점도"
        }}
      ],
      "shape_in_choices": [
        {{
          "question": 42,
          "page": 6,
          "location": "선택지 ①②가 기하도형",
          "shape_type": "원|사각형|삼각형|다각형"
        }}
      ],
      "diagram_in_passage": [
        {{
          "question": 5,
          "page": 1,
          "location": "문제 지문 상단",
          "diagram_type": "시스템구조|데이터흐름|네트워크"
        }}
      ],
      "graph_in_passage": [
        {{
          "question": 12,
          "page": 2,
          "location": "문제 지문 하단", 
          "graph_type": "성능그래프|통계차트|비교표"
        }}
      ]
    }},
    "choice_analysis_detailed": {{
      "questions_with_2_choices": [3, 7, 15],
      "questions_with_3_choices": [8, 12],
      "questions_with_4_choices": [1, 2, 4, 5, 6, 9, 10, 11],
      "questions_with_5_choices": [21, 22, 23]
    }},
    "page_boundary_issues_detailed": {{
      "content_split_questions": [
        {{
          "question": 12,
          "split_type": "문제 내용이 페이지 1-2에 걸림",
          "split_location": "지문 중간부분"
        }}
      ],
      "choices_split_questions": [
        {{
          "question": 7,
          "split_location": "선택지 ③④가 다음 페이지",
          "pages": "1-2"
        }}
      ],
      "separated_elements": [
        {{
          "question": 15,
          "separation_type": "지문과 문제가 분리",
          "pages": "2-3"
        }}
      ]
    }}
  }},
  "processing_strategy": {{
    "recommended_approach": "페이지별|문제유형별|요소별",
    "chunk_size_recommendation": "적정_청크_크기",
    "special_handling": ["특별_처리_필요_사항들"],
    "expected_challenges": ["예상_어려움들"],
    "processing_order": ["권장_처리_순서"]
  }}
}}
```

**⚠️ 절대 중요**: 
- 추정이나 가정 금지! 실제 보이는 내용만 분석
- 모든 숫자는 정확한 카운트 기반
- 각 문제별 상세 분석 필수
- 처리 전략은 이 특정 PDF에 최적화되어야 함

🎯 **구조 분석 필수사항**:
- 정확한 문제 개수가 가장 중요합니다
- 페이지별 문제 분포를 정확히 파악하세요
- 특수 요소가 있는 문제만 선별적으로 분석하세요
- 복잡한 개별 분석보다는 전체 구조 파악에 집중하세요

🚨 **페이지 구분 최우선 지침**:
- 각 페이지를 정확히 분류하는 것이 가장 중요합니다
- 문제가 없는 페이지를 문제 페이지로 잘못 분류하지 마세요
- 정답만 나열된 페이지는 반드시 "answer_sheet"로 분류하세요
- 해설만 있는 페이지는 반드시 "explanation_sheet"로 분류하세요
- question_density는 실제 문제가 있을 때만 1 이상으로 설정하세요

📸 **간단한 이미지 확인**:
- 페이지에 이미지가 있으면 special_elements에 "images" 포함
- 상세한 이미지 분석은 필요 없음
- 전체 구조 분석 품질을 우선으로 하세요

실제 PDF 내용을 극도로 정밀하게 분석하여 완벽한 구조 정보를 제공하세요."""
    
    async def _perform_special_elements_analysis(self, pdf_path: str, basic_structure: Dict, upload_id: int) -> Dict[str, Any]:
        """2단계: 특수 요소 집중 분석 (이미지/표/코드/선택지 등)"""
        
        print(f"🎯 2단계: 특수 요소 집중 분석 시작 - Upload {upload_id}")
        
        # 기본 구조에서 특수 요소가 있는 페이지 찾기
        special_pages = []
        page_analysis = basic_structure.get('page_analysis', [])
        
        for page in page_analysis:
            special_elements = page.get('special_elements', [])
            if any(element in special_elements for element in ['images', 'tables', 'diagrams', 'code_blocks']):
                special_pages.append(page.get('page_number'))
        
        if not special_pages:
            print("🎯 특수 요소가 있는 페이지 없음, 특수 분석 스킵")
            return {"special_analysis": [], "success": True}
        
        print(f"🎯 특수 요소 분석 대상 페이지: {special_pages}")
        
        try:
            # 해당 페이지들만 고해상도 이미지 생성
            special_pages_data = await self._create_selected_pages_images(pdf_path, special_pages)
            
            # 특수 요소 전용 프롬프트로 분석
            special_analysis_prompt = self._create_special_elements_prompt(basic_structure, special_pages)
            
            messages = [
                {
                    "role": "system", 
                    "content": "당신은 PDF 내 특수 요소 전문 분석가입니다. 표/코드/이미지/선택지를 정확히 구분하고 문제 번호를 기록하세요."
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": special_analysis_prompt}]
                }
            ]
            
            # 선택된 페이지 이미지들을 메시지에 추가
            for img_data in special_pages_data:
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_data['image_data']}",
                        "detail": "high"
                    }
                })
            
            # OpenAI API 호출
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=4000,  # 더 많은 특수 요소 분석을 위해 증가
                temperature=0.05
            )
            
            response_text = response.choices[0].message.content
            print(f"🎯 특수 요소 분석 응답 길이: {len(response_text)}자")
            
            # JSON 파싱
            special_analysis = self._parse_special_elements_response(response_text)
            
            print(f"✅ 특수 요소 집중 분석 완료")
            return {"special_analysis": special_analysis, "success": True}
            
        except Exception as e:
            print(f"❌ 특수 요소 집중 분석 실패: {e}")
            return {"special_analysis": [], "success": False, "error": str(e)}
    
    async def _create_selected_pages_images(self, pdf_path: str, page_numbers: list) -> List[Dict]:
        """선택된 페이지들만 고해상도 이미지 생성"""
        
        try:
            doc = fitz.open(pdf_path)
            selected_images = []
            
            for page_num in page_numbers:
                if page_num <= len(doc):
                    page = doc.load_page(page_num - 1)  # 0-based index
                    
                    # 고해상도 렌더링 (API 제한 고려)
                    mat = fitz.Matrix(12.0, 12.0)  # 12배 고해상도
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    
                    # Base64 인코딩
                    img_data = self._optimize_image_size(pix)
                    base64_img = base64.b64encode(img_data).decode('utf-8')
                    
                    selected_images.append({
                        'page_number': page_num,
                        'width': pix.width,
                        'height': pix.height,
                        'image_data': base64_img,
                        'format': 'png'
                    })
                    
                    print(f"   📄 이미지 페이지 {page_num} 생성: {pix.width}x{pix.height}")
            
            doc.close()
            return selected_images
            
        except Exception as e:
            print(f"❌ 선택된 페이지 이미지 생성 실패: {e}")
            return []
    
    def _create_special_elements_prompt(self, basic_structure: Dict, special_pages: list) -> str:
        """특수 요소 집중 분석 전용 프롬프트"""
        
        total_questions = basic_structure.get('analysis_summary', {}).get('total_questions', 0)
        
        return f"""🎯 특수 요소 전문 분석가

📄 **기본 정보**:
- 총 문제 수: {total_questions}개 (실제 PDF에서 감지된 수)
- 특수 요소 분석 대상 페이지: {special_pages}

🎯 **분석 목표** - 문제 번호별로 정확히 분류:
1. **이미지 선택지 문제**: 선택지가 그림/도표로 된 문제
2. **표 포함 문제**: 문제나 지문에 표/테이블이 있는 문제
3. **코드 포함 문제**: 프로그래밍 코드가 있는 문제
4. **다이어그램 문제**: 다이어그램/그래프가 있는 문제
5. **이미지 지문 문제**: 지문에 그림이 포함된 문제

**JSON 출력 형식**:
```json
{{
  "special_questions": [
    {{
      "question_number": 문제번호,
      "page_number": 페이지번호,
      "special_type": "image_choices|table_content|code_block|diagram|image_passage",
      "element_description": "구체적인 설명 (예: P1,P2,P3 프로세스 표)",
      "choice_has_images": true/false,
      "question_has_table": true/false,
      "question_has_code": true/false,
      "question_has_diagram": true/false,
      "passage_has_images": true/false
    }}
  ],
  "summary": {{
    "total_special_questions": 특수요소_문제_총수,
    "image_choice_questions": [이미지선택지_문제번호들],
    "table_questions": [표포함_문제번호들],
    "code_questions": [코드포함_문제번호들],
    "diagram_questions": [다이어그램_문제번호들],
    "image_passage_questions": [이미지지문_문제번호들]
  }}
}}
```

🎯 **분석 중점사항**:
- 문제 번호를 정확히 식별하세요
- 선택지가 이미지인 것과 지문에 이미지가 있는 것을 구분하세요
- 표의 경우 P1, P2, P3 같은 데이터가 있는지 확인하세요
- 표 데이터는 반드시 마크다운 형식으로 기록하세요: | 헤더 | 데이터 |
- 코드 블록의 경우 프로그래밍 언어도 기록하세요
- 특수 요소가 있는 문제만 분석하세요"""
    
    def _parse_special_elements_response(self, response_text: str) -> Dict:
        """특수 요소 분석 응답 파싱"""
        
        try:
            # JSON 블록 찾기
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # 첫 번째 { 부터 마지막 } 까지 추출
                start = response_text.find('{')
                end = response_text.rfind('}')
                if start != -1 and end != -1:
                    json_text = response_text[start:end+1]
                else:
                    return {"special_questions": [], "summary": {}}
            
            # JSON 파싱
            data = json.loads(json_text)
            
            # 결과 구조화
            special_questions = data.get('special_questions', [])
            summary = data.get('summary', {})
            
            # 문제 번호별로 분류해서 로그 출력
            if special_questions:
                print(f"   🎯 특수 요소 문제 발견:")
                
                image_choices = summary.get('image_choice_questions', [])
                table_questions = summary.get('table_questions', [])
                code_questions = summary.get('code_questions', [])
                diagram_questions = summary.get('diagram_questions', [])
                image_passages = summary.get('image_passage_questions', [])
                
                if image_choices:
                    print(f"   🖼️ 이미지 선택지: {image_choices}")
                if table_questions:
                    print(f"   📊 표 포함: {table_questions}")
                if code_questions:
                    print(f"   💻 코드 포함: {code_questions}")
                if diagram_questions:
                    print(f"   📈 다이어그램: {diagram_questions}")
                if image_passages:
                    print(f"   🖼️ 이미지 지문: {image_passages}")
            
            return {
                "special_questions": special_questions,
                "summary": summary
            }
            
        except Exception as e:
            print(f"⚠️ 특수 요소 분석 응답 파싱 실패: {e}")
            return {"special_questions": [], "summary": {}}
    
    async def _integrate_structure_and_special_analysis(self, basic_structure: Dict, special_analysis: Dict, upload_id: int) -> Dict[str, Any]:
        """기본 구조와 특수 요소 분석 결과 통합"""
        
        print(f"🔧 구조 분석 결과 통합 중 - Upload {upload_id}")
        
        try:
            # 기본 구조를 베이스로 복사
            integrated = basic_structure.copy()
            
            # 🆕 기본 정보에 있는 cross_page_issues를 최상위로 복사
            basic_info_cross_page = basic_structure.get('basic_info', {}).get('cross_page_issues')
            if basic_info_cross_page:
                integrated['cross_page_issues'] = basic_info_cross_page
            
            # 특수 요소 분석 결과 가져오기
            special_questions = special_analysis.get('special_analysis', {}).get('special_questions', [])
            summary = special_analysis.get('special_analysis', {}).get('summary', {})
            
            if not special_questions:
                print("🎯 특수 요소 분석 결과 없음, 기본 구조만 사용")
                return integrated
            
            # 기존 question_analysis에 특수 요소 정보 추가
            question_analysis = integrated.get('question_analysis', {})
            
            # detailed_questions 생성 (특수 요소가 있는 문제들만)
            detailed_questions = []
            
            for special_q in special_questions:
                question_detail = {
                    "question_number": special_q.get('question_number'),
                    "question_type": special_q.get('special_type', 'text_only'),
                    "choices_count": 4,  # 기본값
                    "has_passage": special_q.get('passage_has_images', False),
                    "has_table": special_q.get('question_has_table', False),
                    "has_images": special_q.get('choice_has_images', False) or special_q.get('passage_has_images', False),
                    "question_has_images": special_q.get('passage_has_images', False),
                    "choice_has_images": special_q.get('choice_has_images', False),
                    "has_code": special_q.get('question_has_code', False),
                    "has_diagram": special_q.get('question_has_diagram', False),
                    "special_elements": special_q.get('element_description', ''),
                    "page_location": special_q.get('page_number'),
                    "processing_complexity": "high"  # 특수 요소가 있으면 복잡도 높음
                }
                detailed_questions.append(question_detail)
            
            # question_analysis 업데이트
            question_analysis['detailed_questions'] = detailed_questions
            question_analysis['special_questions_count'] = len(detailed_questions)
            
            # 특수 요소별 분류 정보 추가
            question_analysis['special_elements_summary'] = {
                'image_choice_questions': summary.get('image_choice_questions', []),
                'table_questions': summary.get('table_questions', []),
                'code_questions': summary.get('code_questions', []),
                'diagram_questions': summary.get('diagram_questions', []),
                'image_passage_questions': summary.get('image_passage_questions', [])
            }
            
            integrated['question_analysis'] = question_analysis
            
            # 페이지 경계 문제 분석 및 기록
            page_boundary_issues = self._analyze_page_boundary_issues(integrated, special_analysis)
            if page_boundary_issues:
                integrated['page_boundary_analysis'] = page_boundary_issues
            
            # 특수 요소 분석 결과 상세 출력
            self._display_special_elements_summary(summary, detailed_questions, page_boundary_issues)
            
            return integrated
            
        except Exception as e:
            print(f"❌ 구조 통합 실패: {e}")
            return basic_structure
    
    def _analyze_page_boundary_issues(self, structure: Dict, special_analysis: Dict) -> Dict:
        """페이지 경계에서 발생하는 문제들 분석"""
        
        try:
            print(f"🔍 페이지 경계 문제 분석 시작...")
            
            page_analysis = structure.get('page_analysis', [])
            issues = {
                'cross_page_questions': [],
                'incomplete_questions': [],  
                'split_elements': [],
                'missing_content': [],
                'total_issues_found': 0
            }
            
            # 각 페이지의 문제 분포 확인
            for i, page_info in enumerate(page_analysis):
                page_num = page_info.get('page_number', i + 1)
                questions_on_page = page_info.get('questions_on_page', [])
                
                if not questions_on_page:
                    continue
                    
                # 페이지 끝 문제 확인 (다음 페이지로 넘어갈 가능성)
                if questions_on_page:
                    last_question = max(questions_on_page)
                    next_page_info = page_analysis[i + 1] if i + 1 < len(page_analysis) else None
                    
                    if next_page_info:
                        next_questions = next_page_info.get('questions_on_page', [])
                        if next_questions:
                            first_next_question = min(next_questions)
                            
                            # 문제 번호 연속성 확인 (건너뛰는 문제가 있는지)
                            if first_next_question - last_question > 1:
                                missing_questions = list(range(last_question + 1, first_next_question))
                                for missing_q in missing_questions:
                                    issues['cross_page_questions'].append({
                                        'question_number': missing_q,
                                        'start_page': page_num,
                                        'end_page': page_num + 1,
                                        'issue_type': 'missing_between_pages',
                                        'description': f'문제 {missing_q}번이 페이지 {page_num}-{page_num+1} 경계에서 누락됨'
                                    })
                
                # 페이지당 문제 수가 비정상적으로 적은 경우 (선택지 누락 가능성)
                expected_density = page_info.get('question_density', 0)
                if expected_density > 15:  # 한 페이지에 15개 이상은 비정상적으로 많음
                    issues['incomplete_questions'].append({
                        'page_number': page_num,
                        'expected_questions': expected_density,
                        'issue_type': 'high_density_suspicious',
                        'description': f'페이지 {page_num}에 {expected_density}개 문제 - 선택지 누락 가능성'
                    })
            
            # 특수 요소 분석에서 페이지 경계 문제 추출
            special_data = special_analysis.get('special_analysis', {})
            if 'cross_page_issues' in special_data:
                cross_page_analysis = special_data['cross_page_issues']
                if cross_page_analysis and len(cross_page_analysis.strip()) > 10:
                    issues['split_elements'].append({
                        'analysis_type': 'gpt_detected',
                        'description': cross_page_analysis.strip(),
                        'severity': 'high'
                    })
            
            issues['total_issues_found'] = (
                len(issues['cross_page_questions']) + 
                len(issues['incomplete_questions']) + 
                len(issues['split_elements']) + 
                len(issues['missing_content'])
            )
            
            if issues['total_issues_found'] > 0:
                print(f"⚠️ 페이지 경계 문제 발견: {issues['total_issues_found']}건")
                for issue in issues['cross_page_questions']:
                    print(f"   🔗 {issue['description']}")
                for issue in issues['incomplete_questions']:
                    print(f"   📄 {issue['description']}")
            else:
                print(f"✅ 페이지 경계 문제 없음")
            
            return issues if issues['total_issues_found'] > 0 else {}
            
        except Exception as e:
            print(f"❌ 페이지 경계 분석 실패: {e}")
            return {}
    
    def _display_special_elements_summary(self, summary: Dict, detailed_questions: List[Dict], page_boundary_issues: Dict = None):
        """특수 요소 분석 결과 상세 출력"""
        
        print(f"\n🔧 특수 요소 분석 통합 완료: {len(detailed_questions)}개 문제")
        print("=" * 60)
        
        # 각 카테고리별 상세 정보 출력
        categories = [
            ("🖼️ 이미지 선택지가 있는 문제", summary.get('image_choice_questions', []), "image_choice"),
            ("📊 표가 포함된 문제", summary.get('table_questions', []), "table"),
            ("💻 코드가 포함된 문제", summary.get('code_questions', []), "code"), 
            ("📈 다이어그램이 있는 문제", summary.get('diagram_questions', []), "diagram"),
            ("🖼️ 지문에 이미지가 있는 문제", summary.get('image_passage_questions', []), "image_passage")
        ]
        
        for category_name, question_numbers, category_type in categories:
            if question_numbers:
                print(f"\n{category_name}: {len(question_numbers)}개")
                print(f"   문제 번호: {', '.join(map(str, sorted(question_numbers)))}")
                
                # 해당 카테고리 문제들의 상세 정보
                category_details = [q for q in detailed_questions 
                                  if q['question_number'] in question_numbers]
                
                for detail in category_details:
                    elements = []
                    if detail.get('has_table'): elements.append("표")
                    if detail.get('choice_has_images'): elements.append("이미지선택지")  
                    if detail.get('question_has_images'): elements.append("이미지지문")
                    if detail.get('has_code'): elements.append("코드")
                    if detail.get('has_diagram'): elements.append("다이어그램")
                    
                    if elements:
                        print(f"     문제 {detail['question_number']}: {', '.join(elements)}")
            else:
                print(f"\n{category_name}: 0개")
        
        print("\n" + "=" * 60)
        print(f"📋 총 특수 요소 문제: {len(detailed_questions)}개")
        
        # 전체 통계
        total_stats = {
            "이미지 선택지": len(summary.get('image_choice_questions', [])),
            "표 포함": len(summary.get('table_questions', [])),
            "코드 포함": len(summary.get('code_questions', [])),
            "다이어그램": len(summary.get('diagram_questions', [])),
            "이미지 지문": len(summary.get('image_passage_questions', []))
        }
        
        print("📊 카테고리별 통계:")
        for stat_name, count in total_stats.items():
            if count > 0:
                print(f"   {stat_name}: {count}개")
        
        # 페이지 경계 문제 출력
        if page_boundary_issues and page_boundary_issues.get('total_issues_found', 0) > 0:
            print("\n⚠️ 페이지 경계 문제 분석 결과:")
            print("=" * 60)
            
            cross_page = page_boundary_issues.get('cross_page_questions', [])
            if cross_page:
                print(f"🔗 페이지 걸침 문제: {len(cross_page)}개")
                for issue in cross_page[:5]:  # 최대 5개만 표시
                    print(f"   문제 {issue['question_number']}: {issue['description']}")
            
            incomplete = page_boundary_issues.get('incomplete_questions', [])
            if incomplete:
                print(f"📄 선택지 누락 의심: {len(incomplete)}개")
                for issue in incomplete[:3]:
                    print(f"   페이지 {issue['page_number']}: {issue['description']}")
            
            split_elements = page_boundary_issues.get('split_elements', [])
            if split_elements:
                print(f"✂️ 분할된 요소: {len(split_elements)}개")
                for issue in split_elements:
                    print(f"   {issue.get('description', '')[:100]}...")
            
            print("=" * 60)
        
        print("=" * 60)

    def _parse_ultra_detailed_response(self, response_text: str, upload_id: int) -> Dict[str, Any]:
        """초정밀 분석 결과 파싱"""
        
        try:
            # JSON 블록 추출
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                structure_data = json.loads(json_match.group(1))
            else:
                # 직접 JSON 파싱 시도
                structure_data = json.loads(response_text)
            
            # 메타데이터 추가
            structure_data['success'] = True
            structure_data['upload_id'] = upload_id
            structure_data['analysis_method'] = 'ultra_precise_gpt_vision'
            structure_data['analysis_timestamp'] = 'now'  # 실제 구현시 timestamp 추가
            
            # 분석 품질 검증
            quality_score = self._calculate_analysis_quality(structure_data)
            structure_data['analysis_quality_score'] = quality_score
            
            return structure_data
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 파싱 실패, 텍스트 분석으로 대체: {e}")
            return self._fallback_text_parsing(response_text, upload_id)
        except Exception as e:
            print(f"❌ 분석 결과 파싱 실패: {e}")
            return {"success": False, "error": str(e), "upload_id": upload_id}
    
    def _optimize_image_size(self, pix):
        """이미지 크기 최적화 (API 제한 고려)"""
        
        # 초기 PNG 데이터 생성
        img_data = pix.tobytes("png")
        
        # 이미지 크기 확인 (MB 단위)
        size_mb = len(img_data) / (1024 * 1024)
        
        # 10MB 초과 시 JPEG로 변환 및 압축
        if size_mb > 10:
            try:
                # JPEG 변환 (품질 85%)
                img_data = pix.tobytes("jpeg", jpg_quality=85)
                new_size_mb = len(img_data) / (1024 * 1024)
                print(f"   📏 이미지 압축: {size_mb:.1f}MB → {new_size_mb:.1f}MB (JPEG 85%)")
                
                # 아직도 크면 더 낮은 품질로
                if new_size_mb > 15:
                    img_data = pix.tobytes("jpeg", jpg_quality=70)
                    final_size_mb = len(img_data) / (1024 * 1024)
                    print(f"   📏 추가 압축: {new_size_mb:.1f}MB → {final_size_mb:.1f}MB (JPEG 70%)")
                    
            except Exception as e:
                print(f"   ⚠️ 이미지 압축 실패, PNG 사용: {e}")
        
        return img_data
    
    def _calculate_analysis_quality(self, structure_data: Dict) -> float:
        """분석 품질 점수 계산"""
        
        quality_score = 0.0
        max_score = 100.0
        
        try:
            # 기본 정보 완성도 (20점)
            if structure_data.get('analysis_summary'):
                quality_score += 20
            
            # 페이지별 분석 완성도 (30점)
            page_analysis = structure_data.get('page_analysis', [])
            if page_analysis:
                page_quality = min(len(page_analysis) * 5, 30)
                quality_score += page_quality
            
            # 문제별 상세 분석 (25점)
            question_analysis = structure_data.get('question_analysis', {})
            if question_analysis.get('detailed_questions'):
                question_quality = min(len(question_analysis['detailed_questions']) * 2, 25)
                quality_score += question_quality
            
            # 특별 요소 분석 (15점)
            special_elements = structure_data.get('special_elements', {})
            if special_elements:
                special_score = min(len(special_elements) * 5, 15)
                quality_score += special_score
            
            # 처리 전략 제시 (10점)
            if structure_data.get('processing_strategy'):
                quality_score += 10
            
        except Exception as e:
            print(f"⚠️ 품질 점수 계산 실패: {e}")
            
        return round(min(quality_score / max_score, 1.0), 2)
    
    def _fallback_text_parsing(self, text: str, upload_id: int) -> Dict[str, Any]:
        """JSON 파싱 실패시 텍스트 분석 대체"""
        
        structure = {
            "success": True,
            "upload_id": upload_id,
            "analysis_method": "fallback_text_parsing",
            "analysis_summary": {
                "document_type": "questions_only",
                "total_pages": 8,
                "total_questions": 40,
                "confidence_score": 0.5
            }
        }
        
        # 텍스트에서 핵심 정보 추출 시도
        try:
            # 문제 개수 추출
            question_count_match = re.search(r'total_questions["\s:]*(\d+)', text, re.IGNORECASE)
            if question_count_match:
                structure["analysis_summary"]["total_questions"] = int(question_count_match.group(1))
            
            # 페이지 수 추출
            pages_match = re.search(r'total_pages["\s:]*(\d+)', text, re.IGNORECASE)
            if pages_match:
                structure["analysis_summary"]["total_pages"] = int(pages_match.group(1))
                
        except Exception as e:
            print(f"⚠️ 텍스트 파싱 중 오류: {e}")
        
        return structure
    
    async def _validate_and_enhance_structure(self, structure: Dict, pdf_path: str, upload_id: int) -> Dict[str, Any]:
        """분석 결과 검증 및 보완"""
        
        try:
            # 1. 실제 PDF와 분석 결과 대조
            doc = fitz.open(pdf_path)
            actual_pages = len(doc)
            doc.close()
            
            # 페이지 수 검증
            analyzed_pages = structure.get('analysis_summary', {}).get('total_pages', 0)
            if analyzed_pages != actual_pages:
                structure['validation_warnings'] = structure.get('validation_warnings', [])
                structure['validation_warnings'].append(f"페이지 수 불일치: 실제 {actual_pages}페이지 vs 분석 {analyzed_pages}페이지")
                structure['analysis_summary']['total_pages'] = actual_pages
            
            # 2. 페이지별 문제 수 vs 총 문제 수 검증 및 수정
            self._validate_and_fix_question_counts(structure)
            
            # 3. 분석 결과 품질 검증
            quality_checks = self._perform_quality_checks(structure)
            structure['quality_checks'] = quality_checks
            
            # 4. 처리 전략 보완
            enhanced_strategy = self._enhance_processing_strategy(structure)
            structure['processing_strategy'] = enhanced_strategy
            
            structure['validation_completed'] = True
            return structure
            
        except Exception as e:
            print(f"⚠️ 구조 검증 중 오류: {e}")
            structure['validation_error'] = str(e)
            return structure
    
    async def extract_questions_based_on_structure(self, pdf_path: str, structure_analysis: Dict, upload_id: int) -> Dict[str, Any]:
        """구조 분석 결과를 바탕으로 페이지별 분할 문제 추출 (구조 분석 성공 방식 차용)"""
        
        print(f"🎯 페이지별 분할 문제 추출 시작 - Upload {upload_id}")
        print("=" * 60)
        
        try:
            # 1. 구조 분석에서 문제가 있는 페이지들만 선별 (개선된 필터링)
            question_pages = []
            page_analysis = structure_analysis.get('page_analysis', [])
            global_overview = structure_analysis.get('global_overview', {})
            page_roles = global_overview.get('page_roles', [])
            
            # page_analysis에서 문제 페이지 수집
            for page_info in page_analysis:
                if page_info.get('page_type') == 'pure_questions' and page_info.get('question_density', 0) > 0:
                    question_pages.append(page_info)
            
            # global_overview에서 누락된 문제 페이지 추가 확인
            existing_page_numbers = {p.get('page_number') for p in question_pages}
            
            for role_info in page_roles:
                if (role_info.get('role') == 'questions' and 
                    role_info.get('question_count', 0) > 0 and
                    role_info.get('page_number') not in existing_page_numbers):
                    
                    # page_analysis에 누락된 문제 페이지를 추가
                    question_range = role_info.get('question_range', '1-1')
                    # 한국어 "번" 접미사 제거
                    question_range_clean = question_range.replace('번', '').strip()
                    
                    questions_on_page = []
                    if question_range_clean and '-' in question_range_clean:
                        try:
                            start, end = question_range_clean.split('-')
                            questions_on_page = list(range(int(start.strip()), int(end.strip()) + 1))
                        except (ValueError, IndexError) as e:
                            print(f"⚠️ 문제 범위 파싱 실패: {question_range} → {e}")
                    
                    missing_page = {
                        'page_number': role_info['page_number'],
                        'page_type': 'pure_questions',
                        'questions_on_page': questions_on_page,
                        'question_density': role_info.get('question_count', 0),
                        'special_elements': ['unknown'],  # 임시값
                        'layout_complexity': 'medium',
                        'processing_notes': f"global_overview에서 복구된 페이지 (문제 {role_info.get('question_range', '')})"
                    }
                    question_pages.append(missing_page)
                    print(f"🔧 누락된 페이지 {role_info['page_number']} 복구: {role_info.get('question_range', '')}")
            
            print(f"📄 문제 추출 대상: {len(question_pages)}개 페이지")
            
            # 2. 페이지별 문제 추출 (구조 분석 방식 차용)
            all_extracted_questions = []
            total_questions = structure_analysis.get('analysis_summary', {}).get('total_questions', 60)
            
            for i, page_info in enumerate(question_pages):
                print(f"\n📄 페이지 {page_info['page_number']} 문제 추출 중...")
                
                # 페이지별 고해상도 이미지 생성 (구조 분석과 동일한 방식)
                page_images = await self._create_single_page_images(pdf_path, page_info, upload_id)
                
                # 특수 요소 포함 프롬프트 (구조 분석 정보 활용)
                page_extraction_prompt = self._create_simple_page_extraction_prompt(page_info, structure_analysis)
                
                # GPT-4V로 페이지별 문제 추출
                page_questions = await self._extract_questions_from_single_page(
                    page_images, page_extraction_prompt, page_info
                )
                
                if page_questions:
                    all_extracted_questions.extend(page_questions)
                    print(f"   ✅ 페이지 {page_info['page_number']}: {len(page_questions)}개 문제 추출")
                else:
                    print(f"   ⚠️ 페이지 {page_info['page_number']}: 문제 추출 실패")
            
            print(f"\n📊 전체 추출 결과: {len(all_extracted_questions)}개 문제")
            
            # 3. 누락된 문제 재추출 (구조 분석 방식 참고)
            missing_questions = await self._extract_missing_questions(
                pdf_path, all_extracted_questions, structure_analysis, upload_id
            )
            
            if missing_questions:
                all_extracted_questions.extend(missing_questions)
                print(f"🔄 재추출 완료: {len(missing_questions)}개 추가 문제")
            
            # 4. 특수 요소 검증 및 보완
            print(f"\n🔍 특수 요소 검증 중...")
            validated_questions = await self._validate_special_elements(all_extracted_questions, structure_analysis, pdf_path, upload_id)
            
            # 5. 최종 검증 및 정리
            final_questions = self._clean_and_sort_questions(validated_questions)
            verification_result = self._verify_extraction_against_structure(final_questions, structure_analysis)
            
            print(f"✅ 페이지별 분할 추출 완료: {len(final_questions)}개 문제 (정확도: {verification_result.get('accuracy_rate', 0):.1f}%)")
            
            return {
                "success": True,
                "questions": final_questions,
                "extraction_method": "page_by_page_extraction",
                "structure_verification": verification_result,
                "total_extracted": len(final_questions),
                "expected_count": total_questions,
                "pages_processed": len(question_pages),
                "upload_id": upload_id
            }
            
        except Exception as e:
            print(f"❌ 페이지별 분할 추출 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_structure_guided_images(self, pdf_path: str, question_pages: List[Dict], upload_id: int) -> List[Dict]:
        """구조 정보를 바탕으로 맞춤형 이미지 생성"""
        
        images = []
        doc = fitz.open(pdf_path)
        
        for page_info in question_pages:
            page_num = page_info['page_number'] - 1  # 0-based index
            page = doc.load_page(page_num)
            
            # API 제한을 고려한 적응적 해상도 설정
            has_special = page_info.get('special_elements', [])
            scale = 14.0 if has_special else 12.0  # 특수 요소 있으면 14배, 일반은 12배
            
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat)
            img_data = self._optimize_image_size(pix)
            
            # Base64 인코딩
            import base64
            img_b64 = base64.b64encode(img_data).decode('utf-8')
            
            images.append({
                'page_number': page_info['page_number'],
                'image_data': img_b64,
                'scale': scale,
                'question_range': page_info.get('questions_on_page', []),
                'special_elements': has_special
            })
            
            print(f"   📄 구조 기반 {scale}배 해상도 페이지 {page_info['page_number']} 생성: {pix.width}x{pix.height}")
        
        doc.close()
        return images
    
    def _create_structure_guided_extraction_prompt(self, structure_analysis: Dict, total_questions: int) -> str:
        """구조 분석 기반 맞춤형 추출 프롬프트"""
        
        page_analysis = structure_analysis.get('page_analysis', [])
        special_questions = structure_analysis.get('question_analysis', {}).get('detailed_questions', [])
        
        prompt = f"""🎯 구조 기반 정밀 문제 추출
📊 **분석된 구조 정보**:
- 총 문제 수: {total_questions}개
- 문제 페이지: {len([p for p in page_analysis if p.get('page_type') == 'pure_questions'])}개 페이지

📄 **페이지별 문제 구성**:"""
        
        for page_info in page_analysis:
            if page_info.get('page_type') == 'pure_questions':
                questions_on_page = page_info.get('questions_on_page', [])
                special_elements = page_info.get('special_elements', [])
                
                prompt += f"""
페이지 {page_info['page_number']}: 문제 {min(questions_on_page) if questions_on_page else 0}-{max(questions_on_page) if questions_on_page else 0}번 ({len(questions_on_page)}개)"""
                
                if special_elements:
                    prompt += f" - 특수요소: {', '.join(special_elements)}"
        
        if special_questions:
            prompt += f"""

🔍 **특수 요소 문제 주의사항**:"""
            for special_q in special_questions:
                prompt += f"""
- 문제 {special_q['question_number']}번: {special_q['special_elements']} (페이지 {special_q['page_location']})"""
        
        prompt += f"""

📝 **추출 요구사항**:
1. 위 구조 정보에 정확히 일치하는 문제들만 추출
2. 각 문제는 번호, 지문, 선택지를 완전히 포함
3. 특수 요소가 있는 문제는 표/코드/다이어그램도 정확히 추출
4. 불완전한 문제는 절대 포함하지 마세요

📊 **JSON 출력 형식**:
```json
{{
  "questions": [
    {{
      "question_number": 1,
      "question_text": "문제 지문",
      "options": ["① 선택지1", "② 선택지2", "③ 선택지3", "④ 선택지4"],
      "passage": "지문이 있다면",
      "page_number": 1,
      "has_table": false,
      "has_code": false,
      "has_diagram": false,
      "table_data": null,
      "code_content": null
    }}
  ]
}}
```

⚡ **매우 중요**: 구조 분석에서 확인된 {total_questions}개 문제를 정확히 추출하세요!"""
        
        return prompt
    
    def _parse_extraction_response(self, response_text: str) -> List[Dict]:
        """문제 추출 응답 파싱 (선택지 복구 로직 포함)"""
        
        try:
            # JSON 추출 시도
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # JSON 블록이 없으면 전체에서 찾기
                json_str = response_text
            
            parsed = json.loads(json_str)
            questions = parsed.get('questions', [])
            
            # 선택지 복구 로직 적용
            fixed_questions = []
            for question in questions:
                fixed_question = self._fix_embedded_options(question)
                fixed_questions.append(fixed_question)
            
            print(f"📝 파싱된 문제 수: {len(fixed_questions)}개")
            return fixed_questions
            
        except Exception as e:
            print(f"⚠️ 응답 파싱 실패: {e}")
            return []
    
    def _parse_special_element_response(self, response_text: str) -> List[Dict]:
        """특수 요소 추출 응답 전용 파싱"""
        
        try:
            print(f"🔍 특수 요소 응답 길이: {len(response_text)}자")
            print(f"🔍 응답 미리보기: {response_text[:200]}...")
            
            # JSON 추출 시도
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                print(f"📄 JSON 블록 추출 성공: {len(json_str)}자")
            else:
                # JSON 블록이 없으면 중괄호로 감싸진 부분 찾기
                brace_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', response_text, re.DOTALL)
                if brace_match:
                    json_str = brace_match.group(1)
                    print(f"📄 중괄호 블록 추출 성공: {len(json_str)}자")
                else:
                    print(f"❌ JSON 구조를 찾을 수 없음")
                    return []
            
            # JSON 파싱
            parsed = json.loads(json_str)
            print(f"✅ JSON 파싱 성공")
            
            # 단일 객체를 리스트로 래핑
            if isinstance(parsed, dict):
                result = [parsed]
                print(f"📝 특수 요소 파싱 완료: 1개 객체")
                
                # 파싱된 데이터 검증
                if 'question_number' in parsed:
                    print(f"✅ 문제 번호: {parsed['question_number']}")
                if 'has_table' in parsed:
                    print(f"📊 표 포함: {parsed.get('has_table', False)}")
                if 'has_code' in parsed:
                    print(f"💻 코드 포함: {parsed.get('has_code', False)}")
                if 'has_diagram' in parsed:
                    print(f"📈 다이어그램 포함: {parsed.get('has_diagram', False)}")
                    
                return result
            else:
                print(f"⚠️ 예상과 다른 JSON 구조: {type(parsed)}")
                return []
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {e}")
            print(f"📄 파싱 시도한 JSON: {json_str[:500] if 'json_str' in locals() else 'N/A'}")
            return []
        except Exception as e:
            print(f"⚠️ 특수 요소 파싱 실패: {e}")
            return []
    
    def _fix_embedded_options(self, question: Dict) -> Dict:
        """question_text에 포함된 선택지 및 보기를 정확히 분리 (중복 방지 강화)"""
        
        text = question.get('question_text', '')
        if not text:
            return question
        
        print(f"🔧 문제 {question.get('question_number', '?')}번 중복 분리 처리 시작")
        
        # 1. 선택지 패턴 사전 감지 (문제 텍스트에 선택지가 섞여있는지 확인)
        choice_markers_in_text = re.findall(r'[①②③④⑤]|[1-5]\)', text)
        existing_options = question.get('options', [])
        
        print(f"   - 문제 텍스트 내 선택지 마커: {len(choice_markers_in_text)}개")
        print(f"   - 기존 선택지: {len(existing_options)}개")
        
        # 2. 보기/지문 분리 (passage 필드가 없거나 비어있을 때)
        if not question.get('passage') or question.get('passage').strip() == '':
            question = self._extract_passage_from_text(question, text)
            text = question['question_text']  # 업데이트된 텍스트 사용
        
        # 3. 선택지 분리 및 중복 방지 (선택지가 부족하거나 텍스트에 섞여있을 때)
        if len(existing_options) < 2 or len(choice_markers_in_text) > len(existing_options):
            question = self._extract_options_from_text(question, text)
        
        # 4. 강화된 중복 내용 제거
        question = self._clean_duplicate_content(question)
        
        # 5. 최종 검증 및 품질 확인
        question = self._verify_content_separation_quality(question)
        
        return question
    
    def _extract_passage_from_text(self, question: Dict, text: str) -> Dict:
        """텍스트에서 보기/지문 추출 (향상된 패턴 매칭)"""
        
        # 확장된 보기 패턴 검색
        passage_patterns = [
            # 명시적 보기 마크
            r'<보기>\s*(.*?)(?=\n\s*[①②③④⑤]|\n\s*[1-5]\)|다음|문제|$)',
            r'\[보기\]\s*(.*?)(?=\n\s*[①②③④⑤]|\n\s*[1-5]\)|다음|문제|$)',
            r'보기\s*:?\s*(.*?)(?=\n\s*[①②③④⑤]|\n\s*[1-5]\)|다음|문제|$)',
            
            # 표 패턴 (개선)
            r'\|[^|\n]*\|[^\n]*\n\|[^|\n]*\|[^\n]*(?:\n\|[^|\n]*\|[^\n]*)*',
            
            # 코드 패턴 (확장)
            r'(?:public|private|class|function|def|int|void|for|while|if|import|include)\s+[^\n]*(?:\n\s*[^\n①②③④⑤]*)*(?=\n\s*[①②③④⑤]|$)',
            
            # 마크다운 코드 블록
            r'```[\s\S]*?```',
            
            # 수식이나 다이어그램
            r'[A-Z]\s*→\s*[A-Z].*?(?=\n\s*[①②③④⑤]|$)',
            r'\w+\s*=\s*\w+.*?(?=\n\s*[①②③④⑤]|$)'
        ]
        
        for pattern in passage_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
            if match:
                passage_content = match.group(0).strip()
                # 유의미한 길이의 보기만 추출 (최소 15자)
                if len(passage_content) > 15 and not re.match(r'^\s*[①②③④⑤]', passage_content):
                    question['passage'] = passage_content
                    # 문제 텍스트에서 보기 부분 정확히 제거
                    clean_text = text.replace(passage_content, '').strip()
                    clean_text = re.sub(r'\s+', ' ', clean_text)  # 공백 정리
                    question['question_text'] = clean_text
                    print(f"📖 문제 {question.get('question_number', '?')}번 보기 분리: {len(passage_content)}자")
                    break
        
        return question
    
    def _extract_options_from_text(self, question: Dict, text: str) -> Dict:
        """텍스트에서 선택지 추출 (중복 방지 및 숫자 선택지 강화)"""
        
        # 기존 선택지 보존 (덮어쓰지 않고 보강)
        existing_options = question.get('options', [])
        
        # 확장된 선택지 패턴 (순서대로 시도)
        patterns = [
            # 1순위: 동그라미 숫자 (한국어 시험 표준)
            r'([①②③④⑤])\s*([^\n①②③④⑤]*?)(?=\s*[①②③④⑤]|\n\n|$)',
            # 2순위: 괄호 숫자
            r'([1-5]\))\s*([^\n1-5)]*?)(?=\s*[1-5]\)|\n\n|$)',
            # 3순위: 알파벳
            r'([A-E]\))\s*([^\nA-E)]*?)(?=\s*[A-E]\)|\n\n|$)',
        ]
        
        extracted_options = []
        clean_question_text = text
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
            if len(matches) >= 2:  # 최소 2개 선택지 발견
                
                # 첫 번째 선택지 위치 찾기
                first_match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
                if first_match:
                    # 선택지 이전까지가 문제 지문
                    clean_question_text = text[:first_match.start()].strip()
                    
                    # 선택지 배열 구성
                    for marker, content in matches:
                        content = content.strip()
                        
                        # 빈 내용 제외
                        if not content or content == marker:
                            continue
                            
                        # 숫자 선택지 특별 처리
                        if self._is_numeric_choice(content):
                            option_text = f"{marker} {content}"
                            print(f"   🔢 숫자 선택지 감지: {option_text}")
                        elif len(content) > 100:  # 너무 긴 내용은 문제 지문이 섞인 것
                            continue
                        else:
                            option_text = f"{marker} {content}"
                        
                        extracted_options.append(option_text)
                    
                    break  # 첫 번째 성공한 패턴 사용
        
        # 추출 결과 적용
        if len(extracted_options) >= 2:
            # 기존 선택지보다 더 많이 추출했거나 기존이 없다면 교체
            if len(extracted_options) > len(existing_options):
                question['options'] = extracted_options
                question['question_text'] = clean_question_text
                print(f"🔧 문제 {question.get('question_number', '?')}번 선택지 추출: {len(extracted_options)}개 (기존: {len(existing_options)}개)")
            else:
                print(f"   기존 선택지 유지: {len(existing_options)}개")
        
        return question
    
    def _is_numeric_choice(self, content: str) -> bool:
        """숫자 선택지 여부 판단"""
        
        # 순수 숫자
        if re.match(r'^\d+(\.\d+)?$', content):
            return True
        
        # 숫자 + 단위
        if re.match(r'^\d+(\.\d+)?\s*[%개명원달러초분시km²㎡㎥kg]', content):
            return True
            
        # 수식
        if re.match(r'^[x-z]\s*=\s*\d+', content):
            return True
            
        # 분수/비율
        if re.match(r'^\d+/\d+|\d+:\d+', content):
            return True
        
        return False
    
    def _clean_duplicate_content(self, question: Dict) -> Dict:
        """중복 내용 정리 및 검증 (강화된 중복 제거)"""
        
        question_text = question.get('question_text', '')
        options = question.get('options', [])
        passage = question.get('passage', '')
        
        print(f"   🧹 중복 내용 정리 시작")
        
        # 1. 문제 텍스트에서 선택지 마커 및 내용 제거
        cleaned_text = question_text
        
        for option in options:
            if option and len(option) > 2:
                # 마커 추출 (①, ②, 1), 2) 등)
                marker_match = re.match(r'^([①②③④⑤]|[1-5]\))', option)
                if marker_match:
                    marker = marker_match.group(1)
                    # 마커가 문제 텍스트에 남아있으면 제거
                    cleaned_text = cleaned_text.replace(marker, '').strip()
                    
                    # 선택지 내용이 문제 텍스트에 중복되어 있으면 제거
                    option_content = option.replace(marker, '').strip()
                    if option_content and len(option_content) > 5:
                        # 부분 일치 제거 (선택지 내용이 문제에 포함된 경우)
                        if option_content in cleaned_text:
                            cleaned_text = cleaned_text.replace(option_content, '').strip()
        
        # 2. 연속된 공백 정리
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        # 3. 불완전한 문장 정리 (선택지 제거 후 남은 조각들)
        cleaned_text = re.sub(r'\s*[①②③④⑤]\s*$', '', cleaned_text)  # 끝에 남은 마커
        cleaned_text = re.sub(r'\s*[1-5]\)\s*$', '', cleaned_text)  # 끝에 남은 괄호 숫자
        
        # 4. 문제 텍스트가 너무 짧아지면 경고
        if len(cleaned_text) < 10 and len(question_text) > 10:
            print(f"   ⚠️ 문제 텍스트가 너무 짧아짐: '{cleaned_text[:30]}...'")
            # 원본의 일부를 보존
            cleaned_text = question_text[:100] + '...' if len(question_text) > 100 else question_text
        
        question['question_text'] = cleaned_text
        
        # 5. 빈 필드 처리
        if not passage:
            question['passage'] = ''
        
        # 6. 선택지 중복 제거
        unique_options = []
        seen_contents = set()
        
        for option in options:
            option_key = re.sub(r'^[①②③④⑤]|^[1-5]\)', '', option).strip().lower()
            if option_key not in seen_contents and len(option_key) > 0:
                unique_options.append(option)
                seen_contents.add(option_key)
        
        question['options'] = unique_options
        
        print(f"   ✅ 정리 완료 - 텍스트: {len(cleaned_text)}자, 선택지: {len(unique_options)}개")
        
        return question
    
    def _verify_content_separation_quality(self, question: Dict) -> Dict:
        """내용 분리 품질 최종 검증"""
        
        q_num = question.get('question_number', '?')
        question_text = question.get('question_text', '')
        options = question.get('options', [])
        passage = question.get('passage', '')
        
        issues = []
        
        # 1. 선택지 개수 검증
        if len(options) < 2:
            issues.append("선택지 부족")
        elif len(options) > 5:
            issues.append("선택지 과다")
        
        # 2. 문제 텍스트에 선택지 마커 잔존 검증
        remaining_markers = re.findall(r'[①②③④⑤]|[1-5]\)', question_text)
        if len(remaining_markers) > 0:
            issues.append(f"마커 잔존 {len(remaining_markers)}개")
        
        # 3. 선택지 형식 검증
        malformed_options = 0
        for option in options:
            if not re.match(r'^[①②③④⑤]|^[1-5]\)', option):
                malformed_options += 1
        
        if malformed_options > 0:
            issues.append(f"형식 오류 {malformed_options}개")
        
        # 4. 결과 출력
        if issues:
            print(f"   ⚠️ 문제 {q_num}번 품질 이슈: {', '.join(issues)}")
        else:
            print(f"   ✅ 문제 {q_num}번 분리 품질 양호")
        
        return question
    
    def _verify_extraction_against_structure(self, extracted_questions: List[Dict], structure_analysis: Dict) -> Dict:
        """추출 결과와 구조 분석 비교 검증"""
        
        expected_count = structure_analysis.get('analysis_summary', {}).get('total_questions', 0)
        actual_count = len(extracted_questions)
        
        # 문제 번호 검증
        expected_numbers = set(range(1, expected_count + 1))
        actual_numbers = {q.get('question_number', 0) for q in extracted_questions}
        
        missing_numbers = expected_numbers - actual_numbers
        extra_numbers = actual_numbers - expected_numbers
        
        verification = {
            "expected_count": expected_count,
            "actual_count": actual_count,
            "count_match": expected_count == actual_count,
            "missing_questions": sorted(list(missing_numbers)),
            "extra_questions": sorted(list(extra_numbers)),
            "accuracy_rate": len(actual_numbers & expected_numbers) / max(len(expected_numbers), 1) * 100
        }
        
        print(f"🔍 추출 검증 결과: {actual_count}/{expected_count}개 추출 (정확도: {verification['accuracy_rate']:.1f}%)")
        
        if missing_numbers:
            print(f"   ⚠️ 누락된 문제: {sorted(list(missing_numbers))}")
        if extra_numbers:
            print(f"   ⚠️ 추가된 문제: {sorted(list(extra_numbers))}")
        
        return verification
    
    async def _create_single_page_images(self, pdf_path: str, page_info: Dict, upload_id: int, 
                                       include_boundary: bool = True) -> List[Dict]:
        """단일 페이지의 고해상도 이미지 생성 (페이지 경계 고려)"""
        
        doc = fitz.open(pdf_path)
        page_num = page_info['page_number'] - 1  # 0-based index
        total_pages = len(doc)
        
        images = []
        
        # 메인 페이지 이미지
        page = doc.load_page(page_num)
        has_special = page_info.get('special_elements', [])
        # API 제한을 고려한 적응적 해상도 설정
        scale = 14.0 if has_special else 12.0  # 특수 요소 있으면 14배, 일반은 12배
        
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        
        # 이미지 크기 최적화
        img_data = self._optimize_image_size(pix)
        
        import base64
        img_b64 = base64.b64encode(img_data).decode('utf-8')
        
        images.append({
            'page_number': page_info['page_number'],
            'image_data': img_b64,
            'scale': scale,
            'question_range': page_info.get('questions_on_page', []),
            'special_elements': has_special,
            'is_main': True
        })
        
        # 페이지 경계 처리: 다음 페이지 일부도 포함 (선택지 연속성을 위해)
        if include_boundary and page_num + 1 < total_pages:
            next_page = doc.load_page(page_num + 1)
            
            # 다음 페이지의 상단 일부만 캡처 (선택지 연속성 확인용)
            page_rect = next_page.rect
            top_portion_rect = fitz.Rect(0, 0, page_rect.width, page_rect.height * 0.3)  # 상단 30%
            
            mat = fitz.Matrix(scale, scale)
            pix = next_page.get_pixmap(matrix=mat, clip=top_portion_rect)
            img_data = self._optimize_image_size(pix)
            img_b64 = base64.b64encode(img_data).decode('utf-8')
            
            images.append({
                'page_number': page_info['page_number'] + 1,
                'image_data': img_b64,
                'scale': scale,
                'question_range': [],
                'special_elements': [],
                'is_main': False,
                'is_boundary_check': True,
                'boundary_type': 'next_page_top'
            })
            
            print(f"   📄 페이지 경계 확인: 다음 페이지 상단 포함")
        
        doc.close()
        return images
    
    def _create_simple_page_extraction_prompt(self, page_info: Dict, structure_analysis: Optional[Dict] = None) -> str:
        """템플릿 기반 정밀 페이지별 추출 프롬프트 (상세 구조 분석 활용)"""
        
        questions_on_page = page_info.get('questions_on_page', [])
        page_num = page_info['page_number']
        question_count = len(questions_on_page)
        special_elements = page_info.get('special_elements', [])
        
        if questions_on_page:
            question_range = f"{min(questions_on_page)}번 ~ {max(questions_on_page)}번"
        else:
            question_range = "알 수 없음"
        
        # 구조 분석에서 이 페이지의 상세 템플릿 찾기
        detailed_templates = []
        special_questions_on_this_page = []
        if structure_analysis:
            # 새로운 상세 템플릿 정보 추출
            question_templates = structure_analysis.get('question_analysis', {}).get('detailed_question_templates', [])
            for template in question_templates:
                if template.get('question_number') in questions_on_page:
                    detailed_templates.append(template)
            
            # 기존 특수 문제 정보도 유지
            detailed_questions = structure_analysis.get('question_analysis', {}).get('detailed_questions', [])
            for special_q in detailed_questions:
                if special_q.get('page_location') == page_num:
                    special_questions_on_this_page.append(special_q)
        
        # 템플릿 기반 프롬프트
        prompt = f"""📄 페이지 {page_num} 템플릿 기반 정밀 문제 추출

🎯 **추출 목표**:
- 이 페이지에 있는 문제 {question_range} 추출
- 총 {question_count}개 문제 예상
- 구조 분석에서 제공된 정확한 템플릿 사용"""
        
        # 상세 템플릿 정보 추가
        if detailed_templates:
            prompt += f"""

🎯 **문제별 정확한 추출 템플릿**:"""
            
            for template in detailed_templates:
                q_num = template.get('question_number')
                number_format = template.get('number_format', f'{q_num}.')
                text_start = template.get('text_start_pattern', '')
                text_end = template.get('text_end_pattern', '')
                choice_format = template.get('choice_format', '①②③④')
                choice_count = template.get('choice_count', 4)
                special_elem = template.get('special_elements', {})
                
                prompt += f"""
                
📋 **문제 {q_num}번 추출 템플릿**:
- 번호 형식: "{number_format}"
- 지문 시작: "{text_start}"
- 지문 끝: "{text_end}"
- 선택지: {choice_format} ({choice_count}개)"""
                
                if special_elem.get('has_table'):
                    table_pos = special_elem.get('table_position', '지문 아래')
                    table_struct = special_elem.get('table_structure', '표')
                    prompt += f"""
- 🔸 표 위치: {table_pos}
- 🔸 표 구조: {table_struct}
- 🔸 반드시 마크다운 표 형식으로 추출: | 헤더1 | 헤더2 |"""
                
                if special_elem.get('has_code'):
                    prompt += f"""
- 🔸 코드 블록 포함됨 - 들여쓰기와 구조 정확히 보존"""
                    
                if special_elem.get('has_diagram'):
                    prompt += f"""
- 🔸 다이어그램 포함됨 - 모든 구성요소 상세히 설명"""

        # 특수 요소가 있는 경우 세부 지시 추가
        if special_elements or special_questions_on_this_page:
            prompt += f"""
            
🔍 **특수 요소 주의사항**:"""
            
            if special_questions_on_this_page:
                for special_q in special_questions_on_this_page:
                    q_num = special_q.get('question_number')
                    special_type = special_q.get('question_type', '')
                    special_desc = special_q.get('special_elements', '')
                    
                    if 'table' in special_type:
                        prompt += f"""
- 🔸 문제 {q_num}번: 표 데이터가 포함됨 ({special_desc})
  → 표의 모든 행과 열을 정확히 추출하세요
  → 마크다운 표 형식으로 추출하세요: | 헤더1 | 헤더2 | 헤더3 |
  → 표 구분선도 포함하세요: |-------|-------|-------|
  → 모든 데이터 행을 완전히 포함하세요"""
                    
                    elif 'diagram' in special_type:
                        prompt += f"""
- 🔸 문제 {q_num}번: 다이어그램 포함됨 ({special_desc})
  → 다이어그램의 구조와 내용을 텍스트로 설명하세요
  → 트리, 그래프, 차트 등의 관계를 명확히 기술하세요"""
                    
                    elif 'code' in special_type:
                        prompt += f"""
- 🔸 문제 {q_num}번: 코드 블록 포함됨 ({special_desc})
  → 코드의 들여쓰기와 구조를 정확히 보존하세요
  → 모든 변수명, 함수명을 정확히 추출하세요"""
            
            if 'tables' in special_elements:
                prompt += """
- 📊 이 페이지에 표가 있습니다 - 마크다운 표 형식으로 완전히 추출하세요
  예: | 열1 | 열2 | 열3 |
      |-----|-----|-----|
      | 값1 | 값2 | 값3 |"""
            
            if 'code_blocks' in special_elements:
                prompt += """
- 💻 이 페이지에 코드가 있습니다 - 코드 구조를 정확히 보존하세요"""
            
            if 'diagrams' in special_elements:
                prompt += """
- 📈 이 페이지에 다이어그램이 있습니다 - 구조를 텍스트로 설명하세요"""

        prompt += f"""

📝 **추출 방법**:
1. 각 문제의 번호를 정확히 확인
2. 문제 지문을 완전히 추출
3. 모든 선택지(①②③④⑤)를 완전히 추출
4. 페이지 끝에서 잘린 선택지가 있다면:
   - 메인 이미지에서 보이는 부분까지 추출
   - 추가 이미지(다음 페이지 상단)에서 연속 부분 확인
   - 두 이미지를 종합해서 완전한 선택지 구성
5. 불완전한 문제는 제외하지 말고 가능한 부분까지 추출
6. 여러 이미지가 제공되면 모두 활용해서 완전한 문제 추출

🔍 **페이지 경계 처리**:
- 첫 번째 이미지: 메인 페이지 (문제 {question_range})
- 두 번째 이미지 (있다면): 다음 페이지 상단 (선택지 연속성 확인용)
- 두 이미지를 종합해서 완전한 문제를 구성하세요

📊 **완전한 JSON 출력 형식**:
```json
{{
  "questions": [
    {{
      "question_number": 1,
      "question_text": "문제 지문만 (선택지, 보기 제외)",
      "passage": "보기/표/코드/다이어그램 내용 (없으면 빈 문자열)",
      "options": ["① 첫번째 선택지", "② 두번째 선택지", "③ 세번째 선택지", "④ 네번째 선택지"],
      "page_number": {page_num},
      "has_table": true/false,
      "has_code": true/false,
      "has_diagram": true/false
    }}
  ]
}}
```

🚨 **절대 금지사항**:
- question_text에 선택지(①②③④)를 포함하지 마세요
- question_text에 보기 내용을 포함하지 마세요
- question_text는 오직 문제 지문만 포함하세요  
- 선택지는 반드시 options 배열에 별도로 분리하세요
- 보기는 반드시 passage 필드에 별도로 분리하세요

📖 **보기/지문 분리 가이드**:
- <보기>로 시작하는 내용
- 표, 코드, 다이어그램 등
- 문제 앞에 제시된 추가 정보
- 이런 내용은 모두 "passage" 필드에 저장하세요

⚡ **매우 중요**: 
- 표, 다이어그램, 코드 등 특수 요소를 절대 누락하지 마세요
- 표는 반드시 마크다운 표 형식으로 추출하세요 (| 데이터 | 형태)
- 다이어그램은 모든 구성요소와 관계를 상세히 설명하세요
- 다이어그램 설명에는 노드명, 연결관계, 시각적 요소를 전부 포함하세요
- 표의 모든 행과 열을 완전히 보존하세요
- **특별 주의**: 선택지에 포함된 숫자+단위(예: 256KB), 연산자(예: !=, >=), SQL 문(예: SELECT * FROM), 16진수(예: 0xFFFF), 코드 문법(예: int main())을 반드시 정확히 추출하세요
- 페이지 경계에서 잘린 선택지도 보이는 부분까지 추출하세요
- 문제 번호와 내용을 정확히 매칭하세요"""
        
        return prompt
    
    async def _extract_questions_from_single_page(self, page_images: List[Dict], prompt: str, page_info: Dict) -> List[Dict]:
        """단일 페이지에서 문제 추출"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": """당신은 원본 텍스트 완전 보존 전문가입니다.

🔒 **절대 원칙 - 원본 그대로**:
- 보이는 텍스트를 **한 글자도** 바꾸지 마세요
- 숫자를 **절대** 다른 숫자로 바꾸지 마세요 (8.2 → 8 금지)
- 선택지 개수를 **절대** 조작하지 마세요 (4개 → 5개 금지) 
- 소수점을 **절대** 제거하지 마세요 (9.4 → 9 금지)

🚨 **재해석/생성 절대 금지**:
- 문제나 선택지를 의역하지 마세요
- 없는 선택지를 만들어내지 마세요
- 선택지 순서를 바꾸지 마세요
- 내용을 요약하거나 수정하지 마세요

📸 **복사기 모드**: 
- 이 이미지를 복사기로 생각하세요
- 보이는 것을 **그대로** 복사하세요
- **해석하지 말고** **복사**하세요

🔢 **숫자 선택지 특별 주의**:
- "① 7.2" → 정확히 "① 7.2"로 추출
- "② 8.5%" → 정확히 "② 8.5%"로 추출
- "③ x = 10" → 정확히 "③ x = 10"으로 추출
- "④ 256KB" → 정확히 "④ 256KB"로 추출

📖 **보기/지문 완벽 분리**:
- 문제 앞의 <보기>, 표, 코드, 다이어그램은 "passage"에 저장
- 문제 지문은 "question_text"에만 저장
- 선택지는 "options"에만 저장
- 절대 내용을 섞지 마세요!

⚡ **분리 규칙**:
- question_text: 지문만 (선택지, 보기 제외)
- passage: 보기/표/코드/다이어그램만
- options: 보이는 선택지 **정확한 개수**만큼
- 특수기호, 숫자, 소수점 **원본 그대로**"""
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ]
            
            # 페이지 이미지 추가
            for img_data in page_images:
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_data['image_data']}",
                        "detail": "high"
                    }
                })
            
            # GPT-4V 호출 (더 많은 토큰 허용)
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=6000,  # 토큰 수 증가
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content
            
            # 응답 파싱
            questions = self._parse_extraction_response(response_text)
            
            return questions
            
        except Exception as e:
            print(f"⚠️ 페이지 {page_info['page_number']} 문제 추출 실패: {e}")
            return []
    
    async def _extract_missing_questions(self, pdf_path: str, extracted_questions: List[Dict], 
                                       structure_analysis: Dict, upload_id: int) -> List[Dict]:
        """누락된 문제 재추출 (구조 분석 방식 참고)"""
        
        try:
            # 추출된 문제 번호 확인
            extracted_numbers = {q.get('question_number', 0) for q in extracted_questions}
            total_questions = structure_analysis.get('analysis_summary', {}).get('total_questions', 60)
            expected_numbers = set(range(1, total_questions + 1))
            
            missing_numbers = expected_numbers - extracted_numbers
            
            if not missing_numbers:
                print("✅ 모든 문제가 추출되었습니다.")
                return []
            
            print(f"🔍 누락된 문제 재추출 중: {sorted(list(missing_numbers))}")
            
            # 누락된 문제가 있는 페이지들 찾기
            page_analysis = structure_analysis.get('page_analysis', [])
            missing_questions = []
            
            for page_info in page_analysis:
                if page_info.get('page_type') != 'pure_questions':
                    continue
                
                questions_on_page = set(page_info.get('questions_on_page', []))
                missing_on_this_page = missing_numbers & questions_on_page
                
                if missing_on_this_page:
                    print(f"   📄 페이지 {page_info['page_number']}에서 {len(missing_on_this_page)}개 문제 재추출")
                    
                    # 재추출 시도
                    retry_questions = await self._retry_extract_specific_questions(
                        pdf_path, page_info, list(missing_on_this_page), upload_id
                    )
                    
                    if retry_questions:
                        missing_questions.extend(retry_questions)
            
            return missing_questions
            
        except Exception as e:
            print(f"⚠️ 누락 문제 재추출 실패: {e}")
            return []
    
    async def _retry_extract_specific_questions(self, pdf_path: str, page_info: Dict, 
                                              missing_numbers: List[int], upload_id: int) -> List[Dict]:
        """특정 문제 번호들을 타겟으로 재추출"""
        
        try:
            # 재추출용 고해상도 이미지 생성
            retry_images = await self._create_single_page_images(pdf_path, page_info, upload_id)
            
            # 특정 문제를 타겟으로 한 프롬프트
            retry_prompt = f"""🔍 특정 문제 재추출

🎯 **타겟 문제**: {', '.join(map(str, missing_numbers))}번
📄 **페이지**: {page_info['page_number']}

📝 **추출 방법**:
위 문제 번호들만 정확히 찾아서 추출하세요.
- 문제 번호, 지문, 선택지를 완전히 추출
- 불완전한 경우 제외

📊 **JSON 출력**:
```json
{{"questions": [...]}}
```"""
            
            messages = [
                {
                    "role": "system",
                    "content": "특정 문제 번호를 타겟으로 정확한 문제 재추출을 수행하는 전문가입니다."
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": retry_prompt}]
                }
            ]
            
            # 이미지 추가
            for img_data in retry_images:
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_data['image_data']}",
                        "detail": "high"
                    }
                })
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=4000,
                temperature=0.1
            )
            
            questions = self._parse_extraction_response(response.choices[0].message.content)
            
            # 타겟 문제 번호만 필터링
            filtered_questions = [q for q in questions if q.get('question_number', 0) in missing_numbers]
            
            return filtered_questions
            
        except Exception as e:
            print(f"⚠️ 특정 문제 재추출 실패: {e}")
            return []
    
    def _clean_and_sort_questions(self, questions: List[Dict]) -> List[Dict]:
        """문제 정리 및 정렬"""
        
        # 중복 제거 (문제 번호 기준)
        seen_numbers = set()
        cleaned_questions = []
        
        for question in questions:
            q_num = question.get('question_number', 0)
            if q_num > 0 and q_num not in seen_numbers:
                seen_numbers.add(q_num)
                cleaned_questions.append(question)
        
        # 문제 번호순으로 정렬
        cleaned_questions.sort(key=lambda x: x.get('question_number', 0))
        
        return cleaned_questions
    
    async def _validate_special_elements(self, questions: List[Dict], structure_analysis: Dict, 
                                       pdf_path: str, upload_id: int) -> List[Dict]:
        """특수 요소 추출 검증 및 보완"""
        
        try:
            # 구조 분석에서 특수 요소가 있는 문제들 찾기
            detailed_questions = structure_analysis.get('question_analysis', {}).get('detailed_questions', [])
            
            special_question_numbers = []
            for special_q in detailed_questions:
                special_question_numbers.append(special_q.get('question_number'))
            
            if not special_question_numbers:
                print("   ✅ 특수 요소 문제 없음")
                return questions
            
            print(f"   🔍 특수 요소 검증 대상: {special_question_numbers}번")
            
            validated_questions = []
            missing_special_elements = []
            
            for question in questions:
                q_num = question.get('question_number', 0)
                
                if q_num in special_question_numbers:
                    # 특수 요소가 있어야 하는 문제인지 확인
                    special_info = None
                    for special_q in detailed_questions:
                        if special_q.get('question_number') == q_num:
                            special_info = special_q
                            break
                    
                    if special_info:
                        has_table = question.get('has_table', False) or question.get('table_data')
                        has_diagram = question.get('has_diagram', False) 
                        has_code = question.get('has_code', False) or question.get('code_content')
                        
                        expected_table = special_info.get('has_table', False)
                        expected_diagram = special_info.get('has_diagram', False)
                        expected_code = special_info.get('has_code', False)
                        
                        # 특수 요소 누락 검사
                        missing_elements = []
                        if expected_table and not has_table:
                            missing_elements.append('table')
                        if expected_diagram and not has_diagram:
                            missing_elements.append('diagram')
                        if expected_code and not has_code:
                            missing_elements.append('code')
                        
                        if missing_elements:
                            print(f"   ⚠️ 문제 {q_num}번: {missing_elements} 누락 감지")
                            missing_special_elements.append({
                                'question_number': q_num,
                                'missing_elements': missing_elements,
                                'special_info': special_info,
                                'current_question': question
                            })
                        else:
                            print(f"   ✅ 문제 {q_num}번: 특수 요소 확인됨")
                
                validated_questions.append(question)
            
            # 구조 분석에서 상세 템플릿 찾기
            detailed_templates = structure_analysis.get('question_analysis', {}).get('detailed_question_templates', [])
            
            # 누락된 특수 요소 템플릿 기반 재추출
            if missing_special_elements:
                print(f"   🔄 {len(missing_special_elements)}개 문제의 템플릿 기반 재추출 중...")
                
                for missing_item in missing_special_elements:
                    q_num = missing_item['question_number']
                    
                    # 해당 문제의 상세 템플릿 찾기
                    question_template = None
                    for template in detailed_templates:
                        if template.get('question_number') == q_num:
                            question_template = template
                            break
                    
                    if question_template:
                        # 템플릿 기반 재추출 시도
                        page_location = None
                        for special_q in detailed_questions:
                            if special_q.get('question_number') == q_num:
                                page_location = special_q.get('page_location')
                                break
                        
                        if page_location:
                            enhanced_question = await self._re_extract_with_template(
                                question_template, pdf_path, page_location, upload_id
                            )
                            
                            if enhanced_question:
                                # 기존 문제를 보완된 문제로 교체
                                for i, q in enumerate(validated_questions):
                                    if q.get('question_number') == q_num:
                                        validated_questions[i] = enhanced_question
                                        print(f"   ✅ 문제 {q_num}번 템플릿 기반 재추출 완료")
                                        break
                    else:
                        # 템플릿이 없으면 기존 방식으로 재추출
                        enhanced_question = await self._re_extract_special_elements(
                            missing_item, pdf_path, upload_id
                        )
                        
                        if enhanced_question:
                            # 기존 문제를 보완된 문제로 교체
                            for i, q in enumerate(validated_questions):
                                if q.get('question_number') == missing_item['question_number']:
                                    validated_questions[i] = enhanced_question
                                    print(f"   ✅ 문제 {missing_item['question_number']}번 특수 요소 보완 완료")
                                    break
            
            # 2단계 정밀 처리 시스템으로 대체
            print(f"\n🎯 2단계 정밀 처리 시스템 시작...")
            
            try:
                enhanced_questions = await self._two_stage_precision_processing(
                    validated_questions, pdf_path, structure_analysis, upload_id
                )
                validated_questions = enhanced_questions
                
            except Exception as ve:
                print(f"⚠️ 2단계 정밀 처리 오류: {ve}")
            
            return validated_questions
            
        except Exception as e:
            print(f"   ⚠️ 특수 요소 검증 오류: {e}")
            return questions
    
    async def _two_stage_precision_processing(
        self, 
        questions: List[Dict], 
        pdf_path: str, 
        structure_analysis: Dict,
        upload_id: int
    ) -> List[Dict]:
        """2단계 정밀 처리 시스템 - 선택지 수와 보기 종류별 차별화 처리"""
        
        try:
            print("🎯 2단계 정밀 처리 시작...")
            
            # 1단계: 문제 분류 및 처리 전략 결정
            categorized_questions = self._categorize_questions_by_complexity(questions, structure_analysis)
            
            # 2단계: 분류별 차별화 처리
            enhanced_questions = []
            
            for category, question_group in categorized_questions.items():
                if not question_group:
                    continue
                
                print(f"📊 {category} 처리 중... ({len(question_group)}개)")
                
                if category == "simple_text":
                    # 단순 텍스트 문제 - 낮은 해상도로 빠른 처리
                    enhanced = await self._process_simple_text_questions(question_group, pdf_path)
                elif category == "with_tables":
                    # 표 포함 문제 - 고해상도 + 표 특화 처리
                    enhanced = await self._process_table_questions(question_group, pdf_path, structure_analysis)
                elif category == "with_code":
                    # 코드 포함 문제 - 초고해상도 + 코드 특화 처리
                    enhanced = await self._process_code_questions(question_group, pdf_path, structure_analysis)
                elif category == "with_diagrams":
                    # 다이어그램 포함 문제 - 최고해상도 + 시각적 분석
                    enhanced = await self._process_diagram_questions(question_group, pdf_path, structure_analysis)
                elif category == "complex_choices":
                    # 복잡한 선택지 - 선택지 수별 맞춤 처리
                    enhanced = await self._process_complex_choice_questions(question_group, pdf_path, structure_analysis)
                else:
                    enhanced = question_group
                
                enhanced_questions.extend(enhanced)
                
                # 진행률 업데이트 (향후 구현 예정)
                # await self._update_progress(upload_id, f"2단계 처리: {category} 완료", 
                #                          len(enhanced_questions) / len(questions) * 100)
                print(f"📊 2단계 처리: {category} 완료 ({len(enhanced_questions)}/{len(questions)})")
            
            print(f"✅ 2단계 정밀 처리 완료: {len(enhanced_questions)}개 문제")
            return enhanced_questions
            
        except Exception as e:
            print(f"❌ 2단계 정밀 처리 실패: {e}")
            return questions
    
    def _categorize_questions_by_complexity(self, questions: List[Dict], structure_analysis: Dict) -> Dict[str, List[Dict]]:
        """문제를 복잡도와 특수 요소별로 분류"""
        
        categories = {
            "simple_text": [],           # 단순 텍스트 문제 (선택지 2-4개)
            "with_tables": [],           # 표 포함 문제
            "with_code": [],             # 코드 포함 문제  
            "with_diagrams": [],         # 다이어그램/이미지 포함 문제
            "complex_choices": []        # 복잡한 선택지 (5개 이상)
        }
        
        # 구조 분석에서 특수 요소 정보 추출
        special_elements = structure_analysis.get("detailed_analysis", {}).get("special_elements", {})
        
        # 표 포함 문제 번호들
        table_questions = set()
        if "tables" in special_elements:
            for table_info in special_elements["tables"]:
                if "question" in table_info:
                    table_questions.add(table_info["question"])
        
        # 코드 포함 문제 번호들  
        code_questions = set()
        if "code_blocks" in special_elements:
            for code_info in special_elements["code_blocks"]:
                if "question" in code_info:
                    code_questions.add(code_info["question"])
        
        # 다이어그램 포함 문제 번호들
        diagram_questions = set()
        visual_elements = special_elements.get("visual_elements_detailed", {})
        for element_type in ["diagram_in_choices", "graph_in_choices", "shape_in_choices", 
                           "diagram_in_passage", "graph_in_passage"]:
            if element_type in visual_elements:
                for visual_info in visual_elements[element_type]:
                    diagram_questions.add(visual_info.get("question", 0))
        
        # 문제별 분류
        for question in questions:
            q_num = question.get("question_number", 0)
            options = question.get("options", [])
            option_count = len(options)
            
            if q_num in table_questions:
                categories["with_tables"].append(question)
            elif q_num in code_questions:
                categories["with_code"].append(question)
            elif q_num in diagram_questions:
                categories["with_diagrams"].append(question)
            elif option_count >= 5:
                categories["complex_choices"].append(question)
            else:
                categories["simple_text"].append(question)
        
        # 분류 결과 출력
        for category, items in categories.items():
            if items:
                q_nums = [q.get("question_number") for q in items]
                print(f"📋 {category}: {len(items)}개 문제 - {q_nums}")
        
        return categories
    
    async def _process_simple_text_questions(self, questions: List[Dict], pdf_path: str) -> List[Dict]:
        """단순 텍스트 문제 처리 (2x 해상도)"""
        return questions  # 기존 추출 결과 유지
    
    async def _process_table_questions(self, questions: List[Dict], pdf_path: str, structure_analysis: Dict) -> List[Dict]:
        """표 포함 문제 특화 처리 (8x 해상도)"""
        
        enhanced_questions = []
        
        for question in questions:
            try:
                q_num = question.get("question_number", 0)
                page_num = question.get("page_number", 1)
                
                print(f"📊 문제 {q_num}번 표 특화 처리...")
                
                # 8배 고해상도로 표 데이터 정밀 추출
                doc = fitz.open(pdf_path)
                page = doc[page_num - 1]
                mat = fitz.Matrix(8, 8)  # 표 처리용 8배 해상도
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                doc.close()
                
                # 표 특화 프롬프트
                table_prompt = f"""📊 표 데이터 정밀 추출 (문제 {q_num}번)

🎯 **표 처리 전용 모드**:
- 표의 모든 셀 데이터를 정확히 추출
- 숫자는 소수점까지 완벽하게 보존
- 헤더와 데이터 행을 구분하여 추출
- 표 구조를 완전히 보존

📋 **추출 방법**:
1. 표 헤더 식별 및 추출
2. 각 데이터 행의 모든 셀 값 추출
3. P1, P2, P3 등의 프로세스 데이터 완전 추출
4. 계산 관련 숫자 (도착시간, 실행시간 등) 정확 추출

🔢 **숫자 정확성**:
- 8.2 → 8.2 (소수점 보존)
- 9.4 → 9.4 (소수점 보존)
- 정수는 정수로, 소수는 소수로 정확히

🚨 **선택지 오인식 방지**:
- ①②③④⑤ 같은 동그라미 숫자는 선택지입니다! 문제 번호가 아닙니다!
- 1)2)3)4)5) 같은 괄호 숫자도 선택지입니다! 문제 번호가 아닙니다!
- 문제 {q_num}번 하나만 추출하세요! 선택지를 별개 문제로 만들지 마세요!

JSON 형식으로 문제와 선택지를 정확히 추출하세요."""

                messages = [
                    {"role": "system", "content": "표 데이터 정밀 추출 전문가. 숫자와 표 구조를 완벽하게 보존."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": table_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64.b64encode(img_data).decode()}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ]
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=4000,
                    temperature=0.0
                )
                
                # 응답 처리 및 기존 문제 정보 업데이트
                enhanced_question = self._enhance_question_with_table_data(
                    question, response.choices[0].message.content
                )
                enhanced_questions.append(enhanced_question)
                
            except Exception as e:
                print(f"⚠️ 문제 {q_num}번 표 처리 실패: {e}")
                enhanced_questions.append(question)
        
        return enhanced_questions
    
    async def _process_code_questions(self, questions: List[Dict], pdf_path: str, structure_analysis: Dict) -> List[Dict]:
        """코드 포함 문제 특화 처리 (16x 해상도)"""
        
        enhanced_questions = []
        
        for question in questions:
            try:
                q_num = question.get("question_number", 0)
                page_num = question.get("page_number", 1)
                
                print(f"💻 문제 {q_num}번 코드 특화 처리...")
                
                # 16배 초고해상도로 코드 정밀 추출
                doc = fitz.open(pdf_path)
                page = doc[page_num - 1]
                mat = fitz.Matrix(16, 16)  # 코드 처리용 16배 해상도
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                doc.close()
                
                # 코드 특화 프롬프트
                code_prompt = f"""💻 코드 정밀 추출 (문제 {q_num}번)

🎯 **코드 처리 전용 모드**:
- 코드의 모든 문법 요소를 정확히 추출
- 변수명, 함수명을 정확히 보존
- 들여쓰기와 공백을 완벽하게 유지
- 세미콜론, 괄호, 연산자 정확히 추출

📋 **추출 방법**:
1. 코드 블록 전체를 정확히 식별
2. 각 라인의 들여쓰기 보존
3. 변수명과 값을 정확히 추출
4. 실행 결과나 출력값 정확히 추출

🔤 **문법 정확성**:
- 변수명: i, j, sum, result 등 정확히
- 연산자: ++, --, +=, == 등 정확히  
- 값: 문자열, 숫자, 불린 등 정확히

🚨 **선택지 오인식 방지**:
- ①②③④⑤ 같은 동그라미 숫자는 선택지입니다! 문제 번호가 아닙니다!
- 1)2)3)4)5) 같은 괄호 숫자도 선택지입니다! 문제 번호가 아닙니다!
- 문제 {q_num}번 하나만 추출하세요! 선택지를 별개 문제로 만들지 마세요!

JSON 형식으로 문제와 선택지를 정확히 추출하세요."""

                messages = [
                    {"role": "system", "content": "코드 정밀 추출 전문가. 문법과 구조를 완벽하게 보존."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": code_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64.b64encode(img_data).decode()}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ]
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=4000,
                    temperature=0.0
                )
                
                # 응답 처리 및 기존 문제 정보 업데이트
                enhanced_question = self._enhance_question_with_code_data(
                    question, response.choices[0].message.content
                )
                enhanced_questions.append(enhanced_question)
                
            except Exception as e:
                print(f"⚠️ 문제 {q_num}번 코드 처리 실패: {e}")
                enhanced_questions.append(question)
        
        return enhanced_questions
    
    async def _process_diagram_questions(self, questions: List[Dict], pdf_path: str, structure_analysis: Dict) -> List[Dict]:
        """다이어그램 포함 문제 특화 처리 (최고 해상도)"""
        
        enhanced_questions = []
        
        for question in questions:
            try:
                q_num = question.get("question_number", 0)
                page_num = question.get("page_number", 1)
                
                print(f"🎨 문제 {q_num}번 다이어그램 특화 처리...")
                
                # 최고 해상도로 시각적 요소 정밀 추출
                doc = fitz.open(pdf_path)
                page = doc[page_num - 1]
                mat = fitz.Matrix(20, 20)  # 다이어그램 처리용 최고 해상도
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                doc.close()
                
                # 다이어그램 특화 프롬프트
                diagram_prompt = f"""🎨 다이어그램/시각적 요소 정밀 분석 (문제 {q_num}번)

🎯 **시각적 분석 전용 모드**:
- 다이어그램의 모든 구성 요소 식별
- 화살표, 연결선, 도형의 관계 파악
- 텍스트 라벨과 숫자 정확히 추출
- 그래프의 축, 범례, 데이터 포인트 추출

📋 **분석 방법**:
1. 시각적 요소의 전체 구조 파악
2. 각 요소간의 연결 관계 분석
3. 텍스트와 숫자 라벨 정확 추출
4. 선택지에 포함된 시각적 차이점 식별

🔍 **정확성 포인트**:
- 화살표 방향과 연결점
- 도형의 모양과 크기 관계
- 그래프 데이터의 수치값
- 네트워크 구조의 연결 상태

🚨 **선택지 오인식 방지**:
- ①②③④⑤ 같은 동그라미 숫자는 선택지입니다! 문제 번호가 아닙니다!
- 1)2)3)4)5) 같은 괄호 숫자도 선택지입니다! 문제 번호가 아닙니다!
- 문제 {q_num}번 하나만 추출하세요! 선택지를 별개 문제로 만들지 마세요!

JSON 형식으로 문제와 선택지를 정확히 추출하세요."""

                messages = [
                    {"role": "system", "content": "시각적 요소 분석 전문가. 다이어그램과 그래프를 정확히 해석."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": diagram_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64.b64encode(img_data).decode()}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ]
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=4000,
                    temperature=0.0
                )
                
                # 응답 처리 및 기존 문제 정보 업데이트
                enhanced_question = self._enhance_question_with_diagram_data(
                    question, response.choices[0].message.content
                )
                enhanced_questions.append(enhanced_question)
                
            except Exception as e:
                print(f"⚠️ 문제 {q_num}번 다이어그램 처리 실패: {e}")
                enhanced_questions.append(question)
        
        return enhanced_questions
    
    async def _process_complex_choice_questions(self, questions: List[Dict], pdf_path: str, structure_analysis: Dict) -> List[Dict]:
        """복잡한 선택지 문제 처리 (선택지 5개 이상)"""
        
        enhanced_questions = []
        
        for question in questions:
            try:
                q_num = question.get("question_number", 0)
                page_num = question.get("page_number", 1)
                option_count = len(question.get("options", []))
                
                print(f"🎯 문제 {q_num}번 복잡 선택지 처리 ({option_count}개)...")
                
                # 선택지 수에 따른 해상도 조정
                resolution_scale = min(12, 8 + option_count)  # 최대 12배
                
                doc = fitz.open(pdf_path)
                page = doc[page_num - 1]
                mat = fitz.Matrix(resolution_scale, resolution_scale)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                doc.close()
                
                # 2단계 정밀 처리 특화 프롬프트 (강화됨)
                complex_prompt = f"""🎯 2단계 정밀 선택지 추출 (문제 {q_num}번)

🚨 **1차 처리에서 놓친 문제 정확 보완**:
- 선택지 개수: {option_count}개 (예상)
- 해상도: {resolution_scale}배 (초고해상도)
- 목표: 100% 정확한 선택지 추출

🔍 **정밀 추출 단계**:
1️⃣ 먼저 문제 {q_num}번을 찾으세요
2️⃣ 문제 지문과 선택지를 명확히 구분하세요
3️⃣ 모든 선택지를 빠뜨리지 말고 추출하세요
4️⃣ 보기/표/코드가 있다면 따로 추출하세요

📋 **선택지 마커 완전 가이드**:
✅ **한국어 시험 표준**: ①, ②, ③, ④, ⑤
✅ **일반 형식**: 1), 2), 3), 4), 5)
✅ **영어 형식**: A), B), C), D), E)
⚠️ **주의**: 점(.) 대신 괄호()) 사용하는 경우도 있음

🔢 **숫자 선택지 초정밀 처리** (매우 중요!):
예시 1: ① 7.2    → "① 7.2" (소수점 보존)
예시 2: ② 15개   → "② 15개" (단위 포함)
예시 3: ③ x=10   → "③ x=10" (수식 완전 보존)
예시 4: ④ 80%    → "④ 80%" (퍼센트 보존)
🚨 **절대 금지**: 7.2 → 7, 15개 → 15, 80% → 80 같은 변경

📖 **보기/지문/표 정밀 추출**:
🔍 **찾을 것들**:
- <보기> 또는 [보기] 마크
- 표 (| 기호로 구성된 표)
- 코드 블록 (public, class, for, while 등)
- 다이어그램/그림 설명
- 수식 집합
⭐ **보기 위치**: 보통 문제 지문 앞 또는 중간에 있음
⭐ **보기 길이**: 보통 2줄 이상의 긴 내용

💡 **선택지 vs 문제지문 구분법**:
- 문제 지문: 길고 설명적, 질문으로 끝남
- 선택지: 짧고 답변 형태, ①②③④ 마커로 시작
- 보기: 표/코드/데이터, 문제와 선택지 사이

🚨 **2단계 처리 특별 지침**:
✅ 1차에서 놓친 선택지 모두 찾기
✅ 숫자 선택지 원본 그대로 보존
✅ 보기 내용 완전 추출
❌ 선택지를 문제 텍스트에 혼합 금지
❌ 보기를 선택지로 착각 금지
❌ 숫자/기호 임의 변경 금지

📊 **출력 JSON 형식** (반드시 이 구조로):
```json
{{
  "question_number": {q_num},
  "question_text": "순수한 문제 지문만 (선택지/보기 제외)",
  "passage": "보기/표/코드/다이어그램 (없으면 \"\")",
  "options": ["① 완전한선택지1", "② 완전한선택지2", "③ 완전한선택지3", "④ 완전한선택지4"],
  "page_number": {page_num},
  "extraction_confidence": "high",
  "processing_notes": "2단계 정밀 추출 완료"
}}
```

⚡ **성공 기준**:
- 모든 선택지 마커 정확 인식
- 숫자 선택지 원본 완전 보존
- 보기와 선택지 완벽 분리
- 문제 텍스트에서 선택지 완전 제거"""

                messages = [
                    {"role": "system", "content": "선택지 정밀 추출 전문가. 실제 선택지 개수를 정확히 파악하고 숫자/보기 내용을 완벽 보존."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": complex_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64.b64encode(img_data).decode()}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ]
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=5000,
                    temperature=0.0
                )
                
                # 응답 처리 및 기존 문제 정보 업데이트
                enhanced_question = self._enhance_question_with_complex_choices(
                    question, response.choices[0].message.content, option_count
                )
                enhanced_questions.append(enhanced_question)
                
            except Exception as e:
                print(f"⚠️ 문제 {q_num}번 복잡 선택지 처리 실패: {e}")
                enhanced_questions.append(question)
        
        return enhanced_questions

    async def _re_extract_with_template(self, question_template: Dict, pdf_path: str, page_num: int, upload_id: int) -> Optional[Dict]:
        """템플릿 기반 정밀 재추출"""
        
        try:
            q_num = question_template.get('question_number')
            extraction_template = question_template.get('extraction_template', {})
            
            print(f"   🎯 문제 {q_num}번 템플릿 기반 재추출")
            
            # 해당 페이지 고해상도 이미지 생성
            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]
            mat = fitz.Matrix(14, 14)  # 14배 해상도
            pix = page.get_pixmap(matrix=mat)
            img_data = self._optimize_image_size(pix)
            doc.close()
            
            # 템플릿 기반 추출 프롬프트
            template_prompt = f"""🎯 문제 {q_num}번 템플릿 기반 정밀 추출

📋 **정확한 추출 템플릿**:
- 문제 시작 마커: "{extraction_template.get('question_start_marker', '')}"
- 문제 끝 마커: "{extraction_template.get('question_end_marker', '')}"  
- 선택지 시작: "{extraction_template.get('choice_start_marker', '①')}"
- 선택지 개수: {question_template.get('choice_count', 4)}개

🎯 **특수 요소 추출**:"""
            
            if extraction_template.get('table_extraction_needed'):
                table_format = extraction_template.get('table_format', 'markdown')
                template_prompt += f"""
- 🔸 표 추출 필수: {table_format} 형식으로
- 🔸 모든 행과 열 완전히 추출"""
            
            if question_template.get('special_elements', {}).get('has_code'):
                template_prompt += f"""
- 🔸 코드 블록 완전히 추출
- 🔸 들여쓰기와 구문 정확히 보존"""
            
            if question_template.get('special_elements', {}).get('has_diagram'):
                template_prompt += f"""
- 🔸 다이어그램 모든 구성요소 설명
- 🔸 연결관계와 구조 상세히 기술"""
            
            template_prompt += f"""

📊 **JSON 출력**:
```json
{{
  "question_number": {q_num},
  "question_text": "지문만 (선택지 제외)",
  "options": ["① 선택지1", "② 선택지2", "③ 선택지3", "④ 선택지4"],
  "has_table": true/false,
  "table_data": "마크다운 표 형식",
  "has_code": true/false,
  "code_content": "코드 내용",
  "has_diagram": true/false,
  "diagram_description": "다이어그램 상세 설명"
}}
```"""
            
            messages = [
                {
                    "role": "system",
                    "content": "템플릿 기반 정밀 문제 추출 전문가입니다. 제공된 템플릿을 정확히 따라 추출하세요."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": template_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64.b64encode(img_data).decode()}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=4000,
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content
            
            # JSON 파싱
            try:
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                    # 선택지 복구 적용
                    result = self._fix_embedded_options(result)
                    return result
            except:
                pass
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ 템플릿 기반 재추출 실패: {e}")
            return None

    async def _re_extract_special_elements(self, missing_item: Dict, pdf_path: str, upload_id: int) -> Optional[Dict]:
        """🔧 **강화된 특수 요소 재추출** - 원본 보존 우선"""
        
        try:
            question_number = missing_item['question_number']
            special_info = missing_item['special_info']
            current_question = missing_item['current_question']
            missing_elements = missing_item['missing_elements']
            
            print(f"   🎯 문제 {question_number}번 특수 요소 집중 재추출: {missing_elements}")
            
            # 해당 문제가 있는 페이지 특정
            page_number = special_info.get('page_location', current_question.get('page_number', 1))
            missing_elements = missing_item['missing_elements']
            page_location = special_info.get('page_location', 1)
            
            # 해당 페이지 고해상도 이미지 생성
            doc = fitz.open(pdf_path)
            page = doc.load_page(page_location - 1)  # 0-based index
            
            # 높은 해상도로 특수 요소 집중 분석 (API 제한 고려)
            mat = fitz.Matrix(14.0, 14.0)  # 14배 해상도
            pix = page.get_pixmap(matrix=mat)
            img_data = self._optimize_image_size(pix)
            
            import base64
            img_b64 = base64.b64encode(img_data).decode('utf-8')
            doc.close()
            
            # 특수 요소 집중 추출 프롬프트
            special_prompt = f"""🔍 문제 {question_number}번 특수 요소 집중 추출

🎯 **목표**: 문제 {question_number}번에서 누락된 특수 요소 추출
⚠️ **누락된 요소**: {', '.join(missing_elements)}

📋 **현재 문제**: {current_question.get('question_text', '')}

🔍 **집중 추출 요청**:"""
            
            if 'table' in missing_elements:
                special_prompt += """
- 📊 **표 데이터**: 모든 행과 열, 헤더, 데이터를 완전히 추출
  → 반드시 마크다운 표 형식으로 추출하세요
  → 예시: | 헤더1 | 헤더2 | 헤더3 |
          |------|------|------|
          | 데이터 1 | 데이터 2 | 데이터 3 |
  → 모든 행과 열을 완전히 보존하세요"""
            
            if 'diagram' in missing_elements:
                special_prompt += """
- 📈 **다이어그램**: 구조, 연결 관계, 노드, 라벨을 상세히 텍스트로 설명
  → 모든 노드와 그 라벨을 나열하세요
  → 노드 간 연결 방향과 관계(화살표, 선)를 명시하세요
  → 다이어그램의 전체적인 배치와 계층 구조를 설명하세요
  → 색상, 모양, 크기 등 시각적 특징도 포함하세요
  → 텍스트로 설명하되 시각적으로 이해 가능하도록 상세히 기록하세요"""
            
            if 'code' in missing_elements:
                special_prompt += """
- 💻 **코드 블록**: 모든 코드, 들여쓰기, 변수명, 함수명 추출
  → 코드의 정확한 구조와 내용을 보존
  → SQL 문(예: SELECT, INSERT, WHERE), 프로그래밍 코드 정확히 추출
  → 선택지에 포함된 코드도 누락없이 추출하세요"""
            
            special_prompt += f"""

📊 **JSON 출력**:
```json
{{
  "question_number": {question_number},
  "enhanced_question_text": "보완된 문제 지문 (특수 요소 포함)",
  "table_data": "표가 있다면 마크다운 표 형식\n| 헤더 | 헤더1 | 헤더2 |\n|------|-----|-----|\n| 데이터 | 값 | 값 |",
  "diagram_description": "다이어그램이 있다면 노드, 연결관계, 라벨, 배치 등 전체 구조를 상세하게 설명",
  "code_content": "코드가 있다면 완전한 코드",
  "has_table": true/false,
  "has_diagram": true/false,
  "has_code": true/false
}}
```"""
            
            # GPT-4V로 특수 요소 재추출
            messages = [
                {
                    "role": "system",
                    "content": "특수 요소(표, 다이어그램, 코드) 집중 추출 전문가입니다."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": special_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_b64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=3000,
                temperature=0.1
            )
            
            # 응답 파싱 및 기존 문제 보완 (특수 요소 전용)
            special_result = self._parse_special_element_response(response.choices[0].message.content)
            
            if special_result and len(special_result) > 0:
                enhanced_data = special_result[0]
                
                # 기존 문제에 특수 요소 정보 추가
                enhanced_question = current_question.copy()
                enhanced_question['question_text'] = enhanced_data.get('enhanced_question_text', current_question.get('question_text'))
                enhanced_question['table_data'] = enhanced_data.get('table_data')
                enhanced_question['code_content'] = enhanced_data.get('code_content')
                enhanced_question['has_table'] = enhanced_data.get('has_table', False)
                enhanced_question['has_diagram'] = enhanced_data.get('has_diagram', False)
                enhanced_question['has_code'] = enhanced_data.get('has_code', False)
                
                if enhanced_data.get('diagram_description'):
                    enhanced_question['question_text'] += f"\n\n[다이어그램 설명: {enhanced_data['diagram_description']}]"
                    enhanced_question['diagram_description'] = enhanced_data['diagram_description']
                
                return enhanced_question
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ 문제 {question_number}번 특수 요소 재추출 실패: {e}")
            return None

    def _validate_and_fix_question_counts(self, structure: Dict):
        """문제 수 불일치 검증 및 수정"""
        
        try:
            # 페이지별 문제 수 집계
            page_analysis = structure.get('page_analysis', [])
            total_questions_in_pages = 0
            all_questions_found = []
            
            for page_info in page_analysis:
                questions_on_page = page_info.get('questions_on_page', [])
                if questions_on_page:
                    all_questions_found.extend(questions_on_page)
                else:
                    # questions_on_page가 없으면 question_density 사용
                    question_density = page_info.get('question_density', 0)
                    total_questions_in_pages += question_density
            
            # 실제 발견된 문제 번호 기준으로 계산
            if all_questions_found:
                actual_max_question = max(all_questions_found)
                actual_question_count = len(set(all_questions_found))  # 중복 제거
                
                # 총 문제 수와 비교
                declared_total = structure.get('analysis_summary', {}).get('total_questions', 0)
                
                # ⚠️ 자동 수정 조건을 엄격하게 제한
                if declared_total != actual_max_question:
                    # 개괄 분석 결과와 비교
                    overview_total = structure.get('global_overview', {}).get('actual_total_questions', 0)
                    
                    if overview_total > 0 and overview_total != actual_max_question:
                        print(f"⚠️ 구조 분석 불일치 발견:")
                        print(f"   개괄 분석: {overview_total}개")
                        print(f"   상세 분석: {declared_total}개") 
                        print(f"   실제 발견: {actual_max_question}개")
                        
                        # 개괄 분석 결과를 더 신뢰
                        if abs(overview_total - actual_max_question) > abs(declared_total - actual_max_question):
                            print(f"🔧 개괄 분석 우선: {declared_total} → {overview_total}")
                            structure['analysis_summary']['total_questions'] = overview_total
                        else:
                            print(f"🔧 실제 발견 반영: {declared_total} → {actual_max_question}")
                            structure['analysis_summary']['total_questions'] = actual_max_question
                    else:
                        print(f"🔧 문제 수 자동 수정: {declared_total} → {actual_max_question}")
                        structure['analysis_summary']['total_questions'] = actual_max_question
                    
                    # 검증 경고 추가
                    if 'validation_warnings' not in structure:
                        structure['validation_warnings'] = []
                    structure['validation_warnings'].append(
                        f"문제 수 불일치: 선언 {declared_total}개 vs 발견 {actual_max_question}개 vs 개괄 {overview_total}개"
                    )
                
                # 누락된 문제 번호 확인
                expected_questions = set(range(1, actual_max_question + 1))
                found_questions = set(all_questions_found)
                missing_questions = expected_questions - found_questions
                
                if missing_questions:
                    structure.setdefault('validation_warnings', []).append(
                        f"누락된 문제 번호: {sorted(list(missing_questions))}"
                    )
            
        except Exception as e:
            print(f"⚠️ 문제 수 검증 실패: {e}")
            if 'validation_warnings' not in structure:
                structure['validation_warnings'] = []
            structure['validation_warnings'].append(f"문제 수 검증 실패: {str(e)}")
    
    def _perform_quality_checks(self, structure: Dict) -> Dict[str, Any]:
        """분석 품질 검사"""
        
        checks = {
            "completeness_score": 0.0,
            "consistency_score": 0.0,
            "reliability_score": 0.0,
            "issues_found": []
        }
        
        try:
            # 완성도 검사
            required_fields = ['analysis_summary', 'page_analysis', 'question_analysis']
            present_fields = sum(1 for field in required_fields if structure.get(field))
            checks['completeness_score'] = present_fields / len(required_fields)
            
            # 일관성 검사
            total_questions_summary = structure.get('analysis_summary', {}).get('total_questions', 0)
            detailed_questions = structure.get('question_analysis', {}).get('detailed_questions', [])
            if total_questions_summary != len(detailed_questions):
                checks['issues_found'].append("문제 개수 불일치")
                checks['consistency_score'] = 0.7
            else:
                checks['consistency_score'] = 1.0
                
            # 신뢰도 점수 계산
            confidence = structure.get('analysis_summary', {}).get('confidence_score', 0.0)
            checks['reliability_score'] = confidence
            
        except Exception as e:
            checks['issues_found'].append(f"품질 검사 오류: {str(e)}")
            
        return checks
    
    def _enhance_processing_strategy(self, structure: Dict) -> Dict[str, Any]:
        """처리 전략 보완"""
        
        try:
            existing_strategy = structure.get('processing_strategy', {})
            
            # 기본 전략 보완
            enhanced_strategy = {
                **existing_strategy,
                "ultra_precise_mode": True,
                "structure_based": True,
                "estimated_processing_time": "5-10분",
                "resource_requirements": "고사양 API 호출",
                "fallback_options": ["레거시 시스템", "단순 청크 처리"]
            }
            
            return enhanced_strategy
            
        except Exception as e:
            print(f"⚠️ 처리 전략 보완 실패: {e}")
            return structure.get('processing_strategy', {})
    
    def _print_detailed_analysis_result(self, structure: Dict):
        """상세 분석 결과 콘솔 출력"""
        
        try:
            print("\n" + "="*80)
            print("🔬 초정밀 PDF 구조 분석 결과")
            print("="*80)
            
            # 기본 요약
            summary = structure.get('analysis_summary', {})
            total_questions = summary.get('total_questions', 0)
            print(f"📄 문서 타입: {summary.get('document_type', '미상')}")
            print(f"📊 총 페이지: {summary.get('total_pages', 0)}페이지") 
            print(f"📝 총 문제 수: {total_questions}문제")
            print(f"🎯 분석 신뢰도: {summary.get('confidence_score', 0.0)*100:.1f}%")
            
            # 페이지별 분석 + 문제 수 검증
            page_analysis = structure.get('page_analysis', [])
            if page_analysis:
                print(f"\n📄 페이지별 분석:")
                total_questions_in_pages = 0
                all_questions_found = []
                
                for page_info in page_analysis:
                    page_num = page_info.get('page_number', 0)
                    page_type = page_info.get('page_type', '미상')
                    question_count = page_info.get('question_density', 0)
                    questions_on_page = page_info.get('questions_on_page', [])
                    
                    print(f"   페이지 {page_num}: {page_type} ({question_count}문제)")
                    
                    # 실제 문제 번호 목록이 있을 때만 카운트
                    if questions_on_page:
                        total_questions_in_pages += len(questions_on_page)
                        all_questions_found.extend(questions_on_page)
                        if len(questions_on_page) > 0:
                            min_q = min(questions_on_page)
                            max_q = max(questions_on_page)
                            print(f"      → 문제 {min_q}~{max_q}번 ({len(questions_on_page)}개)")
                    else:
                        # questions_on_page가 없으면 question_density 사용
                        total_questions_in_pages += question_count
                
                # 문제 수 일치 여부 확인
                print(f"\n🔍 문제 수 검증:")
                print(f"   총 선언된 문제 수: {total_questions}개")
                print(f"   페이지별 문제 수 합계: {total_questions_in_pages}개")
                
                if total_questions != total_questions_in_pages:
                    print(f"   ⚠️ 불일치 감지: {abs(total_questions - total_questions_in_pages)}개 차이")
                    
                    # 누락된 문제 번호 찾기
                    if all_questions_found:
                        expected_questions = set(range(1, total_questions + 1))
                        found_questions = set(all_questions_found)
                        missing_questions = expected_questions - found_questions
                        extra_questions = found_questions - expected_questions
                        
                        if missing_questions:
                            print(f"   📝 누락된 문제: {sorted(list(missing_questions))}")
                        if extra_questions:
                            print(f"   ➕ 추가 발견 문제: {sorted(list(extra_questions))}")
                        
                        # 실제 발견된 최대 문제 번호로 총 문제 수 수정
                        if found_questions:
                            actual_max_question = max(found_questions)
                            print(f"   🎯 실제 최대 문제 번호: {actual_max_question}번")
                            print(f"   💡 권장: 총 문제 수를 {actual_max_question}개로 수정")
                else:
                    print(f"   ✅ 문제 수 일치 확인")
            
            # 선택지 수 통계 출력 (새로 추가)
            self._display_choice_count_statistics(structure)
            
            # 향상된 페이지 경계 분석 결과 출력
            self._display_cross_page_analysis_results(structure)
            
            # 처리 전략
            strategy = structure.get('processing_strategy', {})
            if strategy:
                print(f"\n⚙️ 권장 처리 전략:")
                print(f"   접근법: {strategy.get('recommended_approach', '미정')}")
                print(f"   청크 크기: {strategy.get('chunk_size_recommendation', '미정')}")
                
            # 품질 검사 결과
            quality = structure.get('quality_checks', {})
            if quality:
                print(f"\n✅ 분석 품질:")
                print(f"   완성도: {quality.get('completeness_score', 0)*100:.1f}%")
                print(f"   일관성: {quality.get('consistency_score', 0)*100:.1f}%")
                
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"⚠️ 분석 결과 출력 실패: {e}")
    
    def _display_cross_page_analysis_results(self, structure: Dict):
        """향상된 페이지 경계 분석 결과 출력"""
        
        try:
            # 텍스트 기반 사전 분석 결과 표시
            cross_page_issues = structure.get('cross_page_issues')
            if cross_page_issues and not cross_page_issues.get('error'):
                print(f"\n🔍 향상된 페이지 경계 분석 결과:")
                print("=" * 50)
                
                # 분할된 문제들
                split_questions = cross_page_issues.get('split_questions', [])
                if split_questions:
                    print(f"⚠️ 페이지 간 분할 문제: {len(split_questions)}개")
                    for issue in split_questions[:3]:
                        q_num = issue.get('question_number', '?')
                        print(f"   문제 {q_num}번: {issue.get('issue', '')}")
                
                # 불완전한 선택지들
                incomplete_choices = cross_page_issues.get('incomplete_choices', [])
                if incomplete_choices:
                    print(f"📝 선택지 분할 문제: {len(incomplete_choices)}개")
                    for issue in incomplete_choices[:3]:
                        print(f"   {issue.get('issue', '')}")
                        if issue.get('is_sequential'):
                            print(f"      연속성 확인: {issue.get('current_max')} → {issue.get('next_min')}")
                
                # 새로운 기능: 텍스트/코드 요소 (실제 데이터 검증)
                text_code_elements = cross_page_issues.get('text_code_elements', [])
                if text_code_elements:
                    print(f"🔍 선택지 내 특수 요소: {len(text_code_elements)}개 (실제 분석됨)")
                    
                    # 실제 데이터인지 검증하기 위해 첫 번째 요소 디버깅
                    if len(text_code_elements) > 0:
                        first_element = text_code_elements[0]
                        print(f"   🔍 첫 번째 요소 검증: 페이지 {first_element.get('page')}, "
                              f"선택지 {first_element.get('choice')}, "
                              f"요소 {first_element.get('elements', [])}")
                        print(f"   📝 내용 미리보기: {first_element.get('content_preview', 'N/A')}")
                    
                    choice_summary = {}
                    actual_count = 0
                    for element in text_code_elements:
                        page = element.get('page')
                        choice = element.get('choice')
                        elements = element.get('elements', [])
                        
                        if elements:  # 실제 요소가 있는 경우만 카운트
                            actual_count += 1
                            key = f"페이지 {page}"
                            if key not in choice_summary:
                                choice_summary[key] = []
                            choice_summary[key].append(f"선택지 {choice}: {', '.join(elements)}")
                    
                    print(f"   📊 실제 특수 요소 포함 선택지: {actual_count}개")
                    
                    for page_key, elements in list(choice_summary.items())[:3]:  # 최대 3페이지만 표시
                        print(f"   {page_key}:")
                        for elem in elements[:2]:  # 페이지당 최대 2개씩
                            print(f"      • {elem}")
                
                # 페이지 간 표 분할
                cross_page_tables = cross_page_issues.get('cross_page_tables', [])
                if cross_page_tables:
                    print(f"📊 페이지 간 표 분할: {len(cross_page_tables)}개")
                    for table in cross_page_tables[:2]:
                        print(f"   {table.get('issue', '')}")
                
                # 종합 분석 결과
                detailed_issues = cross_page_issues.get('detailed_issues', {})
                if detailed_issues:
                    total_problems = detailed_issues.get('total_cross_page_problems', 0)
                    severity = detailed_issues.get('severity_level', 'low')
                    print(f"📊 종합 분석: {total_problems}개 이슈 ({severity} 심각도)")
                    
                    recommendations = detailed_issues.get('processing_recommendations', [])
                    if recommendations:
                        print(f"💡 처리 권장사항:")
                        for rec in recommendations[:3]:
                            print(f"   • {rec}")
                
                if not any([split_questions, incomplete_choices, text_code_elements, cross_page_tables]):
                    print("✅ 페이지 경계 문제 없음")
                
                print("=" * 50)
                
        except Exception as e:
            print(f"⚠️ 페이지 경계 분석 결과 출력 실패: {e}")
    
    def _display_choice_count_statistics(self, structure: Dict):
        """선택지 수 통계 출력"""
        
        try:
            print("\n📊 문제별 선택지 수 통계:")
            print("=" * 50)
            
            # detailed_analysis에서 선택지 분석 정보 추출
            detailed_analysis = structure.get('detailed_analysis', {})
            special_elements = detailed_analysis.get('special_elements', {})
            
            # 선택지 수별 상세 분석이 있는지 확인
            choice_analysis = special_elements.get('choice_analysis_detailed', {})
            
            if choice_analysis:
                # 기존 데이터가 있는 경우
                total_questions = 0
                for choice_count, questions in choice_analysis.items():
                    if isinstance(questions, list) and questions:
                        count = len(questions)
                        total_questions += count
                        choice_num = choice_count.replace('questions_with_', '').replace('_choices', '')
                        print(f"📝 {choice_num}개 선택지: {count}개 문제 - {questions}")
                
                print(f"\n📊 총 {total_questions}개 문제 분석 완료")
                
                # 평균 선택지 수 계산
                if total_questions > 0:
                    weighted_sum = 0
                    for choice_count, questions in choice_analysis.items():
                        if isinstance(questions, list) and questions:
                            choice_num = int(choice_count.replace('questions_with_', '').replace('_choices', ''))
                            weighted_sum += choice_num * len(questions)
                    
                    average_choices = weighted_sum / total_questions
                    print(f"📈 평균 선택지 수: {average_choices:.1f}개")
                    
            else:
                # 기본 추정치 제공
                total_questions = structure.get('analysis_summary', {}).get('total_questions', 0)
                print(f"📝 분석 대기 중... (총 {total_questions}개 문제)")
                print("   상세 선택지 분석은 문제 추출 과정에서 수행됩니다")
            
            # 특수 요소가 있는 문제들의 선택지 특성
            special_question_types = ['tables', 'code_blocks', 'visual_elements_detailed']
            for element_type in special_question_types:
                if element_type in special_elements:
                    elements = special_elements[element_type]
                    if elements:
                        if element_type == 'tables':
                            table_questions = [elem.get('question') for elem in elements if elem.get('question')]
                            if table_questions:
                                print(f"📊 표 포함 문제({len(table_questions)}개): 선택지 정밀 추출 필요 - {table_questions}")
                        elif element_type == 'code_blocks':
                            code_questions = [elem.get('question') for elem in elements if elem.get('question')]
                            if code_questions:
                                print(f"💻 코드 포함 문제({len(code_questions)}개): 문법 정확성 중요 - {code_questions}")
                        elif element_type == 'visual_elements_detailed':
                            visual_questions = []
                            for visual_type in ['diagram_in_choices', 'graph_in_choices', 'shape_in_choices']:
                                if visual_type in elements:
                                    visual_questions.extend([elem.get('question') for elem in elements[visual_type] if elem.get('question')])
                            if visual_questions:
                                visual_questions = list(set(visual_questions))  # 중복 제거
                                print(f"🎨 시각적 선택지 문제({len(visual_questions)}개): 고해상도 처리 필요 - {visual_questions}")
            
            print("=" * 50)
            
        except Exception as e:
            print(f"⚠️ 선택지 수 통계 출력 실패: {e}")
    
    def _enhance_question_with_table_data(self, original_question: Dict, api_response: str) -> Dict:
        """표 데이터로 문제 정보 향상"""
        
        try:
            # JSON 응답 파싱
            import json
            import re
            
            # JSON 블록 추출
            json_match = re.search(r'```json\s*(.*?)\s*```', api_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = api_response
            
            parsed_response = json.loads(json_str)
            
            # 기존 문제 정보를 복사하고 향상된 데이터로 업데이트
            enhanced_question = original_question.copy()
            
            if isinstance(parsed_response, dict):
                # 단일 문제 응답
                if "question_text" in parsed_response:
                    enhanced_question["question_text"] = parsed_response["question_text"]
                if "options" in parsed_response:
                    enhanced_question["options"] = parsed_response["options"]
                if "table_data" in parsed_response:
                    enhanced_question["table_data"] = parsed_response["table_data"]
                    
            elif isinstance(parsed_response, list) and len(parsed_response) > 0:
                # 다중 문제 응답 중 첫 번째
                first_question = parsed_response[0]
                if "question_text" in first_question:
                    enhanced_question["question_text"] = first_question["question_text"]
                if "options" in first_question:
                    enhanced_question["options"] = first_question["options"]
                if "table_data" in first_question:
                    enhanced_question["table_data"] = first_question["table_data"]
            
            # 처리 메타데이터 추가
            enhanced_question["processing_enhanced"] = "table_specialized"
            enhanced_question["enhancement_timestamp"] = str(int(time.time()))
            
            return enhanced_question
            
        except Exception as e:
            print(f"⚠️ 표 데이터 향상 실패: {e}")
            return original_question
    
    def _enhance_question_with_code_data(self, original_question: Dict, api_response: str) -> Dict:
        """코드 데이터로 문제 정보 향상"""
        
        try:
            import json
            import re
            
            # JSON 응답 파싱
            json_match = re.search(r'```json\s*(.*?)\s*```', api_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = api_response
            
            parsed_response = json.loads(json_str)
            
            # 기존 문제 정보를 복사하고 향상된 데이터로 업데이트
            enhanced_question = original_question.copy()
            
            if isinstance(parsed_response, dict):
                # 단일 문제 응답
                if "question_text" in parsed_response:
                    enhanced_question["question_text"] = parsed_response["question_text"]
                if "options" in parsed_response:
                    enhanced_question["options"] = parsed_response["options"]
                if "code_block" in parsed_response:
                    enhanced_question["code_block"] = parsed_response["code_block"]
                    
            elif isinstance(parsed_response, list) and len(parsed_response) > 0:
                # 다중 문제 응답 중 첫 번째
                first_question = parsed_response[0]
                if "question_text" in first_question:
                    enhanced_question["question_text"] = first_question["question_text"]
                if "options" in first_question:
                    enhanced_question["options"] = first_question["options"]
                if "code_block" in first_question:
                    enhanced_question["code_block"] = first_question["code_block"]
            
            # 처리 메타데이터 추가
            enhanced_question["processing_enhanced"] = "code_specialized"
            enhanced_question["enhancement_timestamp"] = str(int(time.time()))
            
            return enhanced_question
            
        except Exception as e:
            print(f"⚠️ 코드 데이터 향상 실패: {e}")
            return original_question
    
    def _enhance_question_with_diagram_data(self, original_question: Dict, api_response: str) -> Dict:
        """다이어그램 데이터로 문제 정보 향상"""
        
        try:
            import json
            import re
            
            # JSON 응답 파싱
            json_match = re.search(r'```json\s*(.*?)\s*```', api_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = api_response
            
            parsed_response = json.loads(json_str)
            
            # 기존 문제 정보를 복사하고 향상된 데이터로 업데이트
            enhanced_question = original_question.copy()
            
            if isinstance(parsed_response, dict):
                # 단일 문제 응답
                if "question_text" in parsed_response:
                    enhanced_question["question_text"] = parsed_response["question_text"]
                if "options" in parsed_response:
                    enhanced_question["options"] = parsed_response["options"]
                if "diagram_description" in parsed_response:
                    enhanced_question["diagram_description"] = parsed_response["diagram_description"]
                    
            elif isinstance(parsed_response, list) and len(parsed_response) > 0:
                # 다중 문제 응답 중 첫 번째
                first_question = parsed_response[0]
                if "question_text" in first_question:
                    enhanced_question["question_text"] = first_question["question_text"]
                if "options" in first_question:
                    enhanced_question["options"] = first_question["options"]
                if "diagram_description" in first_question:
                    enhanced_question["diagram_description"] = first_question["diagram_description"]
            
            # 처리 메타데이터 추가
            enhanced_question["processing_enhanced"] = "diagram_specialized"
            enhanced_question["enhancement_timestamp"] = str(int(time.time()))
            
            return enhanced_question
            
        except Exception as e:
            print(f"⚠️ 다이어그램 데이터 향상 실패: {e}")
            return original_question
    
    def _enhance_question_with_complex_choices(self, original_question: Dict, api_response: str, expected_choice_count: int) -> Dict:
        """복잡한 선택지로 문제 정보 향상"""
        
        try:
            import json
            import re
            
            # JSON 응답 파싱
            json_match = re.search(r'```json\s*(.*?)\s*```', api_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = api_response
            
            parsed_response = json.loads(json_str)
            
            # 기존 문제 정보를 복사하고 향상된 데이터로 업데이트
            enhanced_question = original_question.copy()
            
            if isinstance(parsed_response, dict):
                # 단일 문제 응답
                if "question_text" in parsed_response:
                    enhanced_question["question_text"] = parsed_response["question_text"]
                if "options" in parsed_response:
                    new_options = parsed_response["options"]
                    # 선택지 개수 검증
                    if len(new_options) == expected_choice_count:
                        enhanced_question["options"] = new_options
                    else:
                        print(f"⚠️ 선택지 개수 불일치: 예상 {expected_choice_count}개 vs 추출 {len(new_options)}개")
                        # 기존 선택지 유지
                    
            elif isinstance(parsed_response, list) and len(parsed_response) > 0:
                # 다중 문제 응답 중 첫 번째
                first_question = parsed_response[0]
                if "question_text" in first_question:
                    enhanced_question["question_text"] = first_question["question_text"]
                if "options" in first_question:
                    new_options = first_question["options"]
                    # 선택지 개수 검증
                    if len(new_options) == expected_choice_count:
                        enhanced_question["options"] = new_options
                    else:
                        print(f"⚠️ 선택지 개수 불일치: 예상 {expected_choice_count}개 vs 추출 {len(new_options)}개")
            
            # 처리 메타데이터 추가
            enhanced_question["processing_enhanced"] = "complex_choices_specialized"
            enhanced_question["enhancement_timestamp"] = str(int(time.time()))
            enhanced_question["expected_choice_count"] = expected_choice_count
            
            return enhanced_question
            
        except Exception as e:
            print(f"⚠️ 복잡 선택지 향상 실패: {e}")
            return original_question