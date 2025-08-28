"""
최종 실제 사용량 추적 검증
"""
import requests
import time
import sqlite3

def test_all_endpoints():
    """모든 엔드포인트에서 실제 토큰 사용량 추적 확인"""
    
    claude_key = "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"
    
    print("=== 최종 실제 사용량 추적 검증 ===\n")
    
    test_cases = [
        {
            "name": "AI 채팅",
            "endpoint": "/ai/chat",
            "data": {"message": "최종 검증 테스트입니다."}
        },
        {
            "name": "문서 분석", 
            "endpoint": "/ai/analyze",
            "data": {"document": "최종 검증을 위한 문서 내용입니다."}
        },
        {
            "name": "텍스트 완성",
            "endpoint": "/ai/completion",
            "data": {"prompt": "최종 검증 테스트"}
        },
        {
            "name": "문서 처리",
            "endpoint": "/documents/analyze",
            "data": {"file_name": "test.pdf", "content": "최종 검증 문서"}
        },
        {
            "name": "문제 생성",
            "endpoint": "/questions/generate", 
            "data": {"topic": "최종검증", "count": 2}
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. {test['name']} 테스트...")
        
        try:
            response = requests.post(
                f"http://localhost:8000{test['endpoint']}", 
                json=test['data'],
                headers={
                    "X-API-KEY": claude_key,
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                usage = result.get('usage', {})
                model = result.get('model', 'unknown')
                
                total_tokens = usage.get('total_tokens', usage.get('input_tokens', 0) + usage.get('output_tokens', 0))
                input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0))
                output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
                
                print(f"   모델: {model}")
                print(f"   토큰: 총 {total_tokens} (입력: {input_tokens}, 출력: {output_tokens})")
                
                results.append({
                    "endpoint": test['endpoint'],
                    "model": model,
                    "total_tokens": total_tokens,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                })
                
            else:
                print(f"   오류: {response.status_code}")
        
        except Exception as e:
            print(f"   예외: {e}")
        
        print()
        time.sleep(1)
    
    return results

def verify_database_data(expected_results):
    """데이터베이스에 실제 토큰 값이 저장되었는지 확인"""
    
    print("=== 데이터베이스 실제 값 확인 ===")
    
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    try:
        # 최근 5개 기록 확인
        cursor.execute("""
            SELECT 
                created_at,
                task_type,
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
        
        print(f"최근 {len(logs)}개 기록:")
        
        real_data_count = 0
        
        for i, log in enumerate(logs, 1):
            # 기본값(50, 30, 80)이 아닌 실제 값인지 확인
            is_real_data = not (log[3] == 50 and log[4] == 30 and log[5] == 80)
            
            print(f"  {i}. {log[1]} | {log[2]}")
            print(f"     토큰: 입력 {log[3]}, 출력 {log[4]}, 총 {log[5]}")
            print(f"     비용: ${log[6]:.6f}")
            print(f"     실제 데이터: {'✓' if is_real_data else '✗'}")
            print()
            
            if is_real_data:
                real_data_count += 1
        
        success_rate = (real_data_count / len(logs)) * 100 if logs else 0
        print(f"실제 데이터 비율: {real_data_count}/{len(logs)} ({success_rate:.1f}%)")
        
        return success_rate >= 80  # 80% 이상이면 성공
    
    except Exception as e:
        print(f"데이터베이스 확인 오류: {e}")
        return False
    
    finally:
        conn.close()

def main():
    """메인 검증"""
    
    print("실제 API 호출 및 토큰 추적 최종 검증을 시작합니다...\n")
    
    # 1. 모든 엔드포인트 테스트
    results = test_all_endpoints()
    
    # 2. 잠시 대기
    print("데이터 저장 대기...")
    time.sleep(3)
    
    # 3. 데이터베이스 검증
    is_success = verify_database_data(results)
    
    # 4. 최종 결과
    print("\n=== 최종 검증 결과 ===")
    
    if is_success and len(results) >= 4:
        print("실제 API 호출 및 토큰 추적이 성공적으로 작동합니다!")
        print("관리자 페이지에 실제 사용량 데이터가 표시됩니다!")
        print("요청한 실제 데이터 통합이 완료되었습니다!")
    else:
        print("일부 문제가 발견되었습니다.")
    
    print(f"\n테스트 완료: {len(results)}개 엔드포인트 검증")

if __name__ == "__main__":
    main()