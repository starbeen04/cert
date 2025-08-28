#!/usr/bin/env python3
"""
개선된 PDF 처리 시스템 직접 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.pdf_layout_analyzer import PDFLayoutAnalyzer
import json

def test_layout_analyzer_direct():
    """레이아웃 분석기 직접 테스트"""
    print("=== 레이아웃 분석기 직접 테스트 ===")
    
    # 테스트할 PDF 파일들 찾기
    possible_files = [
        "uploads/pdfs/20250819_230927_9d999864_2. 2024년2회_정보처리산업기사필기 기출문제.pdf",
        "uploads/pdfs/20250819_233440_bcacb893_2. 2024년2회_정보처리산업기사필기 기출문제.pdf",
        "uploads/pdfs/20250820_001326_21d9c23d_2. 2024년2회_정보처리산업기사필기 기출문제.pdf",
        "uploads/test.pdf",
        "uploads/sample.pdf", 
        "uploads/questions.pdf"
    ]
    
    test_file = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            test_file = file_path
            print(f"[발견] 테스트 파일: {file_path}")
            break
    
    if not test_file:
        print("[경고] 테스트할 PDF 파일을 찾을 수 없습니다.")
        print("다음 위치 중 하나에 PDF 파일을 배치하세요:")
        for file_path in possible_files:
            print(f"  - {file_path}")
        return
    
    # 레이아웃 분석기 초기화 및 실행
    analyzer = PDFLayoutAnalyzer()
    
    print(f"\n[Step 1] PDF 텍스트 추출 테스트")
    raw_pages = analyzer._extract_pdf_text(test_file)
    
    if raw_pages:
        print(f"[성공] PDF 텍스트 추출 성공 - {len(raw_pages)}페이지")
        
        # 첫 번째 페이지 내용 미리보기
        first_page_text = raw_pages[0]["raw_text"][:300]
        print(f"첫 페이지 미리보기:\n{first_page_text}...")
    else:
        print("[실패] PDF 텍스트 추출 실패")
        return
    
    print(f"\n[Step 2] 레이아웃 분석 테스트")
    layout_analysis = analyzer._analyze_page_layouts(raw_pages)
    
    if layout_analysis:
        print(f"[성공] 레이아웃 분석 성공")
        
        # 페이지별 결과 요약
        for page_data in layout_analysis[:3]:  # 첫 3페이지만
            page_num = page_data["page_num"]
            page_type = page_data["page_type"]
            element_count = len(page_data["elements"])
            
            print(f"  페이지 {page_num}: {page_type}, 요소 {element_count}개")
            
            # 요소별 세부 정보
            for element in page_data["elements"][:3]:  # 각 페이지의 첫 3개 요소
                print(f"    - {element.type}: {element.content[:50]}...")
    
    print(f"\n[Step 3] 문제 구조 식별 테스트")
    question_structures = analyzer._identify_question_structures(layout_analysis)
    
    if question_structures:
        print(f"[성공] 문제 구조 식별 성공 - {len(question_structures)}개")
        
        # 처음 5개 문제 상세 정보
        for i, structure in enumerate(question_structures[:5]):
            print(f"\n--- 문제 {i+1} (번호: {structure.question_number}) ---")
            print(f"지문: {'있음' if structure.passage else '없음'}")
            if structure.passage:
                print(f"   {structure.passage[:80]}...")
            print(f"문제: {structure.question_text[:80]}...")
            print(f"선택지: {len(structure.options)}개")
            for j, option in enumerate(structure.options[:2]):
                print(f"   {j+1}) {option[:50]}...")
            print(f"페이지 범위: {structure.page_range}")
    else:
        print("[실패] 문제 구조 식별 실패")
    
    print(f"\n[Step 4] 통합 테스트")
    full_result = analyzer.analyze_pdf_layout(test_file)
    
    if full_result.get("success"):
        print(f"[성공] 전체 시스템 성공")
        print(f"   - 총 페이지: {full_result.get('total_pages')}")
        print(f"   - 식별된 문제: {full_result.get('identified_questions')}개")
        
        # 구조화된 문제 추출 테스트
        structured_questions = analyzer.extract_structured_questions(test_file)
        print(f"   - 구조화된 문제: {len(structured_questions)}개")
        
        # 결과를 JSON 파일로 저장
        output_file = "layout_analysis_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "layout_result": full_result,
                "structured_questions": structured_questions
            }, f, ensure_ascii=False, indent=2)
        print(f"   - 결과 저장: {output_file}")
        
        # 요약 통계
        questions_with_passage = sum(1 for q in structured_questions if q.get('passage'))
        questions_with_options = sum(1 for q in structured_questions if q.get('options'))
        
        print(f"\n[최종 통계]")
        print(f"전체 문제: {len(structured_questions)}개")
        print(f"지문 있는 문제: {questions_with_passage}개 ({questions_with_passage/len(structured_questions)*100:.1f}%)")
        print(f"선택지 있는 문제: {questions_with_options}개 ({questions_with_options/len(structured_questions)*100:.1f}%)")
        
    else:
        print(f"[실패] 전체 시스템 실패: {full_result.get('error')}")

if __name__ == "__main__":
    test_layout_analyzer_direct()