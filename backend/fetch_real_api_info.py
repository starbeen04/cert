"""
실제 API 키 정보 수집 스크립트
"""
import requests
import json
from datetime import datetime, timedelta
import sqlite3

class APIKeyInfoFetcher:
    """실제 API 키 정보를 가져오는 클래스"""
    
    def __init__(self):
        self.openai_key = "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"
        self.claude_key = "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"
    
    def fetch_openai_info(self):
        """OpenAI API 키 정보 수집"""
        print("=== OpenAI API 키 정보 수집 ===")
        
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        # 1. 구독 정보 조회
        print("1. 구독 정보 조회 중...")
        try:
            response = requests.get(
                "https://api.openai.com/v1/dashboard/billing/subscription",
                headers=headers
            )
            print(f"   상태 코드: {response.status_code}")
            if response.status_code == 200:
                subscription_data = response.json()
                print(f"   구독 정보: {json.dumps(subscription_data, indent=2, ensure_ascii=False)}")
            else:
                print(f"   오류: {response.text}")
        except Exception as e:
            print(f"   예외 발생: {e}")
        
        # 2. 사용량 조회 (이번 달)
        print("\n2. 이번 달 사용량 조회 중...")
        try:
            # 이번 달 첫날부터 오늘까지
            start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            response = requests.get(
                f"https://api.openai.com/v1/usage?start_date={start_date}&end_date={end_date}",
                headers=headers
            )
            print(f"   상태 코드: {response.status_code}")
            if response.status_code == 200:
                usage_data = response.json()
                print(f"   사용량 정보: {json.dumps(usage_data, indent=2, ensure_ascii=False)}")
            else:
                print(f"   오류: {response.text}")
        except Exception as e:
            print(f"   예외 발생: {e}")
        
        # 3. 크레딧/잔액 조회
        print("\n3. 크레딧/잔액 조회 중...")
        try:
            response = requests.get(
                "https://api.openai.com/v1/dashboard/billing/credit_grants",
                headers=headers
            )
            print(f"   상태 코드: {response.status_code}")
            if response.status_code == 200:
                credit_data = response.json()
                print(f"   크레딧 정보: {json.dumps(credit_data, indent=2, ensure_ascii=False)}")
            else:
                print(f"   오류: {response.text}")
        except Exception as e:
            print(f"   예외 발생: {e}")
    
    def test_openai_call_with_headers(self):
        """OpenAI API 호출하여 헤더에서 제한 정보 추출"""
        print("\n=== OpenAI API 호출 - 헤더 정보 확인 ===")
        
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Hello, this is a test."}
            ],
            "max_tokens": 10
        }
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            print(f"응답 상태: {response.status_code}")
            
            # 중요한 헤더들 출력
            important_headers = [
                'x-ratelimit-limit-requests',
                'x-ratelimit-remaining-requests', 
                'x-ratelimit-limit-tokens',
                'x-ratelimit-remaining-tokens',
                'x-ratelimit-reset-requests',
                'x-ratelimit-reset-tokens'
            ]
            
            print("Rate Limit 헤더:")
            for header in important_headers:
                value = response.headers.get(header)
                if value:
                    print(f"  {header}: {value}")
            
            if response.status_code == 200:
                result = response.json()
                usage = result.get('usage', {})
                print(f"\n사용량 정보:")
                print(f"  입력 토큰: {usage.get('prompt_tokens', 0)}")
                print(f"  출력 토큰: {usage.get('completion_tokens', 0)}")
                print(f"  총 토큰: {usage.get('total_tokens', 0)}")
            else:
                print(f"오류: {response.text}")
                
        except Exception as e:
            print(f"예외 발생: {e}")
    
    def test_claude_call_with_usage(self):
        """Claude API 호출하여 사용량 정보 추출"""
        print("\n=== Claude API 호출 - 사용량 정보 확인 ===")
        
        headers = {
            "x-api-key": self.claude_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 10,
            "messages": [
                {"role": "user", "content": "Hello, this is a test."}
            ]
        }
        
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data
            )
            
            print(f"응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                usage = result.get('usage', {})
                print(f"\nClaude 사용량 정보:")
                print(f"  입력 토큰: {usage.get('input_tokens', 0)}")
                print(f"  출력 토큰: {usage.get('output_tokens', 0)}")
                print(f"  총 토큰: {usage.get('input_tokens', 0) + usage.get('output_tokens', 0)}")
                
                # 응답 헤더에서 제한 정보 확인
                print(f"\n응답 헤더:")
                for key, value in response.headers.items():
                    if 'limit' in key.lower() or 'usage' in key.lower() or 'anthropic' in key.lower():
                        print(f"  {key}: {value}")
            else:
                print(f"오류: {response.text}")
                
        except Exception as e:
            print(f"예외 발생: {e}")
    
    def update_database_with_real_info(self, openai_data=None, claude_data=None):
        """실제 정보로 데이터베이스 업데이트"""
        print("\n=== 데이터베이스 업데이트 ===")
        
        conn = sqlite3.connect('cert_fast_test.db')
        cursor = conn.cursor()
        
        try:
            # 실제 정보가 있으면 업데이트
            if openai_data:
                cursor.execute("""
                    UPDATE api_keys 
                    SET daily_limit = ?, monthly_limit = ?, updated_at = ?
                    WHERE provider = 'openai'
                """, (
                    openai_data.get('daily_limit', 50),
                    openai_data.get('monthly_limit', 500),
                    datetime.now().isoformat()
                ))
                print(f"OpenAI 키 정보 업데이트됨")
            
            if claude_data:
                cursor.execute("""
                    UPDATE api_keys 
                    SET daily_limit = ?, monthly_limit = ?, updated_at = ?
                    WHERE provider = 'anthropic'
                """, (
                    claude_data.get('daily_limit', 100),
                    claude_data.get('monthly_limit', 1000),
                    datetime.now().isoformat()
                ))
                print(f"Claude 키 정보 업데이트됨")
            
            conn.commit()
            print("데이터베이스 업데이트 완료")
            
        except Exception as e:
            print(f"데이터베이스 업데이트 오류: {e}")
        finally:
            conn.close()

def main():
    """메인 함수"""
    fetcher = APIKeyInfoFetcher()
    
    print("실제 API 키 정보 수집 시작...\n")
    
    # OpenAI 정보 수집
    fetcher.fetch_openai_info()
    
    # OpenAI API 테스트 호출
    fetcher.test_openai_call_with_headers()
    
    # Claude API 테스트 호출  
    fetcher.test_claude_call_with_usage()
    
    print("\n=== 정보 수집 완료 ===")

if __name__ == "__main__":
    main()