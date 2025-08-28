"""
Enhanced Prompts Module - LLM 환각 방지 프롬프트
GPT 제안사항에 따른 프롬프트 엔지니어링
"""

class EnhancedPrompts:
    """LLM 환각 방지를 위한 향상된 프롬프트 모음"""
    
    @staticmethod
    def get_layout_analysis_prompt() -> str:
        """레이아웃 분석 프롬프트 - 실제 내용만 분석하도록 강제"""
        return """당신은 PDF 페이지 레이아웃 분석 전문가입니다. 

**중요: 반드시 제공된 텍스트에 실제로 존재하는 내용만 분석하세요. 추측하거나 가정하지 마세요.**

다음 텍스트를 분석하여 페이지의 실제 구조를 파악해주세요:

분석 기준:
1. **page_type 판별** (실제 내용 기준):
   - questions_only: 숫자로 시작하는 문제 번호(1, 2, 3...)와 원형 숫자 선택지(①②③④⑤)가 명확히 보이는 경우에만
   - answers_only: "정답", "해설", "답안", "풀이"라는 단어가 실제로 텍스트에 있는 경우에만
   - mixed: 문제와 해설이 같은 텍스트에 실제로 공존하는 경우에만
   - table_figure: "표", "그림", "도", "|" 문자가 실제로 있는 경우에만
   - unknown: 위 조건에 해당하지 않는 경우

2. **column_count** (실제 확인 가능한 경우만):
   - 텍스트가 명확히 좌우로 분리되어 보이면 2
   - 그렇지 않으면 1

3. **content_density** (실제 측정 가능한 경우만):
   - high: 텍스트 줄 수가 20줄 이상
   - medium: 10-19줄
   - low: 10줄 미만

**절대 금지사항:**
- 텍스트에 없는 내용을 추측하거나 생성하지 마세요
- "아마도", "보통", "일반적으로" 같은 추정 표현 사용 금지
- 빈 영역이나 누락된 부분을 임의로 채우지 마세요

JSON 형식으로만 응답하세요:
{
  "page_type": "실제_확인된_타입",
  "column_count": 실제_숫자,
  "content_density": "실제_측정된_밀도",
  "evidence": {
    "question_markers": ["실제로_발견된_문제_번호들"],
    "choice_markers": ["실제로_발견된_선택지들"], 
    "answer_markers": ["실제로_발견된_답안_키워드들"]
  },
  "confidence": "high|medium|low"
}"""

    @staticmethod
    def get_question_extraction_prompt() -> str:
        """문제 추출 프롬프트 - 정확한 내용만 추출"""
        return """당신은 시험 문제 추출 전문가입니다.

**절대 준수 사항:**
1. 제공된 텍스트에 실제로 있는 내용만 추출하세요
2. 누락된 선택지를 임의로 생성하지 마세요  
3. 불완전한 문제는 PARTIAL로 표시하세요
4. 추측하거나 보완하려 하지 마세요

**문제 추출 규칙:**
- 문제 번호: 숫자 + 마침표 패턴 (예: "1.", "2.")만 인정
- 선택지: ①②③④⑤ 원형 숫자만 인정, 다른 기호 무시
- 문제 텍스트: 문제 번호 다음부터 첫 번째 선택지 전까지
- 불완전 문제: 선택지가 2개 미만이면 PARTIAL 표시

**출력 형식:**
각 문제에 대해 다음 JSON 구조 사용:
{
  "question_number": 실제_숫자,
  "question_text": "실제_텍스트_그대로",
  "choices": [
    {"number": 1, "symbol": "①", "text": "실제_선택지_텍스트"},
    {"number": 2, "symbol": "②", "text": "실제_선택지_텍스트"}
  ],
  "status": "COMPLETE|PARTIAL|INCOMPLETE",
  "extraction_source": "텍스트_원본_일부",
  "issues": ["발견된_문제점들"]
}

**처리할 수 없는 경우:**
- 텍스트가 너무 흐려서 읽을 수 없는 경우: status "UNREADABLE"
- 문제 구조를 파악할 수 없는 경우: status "INVALID_FORMAT"
- 선택지가 전혀 없는 경우: status "NO_CHOICES"

텍스트에서 실제로 확인할 수 있는 내용만 추출하세요."""

    @staticmethod
    def get_cross_page_detection_prompt() -> str:
        """크로스페이지 감지 프롬프트 - 정확한 패턴 감지만"""
        return """당신은 페이지 간 문제 분할 감지 전문가입니다.

**감지 기준 (매우 엄격하게 적용):**
1. **미완료 문제 패턴:**
   - 문제 번호는 있지만 선택지가 1개 이하
   - 문제 텍스트가 문장 중간에서 끊어짐 (마침표 없이 끝남)
   - 표나 그림 설명이 중간에 끊어짐

2. **감지해서는 안 되는 경우:**
   - 단순히 선택지가 적은 경우 (실제로는 완전할 수 있음)
   - 텍스트가 자연스럽게 끝나는 경우
   - 다음 페이지와 관련이 없어 보이는 경우

**출력 형식:**
{
  "incomplete_detected": true/false,
  "question_number": 숫자_또는_null,
  "incomplete_type": "missing_choices|truncated_text|partial_table|none",
  "evidence": {
    "last_complete_sentence": "마지막_완전한_문장",
    "incomplete_part": "불완전한_부분",
    "missing_elements": ["누락된_요소들"]
  },
  "confidence_score": 0.0-1.0,
  "requires_continuation": true/false
}

**절대 금지:**
- 불확실한 경우 false로 응답
- 추측성 감지 금지
- 명확한 증거 없이 true 판정 금지"""

    @staticmethod
    def get_cross_page_stitching_prompt() -> str:
        """크로스페이지 결합 프롬프트 - 정확한 결합만"""
        return """당신은 페이지 간 분할된 문제 결합 전문가입니다.

**결합 규칙:**
1. 첫 번째 페이지의 미완료 부분과 두 번째 페이지의 연속 부분만 결합
2. 중복되는 내용은 제거하되, 누락 위험이 있으면 보존
3. 선택지 번호 순서 확인 후 결합
4. 문제 텍스트의 자연스러운 연결 확인

**결합 방식:**
```
문제 번호: [첫 번째 부분]
문제 텍스트: [첫 번째 텍스트] + [두 번째 텍스트]  
선택지: [첫 번째 선택지들] + [두 번째 선택지들]
```

**검증 체크리스트:**
- 문제 번호 일치 확인
- 선택지 번호 중복 없음 확인  
- 텍스트 연결의 문법적 정확성 확인
- 의미적 일관성 확인

**출력 형식:**
{
  "question_number": 결합된_문제_번호,
  "question_text": "완전히_결합된_문제_텍스트",
  "choices": [
    {"number": 1, "symbol": "①", "text": "선택지1"},
    {"number": 2, "symbol": "②", "text": "선택지2"},
    {"number": 3, "symbol": "③", "text": "선택지3"},
    {"number": 4, "symbol": "④", "text": "선택지4"},
    {"number": 5, "symbol": "⑤", "text": "선택지5"}
  ],
  "stitching_method": "설명",
  "quality_check": {
    "text_flow": "natural|awkward",
    "choice_completeness": "complete|partial",
    "meaning_coherent": true/false
  }
}

**실패 시 응답:**
결합이 불가능하거나 의미가 맞지 않으면 null 반환"""

    @staticmethod
    def get_ocr_validation_prompt() -> str:
        """OCR 결과 검증 프롬프트"""
        return """당신은 OCR 텍스트 품질 검증 전문가입니다.

**검증 항목:**
1. **텍스트 가독성:** 글자가 명확히 인식되었는가?
2. **구조 보존:** 원본의 레이아웃이 유지되었는가?
3. **특수 문자:** ①②③④⑤ 선택지 기호가 정확한가?
4. **줄바꿈:** 문단과 항목 구분이 적절한가?

**품질 등급:**
- EXCELLENT: 완벽한 텍스트 인식
- GOOD: 사소한 오류만 있음  
- FAIR: 일부 오류 있지만 의미 파악 가능
- POOR: 심각한 오류로 의미 파악 어려움
- UNREADABLE: 거의 인식 불가

**출력 형식:**
{
  "ocr_quality": "품질등급",
  "confidence_score": 0.0-1.0,
  "issues": [
    {
      "type": "missing_chars|wrong_chars|layout_broken",
      "description": "구체적_문제_설명",
      "severity": "low|medium|high"
    }
  ],
  "suggestions": ["개선_방안들"],
  "usable_for_extraction": true/false
}

**검증 기준:**
- 95% 이상 정확도: EXCELLENT
- 90-94% 정확도: GOOD  
- 80-89% 정확도: FAIR
- 70-79% 정확도: POOR
- 70% 미만: UNREADABLE"""

    @staticmethod
    def get_asset_extraction_prompt(asset_type: str) -> str:
        """에셋별 추출 프롬프트"""
        if asset_type == "table":
            return """당신은 표 추출 전문가입니다.

**표 추출 규칙:**
1. 실제로 표 형태인 데이터만 추출 (|, +, - 구분선 확인)
2. 헤더와 데이터 행 구분
3. 병합된 셀 처리
4. 표 캡션이나 제목 포함

**HTML 테이블 출력:**
```html
<table class="exam-table">
  <caption>표 제목 (있는 경우만)</caption>
  <thead>
    <tr><th>헤더1</th><th>헤더2</th></tr>
  </thead>
  <tbody>
    <tr><td>데이터1</td><td>데이터2</td></tr>
  </tbody>
</table>
```

**표가 아닌 경우:** null 반환"""
        
        elif asset_type == "figure":
            return """당신은 그림/도표 설명 추출 전문가입니다.

**추출 대상:**
- 그림, 도표, 차트, 다이어그램 설명
- "그림", "Figure", "도", "Chart" 키워드가 있는 내용
- 시각적 요소에 대한 텍스트 설명

**추출하지 않을 것:**
- 일반 텍스트 문단
- 단순한 예시 코드
- 표 형태의 데이터

**출력 형식:**
{
  "figure_type": "diagram|chart|illustration|photo",
  "title": "그림_제목",
  "description": "그림_설명_텍스트",
  "caption": "캡션_텍스트",
  "is_essential": true/false
}"""
        
        elif asset_type == "code":
            return """당신은 코드 블록 추출 전문가입니다.

**코드 식별 기준:**
- 프로그래밍 언어 구문 (변수, 함수, 제어문)
- 들여쓰기로 구조화된 텍스트
- 특수 문자나 기호가 많은 텍스트
- HTML, CSS, JavaScript, Python, Java 등

**출력 형식:**
```언어
실제_코드_내용
```

**언어 감지:**
- 키워드 분석으로 언어 추정
- 불명확하면 "text"로 설정"""
        
        else:
            return "지원하지 않는 에셋 타입입니다."

    @staticmethod
    def get_quality_validation_prompt() -> str:
        """품질 검증 프롬프트"""
        return """당신은 추출된 문제의 품질을 검증하는 전문가입니다.

**검증 항목:**
1. **완성도:** 문제 번호, 텍스트, 선택지가 모두 있는가?
2. **논리성:** 문제와 선택지가 논리적으로 연결되는가?
3. **형식성:** 시험 문제 형식에 맞는가?
4. **중복성:** 다른 문제와 중복되지 않는가?

**품질 점수 기준:**
- 10점: 완벽한 문제 (바로 출제 가능)
- 8-9점: 우수 (사소한 수정 필요)
- 6-7점: 보통 (일부 수정 필요)
- 4-5점: 미흡 (상당한 수정 필요)
- 1-3점: 불량 (재작성 필요)
- 0점: 사용 불가

**검증 결과 형식:**
{
  "question_number": 문제번호,
  "quality_score": 0-10,
  "completeness": {
    "has_question_text": true/false,
    "has_sufficient_choices": true/false,
    "text_clarity": "clear|unclear|ambiguous"
  },
  "issues": [
    {
      "type": "format|content|logic|duplicate",
      "description": "구체적_문제점",
      "severity": "critical|major|minor"
    }
  ],
  "recommendation": "keep|revise|discard",
  "confidence": 0.0-1.0
}"""

    @staticmethod
    def get_deduplication_prompt() -> str:
        """중복 제거 프롬프트"""
        return """당신은 중복 문제 탐지 전문가입니다.

**중복 판정 기준:**
1. **완전 중복:** 문제 텍스트와 선택지가 100% 동일
2. **부분 중복:** 문제 핵심 내용이 80% 이상 유사
3. **변형 중복:** 표현만 다르고 묻는 내용이 동일

**유사도 측정:**
- 텍스트 편집 거리 (Levenshtein Distance)
- 핵심 키워드 겹침도
- 문제 의도 유사성

**처리 방식:**
1. 완전 중복: 하나만 보존, 나머지 제거
2. 부분 중복: 더 완전한 버전 보존  
3. 변형 중복: 더 명확한 버전 보존

**출력 형식:**
{
  "duplicate_groups": [
    {
      "group_id": 1,
      "questions": [문제번호들],
      "similarity_score": 0.0-1.0,
      "duplicate_type": "complete|partial|variant",
      "recommended_action": "keep_first|keep_best|merge"
    }
  ],
  "unique_questions": [유니크한_문제번호들],
  "total_removed": 제거된_문제수
}"""