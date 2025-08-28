"""
구조 파악 중심 3중 교차검증 시스템
- 방법 1: 구조 분석 (기준점)
- 방법 2: 전체 페이지 연결 이미지 분석 
- 방법 3: 개별 페이지 정밀 분석
"""

import fitz
import asyncio
from typing import Dict, Any, List
from PIL import Image
import io
import base64
import json


class TripleCrossValidator:
    """구조 파악 중심 3중 교차검증 시스템"""
    
    def __init__(self, openai_client, claude_client):
        self.openai_client = openai_client
        self.claude_client = claude_client
    
    async def validate_with_triple_cross_check(self, pdf_path: str, structure_analysis: Dict, upload_id: int) -> Dict[str, Any]:
        """구조 분석을 기준으로 3중 교차검증 수행"""
        
        print(f"🔍 3중 교차검증 시작 - Upload {upload_id}")
        print("=" * 60)
        
        # 방법 1: 구조 분석 (이미 완료된 기준점)
        base_structure = structure_analysis
        print("✅ 방법 1: 구조 분석 (기준점) - 완료")
        
        # 방법 2: 전체 연결 이미지 분석 (페이지 경계 문제 해결)
        print("🔍 방법 2: 전체 연결 이미지 분석 시작...")
        connected_analysis = await self._analyze_connected_pages(pdf_path, base_structure)
        
        # 방법 3: 개별 페이지 정밀 분석 (이미지/그림 인식 강화)
        print("🔍 방법 3: 개별 페이지 정밀 분석 시작...")
        precise_analysis = await self._analyze_individual_pages_precisely(pdf_path, base_structure)
        
        # 3중 결과 통합 및 교차검증
        print("🔄 3중 결과 교차검증 및 통합...")
        final_result = await self._cross_validate_and_merge(
            base_structure, connected_analysis, precise_analysis, upload_id
        )
        
        print("=" * 60)
        print("✅ 3중 교차검증 완료!")
        
        return final_result
    
    async def _analyze_connected_pages(self, pdf_path: str, structure: Dict) -> Dict[str, Any]:
        """방법 2: 전체 페이지를 연결한 긴 이미지로 분석 (페이지 경계 문제 해결)"""
        
        try:
            # 문제 페이지들만 추출 (1-4페이지)
            question_pages = []
            page_analysis = structure.get('page_analysis', [])
            
            for page in page_analysis:
                if page.get('page_type') == 'pure_questions':
                    question_pages.append(page.get('page_number'))
            
            if not question_pages:
                return {"method": "connected_pages", "success": False, "error": "문제 페이지 없음"}
            
            print(f"   📄 연결 대상 페이지: {question_pages}")
            
            # 모든 문제 페이지를 세로로 연결한 긴 이미지 생성
            connected_image = await self._create_connected_image(pdf_path, question_pages)
            
            if not connected_image:
                return {"method": "connected_pages", "success": False, "error": "이미지 생성 실패"}
            
            # 연결 이미지로 페이지 경계 문제 분석
            prompt = self._create_connected_analysis_prompt(structure, question_pages)
            
            messages = [
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{connected_image}"}
                        }
                    ]
                }
            ]
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=4000
            )
            
            result = json.loads(response.choices[0].message.content)
            result["method"] = "connected_pages"
            result["success"] = True
            
            print(f"   ✅ 연결 이미지 분석 완료: {len(result.get('page_boundary_issues', []))}개 경계 문제 발견")
            
            return result
            
        except Exception as e:
            print(f"   ❌ 연결 이미지 분석 실패: {e}")
            return {"method": "connected_pages", "success": False, "error": str(e)}
            
            doc.close()
            
            if not images:
                return ""
            
            # 모든 이미지의 너비를 통일 (가장 넓은 것 기준)
            max_width = max(img.width for img in images)
            total_height = sum(img.height for img in images)
            
            # 연결된 이미지 생성
            connected = Image.new('RGB', (max_width, total_height), 'white')
            
            y_offset = 0
            for img in images:
                # 중앙 정렬로 배치
                x_offset = (max_width - img.width) // 2
                connected.paste(img, (x_offset, y_offset))
                y_offset += img.height
            
            # Base64로 변환
            buffer = io.BytesIO()
            connected.save(buffer, format='PNG', quality=95)
            buffer.seek(0)
            
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except Exception as e:
            print(f"   ❌ 연결 이미지 생성 실패: {e}")
            return ""
    
    def _create_connected_analysis_prompt(self, structure: Dict, pages: List[int]) -> str:
        """연결 이미지 분석용 특화 프롬프트"""
        
        total_questions = structure.get('analysis_summary', {}).get('total_questions', 60)
        
        return f"""
🔍 **페이지 경계 문제 전문 분석기**

이 이미지는 PDF의 페이지 {pages}를 세로로 연결한 것입니다.
총 {total_questions}개 문제가 있어야 합니다.

🎯 **핵심 분석 목표**:
1. **페이지 경계에서 잘린 문제들 찾기**
   - 문제 번호는 있는데 선택지가 부분적으로 누락된 경우
   - 선택지 ①②만 있고 ③④가 다음 페이지에 있는 경우
   
2. **이미지/그림 요소 완전 감지**
   - 문제 지문에 포함된 모든 이미지, 그림, 다이어그램
   - 선택지에 포함된 그래프, 도표, 그림
   - 장식용 이미지와 문제용 이미지 구분
   
3. **선택지 연속성 검증**  
   - 각 문제마다 ①②③④ 모두 있는지 확인
   - 줄바꿈으로 인해 하나의 선택지가 두 줄로 나뉜 경우 감지

⚠️ **중요 검증 포인트**:
- 문제 번호 연속성 (1, 2, 3... 순서대로)
- 각 문제의 선택지 완성도 (보통 4개씩)
- 페이지 경계에서 내용이 잘린 위치

**JSON 응답 형식**:
```json
{{
  "page_boundary_issues": [
    {{
      "question_number": 11,
      "issue_type": "incomplete_choices", 
      "description": "선택지 ③④가 다음 페이지로 넘어감",
      "page_location": "페이지1 끝 → 페이지2 시작"
    }}
  ],
  "image_elements": [
    {{
      "location": "문제 6번 지문",
      "element_type": "table",
      "description": "프로세스 스케줄링 표"
    }}
  ],
  "choice_issues": [
    {{
      "question_number": 25,
      "issue": "하나의 선택지가 두 줄로 분할됨",
      "affected_choice": "② 선택지 내용이 줄바꿈됨"
    }}
  ],
  "total_questions_detected": 60,
  "missing_questions": [],
  "quality_score": 0.95
}}
```
"""
    
    async def _analyze_individual_pages_precisely(self, pdf_path: str, structure: Dict) -> Dict[str, Any]:
        """방법 3: 개별 페이지 정밀 분석 (이미지/그림 인식 강화)"""
        
        try:
            page_analysis = structure.get('page_analysis', [])
            question_pages = [p for p in page_analysis if p.get('page_type') == 'pure_questions']
            
            precise_results = {
                "method": "individual_precise",
                "success": True,
                "page_results": [],
                "image_detections": [],
                "ocr_corrections": []
            }
            
            for page_info in question_pages:
                page_num = page_info.get('page_number')
                print(f"   🔍 페이지 {page_num} 정밀 분석...")
                
                # 초고해상도 이미지 생성 (3배 확대)
                page_image = await self._create_ultra_high_res_image(pdf_path, page_num - 1)
                
                if not page_image:
                    continue
                
                # 이미지/그림 특화 분석 프롬프트
                prompt = self._create_precise_analysis_prompt(page_info, structure)
                
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url", 
                                "image_url": {"url": f"data:image/png;base64,{page_image}"}
                            }
                        ]
                    }
                ]
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    response_format={"type": "json_object"},
                    max_tokens=3000
                )
                
                page_result = json.loads(response.choices[0].message.content)
                page_result["page_number"] = page_num
                precise_results["page_results"].append(page_result)
                
                # 이미지 감지 결과 수집
                if page_result.get("images_found"):
                    precise_results["image_detections"].extend(page_result["images_found"])
                
                print(f"   ✅ 페이지 {page_num} 완료: {len(page_result.get('images_found', []))}개 이미지 요소")
            
            return precise_results
            
        except Exception as e:
            print(f"   ❌ 정밀 분석 실패: {e}")
            return {"method": "individual_precise", "success": False, "error": str(e)}
    
    async def _create_ultra_high_res_image(self, pdf_path: str, page_index: int) -> str:
        """초고해상도 페이지 이미지 생성 (이미지/그림 인식 강화)"""
        
        try:
            doc = fitz.open(pdf_path)
            page = doc.load_page(page_index)
            
            # 3배 고해상도 렌더링
            mat = fitz.Matrix(3.0, 3.0)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            img_data = pix.tobytes("png")
            doc.close()
            
            return base64.b64encode(img_data).decode('utf-8')
            
        except Exception as e:
            print(f"   ❌ 고해상도 이미지 생성 실패: {e}")
            return ""
    
    def _create_precise_analysis_prompt(self, page_info: Dict, structure: Dict) -> str:
        """개별 페이지 정밀 분석용 프롬프트"""
        
        page_num = page_info.get('page_number')
        expected_questions = page_info.get('questions_on_page', [])
        
        return f"""
🔍 **페이지 {page_num} 초정밀 이미지/그림 감지 분석기**

예상 문제: {expected_questions}

🎯 **핵심 분석 목표**:

1. **모든 시각적 요소 완전 감지**:
   - 📊 표, 그래프, 차트 (데이터 포함)
   - 🖼️ 그림, 다이어그램, 도식
   - 🔢 수식, 기호, 특수문자
   - 📈 트리, 네트워크, 플로우차트
   
2. **이미지 위치 및 용도 분류**:
   - 문제 지문 내 이미지
   - 선택지 내 이미지/그래프
   - 장식용 vs 문제용 구분
   
3. **OCR 품질 검증**:
   - 흐릿하거나 작은 글자
   - 특수 기호나 수식
   - 줄바꿈 오인식

**JSON 응답**:
```json
{{
  "images_found": [
    {{
      "location": "문제 6번 지문",
      "type": "table",
      "description": "프로세스 P1, P2, P3 스케줄링 데이터 표",
      "content_detail": "도착시간, 실행시간 포함",
      "is_question_critical": true
    }}
  ],
  "ocr_issues": [
    {{
      "location": "문제 12번 선택지 ②",
      "issue": "특수기호 인식 오류",
      "correction_needed": "→ 기호가 - 로 잘못 인식됨"
    }}
  ],
  "choice_structure_issues": [],
  "page_quality_score": 0.95
}}
```
"""
    
    async def _cross_validate_and_merge(self, base_structure: Dict, connected_analysis: Dict, 
                                      precise_analysis: Dict, upload_id: int) -> Dict[str, Any]:
        """3중 결과 교차검증 및 통합 (구조 분석 중심)"""
        
        print("🔄 3중 교차검증 결과 통합 중...")
        
        # 구조 분석을 기준으로 시작
        integrated_result = base_structure.copy()
        
        # 검증 결과 추가
        validation_report = {
            "triple_validation": {
                "base_method": "structure_analysis",
                "cross_methods": ["connected_pages", "individual_precise"],
                "validation_completed": True,
                "issues_found": [],
                "corrections_applied": [],
                "confidence_boost": 0
            }
        }
        
        try:
            # 연결 이미지 분석 결과 통합
            if connected_analysis.get("success"):
                page_boundary_issues = connected_analysis.get("page_boundary_issues", [])
                if page_boundary_issues:
                    validation_report["triple_validation"]["issues_found"].extend([
                        f"페이지 경계 문제: {len(page_boundary_issues)}건"
                    ])
                    
                    # 기존 page_boundary_analysis에 추가
                    if "page_boundary_analysis" not in integrated_result:
                        integrated_result["page_boundary_analysis"] = {
                            "cross_page_questions": [],
                            "incomplete_questions": [],
                            "split_elements": [],
                            "missing_content": [],
                            "total_issues_found": 0
                        }
                    
                    # 연결 이미지에서 발견한 경계 문제 추가
                    for issue in page_boundary_issues:
                        integrated_result["page_boundary_analysis"]["cross_page_questions"].append({
                            "question_number": issue.get("question_number"),
                            "validation_method": "connected_image",
                            "description": issue.get("description"),
                            "location": issue.get("page_location")
                        })
                    
                    integrated_result["page_boundary_analysis"]["total_issues_found"] = len(page_boundary_issues)
            
            # 정밀 분석 결과 통합
            if precise_analysis.get("success"):
                image_detections = precise_analysis.get("image_detections", [])
                if image_detections:
                    validation_report["triple_validation"]["issues_found"].extend([
                        f"추가 이미지 요소: {len(image_detections)}개"
                    ])
                    
                    # special_elements에 추가
                    if "enhanced_image_analysis" not in integrated_result:
                        integrated_result["enhanced_image_analysis"] = []
                    
                    integrated_result["enhanced_image_analysis"].extend(image_detections)
            
            # 신뢰도 점수 계산
            base_confidence = integrated_result.get("analysis_summary", {}).get("confidence_score", 0.8)
            
            confidence_boost = 0
            if connected_analysis.get("success"):
                confidence_boost += 0.1
            if precise_analysis.get("success"): 
                confidence_boost += 0.1
                
            final_confidence = min(base_confidence + confidence_boost, 1.0)
            integrated_result["analysis_summary"]["confidence_score"] = final_confidence
            validation_report["triple_validation"]["confidence_boost"] = confidence_boost
            
            # 검증 보고서 추가
            integrated_result["validation_report"] = validation_report
            
            self._display_validation_summary(validation_report, integrated_result)
            
            return integrated_result
            
        except Exception as e:
            print(f"❌ 교차검증 통합 실패: {e}")
            return base_structure
    
    def _display_validation_summary(self, validation_report: Dict, result: Dict):
        """검증 결과 요약 출력"""
        
        print("\n🔍 3중 교차검증 결과 요약:")
        print("=" * 50)
        
        issues = validation_report["triple_validation"]["issues_found"]
        if issues:
            print("⚠️ 발견된 문제들:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ 추가 문제 발견되지 않음")
        
        confidence = result.get("analysis_summary", {}).get("confidence_score", 0)
        boost = validation_report["triple_validation"]["confidence_boost"]
        
        print(f"\n📊 신뢰도 점수: {confidence:.1%} (+{boost:.1%} 향상)")
        
        page_boundary = result.get("page_boundary_analysis", {})
        if page_boundary.get("total_issues_found", 0) > 0:
            print(f"🔗 페이지 경계 문제: {page_boundary['total_issues_found']}건")
        
        enhanced_images = result.get("enhanced_image_analysis", [])
        if enhanced_images:
            print(f"🖼️ 추가 이미지 요소: {len(enhanced_images)}개")
        
        print("=" * 50)
    
    async def _create_connected_image(self, pdf_path: str, page_numbers: List[int]) -> str:
        """문제 페이지들을 연결한 긴 이미지 생성"""
        
        try:
            doc = fitz.open(pdf_path)
            page_images = []
            
            # 각 페이지를 고해상도로 변환
            for page_num in page_numbers:
                page = doc.load_page(page_num - 1)  # 0-based index
                
                # 고해상도 렌더링 (2.5배)
                mat = fitz.Matrix(2.5, 2.5)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # PIL Image로 변환
                img_data = pix.tobytes("png")
                from PIL import Image
                page_img = Image.open(io.BytesIO(img_data))
                page_images.append(page_img)
                
                print(f"   📄 페이지 {page_num} 연결용 이미지 생성: {page_img.size}")
            
            doc.close()
            
            if not page_images:
                return ""
            
            # 전체 캔버스 크기 계산
            total_width = max(img.width for img in page_images)
            total_height = sum(img.height for img in page_images)
            
            # 연결된 이미지 생성
            connected_image = Image.new('RGB', (total_width, total_height), 'white')
            
            current_y = 0
            for i, img in enumerate(page_images):
                connected_image.paste(img, (0, current_y))
                current_y += img.height
                print(f"   🔗 페이지 {page_numbers[i]} 연결됨 (y={current_y})")
            
            # Base64로 인코딩
            buffer = io.BytesIO()
            connected_image.save(buffer, format='PNG')
            buffer.seek(0)
            
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            print(f"   ✅ 연결 이미지 완성: {total_width}x{total_height}, {len(image_base64)} bytes")
            return image_base64
            
        except Exception as e:
            print(f"   ❌ 연결 이미지 생성 실패: {e}")
            return ""
    
    def _create_connected_analysis_prompt(self, structure: Dict, question_pages: List[int]) -> str:
        """연결 이미지 분석용 프롬프트"""
        
        expected_questions = structure.get('total_questions', '미상')
        
        return f"""
🔗 **전체 연결 이미지 페이지 경계 문제 분석기** 

**분석 대상**: 페이지 {question_pages} (예상 문제 수: {expected_questions}개)

🎯 **핵심 분석 목표**:

1. **페이지 경계 문제 감지**:
   - 문제가 두 페이지에 걸쳐 있는 경우
   - 선택지가 다음 페이지로 넘어간 경우 (①②만 있고 ③④⑤가 다음 페이지)
   - 표나 그래프가 페이지 경계에 분할된 경우
   - 지문이나 설명이 페이지 끝에서 잘린 경우

2. **누락된 내용 식별**:
   - 페이지별 개별 분석에서 놓칠 수 있는 연결 내용
   - 페이지 하단과 다음 페이지 상단의 연관성
   - 완전한 문제 구조 (문제→지문→선택지) 검증

3. **이미지/표 연속성 확인**:
   - 큰 표가 두 페이지에 걸쳐 있는 경우
   - 다이어그램이 페이지 경계에 분할된 경우

**JSON 응답**:
```json
{{
  "page_boundary_issues": [
    {{
      "question_number": 6,
      "issue_type": "split_table",
      "description": "프로세스 스케줄링 표가 페이지 1-2에 걸쳐 분할됨",
      "page_location": "페이지 1 하단 → 페이지 2 상단",
      "content_missing": "P2, P3 데이터 행이 다음 페이지에 있음"
    }},
    {{
      "question_number": 11,
      "issue_type": "split_choices", 
      "description": "선택지 ③④⑤가 다음 페이지로 넘어감",
      "page_location": "페이지 2 하단 → 페이지 3 상단",
      "content_missing": "선택지 ③④⑤ 완전한 내용"
    }}
  ],
  "image_elements": [
    {{
      "location": "문제 6번 지문",
      "element_type": "table",
      "description": "프로세스 스케줄링 표",
      "completeness": "incomplete - 헤더만 있고 데이터는 다음 페이지"
    }}
  ],
  "choice_issues": [
    {{
      "question_number": 25,
      "issue": "하나의 선택지가 두 줄로 분할됨",
      "affected_choice": "② 선택지 내용이 줄바꿈됨"
    }}
  ],
  "total_questions_detected": 60,
  "missing_questions": [],
  "quality_score": 0.95
}}
```
"""