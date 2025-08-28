"""
테스트용 API 키 생성 스크립트
"""
import sqlite3
from datetime import datetime
import hashlib

# 데이터베이스 연결
conn = sqlite3.connect('cert_fast_test.db')
cursor = conn.cursor()

# 테스트 API 키 데이터
test_api_key = "test-key-for-usage-tracking-12345"
key_name = "테스트 사용량 추적 키"
provider = "openai"
daily_limit = 10.0
monthly_limit = 100.0
current_date = datetime.now().date().isoformat()

# API 키가 이미 존재하는지 확인
cursor.execute("SELECT id FROM api_keys WHERE api_key = ?", (test_api_key,))
existing = cursor.fetchone()

if existing:
    print(f"API 키 '{test_api_key}'가 이미 존재합니다. ID: {existing[0]}")
else:
    # 새 API 키 생성
    cursor.execute("""
        INSERT INTO api_keys 
        (key_name, provider, api_key, daily_limit, monthly_limit, 
         current_daily_usage, current_monthly_usage, is_active, 
         created_at, updated_at, last_reset_date)
        VALUES (?, ?, ?, ?, ?, 0.0, 0.0, 1, ?, ?, ?)
    """, (
        key_name, provider, test_api_key, daily_limit, monthly_limit,
        datetime.now().isoformat(), datetime.now().isoformat(), current_date
    ))
    
    api_key_id = cursor.lastrowid
    print(f"테스트 API 키가 생성되었습니다. ID: {api_key_id}")
    print(f"키 이름: {key_name}")
    print(f"API 키: {test_api_key}")
    print(f"제공업체: {provider}")
    print(f"일일 한도: ${daily_limit}")
    print(f"월간 한도: ${monthly_limit}")

# 변경사항 저장 및 연결 종료
conn.commit()
conn.close()

print("\n테스트 API 키 생성이 완료되었습니다!")