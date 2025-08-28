#!/usr/bin/env python3
import sqlite3

def add_missing_columns():
    conn = sqlite3.connect("cert_fast_test.db")
    cursor = conn.cursor()
    
    try:
        # 누락된 컬럼들 추가
        missing_columns = [
            ("agent_type", "VARCHAR(100) DEFAULT 'general'"),
            ("agent_config", "TEXT"),
            ("prompt_template", "TEXT"),
            ("status", "VARCHAR(50) DEFAULT 'active'"),
            ("creator_id", "INTEGER")
        ]
        
        # 기존 컬럼 확인
        cursor.execute("PRAGMA table_info(ai_agents)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print("기존 컬럼:", existing_columns)
        
        for column_name, column_def in missing_columns:
            if column_name not in existing_columns:
                print(f"Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE ai_agents ADD COLUMN {column_name} {column_def}")
            else:
                print(f"Column {column_name} already exists")
        
        conn.commit()
        print("컬럼 추가 완료!")
        
        # 업데이트 후 컬럼 확인
        cursor.execute("PRAGMA table_info(ai_agents)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print("업데이트 후 컬럼:", updated_columns)
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_missing_columns()