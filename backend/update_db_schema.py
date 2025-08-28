#!/usr/bin/env python3
"""데이터베이스 스키마 업데이트 스크립트"""

import sqlite3
import os

def update_ai_schema():
    # 데이터베이스 파일 경로
    db_path = "cert_fast_test.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 기존 컬럼 확인
        cursor.execute("PRAGMA table_info(ai_agents)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print("기존 ai_agents 컬럼:", existing_columns)
        
        # 새로운 컬럼들 추가 (이미 존재하지 않는 경우만)
        new_columns = [
            ("system_prompt", "TEXT"),
            ("is_active", "BOOLEAN DEFAULT 1"),
            ("model_name", "VARCHAR(100)"),
            ("provider", "VARCHAR(50)"),
            ("max_tokens", "INTEGER DEFAULT 4000"),
            ("temperature", "REAL DEFAULT 0.7"),
            ("priority", "INTEGER DEFAULT 1")
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                print(f"Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE ai_agents ADD COLUMN {column_name} {column_type}")
            else:
                print(f"Column {column_name} already exists")
        
        # API 키 테이블 생성
        print("Creating api_keys table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider VARCHAR(50) NOT NULL,
                key_name VARCHAR(100) NOT NULL,
                api_key VARCHAR(500) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                daily_limit REAL,
                monthly_limit REAL,
                current_daily_usage REAL DEFAULT 0.0,
                current_monthly_usage REAL DEFAULT 0.0,
                last_reset_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # AI 사용량 로그 테이블 생성
        print("Creating ai_usage_logs table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id INTEGER NOT NULL,
                api_key_id INTEGER NOT NULL,
                user_id INTEGER,
                task_type VARCHAR(100) NOT NULL,
                model_used VARCHAR(100) NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.0,
                duration_seconds REAL,
                status VARCHAR(50) DEFAULT 'success',
                error_message TEXT,
                request_data TEXT,
                response_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # AI 작업 테이블 생성
        print("Creating ai_tasks table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name VARCHAR(200) NOT NULL,
                task_type VARCHAR(100) NOT NULL,
                agent_id INTEGER NOT NULL,
                user_id INTEGER,
                file_upload_id INTEGER,
                status VARCHAR(50) DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                input_data TEXT,
                output_data TEXT,
                error_message TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        conn.commit()
        print("데이터베이스 스키마 업데이트 완료!")
        
        # 업데이트 후 컬럼 확인
        cursor.execute("PRAGMA table_info(ai_agents)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print("업데이트 후 ai_agents 컬럼:", updated_columns)
        
    except Exception as e:
        print(f"Error updating schema: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_ai_schema()