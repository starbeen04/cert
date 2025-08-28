#!/usr/bin/env python3
"""
🔒 내용 변조 방지 및 원본 대조 검증 시스템
GPT가 선택지나 문제를 재해석/생성하지 못하도록 원본 대조 검증
"""

import re
import base64
import difflib
from typing import Dict, List, Optional, Any
import openai
import fitz

class ContentVerificationSystem:
    """원본 대조 기반 내용 변조 방지 시스템"""
    
    def __init__(self, openai_client: openai.AsyncOpenAI):
        self.openai_client = openai_client
    
    async def verify_extracted_content(
        self, 
        extracted_question: Dict, 
        pdf_path: str, 
        page_num: int,
        structure_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """추출된 내용의 원본 대조 검증"""
        
        try:
            q_num = extracted_question.get('question_number')
            print(f"🔒 문제 {q_num}번 원본 대조 검증 중...")
            
            # 1. 원본 이미지에서 직접 텍스트 추출
            original_content = await self._extract_raw_content_from_image(
                pdf_path, page_num, q_num
            )
            
            # 2. 추출된 내용과 원본 대조
            verification_result = self._compare_with_original(
                extracted_question, original_content
            )
            
            # 3. 변조 의심 항목 감지
            tampering_detected = self._detect_content_tampering(
                extracted_question, original_content
            )
            
            return {
                "question_number": q_num,
                "verification_passed": verification_result['match_score'] > 0.85,
                "match_score": verification_result['match_score'],
                "tampering_detected": tampering_detected,
                "issues_found": verification_result['issues'],
                "original_content": original_content,
                "recommendations": self._generate_fix_recommendations(tampering_detected)
            }
            
        except Exception as e:
            print(f"⚠️ 문제 {q_num}번 검증 실패: {e}")
            return {
                "question_number": q_num,
                "verification_passed": False,
                "error": str(e)
            }
    
    async def _extract_raw_content_from_image(
        self, 
        pdf_path: str, 
        page_num: int, 
        question_number: int
    ) -> Dict[str, str]:
        """이미지에서 원본 텍스트 직접 추출 (재해석 금지)"""
        
        # 초고해상도 이미지 생성
        doc = fitz.open(pdf_path)
        page = doc[page_num - 1]
        mat = fitz.Matrix(16, 16)  # 16배 해상도
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        doc.close()
        
        # 원본 대조용 프롬프트 (재해석 금지)
        verification_prompt = f"""🔒 원본 텍스트 추출 (재해석 절대 금지)

🚨 **절대 금지사항**:
- 내용을 해석, 의역, 요약하지 마세요
- 숫자나 문자를 바꾸지 마세요  
- 선택지 개수를 임의로 조정하지 마세요
- 없는 내용을 만들어내지 마세요

🎯 **임무**: 문제 {question_number}번의 **원본 텍스트 그대로** 추출

📝 **추출 방법**:
1. 문제 {question_number}번 찾기
2. 문제 지문을 **한 글자도 바꾸지 말고** 그대로 추출
3. 선택지를 **보이는 그대로** 정확히 추출
4. 표나 코드가 있다면 **원본 구조** 그대로 추출

📊 **JSON 출력**:
```json
{{
  "question_text_raw": "원본 문제 지문 (한 글자도 바꾸지 말 것)",
  "choices_raw": ["① 원본 그대로", "② 원본 그대로", "③ 원본 그대로", "④ 원본 그대로"],
  "table_raw": "표가 있다면 원본 텍스트 그대로",
  "code_raw": "코드가 있다면 원본 그대로",
  "total_choices_found": 실제_선택지_개수
}}
```

⚡ **핵심**: 보이는 것을 **완전히 그대로** 복사하세요. 해석하지 마세요."""
        
        messages = [
            {
                "role": "system", 
                "content": "원본 텍스트 추출 전문가. 재해석이나 의역을 절대 하지 않고 보이는 그대로만 추출."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": verification_prompt},
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
            max_tokens=3000,
            temperature=0.0  # 가장 낮은 창의성
        )
        
        response_text = response.choices[0].message.content
        
        # JSON 파싱
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
        except:
            pass
        
        return {"error": "원본 추출 실패"}
    
    def _compare_with_original(
        self, 
        extracted: Dict, 
        original: Dict
    ) -> Dict[str, Any]:
        """추출된 내용과 원본 대조"""
        
        issues = []
        total_score = 0
        max_score = 100
        
        # 1. 문제 지문 대조 (40점)
        extracted_text = extracted.get('question_text', '').strip()
        original_text = original.get('question_text_raw', '').strip()
        
        if original_text:
            text_similarity = difflib.SequenceMatcher(None, extracted_text, original_text).ratio()
            text_score = text_similarity * 40
            total_score += text_score
            
            if text_similarity < 0.9:
                issues.append(f"문제 지문 불일치 (유사도: {text_similarity:.2f})")
        
        # 2. 선택지 개수 대조 (20점)
        extracted_choices = extracted.get('options', [])
        original_choices = original.get('choices_raw', [])
        original_count = original.get('total_choices_found', len(original_choices))
        
        if len(extracted_choices) == original_count:
            total_score += 20
        else:
            issues.append(f"선택지 개수 불일치: 추출 {len(extracted_choices)}개 vs 원본 {original_count}개")
        
        # 3. 선택지 내용 대조 (30점)
        if extracted_choices and original_choices:
            choice_matches = 0
            for i, (ext_choice, orig_choice) in enumerate(zip(extracted_choices, original_choices)):
                choice_similarity = difflib.SequenceMatcher(None, ext_choice, orig_choice).ratio()
                if choice_similarity > 0.8:
                    choice_matches += 1
                else:
                    issues.append(f"선택지 {i+1} 불일치: '{ext_choice}' vs '{orig_choice}'")
            
            if original_choices:
                choice_score = (choice_matches / len(original_choices)) * 30
                total_score += choice_score
        
        # 4. 특수 요소 대조 (10점)
        if original.get('table_raw') or original.get('code_raw'):
            # 특수 요소 검증 로직
            total_score += 5  # 임시점수
        
        return {
            "match_score": total_score / max_score,
            "issues": issues
        }
    
    def _detect_content_tampering(
        self, 
        extracted: Dict, 
        original: Dict
    ) -> List[str]:
        """내용 변조 감지"""
        
        tampering_signs = []
        
        # 1. 숫자 변조 감지
        extracted_text = str(extracted.get('options', []))
        original_text = str(original.get('choices_raw', []))
        
        extracted_numbers = re.findall(r'\d+\.?\d*', extracted_text)
        original_numbers = re.findall(r'\d+\.?\d*', original_text)
        
        if len(extracted_numbers) != len(original_numbers):
            tampering_signs.append("숫자 개수 변조 의심")
        
        # 2. 선택지 개수 조작 감지
        extracted_count = len(extracted.get('options', []))
        original_count = original.get('total_choices_found', 4)
        
        if extracted_count > original_count:
            tampering_signs.append("선택지 개수 증가 (생성 의심)")
        elif extracted_count < original_count:
            tampering_signs.append("선택지 개수 감소 (누락 의심)")
        
        # 3. 패턴 변조 감지 (①②③④ → 1234 등)
        extracted_markers = re.findall(r'[①②③④⑤]|[1-5]\)', extracted_text)
        original_markers = re.findall(r'[①②③④⑤]|[1-5]\)', original_text)
        
        if set(extracted_markers) != set(original_markers):
            tampering_signs.append("선택지 마커 형식 변조")
        
        return tampering_signs
    
    def _generate_fix_recommendations(self, tampering_detected: List[str]) -> List[str]:
        """수정 권장사항 생성"""
        
        recommendations = []
        
        if "숫자 개수 변조 의심" in tampering_detected:
            recommendations.append("원본 이미지에서 숫자를 정확히 다시 추출하세요")
        
        if "선택지 개수" in str(tampering_detected):
            recommendations.append("원본 이미지에서 선택지 개수를 다시 확인하세요")
        
        if "마커 형식 변조" in str(tampering_detected):
            recommendations.append("원본 선택지 마커(①②③④)를 그대로 사용하세요")
        
        return recommendations

    async def batch_verify_questions(
        self, 
        questions: List[Dict], 
        pdf_path: str, 
        structure_analysis: Dict
    ) -> Dict[str, Any]:
        """전체 문제 일괄 검증"""
        
        print("🔒 추출된 전체 문제 원본 대조 검증 중...")
        
        verification_results = []
        failed_questions = []
        tampering_detected = []
        
        for question in questions:
            page_num = question.get('page_number', 1)
            result = await self.verify_extracted_content(
                question, pdf_path, page_num, structure_analysis
            )
            
            verification_results.append(result)
            
            if not result.get('verification_passed'):
                failed_questions.append(result['question_number'])
            
            if result.get('tampering_detected'):
                tampering_detected.append(result['question_number'])
        
        # 전체 통계
        total_questions = len(questions)
        passed_count = sum(1 for r in verification_results if r.get('verification_passed'))
        pass_rate = passed_count / total_questions if total_questions > 0 else 0
        
        print(f"🔒 검증 결과: {passed_count}/{total_questions}개 통과 (통과율: {pass_rate:.1%})")
        
        if failed_questions:
            print(f"⚠️ 검증 실패: {failed_questions}")
        
        if tampering_detected:
            print(f"🚨 내용 변조 의심: {tampering_detected}")
        
        return {
            "total_questions": total_questions,
            "passed_count": passed_count,
            "pass_rate": pass_rate,
            "failed_questions": failed_questions,
            "tampering_detected": tampering_detected,
            "detailed_results": verification_results
        }