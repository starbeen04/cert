#!/usr/bin/env python3
"""
🎯 단순화된 3단계 PDF 처리 시스템
1단계: PDF 구조 분석
2단계: 구조 기반 정확한 데이터 추출
"""

import re
import base64
import json
from typing import Dict, List, Optional, Any
import openai
import fitz
import asyncio

class SimplePDFProcessor:
    """단순화된 PDF 처리기"""
    
    def __init__(self, openai_client: openai.AsyncOpenAI):
        self.openai_client = openai_client
    
    async def process_pdf_simple(self, pdf_path: str, upload_id: int) -> Dict[str, Any]:
        """3단계 단순화된 PDF 처리"""
        
        print(f"🎯 단순화된 3단계 PDF 처리 시작 - Upload {upload_id}")
        print("=" * 60)
        
        try:
            # 1단계: PDF 구조 분석
            print("📊 1단계: PDF 구조 분석 중...")
            structure_info = await self._analyze_pdf_structure(pdf_path, upload_id)
            
            if not structure_info['success']:
                print("⚠️ 구조 분석 실패, 기본값으로 대체 처리")
                # 기본 구조로 fallback
                structure_info = self._create_default_structure(pdf_path)
                print(f"📋 기본 구조 적용: {structure_info['basic_info']['total_questions']}개 문제 예상")
            
            # 2단계: 구조 기반 데이터 추출
            print("📝 2단계: 구조 기반 데이터 추출 중...")
            extraction_result = await self._extract_data_by_structure(pdf_path, structure_info, upload_id)
            
            return {
                "success": True,
                "structure_analysis": structure_info,
                "extraction_result": extraction_result,
                "total_questions": len(extraction_result.get('questions', [])),
                "processing_method": "simple_3_stage"
            }
            
        except Exception as e:
            print(f"❌ 단순 처리 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_pdf_structure(self, pdf_path: str, upload_id: int) -> Dict[str, Any]:
        """1단계: PDF 구조 분석"""
        
        print(f"🔍 1단계 구조 분석 시작 - Upload {upload_id}")
        
        try:
            # 전체 PDF를 낮은 해상도로 이미지화
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # 모든 페이지를 2배 해상도로 생성
            images_data = []
            for page_num in range(total_pages):
                page = doc[page_num]
                mat = fitz.Matrix(2, 2)  # 2배 해상도
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                images_data.append(base64.b64encode(img_data).decode())
                print(f"   📄 페이지 {page_num + 1} 이미지 생성 완료")
            
            doc.close()
            
            # 구조 분석 프롬프트
            structure_prompt = self._create_structure_analysis_prompt(total_pages)
            
            # 모든 페이지를 한번에 분석
            messages = [
                {
                    "role": "system",
                    "content": "당신은 PDF 구조 분석 전문가입니다. 시험 문제집의 구조를 정확히 파악하세요."
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": structure_prompt}] +
                              [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}", "detail": "low"}} 
                               for img in images_data]
                }
            ]
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=8000,
                temperature=0.0
            )
            
            # 응답 파싱
            response_text = response.choices[0].message.content
            structure_info = self._parse_structure_analysis(response_text)
            
            print("✅ 1단계 구조 분석 완료")
            return structure_info
            
        except Exception as e:
            print(f"❌ 구조 분석 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_structure_analysis_prompt(self, total_pages: int) -> str:
        """구조 분석용 프롬프트"""
        
        return f"""📋 PDF 구조 완전 분석 ({total_pages}페이지)

🎯 **핵심 분석 목표**:
1. 문서 타입 판별 (문제집/이론서/혼합)
2. 총 문제 개수 정확 파악
3. 각 문제별 상세 정보 추출
4. 페이지별 역할 분석
5. 특수 요소 위치 파악

📊 **필수 분석 항목**:

**1️⃣ 기본 정보**:
- 자격증명: (예: 정보처리기사, 네트워크관리사 등)
- 총 문제 수: 정확한 개수
- 첫 문제 번호: (보통 1번)
- 마지막 문제 번호: (실제 확인된 최고 번호)
- 문서 타입: practice_test/theory/mixed

**2️⃣ 페이지별 분석**:
각 페이지마다:
- 페이지 역할: questions/answers/explanations/theory
- 포함된 문제 번호: [시작번호-끝번호] 
- 문제 개수: 실제 카운트
- 특수 요소: tables/images/codes/diagrams

**3️⃣ 문제별 상세 분석**:
각 문제마다:
- 문제 번호: 정확한 번호
- 선택지 개수: 2/3/4/5개
- 보기 유무: 있음/없음
- 보기 형태: 표/코드/다이어그램/텍스트
- 페이지 경계 이슈: 다음페이지로 이어짐/완결
- 특수 요소: 수식/영어/이미지 등

**4️⃣ 특수 문제 식별**:
- 표가 있는 문제: [번호 리스트]
- 코드가 있는 문제: [번호 리스트]  
- 다이어그램이 있는 문제: [번호 리스트]
- 이미지 선택지가 있는 문제: [번호 리스트]
- 페이지 경계 문제: [번호 리스트]

**5️⃣ 선택지 분포 분석**:
- 2개 선택지: [문제 번호들]
- 3개 선택지: [문제 번호들]  
- 4개 선택지: [문제 번호들]
- 5개 선택지: [문제 번호들]

🔍 **정확도 필수사항**:
- 모든 페이지를 꼼꼼히 확인
- 문제 번호 누락 없이 전체 파악
- 보기와 선택지 명확히 구분
- 페이지 경계 문제 정확히 식별

📤 **JSON 출력 형식**:
```json
{{
  "basic_info": {{
    "certificate_name": "자격증명",
    "total_questions": 총문제수,
    "first_question": 첫번호,
    "last_question": 마지막번호,
    "document_type": "practice_test",
    "total_pages": {total_pages}
  }},
  "page_analysis": [
    {{
      "page_number": 1,
      "role": "questions",
      "question_range": "1-15",
      "question_count": 15,
      "questions": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
      "special_elements": ["tables", "codes"],
      "cross_page_issues": []
    }}
  ],
  "question_details": {{
    "1": {{"choices": 4, "has_passage": false, "passage_type": "", "special_elements": [], "page_location": 1}},
    "6": {{"choices": 4, "has_passage": true, "passage_type": "table", "special_elements": ["table"], "page_location": 1}}
  }},
  "special_questions": {{
    "table_questions": [6, 12],
    "code_questions": [24, 33],
    "diagram_questions": [45],
    "cross_page_questions": []
  }},
  "choice_distribution": {{
    "2_choices": [],
    "3_choices": [],
    "4_choices": [1,2,3,4,5,7,8,9,10,11],
    "5_choices": []
  }},
  "success": true
}}
```

⚡ **중요**: 모든 문제를 빠짐없이 정확히 분석하세요!"""

    def _parse_structure_analysis(self, response_text: str) -> Dict[str, Any]:
        """구조 분석 응답 파싱 (강화된 오류 처리)"""
        
        print(f"🔍 구조 분석 응답 길이: {len(response_text)}자")
        print(f"🔍 응답 미리보기: {response_text[:200]}...")
        
        try:
            # 다양한 JSON 블록 패턴 시도
            patterns = [
                r'```json\s*(\{[\s\S]*?\})\s*```',
                r'```\s*(\{[\s\S]*?\})\s*```',
                r'(\{[\s\S]*?\})',
            ]
            
            json_str = None
            for pattern in patterns:
                json_match = re.search(pattern, response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    print(f"✅ JSON 블록 발견: {len(json_str)}자")
                    break
            
            if not json_str:
                print("⚠️ JSON 블록을 찾을 수 없음")
                return {"success": False, "error": "JSON 블록 찾을 수 없음"}
            
            # JSON 정리 (주석 제거, 비정형 수정)
            json_str = self._clean_json_string(json_str)
            
            # JSON 파싱 시도
            structure_data = json.loads(json_str)
            structure_data['success'] = True
            
            print("✅ JSON 파싱 성공")
            return structure_data
                
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 파싱 오류: {e}")
            print(f"⚠️ 문제 영역: {json_str[max(0, e.pos-50):e.pos+50] if json_str and hasattr(e, 'pos') else 'N/A'}")
            
            # 기본값 반환
            return {
                "success": False, 
                "error": f"JSON 파싱 오류: {e}",
                "basic_info": {
                    "total_questions": 60,  # 기본값
                    "document_type": "practice_test"
                }
            }
        
        except Exception as e:
            print(f"⚠️ 예상치 못한 오류: {e}")
            return {"success": False, "error": f"예상치 못한 오류: {e}"}
    
    def _clean_json_string(self, json_str: str) -> str:
        """기본적인 JSON 정리"""
        
        # 주석 제거
        json_str = re.sub(r'//.*', '', json_str)
        
        # 여러 공백 정리
        json_str = re.sub(r'\s+', ' ', json_str)
        
        # 마지막 쉼표 제거
        json_str = re.sub(r',\s*(\]|\})', r'\1', json_str)
        
        return json_str.strip()
    
    def _create_default_structure(self, pdf_path: str) -> Dict[str, Any]:
        """기본 구조 생성 (fallback)"""
        
        try:
            # 기본 PDF 정보 추출
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            doc.close()
            
            # 기본 구조 설정
            questions_per_page = 15  # 평균
            estimated_questions = min(80, total_pages * questions_per_page)
            
            return {
                "success": True,
                "basic_info": {
                    "certificate_name": "정보처리기사",
                    "total_questions": estimated_questions,
                    "first_question": 1,
                    "last_question": estimated_questions,
                    "document_type": "practice_test",
                    "total_pages": total_pages
                },
                "page_analysis": [
                    {
                        "page_number": i + 1,
                        "role": "questions" if i < total_pages - 2 else "answers",
                        "question_range": f"{i*questions_per_page+1}-{min((i+1)*questions_per_page, estimated_questions)}",
                        "question_count": min(questions_per_page, estimated_questions - i*questions_per_page),
                        "questions": list(range(i*questions_per_page+1, min((i+1)*questions_per_page+1, estimated_questions+1))),
                        "special_elements": [],
                        "cross_page_issues": []
                    }
                    for i in range(total_pages) if i*questions_per_page < estimated_questions
                ],
                "question_details": {
                    str(i): {"choices": 4, "has_passage": False, "passage_type": "", "special_elements": [], "page_location": (i-1)//questions_per_page + 1}
                    for i in range(1, estimated_questions + 1)
                },
                "special_questions": {
                    "table_questions": [],
                    "code_questions": [],
                    "diagram_questions": [],
                    "cross_page_questions": []
                },
                "choice_distribution": {
                    "2_choices": [],
                    "3_choices": [],
                    "4_choices": list(range(1, estimated_questions + 1)),
                    "5_choices": []
                }
            }
        
        except Exception as e:
            print(f"⚠️ 기본 구조 생성 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _extract_data_by_structure(self, pdf_path: str, structure_info: Dict, upload_id: int) -> Dict[str, Any]:
        """2단계: 구조 기반 데이터 추출"""
        
        print(f"📝 2단계 데이터 추출 시작 - Upload {upload_id}")
        
        try:
            questions = []
            page_analysis = structure_info.get('page_analysis', [])
            question_details = structure_info.get('question_details', {})
            
            # 문제가 있는 페이지만 처리
            question_pages = [page for page in page_analysis if page.get('role') == 'questions']
            
            for page_info in question_pages:
                page_num = page_info['page_number']
                page_questions = page_info.get('questions', [])
                
                if not page_questions:
                    continue
                
                print(f"   📄 페이지 {page_num} 처리 중 ({len(page_questions)}개 문제)...")
                
                # 페이지별 고해상도 추출
                page_questions_data = await self._extract_page_questions(
                    pdf_path, page_num, page_questions, question_details
                )
                
                questions.extend(page_questions_data)
            
            print(f"✅ 2단계 데이터 추출 완료: {len(questions)}개 문제")
            
            return {
                "success": True,
                "questions": questions,
                "total_extracted": len(questions),
                "extraction_method": "structure_based"
            }
            
        except Exception as e:
            print(f"❌ 데이터 추출 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _extract_page_questions(self, pdf_path: str, page_num: int, question_numbers: List[int], question_details: Dict) -> List[Dict]:
        """페이지별 문제 추출"""
        
        try:
            # 고해상도 이미지 생성
            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]  # 0-based index
            mat = fitz.Matrix(8, 8)  # 8배 해상도
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            doc.close()
            
            # 문제별 상세 정보 수집
            special_questions = []
            regular_questions = []
            
            for q_num in question_numbers:
                q_detail = question_details.get(str(q_num), {})
                if q_detail.get('special_elements') or q_detail.get('has_passage'):
                    special_questions.append(q_num)
                else:
                    regular_questions.append(q_num)
            
            # 추출 프롬프트 생성
            extraction_prompt = self._create_extraction_prompt(question_numbers, question_details)
            
            messages = [
                {
                    "role": "system",
                    "content": "당신은 정확한 문제 추출 전문가입니다. 구조 분석 정보에 따라 각 문제를 완벽히 추출하세요."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": extraction_prompt},
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
                max_tokens=10000,
                temperature=0.0
            )
            
            # 응답 파싱
            response_text = response.choices[0].message.content
            questions_data = self._parse_extraction_result(response_text)
            
            return questions_data
            
        except Exception as e:
            print(f"   ❌ 페이지 {page_num} 추출 실패: {e}")
            return []
    
    def _create_extraction_prompt(self, question_numbers: List[int], question_details: Dict) -> str:
        """데이터 추출용 프롬프트"""
        
        # 문제별 상세 정보 정리
        question_info_text = ""
        for q_num in question_numbers:
            detail = question_details.get(str(q_num), {})
            choices_count = detail.get('choices', 4)
            has_passage = detail.get('has_passage', False)
            passage_type = detail.get('passage_type', '')
            special_elements = detail.get('special_elements', [])
            
            question_info_text += f"- 문제 {q_num}번: {choices_count}개 선택지"
            if has_passage:
                question_info_text += f", 보기({passage_type})"
            if special_elements:
                question_info_text += f", 특수요소({', '.join(special_elements)})"
            question_info_text += "\n"
        
        return f"""📝 정확한 문제 데이터 추출

🎯 **추출 대상**: {len(question_numbers)}개 문제
{question_info_text}

📋 **추출 지침**:
1. 각 문제를 정확한 번호와 함께 추출
2. 문제 지문과 선택지를 명확히 분리
3. 보기가 있는 문제는 보기를 별도 추출
4. 특수 요소(표/코드/다이어그램)는 완전히 보존
5. 선택지 마커(①②③④)를 정확히 유지

⚠️ **절대 금지사항**:
- 문제 번호 변경 금지
- 선택지 내용 수정 금지  
- 숫자나 기호 임의 변경 금지
- 보기와 선택지 혼동 금지

📤 **JSON 출력 형식**:
```json
{{
  "questions": [
    {{
      "question_number": 1,
      "question_text": "정확한 문제 지문",
      "passage": "보기 내용 (없으면 빈 문자열)",
      "options": ["① 선택지1", "② 선택지2", "③ 선택지3", "④ 선택지4"],
      "page_number": 페이지번호,
      "has_table": false,
      "has_code": false,
      "has_diagram": false,
      "extraction_confidence": "high"
    }}
  ]
}}
```

🔍 **정확성 확인**:
- 모든 문제 번호가 요청한 번호와 일치하는지 확인
- 선택지 개수가 구조 분석과 일치하는지 확인
- 특수 요소가 올바르게 추출되었는지 확인"""

    def _parse_extraction_result(self, response_text: str) -> List[Dict]:
        """추출 결과 파싱"""
        
        try:
            # JSON 블록 추출
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                result_data = json.loads(json_str)
                return result_data.get('questions', [])
            else:
                print("⚠️ JSON 블록을 찾을 수 없음")
                return []
                
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 파싱 오류: {e}")
            return []