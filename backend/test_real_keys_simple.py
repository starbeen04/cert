"""
실제 API 키를 사용한 사용량 추적 테스트 (간단 버전)
"""
import requests
import time
import sqlite3

def test_real_keys():
    """실제 API 키로 테스트"""
    
    # 실제 API 키들
    test_keys = [
        {
            "name": "OpenAI GPT API Key",
            "key": "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",
            "provider": "openai"
        },
        {
            "name": "Claude Anthropic API Key", 
            "key": "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",
            "provider": "anthropic"
        }
    ]
    
    # 테스트 호출
    test_calls = [
        {
            "endpoint": "/ai/chat",
            "data": {"message": "실제 API 키 테스트입니다."}
        },
        {
            "endpoint": "/ai/analyze", 
            "data": {"document": "실제 키로 문서 분석 테스트"}
        }
    ]
    
    print("=== 실제 API 키 테스트 ===")
    
    for key_info in test_keys:
        print(f"\n[{key_info['name']}] 테스트:")
        
        for call in test_calls:
            print(f"  {call['endpoint']} 호출... ", end="")
            
            try:
                response = requests.post(f"http://localhost:8000{call['endpoint']}", 
                    json=call['data'],
                    headers={
                        "X-API-KEY": key_info['key'],
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'usage' in result:
                        usage = result['usage']
                        print(f"성공 (모델: {result.get('model')}, 토큰: {usage.get('total_tokens')})")
                    else:
                        print("성공")
                else:
                    print(f"실패 ({response.status_code})")
                    
            except Exception as e:
                print(f"오류: {e}")
            
            time.sleep(0.3)

def check_usage():
    """사용량 확인"""
    print("\n=== 사용량 확인 ===")
    
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    # 최근 로그
    cursor.execute("""
        SELECT 
            ul.created_at,
            ak.key_name,
            ul.model_used,
            ul.total_tokens,
            ul.cost,
            ul.status
        FROM ai_usage_logs ul
        JOIN api_keys ak ON ul.api_key_id = ak.id
        ORDER BY ul.created_at DESC
        LIMIT 5
    """)
    
    logs = cursor.fetchall()
    
    if logs:
        print("\n[최근 사용 기록]")
        for i, log in enumerate(logs, 1):
            print(f"  {i}. {log[1]} - {log[2]} - 토큰:{log[3]} - 비용:${log[4]:.6f} - {log[5]}")
    
    # 키별 사용량
    cursor.execute("""
        SELECT 
            key_name,
            provider,
            current_daily_usage,
            current_monthly_usage,
            daily_limit,
            monthly_limit
        FROM api_keys
        WHERE is_active = 1
        ORDER BY id
    """)
    
    keys = cursor.fetchall()
    
    print("\n[키별 사용량]")
    for key in keys:
        print(f"  {key[0]} ({key[1]})")
        print(f"    일일: ${key[2]:.6f} / ${key[4]:.0f}")
        print(f"    월간: ${key[3]:.6f} / ${key[5]:.0f}")
    
    conn.close()

if __name__ == "__main__":
    test_real_keys()
    
    print("\n잠시 대기 중...")
    time.sleep(2)
    
    check_usage()
    print("\n=== 테스트 완료 ===")