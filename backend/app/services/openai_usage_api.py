"""
OpenAI Usage API 통합 서비스
2025년 최신 OpenAI Usage API를 사용한 실시간 사용량 추적
"""
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

class OpenAIUsageAPIService:
    """OpenAI Usage API를 활용한 사용량 추적 서비스"""
    
    def __init__(self):
        self.base_url = "https://api.openai.com/v1"
        self.usage_url = f"{self.base_url}/organization/usage"
        self.costs_url = f"{self.base_url}/organization/costs"
        
    async def get_usage_data(
        self, 
        api_key: str, 
        start_time: datetime = None, 
        end_time: datetime = None,
        project_ids: List[str] = None,
        granularity: str = "daily"  # daily, hourly, minutely
    ) -> Dict[str, Any]:
        """
        OpenAI Usage API를 통해 사용량 데이터 조회
        
        Args:
            api_key: OpenAI API 키
            start_time: 시작 시간
            end_time: 종료 시간  
            project_ids: 프로젝트 ID 리스트
            granularity: 데이터 집계 단위
        """
        
        # 기본값 설정 (최근 7일)
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(days=7)
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "start_time": int(start_time.timestamp()),
            "end_time": int(end_time.timestamp()),
            "granularity": granularity
        }
        
        # 프로젝트 ID 필터 추가
        if project_ids:
            params["project_ids"] = project_ids
            
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
    
    async def get_cost_data(
        self, 
        api_key: str, 
        start_time: datetime = None, 
        end_time: datetime = None,
        project_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        OpenAI Costs API를 통해 비용 데이터 조회
        """
        
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(days=30)
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "start_time": int(start_time.timestamp()),
            "end_time": int(end_time.timestamp())
        }
        
        if project_ids:
            params["project_ids"] = project_ids
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.costs_url,
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
    
    async def get_project_usage(
        self,
        api_key: str,
        project_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """특정 프로젝트의 사용량 조회"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 사용량 데이터 조회
        usage_result = await self.get_usage_data(
            api_key=api_key,
            start_time=start_time,
            end_time=end_time,
            project_ids=[project_id],
            granularity="daily"
        )
        
        # 비용 데이터 조회
        cost_result = await self.get_cost_data(
            api_key=api_key,
            start_time=start_time,
            end_time=end_time,
            project_ids=[project_id]
        )
        
        return {
            "project_id": project_id,
            "period": {
                "start_date": start_time.date().isoformat(),
                "end_date": end_time.date().isoformat(),
                "days": days
            },
            "usage": usage_result,
            "costs": cost_result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_realtime_metrics(
        self,
        api_key: str,
        minutes: int = 60
    ) -> Dict[str, Any]:
        """실시간 메트릭 조회 (최근 N분간)"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=minutes)
        
        # 분단위 세밀한 데이터 조회
        result = await self.get_usage_data(
            api_key=api_key,
            start_time=start_time,
            end_time=end_time,
            granularity="minutely"
        )
        
        if result["success"]:
            data = result["data"]
            
            # 요약 통계 계산
            total_requests = 0
            total_tokens = 0
            total_cost = 0.0
            
            if "data" in data:
                for item in data["data"]:
                    total_requests += item.get("n_requests", 0)
                    total_tokens += item.get("n_context_tokens_total", 0)
                    total_tokens += item.get("n_generated_tokens_total", 0)
            
            return {
                "success": True,
                "period_minutes": minutes,
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_requests": total_requests,
                    "total_tokens": total_tokens,
                    "requests_per_minute": total_requests / minutes if minutes > 0 else 0,
                    "tokens_per_minute": total_tokens / minutes if minutes > 0 else 0
                },
                "detailed_data": data
            }
        else:
            return result
    
    async def track_api_key_usage(
        self,
        db: Session,
        api_key_id: int,
        openai_api_key: str
    ) -> Dict[str, Any]:
        """API 키별 사용량 추적 및 DB 업데이트"""
        
        # 최근 24시간 데이터 조회
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = await self.get_usage_data(
            api_key=openai_api_key,
            start_time=start_time,
            end_time=end_time,
            granularity="hourly"
        )
        
        if not result["success"]:
            return result
        
        try:
            # 사용량 데이터 파싱
            usage_data = result["data"]
            total_cost = 0.0
            total_requests = 0
            total_tokens = 0
            
            if "data" in usage_data:
                for item in usage_data["data"]:
                    total_requests += item.get("n_requests", 0)
                    total_tokens += item.get("n_context_tokens_total", 0) + item.get("n_generated_tokens_total", 0)
            
            # 비용 데이터 조회
            cost_result = await self.get_cost_data(
                api_key=openai_api_key,
                start_time=start_time,
                end_time=end_time
            )
            
            if cost_result["success"] and "data" in cost_result["data"]:
                cost_data = cost_result["data"]["data"]
                for item in cost_data:
                    total_cost += float(item.get("amount", {}).get("value", 0))
            
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
                    (api_key_id, task_type, model_used, total_tokens, cost, status, created_at)
                    VALUES (:api_key_id, 'usage_sync', 'openai', :total_tokens, :cost, 'success', :created_at)
                """),
                {
                    "api_key_id": api_key_id,
                    "total_tokens": total_tokens,
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
                    "total_tokens": total_tokens,
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
    
    def parse_usage_response(self, response_data: Dict) -> Dict[str, Any]:
        """OpenAI Usage API 응답 파싱"""
        
        if "data" not in response_data:
            return {"error": "No data field in response"}
        
        parsed_data = {
            "total_requests": 0,
            "total_tokens": 0,
            "by_model": {},
            "by_time": [],
            "aggregation_timestep": response_data.get("aggregation_timestep", "day")
        }
        
        for item in response_data["data"]:
            # 시간별 데이터
            time_entry = {
                "timestamp": item.get("aggregation_timestep"),
                "requests": item.get("n_requests", 0),
                "context_tokens": item.get("n_context_tokens_total", 0),
                "generated_tokens": item.get("n_generated_tokens_total", 0)
            }
            parsed_data["by_time"].append(time_entry)
            
            # 총계 업데이트
            parsed_data["total_requests"] += time_entry["requests"]
            parsed_data["total_tokens"] += time_entry["context_tokens"] + time_entry["generated_tokens"]
            
            # 모델별 통계 (있는 경우)
            if "n_requests_by_model" in item:
                for model, count in item["n_requests_by_model"].items():
                    if model not in parsed_data["by_model"]:
                        parsed_data["by_model"][model] = {"requests": 0, "tokens": 0}
                    parsed_data["by_model"][model]["requests"] += count
        
        return parsed_data

# 전역 인스턴스
openai_usage_api = OpenAIUsageAPIService()