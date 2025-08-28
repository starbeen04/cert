#!/usr/bin/env python3
"""
지문 분리 기능 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database setup
DATABASE_URL = "sqlite:///cert_fast_test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_passage_separation():
    """지문 분리 기능 테스트"""
    print("=== 지문 분리 기능 테스트 ===")
    
    db = SessionLocal()
    
    try:
        # 최근 파일에서 지문이 있는 문제 확인
        questions_with_passage = db.execute(
            text("""
                SELECT q.id, q.question_number, q.passage, q.question_text, q.options
                FROM extracted_questions q
                WHERE q.passage IS NOT NULL
                ORDER BY q.id DESC
                LIMIT 5
            """)
        ).fetchall()
        
        print(f"[결과] 지문이 있는 문제: {len(questions_with_passage)}개")
        
        for q in questions_with_passage:
            print(f"\n--- 문제 {q.question_number} ---")
            print(f"지문: {q.passage[:100]}..." if q.passage else "지문: 없음")
            print(f"문제: {q.question_text}")
            print(f"선택지: {q.options[:100]}...")
        
        # 지문이 없는 문제도 확인
        questions_without_passage = db.execute(
            text("""
                SELECT COUNT(*) as count
                FROM extracted_questions
                WHERE passage IS NULL
            """)
        ).fetchone()
        
        print(f"\n[통계] 지문 없는 문제: {questions_without_passage.count}개")
        
        # 전체 통계
        total_questions = db.execute(
            text("SELECT COUNT(*) as count FROM extracted_questions")
        ).fetchone()
        
        print(f"[통계] 전체 문제: {total_questions.count}개")
        
        if questions_with_passage:
            print(f"[통계] 지문 분리율: {len(questions_with_passage)}/{total_questions.count} ({len(questions_with_passage)/total_questions.count*100:.1f}%)")
        
    except Exception as e:
        print(f"[오류] 테스트 실패: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_passage_separation()