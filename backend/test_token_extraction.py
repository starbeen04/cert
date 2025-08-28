"""
토큰 추출 개선 테스트
"""
import requests
import time
import sqlite3

def test_improved_token_extraction():
    """개선된 토큰 추출 테스트"""
    
    claude_key = "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"
    
    print("=== 토큰 추출 개선 테스트 ===\n")
    
    # 간단한 테스트 호출
    test_calls = [
        {
            "endpoint": "/ai/chat",
            "data": {"message": "토큰 추출 테스트입니다."}
        },
        {
            "endpoint": "/ai/analyze",
            "data": {"document": "토큰 추출을 위한 문서 분석 테스트입니다."}
        }
    ]
    
    for i, call in enumerate(test_calls, 1):
        print(f"{i}. {call['endpoint']} 호출...")
        
        try:
            response = requests.post(
                f"http://localhost:8000{call['endpoint']}", 
                json=call['data'],
                headers={
                    "X-API-KEY": claude_key,
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                usage = result.get('usage', {})
                
                print(f"   [응답] 모델: {result.get('model')}")
                print(f"   [응답] 토큰: {usage.get('total_tokens')} (입력: {usage.get('prompt_tokens')}, 출력: {usage.get('completion_tokens')})")
            else:
                print(f"   [실패] {response.status_code}")
                
        except Exception as e:
            print(f"   [오류] {e}")
        
        print()
        time.sleep(1)
    
    # 잠시 대기
    print("데이터베이스 저장 대기...")
    time.sleep(3)
    
    # 데이터베이스에서 최근 기록 확인
    print("=== 데이터베이스 기록 확인 ===")
    
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                created_at,
                model_used,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                cost
            FROM ai_usage_logs
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        logs = cursor.fetchall()
        
        for i, log in enumerate(logs, 1):
            print(f"{i}. 시간: {log[0]}")
            print(f"   모델: {log[1]}")
            print(f"   토큰: 입력 {log[2]}, 출력 {log[3]}, 총 {log[4]}")
            print(f"   비용: ${log[5]:.6f}")
            print()
    
    except Exception as e:
        print(f"오류: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_improved_token_extraction()