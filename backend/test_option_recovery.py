#!/usr/bin/env python3
"""
🔧 선택지 복구 로직 테스트
문제 3, 4번과 같은 embedded options 복구 기능 검증
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.append(str(Path(__file__).parent))

from app.services.ultra_precise_pdf_analyzer import UltraPrecisePDFAnalyzer
import openai

def test_option_recovery():
    """선택지 복구 로직 테스트"""
    
    print("🔧 선택지 복구 로직 테스트")
    print("=" * 50)
    
    # 더미 OpenAI 클라이언트로 analyzer 생성
    analyzer = UltraPrecisePDFAnalyzer(openai.AsyncOpenAI(api_key="test"))
    
    # 테스트 케이스 1: 문제 3번과 같은 embedded options
    test_question_3 = {
        "question_number": 3,
        "question_text": """다이어그램에 대한 설명으로 옳지 않은 것은?
① 활동 다이어그램(Activity Diagram) : 시스템이 얽혀 기능을 수행할 때 객체의 처리 로직이나 조건에 따른 처리를 흐름 순서에 따라 표현한다.
② 시퀀스 다이어그램(Sequence Diagram) : 상호 작용하는 시스템이나 객체들이 주고받는 메시지를 표현한다.
③ 유스케이스 다이어그램(Use Case Diagram) : 사용자의 요구를 분석하고, 그것을 기능 모델링 작업에 사용한다.
④ 객체 다이어그램(Object Diagram) : 클래스와 클래스간의 가지는 속성, 클래스 사이의 관계를 표현한다.""",
        "options": [],
        "page_number": 1
    }
    
    # 테스트 케이스 2: 이미 올바르게 분리된 문제 (30번)
    test_question_30 = {
        "question_number": 30,
        "question_text": "다음 중 빌드 도구가 아닌 것은?",
        "options": ["① Zeplin", "② Ant", "③ Maven", "④ Gradle"],
        "page_number": 3
    }
    
    # 테스트 케이스 3: 1)2)3)4) 형태의 선택지
    test_question_alt = {
        "question_number": 99,
        "question_text": """테스트 문제입니다.
1) 첫 번째 선택지입니다
2) 두 번째 선택지입니다
3) 세 번째 선택지입니다
4) 네 번째 선택지입니다""",
        "options": [],
        "page_number": 1
    }
    
    test_cases = [
        ("문제 3번 (embedded options)", test_question_3),
        ("문제 30번 (already separated)", test_question_30),
        ("대안 형태 (1)2)3)4))", test_question_alt)
    ]
    
    for test_name, test_question in test_cases:
        print(f"\n📋 {test_name} 테스트:")
        print(f"   원본 options: {len(test_question.get('options', []))}개")
        print(f"   원본 question_text 길이: {len(test_question.get('question_text', ''))}")
        
        # 복구 로직 적용
        fixed_question = analyzer._fix_embedded_options(test_question.copy())
        
        print(f"   수정 후 options: {len(fixed_question.get('options', []))}개")
        print(f"   수정 후 question_text 길이: {len(fixed_question.get('question_text', ''))}")
        
        if fixed_question.get('options'):
            print("   복구된 선택지:")
            for i, option in enumerate(fixed_question['options'][:4], 1):  # 최대 4개만 표시
                print(f"     {i}. {option[:50]}...")
        
        if len(fixed_question.get('question_text', '')) < len(test_question.get('question_text', '')):
            print("   ✅ question_text에서 선택지 제거됨")
        else:
            print("   ⚠️ question_text 변경 없음")
    
    print("\n" + "=" * 50)
    print("✅ 선택지 복구 로직 테스트 완료!")
    
    # 실제 정규식 패턴 테스트
    print("\n🔍 정규식 패턴 테스트:")
    test_text = "① 첫번째 ② 두번째 ③ 세번째 ④ 네번째"
    
    import re
    choice_pattern = r'([①②③④⑤]|[1-5]\))\s*([^①②③④⑤\n]*?)(?=\s*[①②③④⑤]|\s*[1-5]\)|$)'
    matches = re.findall(choice_pattern, test_text, re.DOTALL)
    
    print(f"   테스트 텍스트: {test_text}")
    print(f"   매칭 결과: {len(matches)}개")
    for marker, content in matches:
        print(f"     '{marker}' → '{content.strip()}'")

if __name__ == "__main__":
    test_option_recovery()