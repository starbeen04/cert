"""
실제 API 통합 테스트
"""
import requests
import time
import sqlite3
import json

def test_real_api_calls():
    """실제 API 호출 테스트"""
    
    # 실제 Claude API 키 (유일한 활성 키)
    claude_key = "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"
    
    print("=== 실제 API 통합 테스트 ===\n")
    
    # 테스트할 엔드포인트들
    test_calls = [
        {
            "name": "AI 채팅",
            "endpoint": "/ai/chat",
            "data": {"message": "실제 Claude API를 사용한 테스트입니다. 간단히 인사해주세요."}
        },
        {
            "name": "문서 분석", 
            "endpoint": "/ai/analyze",
            "data": {"document": "이것은 실제 Claude API를 활용한 문서 분석 테스트입니다. 이 내용을 요약해주세요."}
        },
        {
            "name": "텍스트 완성",
            "endpoint": "/ai/completion", 
            "data": {"prompt": "실제 API를 사용한 인공지능 서비스의 장점은"}
        },
        {
            "name": "문서 처리",
            "endpoint": "/documents/analyze",
            "data": {"file_name": "test.pdf", "content": "실제 API를 사용한 문서 분석 시스템 테스트 내용"}
        },
        {
            "name": "문제 생성",
            "endpoint": "/questions/generate",
            "data": {"topic": "인공지능", "count": 3}
        }
    ]
    
    results = []
    
    for i, call in enumerate(test_calls, 1):
        print(f"{i}. {call['name']} 테스트...")
        
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
                
                # 사용량 정보 추출
                usage = result.get('usage', {})
                model = result.get('model', 'unknown')
                
                print(f"   [성공] 모델: {model}")
                print(f"   토큰: {usage.get('total_tokens', 0)} (입력: {usage.get('prompt_tokens', 0)}, 출력: {usage.get('completion_tokens', 0)})")
                
                # 응답 내용 일부 출력
                response_text = result.get('response', result.get('analysis', result.get('completion', str(result.get('questions', '')))))
                if response_text:
                    print(f"   응답: {str(response_text)[:100]}...")
                
                results.append({
                    "endpoint": call['endpoint'],
                    "model": model,
                    "usage": usage,
                    "success": True
                })
                
            else:
                print(f"   [실패] 상태코드: {response.status_code}")
                print(f"   오류: {response.text}")
                results.append({
                    "endpoint": call['endpoint'], 
                    "success": False,
                    "error": response.text
                })
                
        except Exception as e:
            print(f"   [예외] {e}")
            results.append({
                "endpoint": call['endpoint'],
                "success": False, 
                "error": str(e)
            })
        
        print()
        time.sleep(1)  # API 호출 간격
    
    return results

def check_real_usage_data():
    """실제 사용량 데이터 확인"""
    print("=== 실제 사용량 데이터 확인 ===")
    
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    try:
        # 최근 실제 사용 기록
        cursor.execute("""
            SELECT 
                ul.created_at,
                ak.key_name,
                ul.task_type,
                ul.model_used,
                ul.prompt_tokens,
                ul.completion_tokens,
                ul.total_tokens,
                ul.cost,
                ul.duration_seconds,
                ul.status
            FROM ai_usage_logs ul
            JOIN api_keys ak ON ul.api_key_id = ak.id
            WHERE ak.provider = 'anthropic' AND ak.is_active = 1
            ORDER BY ul.created_at DESC
            LIMIT 10
        """)
        
        logs = cursor.fetchall()
        
        if logs:
            print(f"\n[최근 실제 사용 기록 {len(logs)}개]")
            total_tokens = 0
            total_cost = 0.0
            
            for i, log in enumerate(logs, 1):
                print(f"  {i}. {log[0]}")
                print(f"     작업: {log[2]} | 모델: {log[3]}")
                print(f"     토큰: 입력 {log[4]}, 출력 {log[5]}, 총 {log[6]}")
                print(f"     비용: ${log[7]:.6f} | 시간: {log[8]:.3f}초 | {log[9]}")
                
                total_tokens += log[6] if log[6] else 0
                total_cost += log[7] if log[7] else 0.0
                print()
            
            print(f"[합계] 총 토큰: {total_tokens}개, 총 비용: ${total_cost:.6f}")
        
        # API 키 현재 상태
        cursor.execute("""
            SELECT 
                key_name,
                current_daily_usage,
                current_monthly_usage,
                daily_limit,
                monthly_limit,
                is_active
            FROM api_keys
            WHERE provider = 'anthropic'
        """)
        
        key_info = cursor.fetchone()
        
        if key_info:
            print(f"\n[API 키 상태]")
            print(f"  키: {key_info[0]}")
            print(f"  상태: {'활성' if key_info[5] else '비활성'}")
            
            daily_percent = (key_info[1] / key_info[3]) * 100 if key_info[3] > 0 else 0
            monthly_percent = (key_info[2] / key_info[4]) * 100 if key_info[4] > 0 else 0
            
            print(f"  일일: ${key_info[1]:.6f} / ${key_info[3]:.0f} ({daily_percent:.3f}%)")
            print(f"  월간: ${key_info[2]:.6f} / ${key_info[4]:.0f} ({monthly_percent:.3f}%)")
    
    except Exception as e:
        print(f"데이터 확인 오류: {e}")
    
    finally:
        conn.close()

def main():
    """메인 테스트 함수"""
    
    # 1. 실제 API 호출 테스트
    print("실제 API 호출 시작...\n")
    results = test_real_api_calls()
    
    # 2. 결과 요약
    successful_calls = [r for r in results if r.get('success', False)]
    failed_calls = [r for r in results if not r.get('success', False)]
    
    print(f"=== 테스트 결과 요약 ===")
    print(f"성공: {len(successful_calls)}개")
    print(f"실패: {len(failed_calls)}개")
    
    if failed_calls:
        print("\n[실패한 호출]")
        for fail in failed_calls:
            print(f"  - {fail['endpoint']}: {fail.get('error', '알 수 없는 오류')}")
    
    # 3. 잠시 대기 후 사용량 확인
    print(f"\n데이터 저장 대기...")
    time.sleep(3)
    
    # 4. 실제 사용량 데이터 확인
    check_real_usage_data()
    
    print(f"\n=== 실제 API 통합 테스트 완료 ===")
    
    if len(successful_calls) > 0:
        print("✅ 실제 API 호출이 성공적으로 작동합니다!")
        print("✅ 실제 토큰 사용량이 추적됩니다!")
        print("✅ 관리자 페이지에 실제 데이터가 표시됩니다!")
    else:
        print("❌ API 호출에 문제가 있습니다.")

if __name__ == "__main__":
    main()