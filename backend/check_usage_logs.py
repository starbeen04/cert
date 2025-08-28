"""
사용량 로그 확인 스크립트
"""
import sqlite3
from datetime import datetime

# 데이터베이스 연결
conn = sqlite3.connect('cert_fast_test.db')
cursor = conn.cursor()

print("=== 최근 AI 사용량 로그 ===")

try:
    # 최근 로그 조회
    cursor.execute("""
        SELECT 
            created_at,
            task_type,
            model_used,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            cost,
            duration_seconds,
            status
        FROM ai_usage_logs
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    logs = cursor.fetchall()
    
    if logs:
        print(f"총 {len(logs)}개의 로그를 발견했습니다:")
        print()
        for i, log in enumerate(logs, 1):
            print(f"{i}. 시간: {log[0]}")
            print(f"   작업 타입: {log[1]}")
            print(f"   모델: {log[2]}")
            print(f"   토큰: {log[5]} (입력: {log[3]}, 출력: {log[4]})")
            print(f"   비용: ${log[6]:.6f}")
            print(f"   처리시간: {log[7]:.3f}초")
            print(f"   상태: {log[8]}")
            print("-" * 50)
    else:
        print("사용량 로그가 없습니다.")
        
        # 테이블이 존재하는지 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_usage_logs';")
        table_exists = cursor.fetchone()
        if table_exists:
            print("ai_usage_logs 테이블은 존재하지만 데이터가 없습니다.")
        else:
            print("ai_usage_logs 테이블이 존재하지 않습니다.")

except Exception as e:
    print(f"오류 발생: {e}")

# API 키 사용량 확인
print("\n=== API 키 사용량 현황 ===")
try:
    cursor.execute("""
        SELECT 
            id,
            key_name,
            current_daily_usage,
            current_monthly_usage,
            daily_limit,
            monthly_limit
        FROM api_keys
        WHERE api_key = 'test-key-for-usage-tracking-12345'
    """)
    
    key_data = cursor.fetchone()
    if key_data:
        print(f"API 키: {key_data[1]}")
        print(f"일일 사용량: ${key_data[2]:.6f} / ${key_data[4]:.2f}")
        print(f"월간 사용량: ${key_data[3]:.6f} / ${key_data[5]:.2f}")
    else:
        print("테스트 API 키를 찾을 수 없습니다.")

except Exception as e:
    print(f"API 키 조회 오류: {e}")

conn.close()
print("\n=== 확인 완료 ===")