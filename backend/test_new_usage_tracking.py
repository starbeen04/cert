"""
새로운 사용량 추적 시스템 테스트
- OpenAI Usage API 통합 테스트
- Anthropic Usage API 통합 테스트  
- 에이전트별 사용량 분리 테스트
- 실시간 모니터링 엔드포인트 테스트
"""
import asyncio
import httpx
import json
from datetime import datetime

class UsageTrackingTester:
    """사용량 추적 시스템 테스터"""
    
    def __init__(self):
        self.base_url = "http://localhost:8100"
        self.admin_token = None
    
    async def login_admin(self):
        """관리자 로그인"""
        
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/auth/login",
                    data=login_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.admin_token = data.get("access_token")
                    print("OK 관리자 로그인 성공")
                    return True
                else:
                    print(f"ERROR 관리자 로그인 실패: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                print(f"ERROR 로그인 요청 실패: {str(e)}")
                return False
    
    def get_auth_headers(self):
        """인증 헤더 반환"""
        if not self.admin_token:
            return {}
        return {"Authorization": f"Bearer {self.admin_token}"}
    
    async def test_health_check(self):
        """서비스 상태 확인 테스트"""
        
        print("\n🔍 서비스 상태 확인 테스트")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/admin/health-check",
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ 서비스 상태 확인 성공")
                    
                    health_status = data.get("health_status", {})
                    print(f"   - 통합 서비스 상태: {health_status.get('unified_service')}")
                    
                    components = health_status.get("components", {})
                    for component, status in components.items():
                        print(f"   - {component}: {status}")
                    
                    return True
                else:
                    print(f"❌ 서비스 상태 확인 실패: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ 서비스 상태 확인 요청 실패: {str(e)}")
                return False
    
    async def test_real_time_usage(self):
        """실시간 사용량 모니터링 테스트"""
        
        print("\n📊 실시간 사용량 모니터링 테스트")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/admin/real-time-usage?minutes=60&include_external=true",
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ 실시간 사용량 조회 성공")
                    
                    summary = data.get("summary", {})
                    print(f"   - 총 요청 수: {summary.get('total_requests', 0)}")
                    print(f"   - 총 비용: ${summary.get('total_cost', 0):.4f}")
                    print(f"   - 활성 에이전트: {summary.get('active_agents', 0)}")
                    print(f"   - 활성 사용자: {summary.get('active_users', 0)}")
                    print(f"   - 분당 요청: {summary.get('requests_per_minute', 0):.2f}")
                    
                    # 외부 메트릭 확인
                    external_metrics = data.get("external_metrics", {})
                    if external_metrics:
                        print("   - 외부 메트릭:")
                        if "openai" in external_metrics:
                            openai_status = "성공" if external_metrics["openai"].get("success") else "실패"
                            print(f"     - OpenAI: {openai_status}")
                        if "anthropic" in external_metrics:
                            anthropic_status = "성공" if external_metrics["anthropic"].get("success") else "실패"
                            print(f"     - Anthropic: {anthropic_status}")
                    
                    return True
                else:
                    print(f"❌ 실시간 사용량 조회 실패: {response.status_code}")
                    print(f"   응답 내용: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ 실시간 사용량 조회 요청 실패: {str(e)}")
                return False
    
    async def test_usage_sync(self):
        """사용량 동기화 테스트"""
        
        print("\n🔄 사용량 동기화 테스트")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/admin/usage-sync",
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ 사용량 동기화 성공")
                    
                    sync_result = data.get("sync_result", {})
                    if sync_result.get("success"):
                        print("   - 외부 API와 동기화 완료")
                        sync_results = sync_result.get("sync_results", {})
                        for provider, result in sync_results.items():
                            status = "성공" if result.get("success") else "실패"
                            print(f"     - {provider}: {status}")
                    
                    db_status = data.get("database_status", {})
                    print(f"   - 오늘 로그 수: {db_status.get('total_logs_today', 0)}")
                    print(f"   - 오늘 총 비용: ${db_status.get('total_cost_today', 0):.4f}")
                    
                    return True
                else:
                    print(f"❌ 사용량 동기화 실패: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ 사용량 동기화 요청 실패: {str(e)}")
                return False
    
    async def test_usage_tracking(self):
        """사용량 추적 시스템 테스트"""
        
        print("\n🧪 사용량 추적 시스템 테스트")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                # Anthropic 테스트
                response = await client.post(
                    f"{self.base_url}/api/admin/test-tracking?provider=anthropic&model=claude-3-haiku-20240307&agent_type=chat_assistant",
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Anthropic 사용량 추적 테스트 성공")
                    
                    test_result = data.get("test_result", {})
                    if test_result.get("success"):
                        usage = test_result.get("usage", {})
                        print(f"   - 토큰 사용량: {usage.get('total_tokens', 0)}")
                        print(f"   - 비용: ${test_result.get('cost', 0):.6f}")
                        print(f"   - 처리 시간: {test_result.get('duration', 0):.2f}초")
                    else:
                        print(f"   - 테스트 실패: {test_result.get('error')}")
                    
                    return True
                else:
                    print(f"❌ 사용량 추적 테스트 실패: {response.status_code}")
                    print(f"   응답 내용: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ 사용량 추적 테스트 요청 실패: {str(e)}")
                return False
    
    async def test_comprehensive_report(self):
        """종합 보고서 테스트"""
        
        print("\n📋 종합 보고서 테스트")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/admin/comprehensive-report?days=7&include_external=true",
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ 종합 보고서 생성 성공")
                    
                    report = data.get("report", {})
                    if report.get("success"):
                        internal_stats = report.get("internal_statistics", {})
                        print(f"   - 총 요청 수: {internal_stats.get('total_requests', 0)}")
                        print(f"   - 총 토큰: {internal_stats.get('total_tokens', 0):,}")
                        print(f"   - 총 비용: ${internal_stats.get('total_cost', 0):.4f}")
                        print(f"   - 고유 API 키: {internal_stats.get('unique_api_keys', 0)}")
                        print(f"   - 고유 에이전트: {internal_stats.get('unique_agents', 0)}")
                        print(f"   - 고유 사용자: {internal_stats.get('unique_users', 0)}")
                        
                        # 제공사별 비교
                        provider_comparison = report.get("provider_comparison", [])
                        if provider_comparison:
                            print("   - 제공사별 비교:")
                            for provider in provider_comparison:
                                print(f"     - {provider.get('provider')}: {provider.get('requests', 0)} 요청, ${provider.get('cost', 0):.4f}")
                    
                    return True
                else:
                    print(f"❌ 종합 보고서 생성 실패: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ 종합 보고서 생성 요청 실패: {str(e)}")
                return False
    
    async def test_monitoring_endpoints(self):
        """모니터링 엔드포인트 테스트"""
        
        print("\n📈 모니터링 엔드포인트 테스트")
        
        endpoints = [
            ("/api/monitoring/real-time-usage", "기본 실시간 사용량"),
            ("/api/monitoring/usage-api/sync", "외부 API 동기화"),
            ("/api/monitoring/usage-api/external-metrics", "외부 메트릭"),
            ("/api/monitoring/usage-api/agent-analytics", "에이전트 분석")
        ]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            success_count = 0
            
            for endpoint, name in endpoints:
                try:
                    response = await client.get(
                        f"{self.base_url}{endpoint}",
                        headers=self.get_auth_headers()
                    )
                    
                    if response.status_code == 200:
                        print(f"   ✅ {name}: 성공")
                        success_count += 1
                    else:
                        print(f"   ❌ {name}: 실패 ({response.status_code})")
                        
                except Exception as e:
                    print(f"   ❌ {name}: 요청 실패 - {str(e)}")
            
            print(f"\n모니터링 엔드포인트 테스트 결과: {success_count}/{len(endpoints)} 성공")
            return success_count == len(endpoints)
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        
        print("새로운 사용량 추적 시스템 테스트 시작")
        print("=" * 60)
        
        # 1. 관리자 로그인
        if not await self.login_admin():
            print("ERROR 관리자 로그인 실패로 테스트 중단")
            return
        
        test_results = []
        
        # 2. 각 테스트 실행
        test_methods = [
            ("서비스 상태 확인", self.test_health_check),
            ("실시간 사용량 모니터링", self.test_real_time_usage),
            ("사용량 동기화", self.test_usage_sync),
            ("사용량 추적 시스템", self.test_usage_tracking),
            ("종합 보고서", self.test_comprehensive_report),
            ("모니터링 엔드포인트", self.test_monitoring_endpoints)
        ]
        
        for test_name, test_method in test_methods:
            try:
                result = await test_method()
                test_results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} 테스트 중 오류: {str(e)}")
                test_results.append((test_name, False))
        
        # 3. 결과 요약
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약:")
        
        successful_tests = 0
        for test_name, result in test_results:
            status = "✅ 성공" if result else "❌ 실패"
            print(f"   - {test_name}: {status}")
            if result:
                successful_tests += 1
        
        total_tests = len(test_results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 전체 성공률: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 테스트 대부분이 성공했습니다! 시스템이 정상 작동 중입니다.")
        elif success_rate >= 50:
            print("⚠️  일부 테스트가 실패했습니다. 시스템을 점검해주세요.")
        else:
            print("🚨 많은 테스트가 실패했습니다. 시스템에 문제가 있을 수 있습니다.")

async def main():
    """메인 테스트 실행"""
    tester = UsageTrackingTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())