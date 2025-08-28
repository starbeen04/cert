#!/usr/bin/env python3
"""
Check database tables
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

def check_tables():
    """Check database tables"""
    print("=== 데이터베이스 테이블 확인 ===")
    
    db = SessionLocal()
    
    try:
        # Get all table names
        tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
        
        print(f"총 {len(tables)}개 테이블 발견:")
        for table in tables:
            print(f"  - {table.name}")
        
        # Check for uploads-related tables
        upload_tables = [t for t in tables if 'upload' in t.name.lower()]
        print(f"\n업로드 관련 테이블: {len(upload_tables)}개")
        for table in upload_tables:
            print(f"  - {table.name}")
            
            # Show table schema
            schema = db.execute(text(f"PRAGMA table_info({table.name})")).fetchall()
            print(f"    컬럼: {', '.join([col.name for col in schema])}")
        
        # Check for questions-related tables  
        question_tables = [t for t in tables if 'question' in t.name.lower()]
        print(f"\n문제 관련 테이블: {len(question_tables)}개")
        for table in question_tables:
            print(f"  - {table.name}")
            
            # Show table schema
            schema = db.execute(text(f"PRAGMA table_info({table.name})")).fetchall()
            print(f"    컬럼: {', '.join([col.name for col in schema])}")
            
    except Exception as e:
        print(f"[오류] 테이블 확인 중 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_tables()