"""
새로운 서비스들을 직접 테스트
인증 없이 서비스 로직만 테스트
"""
import asyncio
import sys
import os

# 현재 디렉토리를 파이썬 패스에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.openai_usage_api import openai_usage_api
from app.services.anthropic_usage_api import anthropic_usage_api
from app.services.unified_usage_service import unified_usage_service

async def test_openai_service():
    """OpenAI Usage API 서비스 테스트"""
    print("OpenAI Usage API 서비스 테스트...")
    
    try:
        # 실시간 메트릭 조회 테스트
        result = await openai_usage_api.get_realtime_metrics(
            api_key="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",
            minutes=60
        )
        
        if result.get("success"):
            print("  OK OpenAI 실시간 메트릭 조회 성공")
            summary = result.get("summary", {})
            print(f"    - 총 요청: {summary.get('total_requests', 0)}")
            print(f"    - 총 토큰: {summary.get('total_tokens', 0)}")
            print(f"    - 분당 요청: {summary.get('requests_per_minute', 0):.2f}")
        else:
            print(f"  ERROR OpenAI 메트릭 조회 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"  ERROR OpenAI 서비스 테스트 오류: {e}")

async def test_anthropic_service():
    """Anthropic Usage API 서비스 테스트"""
    print("\nAnthropic Usage API 서비스 테스트...")
    
    try:
        # 실시간 메트릭 조회 테스트
        result = await anthropic_usage_api.get_realtime_metrics(
            admin_api_key="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",
            hours=1
        )
        
        if result.get("success"):
            print("  OK Anthropic 실시간 메트릭 조회 성공")
            summary = result.get("summary", {})
            print(f"    - 총 요청: {summary.get('total_requests', 0)}")
            print(f"    - 총 토큰: {summary.get('total_tokens', 0)}")
            print(f"    - 총 비용: ${summary.get('total_cost_usd', 0):.6f}")
        else:
            print(f"  ERROR Anthropic 메트릭 조회 실패: {result.get('error', result)}")
            
    except Exception as e:
        print(f"  ERROR Anthropic 서비스 테스트 오류: {e}")

async def test_unified_service():
    """통합 서비스 테스트"""
    print("\n통합 사용량 서비스 테스트...")
    
    try:
        # 서비스 상태 확인
        health_result = await unified_usage_service.health_check()
        
        print(f"  통합 서비스 상태: {health_result.get('unified_service')}")
        
        components = health_result.get("components", {})
        for component, status in components.items():
            print(f"    - {component}: {status}")
            
    except Exception as e:
        print(f"  ERROR 통합 서비스 테스트 오류: {e}")

async def test_simple_anthropic_call():
    """간단한 Anthropic API 호출 테스트"""
    print("\n간단한 Anthropic API 호출 테스트...")
    
    try:
        from app.services.enhanced_usage_tracker import enhanced_usage_tracker
        
        test_messages = [
            {"role": "user", "content": "Hello, this is a test message. Please respond briefly."}
        ]
        
        result = await enhanced_usage_tracker.track_anthropic_usage(
            api_key="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",
            messages=test_messages,
            model="claude-3-haiku-20240307"
        )
        
        if result.get("success"):
            print("  OK Anthropic API 호출 성공")
            usage = result.get("usage", {})
            print(f"    - 입력 토큰: {usage.get('input_tokens', 0)}")
            print(f"    - 출력 토큰: {usage.get('output_tokens', 0)}")
            print(f"    - 비용: ${result.get('cost', 0):.6f}")
            print(f"    - 응답: {result.get('response', '')[:100]}...")
        else:
            print(f"  ERROR Anthropic API 호출 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"  ERROR Anthropic API 호출 테스트 오류: {e}")

async def main():
    """모든 서비스 테스트 실행"""
    print("새로운 사용량 추적 서비스들 직접 테스트")
    print("=" * 50)
    
    await test_openai_service()
    await test_anthropic_service() 
    await test_unified_service()
    await test_simple_anthropic_call()
    
    print("\n테스트 완료")

if __name__ == "__main__":
    asyncio.run(main())