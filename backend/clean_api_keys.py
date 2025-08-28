"""
기존 API 키들 정리하고 실제 키들만 추가
"""
import sqlite3
from datetime import datetime

# 데이터베이스 연결
conn = sqlite3.connect('cert_fast_test.db')
cursor = conn.cursor()

print("=== API 키 데이터베이스 정리 ===")

# 1. 기존 모든 API 키 삭제
print("1. 기존 API 키들 삭제 중...")
cursor.execute("DELETE FROM api_keys")
deleted_count = cursor.rowcount
print(f"   삭제된 키 개수: {deleted_count}개")

# 2. 실제 OpenAI API 키 추가
print("\n2. 실제 OpenAI API 키 추가...")
openai_key_data = {
    "key_name": "OpenAI GPT API Key",
    "provider": "openai", 
    "api_key": "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",
    "daily_limit": 50.0,
    "monthly_limit": 500.0,
    "current_daily_usage": 0.0,
    "current_monthly_usage": 0.0,
    "is_active": 1,
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat(),
    "last_reset_date": datetime.now().date().isoformat()
}

cursor.execute("""
    INSERT INTO api_keys 
    (key_name, provider, api_key, daily_limit, monthly_limit, 
     current_daily_usage, current_monthly_usage, is_active, 
     created_at, updated_at, last_reset_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    openai_key_data["key_name"],
    openai_key_data["provider"],
    openai_key_data["api_key"],
    openai_key_data["daily_limit"],
    openai_key_data["monthly_limit"],
    openai_key_data["current_daily_usage"],
    openai_key_data["current_monthly_usage"],
    openai_key_data["is_active"],
    openai_key_data["created_at"],
    openai_key_data["updated_at"],
    openai_key_data["last_reset_date"]
))

openai_id = cursor.lastrowid
print(f"   OpenAI API 키 추가됨 (ID: {openai_id})")

# 3. 실제 Claude API 키 추가  
print("\n3. 실제 Claude API 키 추가...")
claude_key_data = {
    "key_name": "Claude Anthropic API Key",
    "provider": "anthropic",
    "api_key": "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",
    "daily_limit": 100.0,
    "monthly_limit": 1000.0,
    "current_daily_usage": 0.0,
    "current_monthly_usage": 0.0,
    "is_active": 1,
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat(),
    "last_reset_date": datetime.now().date().isoformat()
}

cursor.execute("""
    INSERT INTO api_keys 
    (key_name, provider, api_key, daily_limit, monthly_limit, 
     current_daily_usage, current_monthly_usage, is_active, 
     created_at, updated_at, last_reset_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    claude_key_data["key_name"],
    claude_key_data["provider"], 
    claude_key_data["api_key"],
    claude_key_data["daily_limit"],
    claude_key_data["monthly_limit"],
    claude_key_data["current_daily_usage"],
    claude_key_data["current_monthly_usage"],
    claude_key_data["is_active"],
    claude_key_data["created_at"],
    claude_key_data["updated_at"],
    claude_key_data["last_reset_date"]
))

claude_id = cursor.lastrowid
print(f"   Claude API 키 추가됨 (ID: {claude_id})")

# 변경사항 저장
conn.commit()

# 4. 결과 확인
print("\n4. 정리 완료 - 현재 API 키 목록:")
cursor.execute("""
    SELECT id, key_name, provider, daily_limit, monthly_limit, is_active
    FROM api_keys
    ORDER BY id
""")

keys = cursor.fetchall()
for key in keys:
    status = "활성" if key[5] else "비활성"
    print(f"   ID: {key[0]} | {key[1]} ({key[2]}) | 일일: ${key[3]:.0f} 월간: ${key[4]:.0f} | {status}")

conn.close()

print(f"\n=== 정리 완료 ===")
print(f"실제 API 키 2개만 남김:")
print(f"- OpenAI GPT API Key (일일 $50, 월간 $500)")
print(f"- Claude Anthropic API Key (일일 $100, 월간 $1000)")