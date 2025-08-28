#!/usr/bin/env python3
"""
패턴 매칭 테스트 - PDF 파일 없이 텍스트로 직접 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.pdf_layout_analyzer import PDFLayoutAnalyzer
import json

def test_pattern_matching():
    """패턴 매칭 직접 테스트"""
    print("=== 패턴 매칭 직접 테스트 ===")
    
    # 테스트용 샘플 텍스트 (실제 정보처리산업기사 문제 형태)
    sample_text = """
1. 다음 그래프에서 차수(Degree)가 홀수인 정점의 개수는?

① 1개  ② 2개  ③ 3개  ④ 4개

2. 다음 프로그램을 실행한 결과는?

#include <stdio.h>
int main() {
    int a = 10, b = 20;
    printf("%d", a + b);
    return 0;
}

① 10    ② 20    ③ 30    ④ 40

3. 데이터베이스에서 정규화(Normalization)의 목적으로 옳은 것은?

① 데이터 중복 제거
② 저장공간 절약  
③ 데이터 무결성 보장
④ 모든 것이 옳다

4. 다음 SQL문에서 DISTINCT 키워드의 역할은?

SELECT DISTINCT name FROM student;

① 중복된 행 제거
② 정렬 수행
③ 그룹화 수행  
④ 조건 검색
"""

    analyzer = PDFLayoutAnalyzer()
    
    print(f"\n[Step 1] 텍스트 요소 식별 테스트")
    
    # 가상의 페이지 데이터 생성
    lines = sample_text.strip().split('\n')
    elements = analyzer._identify_text_elements(sample_text, 1)
    
    print(f"[결과] 식별된 요소: {len(elements)}개")
    
    # 요소별 분류
    question_elements = [e for e in elements if e.type == "question"]
    option_elements = [e for e in elements if e.type == "option"]
    passage_elements = [e for e in elements if e.type == "passage"]
    
    print(f"   - 문제: {len(question_elements)}개")
    print(f"   - 선택지: {len(option_elements)}개")
    print(f"   - 지문: {len(passage_elements)}개")
    
    # 각 요소 상세 출력
    print(f"\n[상세] 식별된 문제들:")
    for i, element in enumerate(question_elements):
        print(f"  문제 {i+1}: {element.content[:50]}...")
    
    print(f"\n[상세] 식별된 선택지들:")
    for i, element in enumerate(option_elements):
        print(f"  선택지 {i+1}: {element.content[:30]}...")
        
    print(f"\n[상세] 식별된 지문들:")
    for i, element in enumerate(passage_elements):
        print(f"  지문 {i+1}: {element.content[:50]}...")
    
    print(f"\n[Step 2] 문제 구조 조립 테스트")
    
    # 가상 레이아웃 분석 데이터 생성
    layout_analysis = [{
        "page_num": 1,
        "page_type": "question_page",
        "elements": elements,
        "raw_text": sample_text
    }]
    
    # 문제 구조 식별
    question_structures = analyzer._identify_question_structures(layout_analysis)
    
    print(f"\n[Step 2.1] 누락된 선택지 찾기 테스트")
    
    # 선택지가 없는 문제들에 대해 다시 검색
    for structure in question_structures:
        if not structure.options:
            print(f"[시도] 문제 {structure.question_number}의 누락된 선택지 찾기...")
            analyzer._find_missing_options_for_question(structure, layout_analysis)
    
    print(f"\n[Step 2.2] 최종 결과 확인")
    print(f"[결과] 구조화된 문제: {len(question_structures)}개")
    
    for i, structure in enumerate(question_structures):
        print(f"\n--- 구조화된 문제 {i+1} ---")
        print(f"번호: {structure.question_number}")
        print(f"지문: {'있음' if structure.passage else '없음'}")
        if structure.passage:
            print(f"   {structure.passage[:60]}...")
        print(f"문제: {structure.question_text[:60]}...")
        print(f"선택지: {len(structure.options)}개")
        for j, option in enumerate(structure.options):
            print(f"   {j+1}) {option[:40]}...")
    
    print(f"\n[Step 3] JSON 변환 테스트 (선택지 추가 후)")
    
    # extract_structured_questions 메서드 시뮬레이션
    structured_questions = []
    
    for structure in question_structures:
        question_dict = {
            "question_number": structure.question_number,
            "passage": structure.passage,
            "question_text": structure.question_text,
            "options": structure.options,
            "page_range": f"{structure.page_range[0]}-{structure.page_range[1]}" if structure.page_range else None
        }
        structured_questions.append(question_dict)
    
    print(f"[결과] JSON 변환 성공: {len(structured_questions)}개")
    
    # JSON 파일로 저장
    output_file = "pattern_test_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(structured_questions, f, ensure_ascii=False, indent=2)
    print(f"   - 결과 저장: {output_file}")
    
    # 최종 통계
    questions_with_passage = sum(1 for q in structured_questions if q.get('passage'))
    questions_with_options = sum(1 for q in structured_questions if q.get('options'))
    
    print(f"\n[최종 통계]")
    print(f"전체 문제: {len(structured_questions)}개")
    print(f"지문 있는 문제: {questions_with_passage}개")
    print(f"선택지 있는 문제: {questions_with_options}개")
    
    if structured_questions:
        passage_rate = questions_with_passage / len(structured_questions) * 100
        option_rate = questions_with_options / len(structured_questions) * 100
        print(f"지문 인식률: {passage_rate:.1f}%")
        print(f"선택지 인식률: {option_rate:.1f}%")
    
    print(f"\n[결론] 패턴 매칭 시스템이 {'성공적으로' if structured_questions else '실패로'} 작동합니다.")

if __name__ == "__main__":
    test_pattern_matching()