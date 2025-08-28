"""
에이전트별 사용량 분리 추적 시스템
각 AI 에이전트(Document Analyzer, Quiz Master, Study Tutor)별로 사용량을 개별 추적
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Literal
from sqlalchemy.orm import Session
from sqlalchemy import text
from enum import Enum

class AgentType(Enum):
    """AI 에이전트 타입 정의"""
    DOCUMENT_ANALYZER = "document_analyzer"
    QUIZ_MASTER = "quiz_master"
    STUDY_TUTOR = "study_tutor"
    CHAT_ASSISTANT = "chat_assistant"
    PDF_PROCESSOR = "pdf_processor"

class AgentUsageTracker:
    """에이전트별 사용량 분리 추적 서비스"""
    
    def __init__(self):
        # 에이전트별 모델 매핑
        self.agent_model_mapping = {
            AgentType.DOCUMENT_ANALYZER: {
                "preferred_models": ["claude-3-sonnet-20241022", "gpt-4"],
                "fallback_models": ["claude-3-haiku-20240307", "gpt-3.5-turbo"],
                "max_tokens": 8000,
                "temperature": 0.3
            },
            AgentType.QUIZ_MASTER: {
                "preferred_models": ["claude-3-5-sonnet-20241022", "gpt-4-turbo"],
                "fallback_models": ["claude-3-sonnet-20241022", "gpt-4"],
                "max_tokens": 4000,
                "temperature": 0.7
            },
            AgentType.STUDY_TUTOR: {
                "preferred_models": ["claude-3-5-sonnet-20241022", "gpt-4"],
                "fallback_models": ["claude-3-haiku-20240307", "gpt-3.5-turbo"],
                "max_tokens": 6000,
                "temperature": 0.8
            },
            AgentType.CHAT_ASSISTANT: {
                "preferred_models": ["claude-3-haiku-20240307", "gpt-3.5-turbo"],
                "fallback_models": ["claude-3-sonnet-20241022", "gpt-4"],
                "max_tokens": 2000,
                "temperature": 0.9
            },
            AgentType.PDF_PROCESSOR: {
                "preferred_models": ["claude-3-sonnet-20241022", "gpt-4-turbo"],
                "fallback_models": ["claude-3-haiku-20240307", "gpt-3.5-turbo"],
                "max_tokens": 10000,
                "temperature": 0.1
            }
        }
    
    async def track_agent_usage(
        self,
        db: Session,
        agent_id: int,
        agent_type: AgentType,
        api_key_id: int,
        user_id: Optional[int],
        task_type: str,
        model_used: str,
        usage_data: Dict[str, Any],
        cost: float,
        duration_seconds: float,
        status: str = "success",
        request_metadata: Optional[Dict] = None,
        response_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        에이전트별 사용량 추적 및 로깅
        
        Args:
            agent_id: AI 에이전트 ID
            agent_type: 에이전트 타입
            api_key_id: 사용된 API 키 ID
            user_id: 사용자 ID (선택사항)
            task_type: 작업 타입
            model_used: 사용된 AI 모델
            usage_data: 토큰 사용량 데이터
            cost: 비용
            duration_seconds: 처리 시간
            status: 상태
            request_metadata: 요청 메타데이터
            response_metadata: 응답 메타데이터
        """
        
        try:
            # 현재 시간
            now = datetime.now()
            
            # 에이전트별 사용량 로그 기록
            log_id = await self._create_agent_usage_log(
                db=db,
                agent_id=agent_id,
                api_key_id=api_key_id,
                user_id=user_id,
                task_type=task_type,
                model_used=model_used,
                usage_data=usage_data,
                cost=cost,
                duration_seconds=duration_seconds,
                status=status,
                request_metadata=request_metadata,
                response_metadata=response_metadata,
                created_at=now
            )
            
            # 에이전트별 통계 업데이트
            await self._update_agent_statistics(
                db=db,
                agent_id=agent_id,
                agent_type=agent_type,
                cost=cost,
                usage_data=usage_data,
                duration_seconds=duration_seconds,
                updated_at=now
            )
            
            # API 키 사용량 업데이트
            await self._update_api_key_usage(
                db=db,
                api_key_id=api_key_id,
                cost=cost,
                updated_at=now
            )
            
            db.commit()
            
            return {
                "success": True,
                "log_id": log_id,
                "agent_id": agent_id,
                "agent_type": agent_type.value,
                "cost": cost,
                "tokens": usage_data.get("total_tokens", 0),
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id,
                "agent_type": agent_type.value
            }
    
    async def _create_agent_usage_log(
        self,
        db: Session,
        agent_id: int,
        api_key_id: int,
        user_id: Optional[int],
        task_type: str,
        model_used: str,
        usage_data: Dict[str, Any],
        cost: float,
        duration_seconds: float,
        status: str,
        request_metadata: Optional[Dict],
        response_metadata: Optional[Dict],
        created_at: datetime
    ) -> int:
        """에이전트 사용량 로그 생성"""
        
        result = db.execute(
            text("""
                INSERT INTO ai_usage_logs 
                (agent_id, api_key_id, user_id, task_type, model_used, 
                 prompt_tokens, completion_tokens, total_tokens, cost, 
                 duration_seconds, status, error_message, request_data, 
                 response_data, created_at)
                VALUES (:agent_id, :api_key_id, :user_id, :task_type, :model_used,
                        :prompt_tokens, :completion_tokens, :total_tokens, :cost,
                        :duration_seconds, :status, :error_message, :request_data,
                        :response_data, :created_at)
            """),
            {
                "agent_id": agent_id,
                "api_key_id": api_key_id,
                "user_id": user_id,
                "task_type": task_type,
                "model_used": model_used,
                "prompt_tokens": usage_data.get("prompt_tokens", usage_data.get("input_tokens", 0)),
                "completion_tokens": usage_data.get("completion_tokens", usage_data.get("output_tokens", 0)),
                "total_tokens": usage_data.get("total_tokens", 0),
                "cost": cost,
                "duration_seconds": duration_seconds,
                "status": status,
                "error_message": None if status == "success" else str(request_metadata or {}),
                "request_data": str(request_metadata) if request_metadata else None,
                "response_data": str(response_metadata) if response_metadata else None,
                "created_at": created_at.isoformat()
            }
        )
        
        return result.lastrowid
    
    async def _update_agent_statistics(
        self,
        db: Session,
        agent_id: int,
        agent_type: AgentType,
        cost: float,
        usage_data: Dict[str, Any],
        duration_seconds: float,
        updated_at: datetime
    ):
        """에이전트별 통계 업데이트 (새 테이블 또는 기존 테이블 확장)"""
        
        # ai_agents 테이블에 통계 컬럼이 없다면 JSON 필드에 저장
        # 먼저 현재 통계 조회
        current_stats = db.execute(
            text("""
                SELECT agent_config FROM ai_agents WHERE id = :agent_id
            """),
            {"agent_id": agent_id}
        ).fetchone()
        
        if current_stats:
            import json
            try:
                config = json.loads(current_stats[0] or "{}")
            except:
                config = {}
            
            # 통계 섹션 초기화
            if "statistics" not in config:
                config["statistics"] = {
                    "total_requests": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_duration": 0.0,
                    "last_used": None,
                    "daily_usage": {},
                    "model_usage": {}
                }
            
            stats = config["statistics"]
            today = updated_at.date().isoformat()
            
            # 통계 업데이트
            stats["total_requests"] += 1
            stats["total_tokens"] += usage_data.get("total_tokens", 0)
            stats["total_cost"] += cost
            stats["total_duration"] += duration_seconds
            stats["last_used"] = updated_at.isoformat()
            
            # 일별 통계
            if today not in stats["daily_usage"]:
                stats["daily_usage"][today] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            
            stats["daily_usage"][today]["requests"] += 1
            stats["daily_usage"][today]["tokens"] += usage_data.get("total_tokens", 0)
            stats["daily_usage"][today]["cost"] += cost
            
            # 모델별 통계
            model = usage_data.get("model", "unknown")
            if model not in stats["model_usage"]:
                stats["model_usage"][model] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            
            stats["model_usage"][model]["requests"] += 1
            stats["model_usage"][model]["tokens"] += usage_data.get("total_tokens", 0)
            stats["model_usage"][model]["cost"] += cost
            
            # 일주일 이전 데이터 정리 (메모리 절약)
            week_ago = (updated_at - timedelta(days=7)).date().isoformat()
            stats["daily_usage"] = {
                k: v for k, v in stats["daily_usage"].items() 
                if k >= week_ago
            }
            
            # DB 업데이트
            db.execute(
                text("""
                    UPDATE ai_agents 
                    SET agent_config = :config, updated_at = :updated_at
                    WHERE id = :agent_id
                """),
                {
                    "config": json.dumps(config),
                    "agent_id": agent_id,
                    "updated_at": updated_at.isoformat()
                }
            )
    
    async def _update_api_key_usage(
        self,
        db: Session,
        api_key_id: int,
        cost: float,
        updated_at: datetime
    ):
        """API 키 사용량 업데이트"""
        
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
                "updated_at": updated_at.isoformat()
            }
        )
    
    async def get_agent_usage_summary(
        self,
        db: Session,
        agent_id: Optional[int] = None,
        agent_type: Optional[AgentType] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """에이전트별 사용량 요약 조회"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 쿼리 조건 구성
        where_conditions = ["ul.created_at >= :start_time", "ul.created_at <= :end_time"]
        params = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        if agent_id:
            where_conditions.append("ul.agent_id = :agent_id")
            params["agent_id"] = agent_id
        
        if agent_type:
            where_conditions.append("ag.agent_type = :agent_type")
            params["agent_type"] = agent_type.value
        
        where_clause = " AND ".join(where_conditions)
        
        # 에이전트별 통계 조회
        agent_stats = db.execute(
            text(f"""
                SELECT 
                    ag.id,
                    ag.name,
                    ag.agent_type,
                    ag.provider,
                    COUNT(*) as total_requests,
                    SUM(ul.total_tokens) as total_tokens,
                    SUM(ul.cost) as total_cost,
                    AVG(ul.duration_seconds) as avg_duration,
                    MAX(ul.created_at) as last_used,
                    COUNT(DISTINCT ul.user_id) as unique_users
                FROM ai_usage_logs ul
                JOIN ai_agents ag ON ul.agent_id = ag.id
                WHERE {where_clause}
                GROUP BY ag.id, ag.name, ag.agent_type, ag.provider
                ORDER BY total_cost DESC
            """),
            params
        ).fetchall()
        
        # 일별 트렌드 데이터
        daily_trends = db.execute(
            text(f"""
                SELECT 
                    DATE(ul.created_at) as date,
                    ag.agent_type,
                    COUNT(*) as requests,
                    SUM(ul.total_tokens) as tokens,
                    SUM(ul.cost) as cost
                FROM ai_usage_logs ul
                JOIN ai_agents ag ON ul.agent_id = ag.id
                WHERE {where_clause}
                GROUP BY DATE(ul.created_at), ag.agent_type
                ORDER BY date DESC, ag.agent_type
            """),
            params
        ).fetchall()
        
        # 모델별 사용량
        model_usage = db.execute(
            text(f"""
                SELECT 
                    ul.model_used,
                    ag.agent_type,
                    COUNT(*) as requests,
                    SUM(ul.total_tokens) as tokens,
                    SUM(ul.cost) as cost
                FROM ai_usage_logs ul
                JOIN ai_agents ag ON ul.agent_id = ag.id
                WHERE {where_clause}
                GROUP BY ul.model_used, ag.agent_type
                ORDER BY cost DESC
            """),
            params
        ).fetchall()
        
        return {
            "period": {
                "days": days,
                "start_date": start_time.date().isoformat(),
                "end_date": end_time.date().isoformat()
            },
            "agent_stats": [
                {
                    "agent_id": row.id,
                    "agent_name": row.name,
                    "agent_type": row.agent_type,
                    "provider": row.provider,
                    "total_requests": row.total_requests,
                    "total_tokens": row.total_tokens or 0,
                    "total_cost": float(row.total_cost or 0),
                    "avg_duration": float(row.avg_duration or 0),
                    "last_used": row.last_used,
                    "unique_users": row.unique_users or 0
                } for row in agent_stats
            ],
            "daily_trends": [
                {
                    "date": row.date,
                    "agent_type": row.agent_type,
                    "requests": row.requests,
                    "tokens": row.tokens or 0,
                    "cost": float(row.cost or 0)
                } for row in daily_trends
            ],
            "model_usage": [
                {
                    "model": row.model_used,
                    "agent_type": row.agent_type,
                    "requests": row.requests,
                    "tokens": row.tokens or 0,
                    "cost": float(row.cost or 0)
                } for row in model_usage
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_agent_performance_metrics(
        self,
        db: Session,
        agent_id: int,
        hours: int = 24
    ) -> Dict[str, Any]:
        """에이전트 성능 메트릭 조회"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 성능 메트릭 조회
        metrics = db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_requests,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_requests,
                    COUNT(CASE WHEN status != 'success' THEN 1 END) as failed_requests,
                    AVG(duration_seconds) as avg_duration,
                    MAX(duration_seconds) as max_duration,
                    MIN(duration_seconds) as min_duration,
                    AVG(cost) as avg_cost,
                    SUM(cost) as total_cost,
                    AVG(total_tokens) as avg_tokens,
                    SUM(total_tokens) as total_tokens
                FROM ai_usage_logs
                WHERE agent_id = :agent_id 
                  AND created_at >= :start_time 
                  AND created_at <= :end_time
            """),
            {
                "agent_id": agent_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        ).fetchone()
        
        if not metrics or metrics.total_requests == 0:
            return {
                "agent_id": agent_id,
                "period_hours": hours,
                "no_data": True,
                "timestamp": datetime.now().isoformat()
            }
        
        success_rate = (metrics.successful_requests / metrics.total_requests * 100) if metrics.total_requests > 0 else 0
        
        return {
            "agent_id": agent_id,
            "period_hours": hours,
            "performance": {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate_percent": round(success_rate, 2)
            },
            "timing": {
                "avg_duration_seconds": float(metrics.avg_duration or 0),
                "max_duration_seconds": float(metrics.max_duration or 0),
                "min_duration_seconds": float(metrics.min_duration or 0)
            },
            "cost": {
                "total_cost": float(metrics.total_cost or 0),
                "avg_cost_per_request": float(metrics.avg_cost or 0),
                "cost_per_hour": float(metrics.total_cost or 0) / hours if hours > 0 else 0
            },
            "tokens": {
                "total_tokens": metrics.total_tokens or 0,
                "avg_tokens_per_request": float(metrics.avg_tokens or 0),
                "tokens_per_hour": (metrics.total_tokens or 0) / hours if hours > 0 else 0
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def get_recommended_model(self, agent_type: AgentType, provider: str = None) -> str:
        """에이전트 타입에 따른 추천 모델 반환"""
        
        mapping = self.agent_model_mapping.get(agent_type)
        if not mapping:
            return "claude-3-haiku-20240307"  # 기본값
        
        if provider:
            # 특정 제공사 모델 필터링
            if provider.lower() == "anthropic":
                preferred = [m for m in mapping["preferred_models"] if "claude" in m.lower()]
                fallback = [m for m in mapping["fallback_models"] if "claude" in m.lower()]
            elif provider.lower() == "openai":
                preferred = [m for m in mapping["preferred_models"] if "gpt" in m.lower()]
                fallback = [m for m in mapping["fallback_models"] if "gpt" in m.lower()]
            else:
                preferred = mapping["preferred_models"]
                fallback = mapping["fallback_models"]
        else:
            preferred = mapping["preferred_models"]
            fallback = mapping["fallback_models"]
        
        return preferred[0] if preferred else (fallback[0] if fallback else "claude-3-haiku-20240307")

# 전역 인스턴스
agent_usage_tracker = AgentUsageTracker()