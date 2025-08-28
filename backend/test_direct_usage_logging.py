"""
직접 사용량 로깅 테스트
"""
import asyncio
import sqlite3
from app.services.usage_logger import usage_logger

async def test_direct_logging():
    """직접 로깅 테스트"""
    
    print("=== 직접 사용량 로깅 테스트 ===\n")
    
    # 테스트 API 키
    test_api_key = "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"
    
    # 실제 토큰 값으로 로깅 테스트
    result = await usage_logger.log_real_usage(
        api_key=test_api_key,
        endpoint="/ai/chat",
        model="claude-3-haiku-20240307",
        prompt_tokens=25,  # 실제 값
        completion_tokens=45,  # 실제 값
        duration_seconds=1.5
    )
    
    print(f"로깅 결과: {result}")
    
    # 데이터베이스에서 확인
    print("\n=== 저장된 데이터 확인 ===")
    
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                created_at,
                model_used,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                cost
            FROM ai_usage_logs
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        log = cursor.fetchone()
        
        if log:
            print(f"최신 기록:")
            print(f"  시간: {log[0]}")
            print(f"  모델: {log[1]}")
            print(f"  토큰: 입력 {log[2]}, 출력 {log[3]}, 총 {log[4]}")
            print(f"  비용: ${log[5]:.6f}")
            
            # 실제 값과 비교
            if log[2] == 25 and log[3] == 45:
                print("\n✅ 실제 토큰 값이 정확히 저장되었습니다!")
            else:
                print(f"\n❌ 토큰 값 불일치: 예상 (25, 45) vs 실제 ({log[2]}, {log[3]})")
        else:
            print("기록이 없습니다.")
    
    except Exception as e:
        print(f"오류: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(test_direct_logging())