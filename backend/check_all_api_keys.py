"""
현재 데이터베이스의 모든 API 키 확인
"""
import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('cert_fast_test.db')
cursor = conn.cursor()

print("=== 현재 데이터베이스의 모든 API 키 ===")

try:
    cursor.execute("""
        SELECT 
            id,
            key_name,
            provider,
            api_key,
            daily_limit,
            monthly_limit,
            current_daily_usage,
            current_monthly_usage,
            is_active,
            created_at
        FROM api_keys
        ORDER BY id
    """)
    
    keys = cursor.fetchall()
    
    if keys:
        print(f"총 {len(keys)}개의 API 키가 있습니다:")
        print()
        for key in keys:
            print(f"ID: {key[0]}")
            print(f"이름: {key[1]}")
            print(f"제공업체: {key[2]}")
            print(f"키 값: {key[3][:20]}...")
            print(f"일일 한도: ${key[4]:.2f}")
            print(f"월간 한도: ${key[5]:.2f}")
            print(f"일일 사용량: ${key[6]:.6f}")
            print(f"월간 사용량: ${key[7]:.6f}")
            print(f"활성화: {'예' if key[8] else '아니오'}")
            print(f"생성일: {key[9]}")
            print("-" * 60)
    else:
        print("API 키가 없습니다.")

except Exception as e:
    print(f"오류 발생: {e}")

conn.close()