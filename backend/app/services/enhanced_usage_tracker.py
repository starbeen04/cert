"""
향상된 실제 사용량 추적 서비스
- API 응답에서 더 정확한 토큰 추출
- Rate limit 헤더 정보 활용  
- 외부 토큰 계산기 사용
- 실제 빌링과 일치하는 정확한 추적
"""
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db

class EnhancedUsageTracker:
    """향상된 실제 사용량 추적 서비스"""
    
    def __init__(self):
        # Anthropic 요금 정보 (2025년 기준)
        self.anthropic_pricing = {
            "claude-3-haiku-20240307": {"input": 0.00000025, "output": 0.00000125},
            "claude-3-sonnet-20241022": {"input": 0.000003, "output": 0.000015},
            "claude-3-5-sonnet-20241022": {"input": 0.000003, "output": 0.000015},
            "claude-3-opus-20240229": {"input": 0.000015, "output": 0.000075},
        }
        
        # OpenAI 요금 정보 (2025년 기준)  
        self.openai_pricing = {
            "gpt-4": {"input": 0.00003, "output": 0.00006},
            "gpt-4-turbo": {"input": 0.00001, "output": 0.00003},
            "gpt-3.5-turbo": {"input": 0.0000005, "output": 0.0000015},
        }
    
    async def track_anthropic_usage(self, api_key: str, messages: list, model: str = "claude-3-haiku-20240307") -> Dict[str, Any]:
        """Anthropic API 호출 및 정확한 사용량 추적"""
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": model,
            "max_tokens": 150,
            "messages": messages
        }
        
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Anthropic 응답에서 정확한 사용량 추출
                    usage_data = data.get("usage", {})
                    input_tokens = usage_data.get("input_tokens", 0)
                    output_tokens = usage_data.get("output_tokens", 0)
                    total_tokens = input_tokens + output_tokens
                    
                    # Rate limit 정보 추출
                    rate_limit_info = self._extract_anthropic_rate_limits(response.headers)
                    
                    # 정확한 비용 계산
                    pricing = self.anthropic_pricing.get(model, self.anthropic_pricing["claude-3-haiku-20240307"])
                    cost = (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])
                    
                    # 응답 텍스트 추출
                    response_text = ""
                    if "content" in data and len(data["content"]) > 0:
                        response_text = data["content"][0].get("text", "")
                    
                    return {
                        "success": True,
                        "provider": "anthropic",
                        "model": model,
                        "response": response_text,
                        "usage": {
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens, 
                            "total_tokens": total_tokens,
                            "prompt_tokens": input_tokens,  # 호환성
                            "completion_tokens": output_tokens  # 호환성
                        },
                        "cost": cost,
                        "duration_seconds": duration,
                        "rate_limits": rate_limit_info,
                        "timestamp": end_time.isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def track_openai_usage(self, api_key: str, messages: list, model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """OpenAI API 호출 및 정확한 사용량 추적"""
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 150
        }
        
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # OpenAI 응답에서 정확한 사용량 추출
                    usage_data = data.get("usage", {})
                    prompt_tokens = usage_data.get("prompt_tokens", 0)
                    completion_tokens = usage_data.get("completion_tokens", 0)
                    total_tokens = usage_data.get("total_tokens", prompt_tokens + completion_tokens)
                    
                    # Rate limit 정보 추출
                    rate_limit_info = self._extract_openai_rate_limits(response.headers)
                    
                    # 정확한 비용 계산
                    pricing = self.openai_pricing.get(model, self.openai_pricing["gpt-3.5-turbo"])
                    cost = (prompt_tokens * pricing["input"]) + (completion_tokens * pricing["output"])
                    
                    # 응답 텍스트 추출
                    response_text = ""
                    if "choices" in data and len(data["choices"]) > 0:
                        response_text = data["choices"][0]["message"]["content"]
                    
                    return {
                        "success": True,
                        "provider": "openai", 
                        "model": model,
                        "response": response_text,
                        "usage": {
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": total_tokens,
                            "input_tokens": prompt_tokens,  # 호환성
                            "output_tokens": completion_tokens  # 호환성
                        },
                        "cost": cost,
                        "duration_seconds": duration,
                        "rate_limits": rate_limit_info,
                        "timestamp": end_time.isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_anthropic_rate_limits(self, headers: Dict) -> Dict[str, Any]:
        """Anthropic 응답 헤더에서 Rate limit 정보 추출"""
        rate_limits = {}
        
        # Anthropic rate limit 헤더들
        rate_limit_headers = [
            "anthropic-ratelimit-requests-limit",
            "anthropic-ratelimit-requests-remaining",
            "anthropic-ratelimit-requests-reset",
            "anthropic-ratelimit-tokens-limit", 
            "anthropic-ratelimit-tokens-remaining",
            "anthropic-ratelimit-tokens-reset",
            "anthropic-ratelimit-input-tokens-limit",
            "anthropic-ratelimit-input-tokens-remaining",
            "anthropic-ratelimit-output-tokens-limit",
            "anthropic-ratelimit-output-tokens-remaining"
        ]
        
        for header in rate_limit_headers:
            if header in headers:
                rate_limits[header] = headers[header]
        
        return rate_limits
    
    def _extract_openai_rate_limits(self, headers: Dict) -> Dict[str, Any]:
        """OpenAI 응답 헤더에서 Rate limit 정보 추출"""
        rate_limits = {}
        
        # OpenAI rate limit 헤더들
        rate_limit_headers = [
            "x-ratelimit-limit-requests",
            "x-ratelimit-remaining-requests",
            "x-ratelimit-reset-requests",
            "x-ratelimit-limit-tokens",
            "x-ratelimit-remaining-tokens",
            "x-ratelimit-reset-tokens"
        ]
        
        for header in rate_limit_headers:
            if header in headers:
                rate_limits[header] = headers[header]
        
        return rate_limits
    
    async def log_enhanced_usage(self, api_key: str, endpoint: str, usage_result: Dict[str, Any]) -> bool:
        """향상된 사용량 데이터를 데이터베이스에 로깅"""
        
        if not usage_result.get("success"):
            print(f"[향상된 사용량 추적] 실패한 호출은 로깅하지 않습니다: {usage_result.get('error')}")
            return False
        
        try:
            import sqlite3
            import os
            
            # 직접 SQLite 연결 사용
            db_path = os.path.join(os.path.dirname(__file__), '../cert_fast.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # API 키 ID 조회
            cursor.execute("SELECT id FROM api_keys WHERE api_key = ? AND is_active = 1", (api_key,))
            api_key_result = cursor.fetchone()
            
            if not api_key_result:
                print(f"[향상된 사용량 추적] API 키를 찾을 수 없음")
                conn.close()
                return False
            
            api_key_id = api_key_result[0]
            usage = usage_result["usage"]
            
            # 정확한 사용량 로깅
            cursor.execute("""
                INSERT INTO ai_usage_logs 
                (api_key_id, task_type, model_used, prompt_tokens, completion_tokens, 
                 total_tokens, cost, duration_seconds, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                api_key_id,
                self._get_task_type_from_endpoint(endpoint),
                usage_result["model"],
                usage.get("prompt_tokens", usage.get("input_tokens", 0)),
                usage.get("completion_tokens", usage.get("output_tokens", 0)),
                usage["total_tokens"],
                usage_result["cost"],
                usage_result["duration_seconds"],
                "success",
                usage_result["timestamp"]
            ))
            
            # API 키 사용량 업데이트
            cursor.execute("""
                UPDATE api_keys 
                SET current_daily_usage = current_daily_usage + ?,
                    current_monthly_usage = current_monthly_usage + ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                usage_result["cost"],
                usage_result["cost"],
                usage_result["timestamp"],
                api_key_id
            ))
            
            conn.commit()
            conn.close()
            
            print(f"[향상된 사용량 추적] 성공 - 모델: {usage_result['model']}, "
                  f"토큰: {usage['total_tokens']}, 비용: ${usage_result['cost']:.6f}")
            
            return True
            
        except Exception as e:
            print(f"[향상된 사용량 추적] 로깅 오류: {e}")
            return False
    
    def _get_task_type_from_endpoint(self, endpoint: str) -> str:
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

# 전역 인스턴스
enhanced_usage_tracker = EnhancedUsageTracker()