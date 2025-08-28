#!/usr/bin/env python3
"""
개선된 레이아웃 분석 시스템 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.pdf_layout_analyzer import PDFLayoutAnalyzer
from services.enhanced_pdf_processor import enhanced_pdf_processor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

# Database setup
DATABASE_URL = "sqlite:///cert_fast_test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_enhanced_layout_system():
    """개선된 레이아웃 분석 시스템 테스트"""
    print("=== 개선된 레이아웃 분석 시스템 테스트 ===")
    
    # 테스트할 PDF 파일 경로
    test_pdf_path = "uploads/test_questions.pdf"
    
    if not os.path.exists(test_pdf_path):
        print(f"[경고] 테스트 PDF 파일이 없습니다: {test_pdf_path}")
        print("대신 기존 처리된 파일을 사용하여 데이터베이스 상태를 확인합니다.")
        await check_database_status()
        return
    
    print(f"[테스트] PDF 파일: {test_pdf_path}")
    
    # 1. 레이아웃 분석 테스트
    print("\n[Step 1] 레이아웃 분석 테스트")
    layout_analyzer = PDFLayoutAnalyzer()
    layout_result = layout_analyzer.analyze_pdf_layout(test_pdf_path)
    
    if layout_result.get("success"):
        print(f"✅ 레이아웃 분석 성공")
        print(f"   - 총 페이지: {layout_result.get('total_pages')}")
        print(f"   - 식별된 문제: {layout_result.get('identified_questions')}개")
        
        # 구조화된 문제 추출 테스트
        print("\n[Step 2] 구조화된 문제 추출 테스트")
        structured_questions = layout_analyzer.extract_structured_questions(test_pdf_path)
        
        print(f"✅ 구조화된 문제 추출: {len(structured_questions)}개")
        
        # 처음 3개 문제 상세 정보 출력
        for i, question in enumerate(structured_questions[:3]):
            print(f"\n--- 문제 {i+1} ---")
            print(f"번호: {question.get('question_number')}")
            print(f"지문: {question.get('passage', '없음')}")
            print(f"문제: {question.get('question_text', '')[:100]}...")
            print(f"선택지: {len(question.get('options', []))}개")
    else:
        print(f"❌ 레이아웃 분석 실패: {layout_result.get('error')}")
    
    # 2. 통합 파이프라인 테스트
    print(f"\n[Step 3] 통합 파이프라인 테스트")
    db = SessionLocal()
    
    try:
        # 가상 업로드 ID 생성
        test_upload_id = 999999
        
        # 개선된 파이프라인 실행
        result = await enhanced_pdf_processor.process_pdf_with_enhanced_pipeline(
            upload_id=test_upload_id,
            file_path=test_pdf_path,
            file_type="questions",
            db=db
        )
        
        if result.get("success", False):
            print(f"✅ 통합 파이프라인 성공")
            print(f"   - 처리된 문제: {len(result.get('questions', []))}개")
            print(f"   - 총 비용: ${result.get('total_cost', 0):.4f}")
        else:
            print(f"❌ 통합 파이프라인 실패: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
    finally:
        db.close()

async def check_database_status():
    """데이터베이스 상태 확인"""
    print("\n=== 데이터베이스 상태 확인 ===")
    
    db = SessionLocal()
    
    try:
        # 최근 문제 추출 결과 확인
        recent_questions = db.execute(
            text("""
                SELECT q.id, q.question_number, q.passage, q.question_text, q.options
                FROM extracted_questions q
                ORDER BY q.id DESC
                LIMIT 10
            """)
        ).fetchall()
        
        print(f"[결과] 최근 추출된 문제: {len(recent_questions)}개")
        
        for q in recent_questions:
            print(f"\n--- 문제 {q.question_number} ---")
            print(f"지문: {'있음' if q.passage else '없음'}")
            print(f"문제: {q.question_text[:60]}...")
            
            # 선택지 파싱
            try:
                if q.options:
                    options = json.loads(q.options) if isinstance(q.options, str) else q.options
                    print(f"선택지: {len(options)}개")
                else:
                    print("선택지: 없음")
            except:
                print("선택지: 파싱 오류")
        
        # 통계
        total_questions = db.execute(
            text("SELECT COUNT(*) as count FROM extracted_questions")
        ).fetchone()
        
        questions_with_passage = db.execute(
            text("SELECT COUNT(*) as count FROM extracted_questions WHERE passage IS NOT NULL")
        ).fetchone()
        
        questions_with_options = db.execute(
            text("SELECT COUNT(*) as count FROM extracted_questions WHERE options IS NOT NULL")
        ).fetchone()
        
        print(f"\n[통계]")
        print(f"전체 문제: {total_questions.count}개")
        print(f"지문 있는 문제: {questions_with_passage.count}개")
        print(f"선택지 있는 문제: {questions_with_options.count}개")
        
    except Exception as e:
        print(f"[오류] 데이터베이스 확인 실패: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import asyncio
    
    print("개선된 레이아웃 분석 시스템 테스트를 시작합니다...")
    asyncio.run(test_enhanced_layout_system())