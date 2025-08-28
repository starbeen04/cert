"""
실제 사용량 로깅 서비스
"""
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db

class UsageLogger:
    """실제 사용량 로깅 서비스"""
    
    def __init__(self):
        self.pricing_config = {
            # OpenAI 가격 (2025년 기준)
            "openai": {
                "gpt-4": {"input": 0.00003, "output": 0.00006},  # per token
                "gpt-3.5-turbo": {"input": 0.0000005, "output": 0.0000015},
            },
            # Anthropic 가격 (2025년 기준) 
            "anthropic": {
                "claude-3-haiku-20240307": {"input": 0.00000025, "output": 0.00000125},
                "claude-3-sonnet-20241022": {"input": 0.000003, "output": 0.000015},
                "claude-3-5-sonnet-20241022": {"input": 0.000003, "output": 0.000015},
                "claude-3-opus-20240229": {"input": 0.000015, "output": 0.000075},
            }
        }
    
    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """실제 토큰 수를 기반으로 비용 계산"""
        
        # 모델별 가격 찾기
        pricing = None
        
        if "gpt-4" in model.lower():
            pricing = self.pricing_config["openai"]["gpt-4"]
        elif "gpt-3.5" in model.lower():
            pricing = self.pricing_config["openai"]["gpt-3.5-turbo"]
        elif "haiku" in model.lower():
            pricing = self.pricing_config["anthropic"]["claude-3-haiku-20240307"]
        elif "sonnet" in model.lower():
            if "3-5" in model:
                pricing = self.pricing_config["anthropic"]["claude-3-5-sonnet-20241022"]
            else:
                pricing = self.pricing_config["anthropic"]["claude-3-sonnet-20241022"]
        elif "opus" in model.lower():
            pricing = self.pricing_config["anthropic"]["claude-3-opus-20240229"]
        
        if not pricing:
            # 기본값 (Claude Haiku)
            pricing = self.pricing_config["anthropic"]["claude-3-haiku-20240307"]
        
        cost = (prompt_tokens * pricing["input"]) + (completion_tokens * pricing["output"])
        return round(cost, 6)
    
    def get_api_key_id(self, api_key: str) -> Optional[int]:
        """API 키로부터 ID 조회"""
        try:
            db = next(get_db())
            result = db.execute(
                text("SELECT id FROM api_keys WHERE api_key = :api_key AND is_active = 1"),
                {"api_key": api_key}
            ).fetchone()
            return result[0] if result else None
        except:
            return None
    
    def get_task_type(self, endpoint: str) -> str:
        """엔드포인트에서 작업 타입 추출"""
        if "chat" in endpoint:
            return "chat_completion"
        elif "analyze" in endpoint:
            return "document_analysis"
        elif "completion" in endpoint:
            return "text_completion"
        elif "generate" in endpoint:
            return "question_generation"
        else:
            return "general"
    
    async def log_real_usage(self, 
                           api_key: str,
                           endpoint: str, 
                           model: str,
                           prompt_tokens: int,
                           completion_tokens: int,
                           duration_seconds: float) -> bool:
        """실제 사용량 로깅"""
        
        try:
            # API 키 ID 조회
            api_key_id = self.get_api_key_id(api_key)
            if not api_key_id:
                print(f"[사용량 로깅] API 키를 찾을 수 없음: {api_key[:20]}...")
                return False
            
            # 비용 계산
            cost = self.calculate_cost(model, prompt_tokens, completion_tokens)
            total_tokens = prompt_tokens + completion_tokens
            
            # 데이터베이스 기록
            db = next(get_db())
            db.execute(
                text("""
                    INSERT INTO ai_usage_logs 
                    (api_key_id, task_type, model_used, prompt_tokens, completion_tokens, 
                     total_tokens, cost, duration_seconds, status, created_at)
                    VALUES (:api_key_id, :task_type, :model_used, :prompt_tokens, 
                            :completion_tokens, :total_tokens, :cost, :duration_seconds, 
                            :status, :created_at)
                """),
                {
                    "api_key_id": api_key_id,
                    "task_type": self.get_task_type(endpoint),
                    "model_used": model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "cost": cost,
                    "duration_seconds": duration_seconds,
                    "status": "success",
                    "created_at": datetime.now().isoformat()
                }
            )
            
            # API 키 사용량 업데이트
            db.execute(
                text("""
                    UPDATE api_keys 
                    SET current_daily_usage = current_daily_usage + :cost,
                        current_monthly_usage = current_monthly_usage + :cost,
                        updated_at = :updated_at
                    WHERE id = :api_key_id
                """),
                {
                    "cost": cost,
                    "api_key_id": api_key_id,
                    "updated_at": datetime.now().isoformat()
                }
            )
            
            db.commit()
            
            print(f"[사용량 로깅] 성공 - 모델: {model}, 토큰: {total_tokens}, 비용: ${cost:.6f}")
            return True
            
        except Exception as e:
            print(f"[사용량 로깅] 오류: {e}")
            return False

# 전역 인스턴스
usage_logger = UsageLogger()