"""
실제 OpenAI/Anthropic Usage API를 사용한 정확한 사용량 추적 서비스
"""
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db

class RealUsageService:
    """실제 Usage API를 통한 정확한 사용량 추적"""
    
    def __init__(self):
        # OpenAI Usage API 설정 (2024년 12월 신규 API)
        self.openai_usage_base_url = "https://api.openai.com/v1"
        self.openai_headers = {
            "Content-Type": "application/json",
        }
        
        # Anthropic Usage & Cost API 설정
        self.anthropic_usage_base_url = "https://api.anthropic.com/v1"
        self.anthropic_headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    def get_api_keys_from_db(self) -> Dict[str, Dict[str, Any]]:
        """데이터베이스에서 실제 API 키 정보 조회"""
        try:
            db = next(get_db())
            
            # 활성 API 키들 조회
            result = db.execute(
                text("""
                    SELECT id, key_name, provider, api_key, is_active,
                           daily_limit, monthly_limit, current_daily_usage, current_monthly_usage
                    FROM api_keys 
                    WHERE is_active = 1
                """)
            ).fetchall()
            
            api_keys = {}
            for row in result:
                api_keys[row[2]] = {  # provider를 키로 사용
                    "id": row[0],
                    "key_name": row[1],
                    "provider": row[2],
                    "api_key": row[3],
                    "is_active": row[4],
                    "daily_limit": row[5],
                    "monthly_limit": row[6],
                    "current_daily_usage": row[7],
                    "current_monthly_usage": row[8]
                }
            
            return api_keys
            
        except Exception as e:
            print(f"[실제 사용량 서비스] API 키 조회 오류: {e}")
            return {}
    
    async def fetch_openai_usage(self, api_key: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """OpenAI Usage API로부터 실제 사용량 데이터 가져오기"""
        try:
            headers = {
                **self.openai_headers,
                "Authorization": f"Bearer {api_key}"
            }
            
            # OpenAI Usage API 호출 (2024년 12월 신규 API)
            async with httpx.AsyncClient() as client:
                # 먼저 usage 엔드포인트 시도
                usage_url = f"{self.openai_usage_base_url}/usage"
                params = {
                    "start_date": start_date,
                    "end_date": end_date
                }
                
                response = await client.get(
                    usage_url,
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # OpenAI Usage API 응답 파싱
                    total_tokens = 0
                    total_cost = 0.0
                    requests_count = 0
                    
                    if "data" in data:
                        for usage_entry in data["data"]:
                            if "n_tokens" in usage_entry:
                                total_tokens += usage_entry["n_tokens"]
                            if "cost" in usage_entry:
                                total_cost += usage_entry["cost"]
                            requests_count += 1
                    
                    return {
                        "success": True,
                        "provider": "openai",
                        "total_tokens": total_tokens,
                        "total_cost": total_cost,
                        "requests_count": requests_count,
                        "period": f"{start_date} to {end_date}",
                        "raw_data": data
                    }
                else:
                    print(f"[OpenAI Usage API] HTTP {response.status_code}: {response.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            print(f"[OpenAI Usage API] 오류: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def fetch_anthropic_usage(self, api_key: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Anthropic Usage & Cost API로부터 실제 사용량 데이터 가져오기"""
        try:
            headers = {
                **self.anthropic_headers,
                "x-api-key": api_key
            }
            
            async with httpx.AsyncClient() as client:
                # Anthropic Usage API 호출
                usage_url = f"{self.anthropic_usage_base_url}/organizations/usage_report/messages"
                
                # 요청 페이로드
                payload = {
                    "start_date": start_date,
                    "end_date": end_date,
                    "bucket_by": ["day"],  # 일별 집계
                    "aggregation_level": "organization"
                }
                
                response = await client.post(
                    usage_url,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Anthropic Usage API 응답 파싱
                    total_input_tokens = 0
                    total_output_tokens = 0
                    total_requests = 0
                    
                    if "usage_data" in data:
                        for entry in data["usage_data"]:
                            total_input_tokens += entry.get("input_tokens", 0)
                            total_output_tokens += entry.get("output_tokens", 0)
                            total_requests += entry.get("request_count", 0)
                    
                    total_tokens = total_input_tokens + total_output_tokens
                    
                    # 이제 비용 API 호출
                    cost_data = await self._fetch_anthropic_cost(client, headers, start_date, end_date)
                    total_cost = cost_data.get("total_cost", 0.0)
                    
                    return {
                        "success": True,
                        "provider": "anthropic",
                        "total_tokens": total_tokens,
                        "input_tokens": total_input_tokens,
                        "output_tokens": total_output_tokens,
                        "total_cost": total_cost,
                        "requests_count": total_requests,
                        "period": f"{start_date} to {end_date}",
                        "raw_usage_data": data,
                        "raw_cost_data": cost_data
                    }
                else:
                    print(f"[Anthropic Usage API] HTTP {response.status_code}: {response.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            print(f"[Anthropic Usage API] 오류: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _fetch_anthropic_cost(self, client: httpx.AsyncClient, headers: Dict, start_date: str, end_date: str) -> Dict[str, Any]:
        """Anthropic Cost API 호출"""
        try:
            cost_url = f"{self.anthropic_usage_base_url}/organizations/cost_report"
            
            payload = {
                "start_date": start_date,
                "end_date": end_date
            }
            
            response = await client.post(
                cost_url,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                cost_data = response.json()
                
                total_cost = 0.0
                if "cost_data" in cost_data:
                    for entry in cost_data["cost_data"]:
                        total_cost += entry.get("amount", 0.0)
                
                return {
                    "total_cost": total_cost,
                    "raw_data": cost_data
                }
            else:
                print(f"[Anthropic Cost API] HTTP {response.status_code}: {response.text}")
                return {"total_cost": 0.0, "error": response.text}
                
        except Exception as e:
            print(f"[Anthropic Cost API] 오류: {e}")
            return {"total_cost": 0.0, "error": str(e)}
    
    async def sync_real_usage_data(self, days_back: int = 7) -> Dict[str, Any]:
        """실제 Usage API에서 데이터를 가져와서 데이터베이스와 동기화"""
        
        print(f"[실제 사용량 동기화] {days_back}일간의 실제 사용량 데이터 동기화 시작...")
        
        # 날짜 범위 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # 데이터베이스에서 API 키들 가져오기
        api_keys = self.get_api_keys_from_db()
        
        sync_results = {
            "success": True,
            "synced_providers": [],
            "errors": [],
            "summary": {
                "total_tokens_synced": 0,
                "total_cost_synced": 0.0,
                "providers_synced": 0
            }
        }
        
        # OpenAI 사용량 동기화
        if "openai" in api_keys:
            openai_key = api_keys["openai"]
            print(f"[실제 사용량 동기화] OpenAI 사용량 가져오는 중...")
            
            openai_usage = await self.fetch_openai_usage(
                openai_key["api_key"], 
                start_date_str, 
                end_date_str
            )
            
            if openai_usage["success"]:
                # 데이터베이스 업데이트
                await self._update_api_key_usage(openai_key["id"], openai_usage)
                sync_results["synced_providers"].append("openai")
                sync_results["summary"]["total_tokens_synced"] += openai_usage["total_tokens"]
                sync_results["summary"]["total_cost_synced"] += openai_usage["total_cost"]
                sync_results["summary"]["providers_synced"] += 1
            else:
                sync_results["errors"].append(f"OpenAI: {openai_usage.get('error', 'Unknown error')}")
        
        # Anthropic 사용량 동기화  
        if "anthropic" in api_keys:
            anthropic_key = api_keys["anthropic"]
            print(f"[실제 사용량 동기화] Anthropic 사용량 가져오는 중...")
            
            anthropic_usage = await self.fetch_anthropic_usage(
                anthropic_key["api_key"],
                start_date_str,
                end_date_str
            )
            
            if anthropic_usage["success"]:
                # 데이터베이스 업데이트
                await self._update_api_key_usage(anthropic_key["id"], anthropic_usage)
                sync_results["synced_providers"].append("anthropic")
                sync_results["summary"]["total_tokens_synced"] += anthropic_usage["total_tokens"]
                sync_results["summary"]["total_cost_synced"] += anthropic_usage["total_cost"]
                sync_results["summary"]["providers_synced"] += 1
            else:
                sync_results["errors"].append(f"Anthropic: {anthropic_usage.get('error', 'Unknown error')}")
        
        if sync_results["errors"]:
            sync_results["success"] = False
        
        print(f"[실제 사용량 동기화] 완료 - 동기화된 제공업체: {sync_results['summary']['providers_synced']}개")
        
        return sync_results
    
    async def _update_api_key_usage(self, api_key_id: int, usage_data: Dict[str, Any]):
        """실제 사용량 데이터로 API 키 정보 업데이트"""
        try:
            db = next(get_db())
            
            # 실제 사용량으로 업데이트
            db.execute(
                text("""
                    UPDATE api_keys 
                    SET current_daily_usage = :daily_cost,
                        current_monthly_usage = :monthly_cost,
                        updated_at = :updated_at
                    WHERE id = :api_key_id
                """),
                {
                    "daily_cost": usage_data["total_cost"],
                    "monthly_cost": usage_data["total_cost"],  # 실제로는 월별 계산 필요
                    "api_key_id": api_key_id,
                    "updated_at": datetime.now().isoformat()
                }
            )
            
            # 실제 사용량 로그도 추가
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
                    "task_type": "real_usage_sync",
                    "model_used": f"{usage_data['provider']}_real_usage",
                    "prompt_tokens": usage_data.get("input_tokens", 0),
                    "completion_tokens": usage_data.get("output_tokens", 0),
                    "total_tokens": usage_data["total_tokens"],
                    "cost": usage_data["total_cost"],
                    "duration_seconds": 0.0,
                    "status": "synced",
                    "created_at": datetime.now().isoformat()
                }
            )
            
            db.commit()
            print(f"[실제 사용량 동기화] API 키 ID {api_key_id} 업데이트 완료")
            
        except Exception as e:
            print(f"[실제 사용량 동기화] 데이터베이스 업데이트 오류: {e}")

# 전역 인스턴스
real_usage_service = RealUsageService()