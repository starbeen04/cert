"""
간단한 사용량 추적 시스템 테스트
"""
import asyncio
import httpx
import json
from datetime import datetime

async def test_endpoints():
    """엔드포인트 테스트"""
    
    base_url = "http://localhost:8100"
    
    # 관리자 로그인
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 로그인
        print("1. 관리자 로그인 시도...")
        try:
            login_response = await client.post(f"{base_url}/api/auth/token", data=login_data)
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                print("   로그인 성공")
            else:
                print(f"   로그인 실패: {login_response.status_code}")
                return
        except Exception as e:
            print(f"   로그인 오류: {e}")
            return
        
        # 2. 서비스 상태 확인
        print("\n2. 서비스 상태 확인...")
        try:
            response = await client.get(f"{base_url}/api/admin/health-check", headers=headers)
            if response.status_code == 200:
                data = response.json()
                health = data.get("health_status", {})
                print(f"   상태: {health.get('unified_service', 'unknown')}")
                components = health.get("components", {})
                for comp, status in components.items():
                    print(f"   - {comp}: {status}")
            else:
                print(f"   상태 확인 실패: {response.status_code}")
        except Exception as e:
            print(f"   상태 확인 오류: {e}")
        
        # 3. 실시간 사용량 조회
        print("\n3. 실시간 사용량 조회...")
        try:
            response = await client.get(f"{base_url}/api/admin/real-time-usage?minutes=60", headers=headers)
            if response.status_code == 200:
                data = response.json()
                summary = data.get("summary", {})
                print(f"   총 요청: {summary.get('total_requests', 0)}")
                print(f"   총 비용: ${summary.get('total_cost', 0):.4f}")
                print(f"   활성 에이전트: {summary.get('active_agents', 0)}")
            else:
                print(f"   실시간 사용량 조회 실패: {response.status_code}")
                print(f"   응답: {response.text[:200]}")
        except Exception as e:
            print(f"   실시간 사용량 조회 오류: {e}")
        
        # 4. 모니터링 엔드포인트 테스트
        print("\n4. 모니터링 엔드포인트 테스트...")
        endpoints = [
            "/api/monitoring/real-time-usage",
            "/api/monitoring/dashboard/overview",
            "/api/monitoring/dashboard/realtime-stats"
        ]
        
        for endpoint in endpoints:
            try:
                response = await client.get(f"{base_url}{endpoint}", headers=headers)
                status = "성공" if response.status_code == 200 else f"실패({response.status_code})"
                print(f"   {endpoint}: {status}")
            except Exception as e:
                print(f"   {endpoint}: 오류 - {e}")
        
        print("\n테스트 완료")

if __name__ == "__main__":
    asyncio.run(test_endpoints())