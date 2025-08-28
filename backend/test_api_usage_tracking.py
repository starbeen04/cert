"""
API 사용량 추적 테스트 스크립트
"""
import requests
import time
import json

# 테스트 API 키 생성
def create_test_api_key():
    """테스트용 API 키 생성"""
    response = requests.post("http://localhost:8000/api/keys/", json={
        "key_name": "테스트 사용량 추적",
        "provider": "openai",
        "api_key": "test-key-for-usage-tracking-12345",
        "monthly_limit": 100.0,
        "daily_limit": 10.0
    }, headers={
        "Authorization": "Bearer admin_token"  # 실제 admin 토큰 필요
    })
    return response.json() if response.status_code == 200 else None

# AI API 엔드포인트 테스트 호출
def test_ai_api_call():
    """AI API 호출 테스트 (사용량 추적 확인용)"""
    test_calls = [
        {
            "endpoint": "/ai/chat",
            "data": {"message": "안녕하세요! API 사용량 추적을 테스트하고 있습니다."}
        },
        {
            "endpoint": "/ai/analyze",
            "data": {"document": "이것은 테스트용 문서 내용입니다. AI가 분석할 예정입니다."}
        },
        {
            "endpoint": "/ai/completion",
            "data": {"prompt": "다음 문장을 완성해주세요: 인공지능의 미래는"}
        },
        {
            "endpoint": "/documents/analyze",
            "data": {"file_name": "test_document.pdf", "content": "테스트 문서 내용"}
        },
        {
            "endpoint": "/questions/generate",
            "data": {"topic": "컴퓨터 과학", "count": 3}
        }
    ]
    
    for call in test_calls:
        print(f"Testing endpoint: {call['endpoint']}")
        try:
            response = requests.post(f"http://localhost:8000{call['endpoint']}", 
                json=call['data'],
                headers={
                    "X-API-KEY": "test-key-for-usage-tracking-12345",
                    "Content-Type": "application/json"
                }
            )
            print(f"Response status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                if 'usage' in result:
                    usage = result['usage']
                    print(f"  Model: {result.get('model', 'unknown')}")
                    print(f"  Tokens: {usage.get('total_tokens', 0)} (Prompt: {usage.get('prompt_tokens', 0)}, Completion: {usage.get('completion_tokens', 0)})")
            time.sleep(0.5)  # 0.5초 대기
        except Exception as e:
            print(f"Error calling {call['endpoint']}: {e}")

# 사용량 통계 확인
def check_usage_stats():
    """사용량 통계 확인"""
    endpoints_to_check = [
        "/api/usage/summary",
        "/api/usage/realtime", 
        "/api/usage/alerts"
    ]
    
    for endpoint in endpoints_to_check:
        print(f"\n=== Checking {endpoint} ===")
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", 
                headers={"Authorization": "Bearer admin_token"}
            )
            if response.status_code == 200:
                data = response.json()
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(f"Error: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print("=== API 사용량 추적 시스템 테스트 ===\n")
    
    # 1. 테스트 API 키 생성 (선택사항)
    # create_test_api_key()
    
    # 2. AI API 호출 테스트
    print("1. AI API 호출 테스트...")
    test_ai_api_call()
    
    # 3. 잠깐 대기
    time.sleep(2)
    
    # 4. 사용량 통계 확인
    print("\n2. 사용량 통계 확인...")
    check_usage_stats()
    
    print("\n=== 테스트 완료 ===")