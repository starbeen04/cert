#!/usr/bin/env python3
"""
🔒 원본 보존 우선 추출 시스템
GPT의 재해석/생성을 방지하고 원본 그대로 추출하는 시스템
"""

import re
import base64
import json
from typing import Dict, List, Optional
import openai
import fitz

class OriginalPreservationExtractor:
    """원본 보존 우선 추출기"""
    
    def __init__(self, openai_client: openai.AsyncOpenAI):
        self.openai_client = openai_client
    
    async def extract_with_original_preservation(
        self, 
        pdf_path: str, 
        page_num: int, 
        question_numbers: List[int]
    ) -> List[Dict]:
        """원본 보존 우선 추출"""
        
        try:
            print(f"🔒 페이지 {page_num} 원본 보존 추출 (문제 {question_numbers})")
            
            # 초고해상도 이미지 생성
            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]
            mat = fitz.Matrix(16, 16)  # 16배 해상도
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            doc.close()
            
            # 원본 보존 전용 프롬프트
            preservation_prompt = self._create_preservation_prompt(question_numbers)
            
            messages = [
                {
                    "role": "system",
                    "content": """당신은 원본 텍스트 보존 전문가입니다.

🔒 **절대 원칙**:
- 보이는 텍스트를 한 글자도 바꾸지 마세요
- 숫자를 다른 숫자로 바꾸지 마세요  
- 선택지를 추가하거나 빼지 마세요
- 내용을 해석하거나 의역하지 마세요
- 없는 내용을 만들어내지 마세요

📸 **복사기 모드**: 보이는 것을 그대로 복사하세요"""
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": preservation_prompt},
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
                max_tokens=8000,
                temperature=0.0  # 창의성 완전 제거
            )
            
            response_text = response.choices[0].message.content
            
            # JSON 파싱 및 검증
            extracted_questions = self._parse_and_verify_response(response_text)
            
            return extracted_questions
            
        except Exception as e:
            print(f"⚠️ 원본 보존 추출 실패: {e}")
            return []
    
    def _create_preservation_prompt(self, question_numbers: List[int]) -> str:
        """원본 보존 전용 프롬프트"""
        
        question_list = ", ".join(map(str, question_numbers))
        
        return f"""🔒 원본 텍스트 완전 보존 추출

🎯 **대상**: 문제 {question_list}번
🔒 **원칙**: 보이는 것을 **완전히 그대로** 복사

🚨 **절대 금지사항** (매우 중요):
1. 숫자 변경 금지: "8.2" → "8" 같은 변경 절대 불가
2. 소수점 제거 금지: "9.4" → "9" 같은 변경 절대 불가  
3. 선택지 개수 조작 금지: 4개 → 5개, 5개 → 4개 절대 불가
4. 선택지 순서 변경 금지: ①②③④ 순서 그대로
5. 문제 지문 의역 금지: 한 단어도 바꾸지 말 것
6. 표 데이터 변경 금지: 숫자나 텍스트 그대로
7. 선택지 내용 재작성 금지: 보이는 그대로만
8. 없는 선택지 생성 금지
9. 문제 번호 변경 금지
10. 마커 형식 변경 금지: ① → 1) 같은 변경 불가

📋 **추출 방법**:
각 문제별로:
1. 문제 번호 확인 (정확히)
2. 문제 지문을 **한 글자도 안 바꾸고** 복사
3. 선택지를 **보이는 개수만큼** 복사
4. **숫자는 소수점까지 정확히** 복사
5. 표나 코드는 **구조 그대로** 복사

📊 **JSON 출력 형식** (절대 이 구조로):
```json
{{
  "questions": [
    {{
      "question_number": 실제_번호,
      "question_text": "원본 지문 그대로 (한글자도 바꾸지 말 것)",
      "options": ["① 원본 그대로", "② 원본 그대로", "③ 원본 그대로", "④ 원본 그대로"],
      "page_number": {len(question_numbers)},
      "extraction_confidence": "high",
      "preservation_notes": "원본에서 보이는 선택지 개수와 내용"
    }}
  ]
}}
```

⚡ **핵심**: 
- 이 이미지를 **복사기**처럼 사용하세요
- **해석하지 말고** **복사**하세요
- **창의성을 발휘하지 말고** **정확성**을 추구하세요"""
    
    def _parse_and_verify_response(self, response_text: str) -> List[Dict]:
        """응답 파싱 및 원본 보존 검증"""
        
        try:
            # JSON 블록 추출
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text
            
            parsed = json.loads(json_str)
            questions = parsed.get('questions', [])
            
            # 원본 보존 검증
            verified_questions = []
            for question in questions:
                if self._verify_preservation_quality(question):
                    verified_questions.append(question)
                else:
                    q_num = question.get('question_number', '?')
                    print(f"⚠️ 문제 {q_num}번 원본 보존 품질 미달")
            
            return verified_questions
            
        except Exception as e:
            print(f"⚠️ 응답 파싱 실패: {e}")
            return []
    
    def _verify_preservation_quality(self, question: Dict) -> bool:
        """원본 보존 품질 검증"""
        
        # 1. 필수 필드 존재 확인
        if not all(key in question for key in ['question_number', 'question_text', 'options']):
            return False
        
        # 2. 선택지 형식 검증 (재해석 방지)
        options = question.get('options', [])
        if not options:
            return False
        
        # 3. 선택지 마커 일관성 검증
        markers = [re.match(r'^([①②③④⑤]|[1-5]\))', opt) for opt in options if opt]
        if not all(markers):
            return False
        
        # 4. 비정상적인 선택지 개수 검증 (보통 2-5개)
        if len(options) < 2 or len(options) > 5:
            print(f"⚠️ 비정상 선택지 개수: {len(options)}개")
            return False
        
        # 5. 내용 길이 검증 (너무 짧으면 누락 의심)
        question_text = question.get('question_text', '').strip()
        if len(question_text) < 10:
            return False
        
        return True
    
    async def re_extract_problematic_questions(
        self, 
        problematic_questions: List[int],
        pdf_path: str,
        page_locations: Dict[int, int]  # {question_number: page_number}
    ) -> List[Dict]:
        """문제가 있는 문제들을 원본 보존 모드로 재추출"""
        
        print(f"🔒 원본 보존 모드 재추출: {problematic_questions}")
        
        re_extracted = []
        
        # 페이지별로 그룹화
        page_groups = {}
        for q_num in problematic_questions:
            page_num = page_locations.get(q_num, 1)
            if page_num not in page_groups:
                page_groups[page_num] = []
            page_groups[page_num].append(q_num)
        
        # 페이지별 재추출
        for page_num, questions in page_groups.items():
            page_results = await self.extract_with_original_preservation(
                pdf_path, page_num, questions
            )
            re_extracted.extend(page_results)
        
        print(f"🔒 원본 보존 재추출 완료: {len(re_extracted)}개 문제")
        return re_extracted