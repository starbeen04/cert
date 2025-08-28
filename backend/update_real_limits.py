"""
실제 API 키 한도 정보로 데이터베이스 업데이트
"""
import sqlite3
from datetime import datetime

def update_real_api_limits():
    """실제 API 한도 정보로 업데이트"""
    
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    try:
        # 1. OpenAI 키 - 유효하지 않으므로 비활성화
        print("1. OpenAI API 키 비활성화...")
        cursor.execute("""
            UPDATE api_keys 
            SET is_active = 0, 
                updated_at = ?,
                key_name = 'OpenAI GPT API Key (비활성화 - 유효하지 않은 키)'
            WHERE provider = 'openai'
        """, (datetime.now().isoformat(),))
        
        openai_affected = cursor.rowcount
        print(f"   OpenAI 키 {openai_affected}개 비활성화됨")
        
        # 2. Claude 키 - 실제 정보로 업데이트
        print("\n2. Claude API 키 실제 정보로 업데이트...")
        
        # Claude 실제 한도 (응답 헤더에서 확인한 값들)
        # - 입력 토큰: 200,000/분 = 288,000,000/일 (1440분)
        # - 출력 토큰: 40,000/분 = 57,600,000/일
        # - 요청: 2,000/분 = 2,880,000/일
        # - 총 토큰: 240,000/분 = 345,600,000/일
        
        # 실제 비용으로 계산 (Claude 3 Haiku: $0.25 per MTok input, $1.25 per MTok output)
        # 일일 한도: 입력 200M * $0.25 = $50 + 출력 40M * $1.25 = $50 = 총 $100
        # 월간 한도: $100 * 30 = $3000 (보수적으로 $1000으로 설정)
        
        cursor.execute("""
            UPDATE api_keys 
            SET daily_limit = 100.0,
                monthly_limit = 1000.0,
                is_active = 1,
                key_name = 'Claude Anthropic API Key (활성)',
                updated_at = ?
            WHERE provider = 'anthropic'
        """, (datetime.now().isoformat(),))
        
        claude_affected = cursor.rowcount
        print(f"   Claude 키 {claude_affected}개 업데이트됨")
        print(f"     - 일일 한도: $100 (실제 토큰 한도 기반)")
        print(f"     - 월간 한도: $1000 (실제 토큰 한도 기반)")
        print(f"     - 분당 요청: 2,000개")
        print(f"     - 분당 토큰: 240,000개")
        
        # 3. 실제 키만 남겨두기 위해 다른 키들 정리
        print("\n3. 사용 가능한 API 키 확인...")
        cursor.execute("""
            SELECT id, key_name, provider, is_active, daily_limit, monthly_limit
            FROM api_keys
            ORDER BY id
        """)
        
        keys = cursor.fetchall()
        print(f"   총 {len(keys)}개 키:")
        
        for key in keys:
            status = "활성" if key[3] else "비활성"
            print(f"   - ID {key[0]}: {key[1]} ({key[2]}) - {status}")
            print(f"     일일: ${key[4]:.0f}, 월간: ${key[5]:.0f}")
        
        conn.commit()
        print(f"\n=== 업데이트 완료 ===")
        print(f"현재 활성 키: Claude API만 사용 가능")
        print(f"OpenAI 키는 유효하지 않아 비활성화됨")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== 실제 API 키 한도 정보 업데이트 ===\n")
    update_real_api_limits()