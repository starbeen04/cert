#!/usr/bin/env python3
"""
개선된 시스템 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from services.enhanced_pdf_processor import EnhancedPDFProcessor

# Database setup
DATABASE_URL = "sqlite:///cert_fast_test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_improved_extraction():
    """개선된 추출 시스템 테스트"""
    print("=== 개선된 문제 추출 시스템 테스트 ===")
    
    db = SessionLocal()
    processor = EnhancedPDFProcessor()
    
    try:
        # 가장 최근 업로드 파일 선택
        latest_upload = db.execute(
            text("SELECT id, file_path, file_type FROM pdf_uploads ORDER BY id DESC LIMIT 1")
        ).fetchone()
        
        if not latest_upload:
            print("[오류] 테스트할 업로드 파일이 없습니다")
            return
        
        upload_id = latest_upload.id
        file_path = latest_upload.file_path
        file_type = latest_upload.file_type
        
        print(f"[테스트] 파일: {file_path}")
        print(f"[테스트] 업로드 ID: {upload_id}")
        print(f"[테스트] 파일 타입: {file_type}")
        
        # 개선된 파이프라인으로 처리
        print("\n[시작] 개선된 PDF 처리 파이프라인 실행...")
        result = await processor.process_pdf_with_enhanced_pipeline(upload_id, file_path, file_type, db)
        
        if result.get("success"):
            questions_count = result.get("questions_count", 0)
            materials_count = result.get("materials_count", 0)
            quality_score = result.get("quality_score", 0)
            
            print(f"\n[결과] 추출 성공!")
            print(f"  - 문제 수: {questions_count}개")
            print(f"  - 자료 수: {materials_count}개")
            print(f"  - 품질 점수: {quality_score}/100")
            
            # 데이터베이스에서 실제 저장된 문제 확인
            saved_questions = db.execute(
                text("SELECT COUNT(*) as count FROM extracted_questions WHERE pdf_upload_id = :upload_id"),
                {"upload_id": upload_id}
            ).fetchone()
            
            print(f"  - 실제 DB 저장: {saved_questions.count}개")
            
            # 선택지 개수 분포 확인
            option_stats = db.execute(
                text("""
                    SELECT 
                        LENGTH(options) - LENGTH(REPLACE(options, '","', '')) + 1 as option_count,
                        COUNT(*) as question_count
                    FROM extracted_questions 
                    WHERE pdf_upload_id = :upload_id
                    GROUP BY option_count
                    ORDER BY option_count
                """),
                {"upload_id": upload_id}
            ).fetchall()
            
            print(f"\n[선택지 분포]")
            for stat in option_stats:
                print(f"  - {stat.option_count}개 선택지: {stat.question_count}문제")
            
            # 특별 표시가 있는 문제 확인
            special_questions = db.execute(
                text("""
                    SELECT question_number, question_text
                    FROM extracted_questions 
                    WHERE pdf_upload_id = :upload_id 
                    AND question_text LIKE '%[표/그림/코드 포함]%'
                """),
                {"upload_id": upload_id}
            ).fetchall()
            
            if special_questions:
                print(f"\n[표/그림/코드 포함 문제] {len(special_questions)}개 발견")
                for q in special_questions[:3]:  # 처음 3개만 표시
                    print(f"  - 문제 {q.question_number}: {q.question_text[:60]}...")
            
        else:
            print(f"[실패] 처리 실패: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"[오류] 테스트 실행 중 오류: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_improved_extraction())