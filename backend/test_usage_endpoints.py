"""
사용량 API 엔드포인트 테스트 (관리자 인증 포함)
"""
import requests
import json

# 관리자 로그인하여 토큰 받기
def get_admin_token():
    """관리자 토큰 획득"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(
        "http://localhost:8000/api/auth/token",
        data=login_data,  # form data로 전송
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get("access_token")
    else:
        print(f"로그인 실패: {response.status_code}")
        return None

def test_usage_endpoints():
    """사용량 API 엔드포인트 테스트"""
    
    # 1. 관리자 토큰 획득
    print("1. 관리자 로그인...")
    token = get_admin_token()
    if not token:
        print("관리자 토큰을 받을 수 없습니다.")
        return
    
    print(f"토큰 받음: {token[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 2. 테스트할 엔드포인트들
    endpoints = [
        ("사용량 요약", "GET", "/api/usage/summary", None),
        ("실시간 사용량", "GET", "/api/usage/realtime", None), 
        ("사용량 알림", "GET", "/api/usage/alerts", None),
        ("비용 트렌드", "GET", "/api/usage/trends?days=7", None),
        ("특정 API 키 통계", "GET", "/api/usage/stats/7?days=7", None)
    ]
    
    print("\n2. 사용량 API 엔드포인트 테스트...")
    for name, method, endpoint, data in endpoints:
        print(f"\n=== {name} ({endpoint}) ===")
        
        try:
            if method == "GET":
                response = requests.get(f"http://localhost:8000{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(f"http://localhost:8000{endpoint}", headers=headers, json=data)
            
            print(f"응답 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("성공!")
                
                # 중요한 정보만 출력
                if "summary" in result:
                    summary = result["summary"]
                    print(f"  총 API 키: {summary.get('total_api_keys', 0)}개")
                    print(f"  월간 총 사용량: ${summary.get('total_monthly_usage', 0):.6f}")
                    print(f"  일간 총 사용량: ${summary.get('total_daily_usage', 0):.6f}")
                    print(f"  오늘 요청 수: {summary.get('total_today_requests', 0)}개")
                    print(f"  활성 키: {summary.get('active_keys', 0)}개")
                
                elif "totals" in result:  # realtime
                    totals = result["totals"]
                    print(f"  최근 1시간 요청: {totals.get('requests', 0)}개")
                    print(f"  최근 1시간 비용: ${totals.get('cost', 0):.6f}")
                    print(f"  활성 키: {totals.get('active_keys', 0)}개")
                
                elif "total_alerts" in result:  # alerts
                    print(f"  총 알림: {result.get('total_alerts', 0)}개")
                    print(f"  중요 알림: {result.get('critical_count', 0)}개")
                    print(f"  경고: {result.get('warning_count', 0)}개")
                
                elif "basic_stats" in result:  # specific key stats
                    stats = result["basic_stats"]
                    print(f"  총 요청: {stats.get('total_requests', 0)}개")
                    print(f"  총 비용: ${stats.get('total_cost', 0):.6f}")
                    print(f"  총 토큰: {stats.get('total_tokens', 0):,}개")
                    print(f"  성공률: {stats.get('success_rate', 0):.1f}%")
                
                else:
                    # 기본 정보 출력 (너무 길지 않게)
                    if len(str(result)) < 500:
                        print(f"  응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    else:
                        print(f"  응답 크기: {len(str(result))}자 (내용 생략)")
                        
            else:
                print(f"오류: {response.text}")
                
        except Exception as e:
            print(f"요청 실패: {e}")

if __name__ == "__main__":
    print("=== 사용량 API 엔드포인트 테스트 ===")
    test_usage_endpoints()
    print("\n=== 테스트 완료 ===")