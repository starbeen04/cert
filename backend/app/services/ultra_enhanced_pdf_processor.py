"""
Ultra Enhanced PDF Processor - 근본적 개선 버전
GPT 제안사항을 반영한 Multi-Stage Processing Pipeline
"""

import json
import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
import hashlib

class UltraEnhancedPDFProcessor:
    def __init__(self, claude_client):
        self.claude_client = claude_client
        
    async def process_chunks_ultra(self, chunks: List[str]) -> Dict[str, Any]:
        """
        멀티스테이지 처리 파이프라인:
        1. Layout Analysis (페이지 유형 분석)
        2. Content Extraction (내용 추출)
        3. Cross-page Linking (페이지간 연결 처리)
        4. Quality Validation (품질 검증)
        5. Deduplication (중복 제거)
        """
        
        all_questions = []
        processing_metadata = []
        
        print(f"\n🔥 Ultra Enhanced Processing Pipeline 시작")
        print(f"📊 총 {len(chunks)}개 청크 처리 예정")
        
        # Stage 1: Layout Analysis for all chunks
        print(f"\n=== Stage 1: Layout Analysis ===")
        layout_results = await self._analyze_layouts(chunks)
        
        # Stage 2: Content Extraction (질 높은 페이지만)
        print(f"\n=== Stage 2: Content Extraction ===")
        for chunk_idx, (chunk, layout_result) in enumerate(zip(chunks, layout_results)):
            if layout_result.get("page_type") not in ["questions_only", "mixed"]:
                print(f"⚠️ Skipping chunk {chunk_idx+1}: {layout_result.get('page_type')}")
                continue
            
            questions = await self._extract_questions_from_chunk(chunk_idx, chunk, layout_result)
            all_questions.extend(questions)
            processing_metadata.append({
                "chunk_idx": chunk_idx,
                "layout": layout_result,
                "questions_extracted": len(questions)
            })
        
        print(f"\n=== Stage 3: Cross-page Linking ===")
        # Stage 3: Handle cross-page questions
        linked_questions = await self._handle_cross_page_questions(all_questions, chunks)
        
        print(f"\n=== Stage 4: Quality Validation ===")
        # Stage 4: Comprehensive validation
        validated_questions = await self._comprehensive_validation(linked_questions)
        
        print(f"\n=== Stage 5: Deduplication ===")
        # Stage 5: Advanced deduplication
        final_questions = await self._advanced_deduplication(validated_questions)
        
        # Final report
        print(f"\n📊 Ultra Enhanced Processing 완료:")
        print(f"  - 원본 청크: {len(chunks)}개")
        print(f"  - 처리된 청크: {len([r for r in layout_results if r.get('page_type') in ['questions_only', 'mixed']])}개")
        print(f"  - 추출된 문제: {len(all_questions)}개")
        print(f"  - 연결 처리 후: {len(linked_questions)}개")
        print(f"  - 검증 통과: {len(validated_questions)}개")
        print(f"  - 최종 문제: {len(final_questions)}개")
        
        return {
            "questions": final_questions,
            "processing_metadata": processing_metadata,
            "stage_stats": {
                "raw_extraction": len(all_questions),
                "cross_page_linking": len(linked_questions),
                "validation_passed": len(validated_questions),
                "final_count": len(final_questions)
            }
        }
    
    async def _analyze_layouts(self, chunks: List[str]) -> List[Dict[str, Any]]:
        """Stage 1: 모든 청크의 레이아웃 분석"""
        layout_results = []
        
        for idx, chunk in enumerate(chunks):
            print(f"🔍 Layout analysis {idx+1}/{len(chunks)}")
            
            layout_prompt = f"""당신은 PDF 페이지 레이아웃 분석 전문가입니다. 다음 마크다운 텍스트를 분석하여 페이지의 구조와 특성을 파악해주세요:

```markdown
{chunk[:800] if len(chunk) > 800 else chunk}
```

**분석 기준**:
1. **page_type 판별**:
   - questions_only: 문제 번호(1, 2, 3...)와 선택지(①②③④)가 명확한 시험 문제 페이지
   - answers_only: "해설", "정답", "풀이", "답안"이 주된 내용인 해설 페이지
   - mixed: 문제와 해설이 섞인 페이지
   - empty: 의미있는 내용이 거의 없는 빈 페이지
   - invalid: OCR 오류로 깨진 텍스트가 많은 페이지

2. **특수 콘텐츠 감지**:
   - 표(table): "|" 문자나 정렬된 데이터가 있는지
   - 그림(figure): "그림", "도표", "Figure" 등의 참조가 있는지
   - 코드(code): 프로그래밍 코드 블록이 있는지

3. **품질 평가**:
   - high: 완전한 문제들이 깔끔하게 정리됨
   - medium: 일부 불완전하거나 깨진 부분 있음
   - low: 대부분 깨지거나 의미를 파악하기 어려움

다음 JSON 형태로만 답변하세요:
{{
  "page_type": "questions_only|answers_only|mixed|empty|invalid",
  "layout_style": "single_column|two_column|table_heavy|mixed",
  "question_count_estimate": 0,
  "has_tables": false,
  "has_figures": false,
  "has_code": false,
  "content_quality": "high|medium|low",
  "special_notes": "특이사항 간단히"
}}"""

            try:
                response = await self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=800,
                    temperature=0,
                    messages=[{"role": "user", "content": layout_prompt}]
                )
                
                result_text = response.content[0].text.strip()
                if result_text.startswith('```json'):
                    result_text = result_text[7:-3].strip()
                elif result_text.startswith('```'):
                    result_text = result_text[3:-3].strip()
                
                layout_result = json.loads(result_text)
                layout_results.append(layout_result)
                
                print(f"  ✅ Chunk {idx+1}: {layout_result.get('page_type')} - {layout_result.get('question_count_estimate')} questions")
                
            except Exception as e:
                print(f"  ❌ Layout analysis failed for chunk {idx+1}: {e}")
                layout_results.append({
                    "page_type": "invalid",
                    "content_quality": "low",
                    "question_count_estimate": 0
                })
            
            # API 과부하 방지
            await asyncio.sleep(0.5)
        
        return layout_results
    
    async def _extract_questions_from_chunk(self, chunk_idx: int, chunk: str, layout_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Stage 2: 개별 청크에서 문제 추출 (레이아웃 분석 결과 기반)"""
        
        extraction_prompt = f"""당신은 시험 문제 전문 추출기입니다. 레이아웃 분석 결과를 바탕으로 이 페이지에서 완전한 문제만을 정확히 추출해주세요.

**레이아웃 분석 결과**: 
- 페이지 유형: {layout_result.get('page_type')}
- 예상 문제 수: {layout_result.get('question_count_estimate')}
- 특수 콘텐츠: 표={layout_result.get('has_tables')}, 그림={layout_result.get('has_figures')}, 코드={layout_result.get('has_code')}

**처리할 마크다운**:
```markdown
{chunk}
```

**🎯 정밀 추출 규칙**:

1. **완전한 문제만 추출**:
   - 문제 번호가 명확 (1, 2, 3... 또는 1), 2), 3)...)
   - 완전한 질문 문장 ("~은?", "~는?", "~인가?")
   - 최소 2개 이상의 완전한 선택지 (①②③④)

2. **표/코드/그림 특별 처리**:
   - 표: 전체 표 구조를 passage에 마크다운 테이블로 포함
   - 코드: 원래 들여쓰기와 형식 보존
   - 그림 참조: "다음 그림을 보고..." 같은 내용도 passage에 포함

3. **불완전한 문제 감지**:
   - 선택지가 중간에 끊어진 경우: special_handling = "incomplete_options"
   - 다음 페이지로 이어지는 경우: special_handling = "continues_next_page"
   - 표가 복잡해 제대로 파싱 안된 경우: special_handling = "complex_table"

4. **절대 제외 대상**:
   - "해설:", "정답:", "풀이:" 등이 포함된 해설 내용
   - 선택지가 없거나 1개뿐인 것
   - 문제 텍스트가 너무 짧은 것 (10자 미만)
   - 깨진 OCR 텍스트

**JSON 출력 형식**:
{{
  "questions": [
    {{
      "question_id": "Q{chunk_idx+1:02d}_{idx:03d}",
      "question_number": 1,
      "question_text": "문제 본문 (지문 제외)",
      "passage": "지문, 표, 그림 참조, 코드 등",
      "options": ["① 선택지1", "② 선택지2", "③ 선택지3", "④ 선택지4"],
      "has_table": true,
      "has_code": false,
      "has_figure": false,
      "special_handling": "none|incomplete_options|continues_next_page|complex_table",
      "confidence": "high|medium|low",
      "extraction_notes": "특이사항"
    }}
  ]
}}

**중요**: JSON만 출력하세요. 확신이 없으면 해당 문제는 제외하세요."""

        try:
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0,
                messages=[{"role": "user", "content": extraction_prompt}]
            )
            
            result_text = response.content[0].text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith('```'):
                result_text = result_text[3:-3].strip()
            
            result = json.loads(result_text)
            questions = result.get('questions', [])
            
            print(f"  ✅ Chunk {chunk_idx+1}: {len(questions)} questions extracted")
            for q in questions:
                special = q.get('special_handling', 'none')
                confidence = q.get('confidence', 'unknown')
                print(f"    - Q{q.get('question_number')}: {len(q.get('options', []))} options, {special}, {confidence}")
            
            return questions
            
        except Exception as e:
            print(f"  ❌ Question extraction failed for chunk {chunk_idx+1}: {e}")
            return []
    
    async def _handle_cross_page_questions(self, questions: List[Dict[str, Any]], chunks: List[str]) -> List[Dict[str, Any]]:
        """Stage 3: 페이지간 분할된 문제들을 연결 처리 (연속 이미지 처리 지원)"""
        
        # 연속 처리에서 오는 partial 문제들을 찾기
        partial_start_questions = []  # PARTIAL_START로 표시된 문제들
        partial_end_questions = []    # PARTIAL_END로 표시된 문제들
        complete_questions = []
        incomplete_questions = []
        
        for q in questions:
            question_text = q.get('question_text', '')
            question_id = q.get('question_id', '')
            
            # 연속 처리에서 오는 partial 문제들 감지
            if 'PARTIAL_START' in question_text or 'PARTIAL_START' in question_id:
                partial_start_questions.append(q)
                print(f"🔗 Partial START found: {question_id}")
            elif 'PARTIAL_END' in question_text or 'PARTIAL_END' in question_id:
                partial_end_questions.append(q)
                print(f"🔗 Partial END found: {question_id}")
            elif q.get('special_handling') in ['incomplete_options', 'continues_next_page']:
                incomplete_questions.append(q)
                print(f"🔗 Incomplete question found: Q{q.get('question_number')} - {q.get('special_handling')}")
            else:
                complete_questions.append(q)
        
        # 연속 처리 partial 문제들 병합
        merged_questions = await self._merge_partial_questions(partial_start_questions, partial_end_questions)
        
        if not incomplete_questions and not partial_start_questions and not partial_end_questions:
            print("✅ No cross-page questions found")
            return questions
        
        # 기존 방식의 연결 처리 로직 (호환성 유지)
        print(f"🔗 Processing {len(incomplete_questions)} incomplete questions...")
        
        for incomplete_q in incomplete_questions:
            q_num = incomplete_q.get('question_number')
            
            # 다음 청크에서 같은 번호의 완전한 문제 찾기
            for complete_q in complete_questions:
                if (complete_q.get('question_number') == q_num and 
                    len(complete_q.get('options', [])) >= 3):
                    
                    # 불완전한 것을 완전한 것으로 교체
                    print(f"  ✅ Linked Q{q_num} across pages")
                    incomplete_q.update(complete_q)
                    incomplete_q['special_handling'] = 'linked_from_continuous_processing'
                    break
        
        # 모든 결과 병합
        all_linked = complete_questions + incomplete_questions + merged_questions
        print(f"🔗 Cross-page linking completed: {len(all_linked)} total questions")
        print(f"  - Complete questions: {len(complete_questions)}")
        print(f"  - Incomplete questions processed: {len(incomplete_questions)}")
        print(f"  - Merged from partials: {len(merged_questions)}")
        
        return all_linked
    
    async def _merge_partial_questions(self, partial_starts: List[Dict], partial_ends: List[Dict]) -> List[Dict]:
        """연속 처리에서 분할된 partial 문제들을 병합"""
        merged = []
        
        if not partial_starts and not partial_ends:
            return merged
            
        print(f"🔗 Merging {len(partial_starts)} partial starts with {len(partial_ends)} partial ends")
        
        # 문제 번호를 기준으로 start와 end 매칭
        start_by_number = {}
        end_by_number = {}
        
        # partial start 문제들 정리
        for start_q in partial_starts:
            # 문제 번호 추출 시도
            question_text = start_q.get('question_text', '')
            question_number = self._extract_question_number_from_text(question_text)
            if question_number:
                start_by_number[question_number] = start_q
        
        # partial end 문제들 정리  
        for end_q in partial_ends:
            question_text = end_q.get('question_text', '')
            question_number = self._extract_question_number_from_text(question_text)
            if question_number:
                end_by_number[question_number] = end_q
        
        # 매칭되는 start-end 쌍들 병합
        for q_num in start_by_number.keys():
            if q_num in end_by_number:
                start_q = start_by_number[q_num]
                end_q = end_by_number[q_num]
                
                # 두 부분을 병합하여 완전한 문제 생성
                merged_question = {
                    'question_id': f"MERGED_Q{q_num:02d}",
                    'question_number': q_num,
                    'question_text': self._merge_question_texts(start_q.get('question_text', ''), end_q.get('question_text', '')),
                    'passage': start_q.get('passage', '') + ' ' + end_q.get('passage', ''),
                    'options': self._merge_options(start_q.get('options', []), end_q.get('options', [])),
                    'has_table': start_q.get('has_table', False) or end_q.get('has_table', False),
                    'has_code': start_q.get('has_code', False) or end_q.get('has_code', False),
                    'has_figure': start_q.get('has_figure', False) or end_q.get('has_figure', False),
                    'special_handling': 'merged_from_partials',
                    'confidence': 'high',
                    'extraction_notes': f'Merged from PARTIAL_START and PARTIAL_END in continuous processing'
                }
                
                merged.append(merged_question)
                print(f"  ✅ Successfully merged Q{q_num} from partials")
        
        # 매칭되지 않은 partial들은 경고 출력
        unmatched_starts = set(start_by_number.keys()) - set(end_by_number.keys())
        unmatched_ends = set(end_by_number.keys()) - set(start_by_number.keys())
        
        if unmatched_starts:
            print(f"  ⚠️ Unmatched partial starts: {unmatched_starts}")
        if unmatched_ends:
            print(f"  ⚠️ Unmatched partial ends: {unmatched_ends}")
            
        return merged
    
    def _extract_question_number_from_text(self, text: str) -> Optional[int]:
        """텍스트에서 문제 번호 추출"""
        import re
        # 다양한 문제 번호 패턴 매칭
        patterns = [
            r'문제\s*(\d+)',
            r'Q\s*(\d+)',
            r'^(\d+)\.',
            r'^(\d+)\)',
            r'PARTIAL_(?:START|END)_Q(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None
    
    def _merge_question_texts(self, start_text: str, end_text: str) -> str:
        """문제 텍스트 병합"""
        # PARTIAL 마커 제거
        start_clean = re.sub(r'PARTIAL_START.*?[\n\r]', '', start_text, flags=re.IGNORECASE)
        end_clean = re.sub(r'PARTIAL_END.*?[\n\r]', '', end_text, flags=re.IGNORECASE)
        
        # 두 텍스트를 자연스럽게 연결
        merged = start_clean.strip() + ' ' + end_clean.strip()
        return merged.strip()
    
    def _merge_options(self, start_options: List[str], end_options: List[str]) -> List[str]:
        """선택지 병합 (중복 제거 및 정렬)"""
        all_options = []
        
        # start 옵션들 추가
        for option in start_options:
            if option and option.strip():
                all_options.append(option.strip())
        
        # end 옵션들 추가 (중복 체크)
        for option in end_options:
            if option and option.strip() and option.strip() not in all_options:
                all_options.append(option.strip())
        
        # 선택지 번호 순으로 정렬 시도
        def get_option_number(option_text):
            import re
            patterns = [r'^[①②③④⑤]', r'^[1-5]\)', r'^[A-E]\)', r'^\([1-5]\)', r'^\([A-E]\)']
            for i, pattern in enumerate(patterns):
                if re.match(pattern, option_text):
                    return i
            return 999  # 패턴에 맞지 않는 경우 마지막으로
        
        all_options.sort(key=get_option_number)
        
        return all_options
    
    async def _comprehensive_validation(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stage 4: 포괄적 품질 검증"""
        
        validated = []
        
        for q in questions:
            # 기본 필드 검증
            question_text = q.get('question_text', '').strip()
            options = q.get('options', [])
            question_number = q.get('question_number')
            
            # 검증 기준들
            validations = {
                'has_question_text': len(question_text) >= 10,
                'has_question_number': question_number and question_number > 0,
                'has_sufficient_options': len(options) >= 2,
                'options_have_content': all(len(opt.strip()) >= 3 for opt in options if opt),
                'not_answer_explanation': not any(keyword in question_text.lower() 
                                                for keyword in ['해설', '정답', '풀이', '답안']),
                'valid_option_format': any(pattern in str(options) 
                                         for pattern in ['①', '②', '1)', '2)', 'A)', 'B)'])
            }
            
            # 통과 조건: 모든 기본 검증 통과
            if all(validations.values()):
                q['validation_status'] = 'passed'
                q['validation_details'] = validations
                validated.append(q)
                print(f"✅ Q{question_number}: PASSED ({len(options)} options)")
            else:
                failed_checks = [k for k, v in validations.items() if not v]
                print(f"❌ Q{question_number}: FAILED - {', '.join(failed_checks)}")
        
        print(f"🔍 Validation completed: {len(validated)}/{len(questions)} questions passed")
        return validated
    
    async def _advanced_deduplication(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stage 5: 고급 중복 제거"""
        
        # 문제 번호별로 그룹화
        by_number = {}
        for q in questions:
            num = q.get('question_number')
            if num not in by_number:
                by_number[num] = []
            by_number[num].append(q)
        
        # 중복된 번호들 처리
        final_questions = []
        for num, q_list in by_number.items():
            if len(q_list) == 1:
                final_questions.append(q_list[0])
            else:
                print(f"🔄 Deduplicating Q{num}: {len(q_list)} versions found")
                
                # 가장 완전한 버전 선택 (옵션 수 기준)
                best_q = max(q_list, key=lambda x: len(x.get('options', [])))
                best_q['dedup_status'] = f'selected_from_{len(q_list)}_versions'
                final_questions.append(best_q)
                
                print(f"  ✅ Selected version with {len(best_q.get('options', []))} options")
        
        # 번호 순 정렬
        final_questions.sort(key=lambda x: x.get('question_number', 0))
        
        print(f"🔄 Deduplication completed: {len(final_questions)} unique questions")
        return final_questions