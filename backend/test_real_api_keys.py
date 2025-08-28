"""
실제 API 키를 사용한 사용량 추적 테스트
"""
import requests
import time
import json

def test_with_real_keys():
    """실제 API 키를 사용해서 테스트"""
    
    # 실제 API 키들 (데이터베이스에서 새로 추가한 키들)
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
    
    # AI API 엔드포인트들
    test_calls = [
        {
            "endpoint": "/ai/chat",
            "data": {"message": "실제 API 키를 사용한 테스트입니다."}
        },
        {
            "endpoint": "/ai/analyze", 
            "data": {"document": "실제 API 키로 문서 분석을 테스트합니다."}
        },
        {
            "endpoint": "/ai/completion",
            "data": {"prompt": "실제 API 키 테스트: 인공지능의 미래는"}
        }
    ]
    
    print("=== 실제 API 키를 사용한 사용량 추적 테스트 ===\n")
    
    for api_key_info in test_keys:
        print(f"[{api_key_info['name']}] ({api_key_info['provider']}) 테스트 중...")
        
        for call in test_calls:
            print(f"  -> {call['endpoint']} 호출...")
            
            try:
                response = requests.post(f"http://localhost:8000{call['endpoint']}", 
                    json=call['data'],
                    headers={
                        "X-API-KEY": api_key_info['key'],
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'usage' in result:
                        usage = result['usage']
                        print(f"     [성공] 모델: {result.get('model', 'unknown')} | 토큰: {usage.get('total_tokens', 0)}")
                    else:
                        print(f"     [성공] 응답 받음")
                else:
                    print(f"     [실패] 상태 코드: {response.status_code}")
                    
                time.sleep(0.5)  # 0.5초 대기
                
            except Exception as e:
                print(f"     [오류] {e}")
        
        print()

def check_real_usage():
    """실제 사용량 확인"""
    import sqlite3
    
    print("=== 실제 사용량 확인 ===")
    
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    try:
        # 최근 로그 확인
        cursor.execute("""
            SELECT 
                ul.created_at,
                ak.key_name,
                ak.provider,
                ul.task_type,
                ul.model_used,
                ul.total_tokens,
                ul.cost,
                ul.status
            FROM ai_usage_logs ul
            JOIN api_keys ak ON ul.api_key_id = ak.id
            ORDER BY ul.created_at DESC
            LIMIT 10
        """)
        
        logs = cursor.fetchall()
        
        if logs:
            print(f"📊 최근 {len(logs)}개 사용 기록:")
            for i, log in enumerate(logs[:5], 1):  # 최근 5개만 표시
                print(f"  {i}. {log[1]} ({log[2]})")
                print(f"     시간: {log[0]}")
                print(f"     작업: {log[3]} | 모델: {log[4]}")
                print(f"     토큰: {log[5]} | 비용: ${log[6]:.6f} | 상태: {log[7]}")
                print()
        
        # API 키별 총 사용량 확인
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
        
        print("💰 API 키별 사용량 현황:")
        for key in keys:
            daily_percent = (key[2] / key[4]) * 100 if key[4] > 0 else 0
            monthly_percent = (key[3] / key[5]) * 100 if key[5] > 0 else 0
            
            print(f"  🔑 {key[0]} ({key[1]})")
            print(f"     일일: ${key[2]:.6f} / ${key[4]:.0f} ({daily_percent:.2f}%)")
            print(f"     월간: ${key[3]:.6f} / ${key[5]:.0f} ({monthly_percent:.2f}%)")
            print()
    
    except Exception as e:
        print(f"오류: {e}")
    
    conn.close()

if __name__ == "__main__":
    # 1. 실제 키로 API 호출 테스트
    test_with_real_keys()
    
    # 잠깐 대기
    print("⏳ 사용량 기록 대기 중...")
    time.sleep(3)
    
    # 2. 사용량 확인
    check_real_usage()
    
    print("=== 테스트 완료 ===")