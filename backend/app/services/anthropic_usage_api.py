"""
Anthropic Usage and Cost API 통합 서비스
2025년 최신 Anthropic Usage and Cost API를 사용한 실시간 사용량 및 비용 추적
"""
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

class AnthropicUsageAPIService:
    """Anthropic Usage and Cost API를 활용한 사용량 추적 서비스"""
    
    def __init__(self):
        self.base_url = "https://api.anthropic.com/v1"
        self.usage_url = f"{self.base_url}/billing/usage"
        self.cost_url = f"{self.base_url}/billing/cost_breakdown"
        
        # Admin API 키가 필요 (sk-ant-admin으로 시작)
        self.admin_api_required = True
        
    async def get_usage_data(
        self, 
        admin_api_key: str,
        start_time: datetime = None, 
        end_time: datetime = None,
        service_tiers: List[str] = None,
        models: List[str] = None,
        granularity: str = "day"  # hour, day
    ) -> Dict[str, Any]:
        """
        Anthropic Usage API를 통해 사용량 데이터 조회
        
        Args:
            admin_api_key: Anthropic Admin API 키 (sk-ant-admin으로 시작)
            start_time: 시작 시간 (ISO format)
            end_time: 종료 시간 (ISO format)
            service_tiers: 서비스 티어 리스트 ["1", "2", "3", "4"]
            models: 모델 리스트 ["claude-3-haiku", "claude-3-sonnet", etc.]
            granularity: 집계 단위 ("hour" or "day")
        """
        
        # 기본값 설정 (최근 7일)
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(days=7)
            
        headers = {
            "x-api-key": admin_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        params = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "granularity": granularity
        }
        
        # 선택적 필터 추가
        if service_tiers:
            params["service_tiers"] = service_tiers
        if models:
            params["models"] = models
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.usage_url,
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "data": response.json(),
                        "timestamp": datetime.now().isoformat()
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
    
    async def get_cost_breakdown(
        self, 
        admin_api_key: str,
        start_time: datetime = None, 
        end_time: datetime = None,
        service_tiers: List[str] = None,
        models: List[str] = None,
        granularity: str = "day"
    ) -> Dict[str, Any]:
        """
        Anthropic Cost Breakdown API를 통해 비용 분석 데이터 조회
        """
        
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(days=30)
            
        headers = {
            "x-api-key": admin_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        params = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "granularity": granularity
        }
        
        if service_tiers:
            params["service_tiers"] = service_tiers
        if models:
            params["models"] = models
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.cost_url,
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "data": response.json(),
                        "timestamp": datetime.now().isoformat()
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
    
    async def get_realtime_metrics(
        self,
        admin_api_key: str,
        hours: int = 1
    ) -> Dict[str, Any]:
        """실시간 메트릭 조회 (최근 N시간)"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 시간 단위 세밀한 데이터 조회
        usage_result = await self.get_usage_data(
            admin_api_key=admin_api_key,
            start_time=start_time,
            end_time=end_time,
            granularity="hour"
        )
        
        cost_result = await self.get_cost_breakdown(
            admin_api_key=admin_api_key,
            start_time=start_time,
            end_time=end_time,
            granularity="hour"
        )
        
        if usage_result["success"] and cost_result["success"]:
            usage_data = usage_result["data"]
            cost_data = cost_result["data"]
            
            # 요약 통계 계산
            total_input_tokens = 0
            total_output_tokens = 0
            total_cost = 0.0
            total_requests = 0
            
            # Usage 데이터 파싱
            if "usage" in usage_data:
                for item in usage_data["usage"]:
                    total_input_tokens += item.get("input_tokens", 0)
                    total_output_tokens += item.get("output_tokens", 0)
                    total_requests += item.get("requests", 0)
            
            # Cost 데이터 파싱  
            if "cost_breakdown" in cost_data:
                for item in cost_data["cost_breakdown"]:
                    total_cost += float(item.get("amount", {}).get("amount", 0))
            
            return {
                "success": True,
                "period_hours": hours,
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_requests": total_requests,
                    "total_input_tokens": total_input_tokens,
                    "total_output_tokens": total_output_tokens,
                    "total_tokens": total_input_tokens + total_output_tokens,
                    "total_cost_usd": total_cost,
                    "requests_per_hour": total_requests / hours if hours > 0 else 0,
                    "tokens_per_hour": (total_input_tokens + total_output_tokens) / hours if hours > 0 else 0,
                    "cost_per_hour": total_cost / hours if hours > 0 else 0
                },
                "usage_data": usage_data,
                "cost_data": cost_data
            }
        else:
            return {
                "success": False,
                "usage_error": usage_result.get("error") if not usage_result["success"] else None,
                "cost_error": cost_result.get("error") if not cost_result["success"] else None
            }
    
    async def track_api_key_usage(
        self,
        db: Session,
        api_key_id: int,
        admin_api_key: str,
        user_api_key: str = None  # 개별 사용자 API 키 (있는 경우)
    ) -> Dict[str, Any]:
        """API 키별 사용량 추적 및 DB 업데이트"""
        
        # 최근 24시간 데이터 조회
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        # 전체 사용량 조회 (Admin API로)
        usage_result = await self.get_usage_data(
            admin_api_key=admin_api_key,
            start_time=start_time,
            end_time=end_time,
            granularity="hour"
        )
        
        cost_result = await self.get_cost_breakdown(
            admin_api_key=admin_api_key,
            start_time=start_time,
            end_time=end_time,
            granularity="hour"
        )
        
        if not (usage_result["success"] and cost_result["success"]):
            return {
                "success": False,
                "usage_error": usage_result.get("error") if not usage_result["success"] else None,
                "cost_error": cost_result.get("error") if not cost_result["success"] else None
            }
        
        try:
            # 사용량 데이터 파싱
            usage_data = usage_result["data"]
            cost_data = cost_result["data"]
            
            total_input_tokens = 0
            total_output_tokens = 0
            total_cost = 0.0
            total_requests = 0
            
            # Usage 데이터 집계
            if "usage" in usage_data:
                for item in usage_data["usage"]:
                    total_input_tokens += item.get("input_tokens", 0)
                    total_output_tokens += item.get("output_tokens", 0)
                    total_requests += item.get("requests", 0)
            
            # Cost 데이터 집계
            if "cost_breakdown" in cost_data:
                for item in cost_data["cost_breakdown"]:
                    total_cost += float(item.get("amount", {}).get("amount", 0))
            
            # DB 업데이트
            db.execute(
                text("""
                    UPDATE api_keys 
                    SET current_daily_usage = :daily_cost,
                        updated_at = :updated_at
                    WHERE id = :api_key_id
                """),
                {
                    "daily_cost": total_cost,
                    "api_key_id": api_key_id,
                    "updated_at": datetime.now().isoformat()
                }
            )
            
            # 사용량 로그 생성
            db.execute(
                text("""
                    INSERT INTO ai_usage_logs 
                    (api_key_id, task_type, model_used, prompt_tokens, completion_tokens, 
                     total_tokens, cost, status, created_at)
                    VALUES (:api_key_id, 'usage_sync', 'claude', :input_tokens, :output_tokens, 
                            :total_tokens, :cost, 'success', :created_at)
                """),
                {
                    "api_key_id": api_key_id,
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "total_tokens": total_input_tokens + total_output_tokens,
                    "cost": total_cost,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            db.commit()
            
            return {
                "success": True,
                "api_key_id": api_key_id,
                "period_hours": 24,
                "metrics": {
                    "total_requests": total_requests,
                    "total_input_tokens": total_input_tokens,
                    "total_output_tokens": total_output_tokens,
                    "total_tokens": total_input_tokens + total_output_tokens,
                    "total_cost": total_cost
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": f"Database update failed: {str(e)}"
            }
    
    async def get_model_usage_breakdown(
        self,
        admin_api_key: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """모델별 사용량 분석"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Claude 모델들
        claude_models = [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20241022", 
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229"
        ]
        
        model_breakdown = {}
        
        for model in claude_models:
            result = await self.get_usage_data(
                admin_api_key=admin_api_key,
                start_time=start_time,
                end_time=end_time,
                models=[model],
                granularity="day"
            )
            
            if result["success"]:
                usage_data = result["data"]
                model_stats = {
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0
                }
                
                if "usage" in usage_data:
                    for item in usage_data["usage"]:
                        model_stats["requests"] += item.get("requests", 0)
                        model_stats["input_tokens"] += item.get("input_tokens", 0)
                        model_stats["output_tokens"] += item.get("output_tokens", 0)
                
                model_stats["total_tokens"] = model_stats["input_tokens"] + model_stats["output_tokens"]
                model_breakdown[model] = model_stats
        
        return {
            "success": True,
            "period_days": days,
            "model_breakdown": model_breakdown,
            "timestamp": datetime.now().isoformat()
        }
    
    def parse_usage_response(self, response_data: Dict) -> Dict[str, Any]:
        """Anthropic Usage API 응답 파싱"""
        
        if "usage" not in response_data:
            return {"error": "No usage field in response"}
        
        parsed_data = {
            "total_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "by_model": {},
            "by_time": [],
            "by_service_tier": {}
        }
        
        for item in response_data["usage"]:
            # 시간별 데이터
            time_entry = {
                "timestamp": item.get("start_time"),
                "requests": item.get("requests", 0),
                "input_tokens": item.get("input_tokens", 0),
                "output_tokens": item.get("output_tokens", 0),
                "model": item.get("model"),
                "service_tier": item.get("service_tier")
            }
            parsed_data["by_time"].append(time_entry)
            
            # 총계 업데이트
            parsed_data["total_requests"] += time_entry["requests"]
            parsed_data["total_input_tokens"] += time_entry["input_tokens"]
            parsed_data["total_output_tokens"] += time_entry["output_tokens"]
            
            # 모델별 통계
            model = item.get("model", "unknown")
            if model not in parsed_data["by_model"]:
                parsed_data["by_model"][model] = {
                    "requests": 0, 
                    "input_tokens": 0, 
                    "output_tokens": 0
                }
            
            parsed_data["by_model"][model]["requests"] += time_entry["requests"]
            parsed_data["by_model"][model]["input_tokens"] += time_entry["input_tokens"]
            parsed_data["by_model"][model]["output_tokens"] += time_entry["output_tokens"]
            
            # 서비스 티어별 통계
            tier = item.get("service_tier", "unknown")
            if tier not in parsed_data["by_service_tier"]:
                parsed_data["by_service_tier"][tier] = {
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0
                }
            
            parsed_data["by_service_tier"][tier]["requests"] += time_entry["requests"]
            parsed_data["by_service_tier"][tier]["input_tokens"] += time_entry["input_tokens"]
            parsed_data["by_service_tier"][tier]["output_tokens"] += time_entry["output_tokens"]
        
        parsed_data["total_tokens"] = parsed_data["total_input_tokens"] + parsed_data["total_output_tokens"]
        
        return parsed_data
    
    def is_admin_api_key(self, api_key: str) -> bool:
        """Admin API 키인지 확인"""
        return api_key.startswith("sk-ant-admin")

# 전역 인스턴스
anthropic_usage_api = AnthropicUsageAPIService()