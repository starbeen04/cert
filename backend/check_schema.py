#!/usr/bin/env python3
import sqlite3

def check_schema():
    conn = sqlite3.connect("cert_fast_test.db")
    cursor = conn.cursor()
    
    # ai_agents 테이블 스키마 확인
    cursor.execute("PRAGMA table_info(ai_agents)")
    columns = cursor.fetchall()
    print("ai_agents 테이블 컬럼:")
    for col in columns:
        print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'} {f'DEFAULT {col[4]}' if col[4] else ''}")
    
    conn.close()

if __name__ == "__main__":
    check_schema()