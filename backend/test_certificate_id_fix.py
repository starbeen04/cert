#!/usr/bin/env python3
"""
Test script to verify certificate_id fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from services.enhanced_pdf_processor import EnhancedPDFProcessor
import json

# Database setup
DATABASE_URL = "sqlite:///cert_fast_test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_certificate_id_fix():
    """Test the certificate_id fix"""
    print("=== Certificate ID 수정 테스트 ===")
    
    db = SessionLocal()
    processor = EnhancedPDFProcessor()
    
    try:
        # 1. Find an upload record with certificate_id
        upload_record = db.execute(
            text("SELECT id, certificate_id FROM pdf_uploads WHERE certificate_id IS NOT NULL LIMIT 1")
        ).fetchone()
        
        if not upload_record:
            print("[오류] certificate_id가 있는 업로드 레코드를 찾을 수 없습니다")
            return
        
        upload_id = upload_record.id
        certificate_id = upload_record.certificate_id
        print(f"[테스트] 업로드 ID: {upload_id}, certificate_id: {certificate_id}")
        
        # 2. Create test questions
        test_questions = [
            {
                "question_number": 1,
                "question_text": "테스트 문제 1",
                "options": ["선택지 1", "선택지 2", "선택지 3", "선택지 4"],
                "correct_answer": "선택지 1",
                "topic_category": "테스트",
                "difficulty_level": "중급",
                "explanation": "테스트 설명"
            },
            {
                "question_number": 2,
                "question_text": "테스트 문제 2",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "topic_category": "테스트",
                "difficulty_level": "고급",
                "explanation": "테스트 설명 2"
            }
        ]
        
        print(f"[테스트] {len(test_questions)}개 테스트 문제 생성")
        
        # 3. Test the fixed _save_questions_to_db method
        print("[테스트] 문제 저장 중...")
        
        # Clear any existing test questions first
        db.execute(
            text("DELETE FROM extracted_questions WHERE pdf_upload_id = :upload_id"),
            {"upload_id": upload_id}
        )
        db.commit()
        
        # Save test questions
        import asyncio
        saved_questions = asyncio.run(
            processor._save_questions_to_db(test_questions, upload_id, db)
        )
        
        db.commit()
        
        print(f"[결과] {len(saved_questions)}개 문제가 성공적으로 저장됨")
        
        # 4. Verify the questions were saved with certificate_id
        verify_result = db.execute(
            text("SELECT id, certificate_id, question_text FROM extracted_questions WHERE pdf_upload_id = :upload_id"),
            {"upload_id": upload_id}
        ).fetchall()
        
        print(f"[검증] 데이터베이스에서 {len(verify_result)}개 문제 확인됨")
        
        for question in verify_result:
            print(f"  - ID: {question.id}, certificate_id: {question.certificate_id}, 문제: {question.question_text[:30]}...")
        
        if len(verify_result) == len(test_questions) and all(q.certificate_id == certificate_id for q in verify_result):
            print("[성공] certificate_id 수정이 완료되었습니다!")
            return True
        else:
            print("[실패] certificate_id가 올바르게 저장되지 않았습니다")
            return False
            
    except Exception as e:
        print(f"[오류] 테스트 실행 중 오류 발생: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_certificate_id_fix()
    sys.exit(0 if success else 1)