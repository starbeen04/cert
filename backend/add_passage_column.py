#!/usr/bin/env python3
"""
extracted_questions 테이블에 passage 컬럼 추가
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

def add_passage_column():
    """passage 컬럼 추가"""
    print("=== 데이터베이스 스키마 업데이트 ===")
    
    db = SessionLocal()
    
    try:
        # 1. 현재 테이블 구조 확인
        columns = db.execute(text("PRAGMA table_info(extracted_questions)")).fetchall()
        existing_columns = [col.name for col in columns]
        
        print(f"[확인] 현재 컬럼: {', '.join(existing_columns)}")
        
        # 2. passage 컬럼이 없으면 추가
        if 'passage' not in existing_columns:
            print("[추가] passage 컬럼 추가 중...")
            db.execute(text("ALTER TABLE extracted_questions ADD COLUMN passage TEXT"))
            db.commit()
            print("[성공] passage 컬럼이 추가되었습니다")
        else:
            print("[정보] passage 컬럼이 이미 존재합니다")
        
        # 3. 업데이트된 테이블 구조 확인
        columns_after = db.execute(text("PRAGMA table_info(extracted_questions)")).fetchall()
        print(f"[결과] 업데이트된 컬럼: {', '.join([col.name for col in columns_after])}")
        
    except Exception as e:
        print(f"[오류] 스키마 업데이트 실패: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_passage_column()