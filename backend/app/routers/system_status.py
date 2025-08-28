# 시스템 상태 및 실제 사용 중인 API 키 정보
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import os

from ..database import get_db
from ..models import APIKey, AIAgent, AIUsageLog

router = APIRouter(prefix="/api/system", tags=["system"])

@router.get("/status")
async def get_system_status(db: Session = Depends(get_db)):
    """시스템 상태 조회 (인증 불필요)"""
    try:
        # 실제 사용 중인 API 키들
        active_keys = db.query(APIKey).filter(APIKey.is_active == True).all()
        
        # 환경변수 체크 
        env_keys = {
            "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY" in os.environ,
            "OPENAI_API_KEY": "OPENAI_API_KEY" in os.environ,
            "GOOGLE_API_KEY": "GOOGLE_API_KEY" in os.environ
        }
        
        # AI 에이전트 현황
        total_agents = db.query(AIAgent).count()
        active_agents = db.query(AIAgent).filter(AIAgent.is_active == True).count()
        
        # 최근 7일 사용량
        week_ago = datetime.now() - timedelta(days=7)
        recent_usage = db.query(
            func.count(AIUsageLog.id).label('requests'),
            func.sum(AIUsageLog.cost).label('total_cost'),
            func.sum(AIUsageLog.total_tokens).label('total_tokens')
        ).filter(AIUsageLog.created_at >= week_ago).first()
        
        return {
            "success": True,
            "current_api_keys": [
                {
                    "id": key.id,
                    "name": key.key_name,
                    "provider": key.provider,
                    "key_preview": key.api_key[:20] + "..." if len(key.api_key) > 20 else key.api_key,
                    "is_active": key.is_active,
                    "daily_usage": key.current_daily_usage or 0,
                    "daily_limit": key.daily_limit or 0,
                    "monthly_usage": key.current_monthly_usage or 0,
                    "monthly_limit": key.monthly_limit or 0
                }
                for key in active_keys
            ],
            "environment_variables": env_keys,
            "ai_agents": {
                "total": total_agents,
                "active": active_agents
            },
            "recent_usage_7days": {
                "total_requests": int(recent_usage.requests or 0),
                "total_cost": float(recent_usage.total_cost or 0),
                "total_tokens": int(recent_usage.total_tokens or 0)
            },
            "system_info": {
                "status": "healthy" if len(active_keys) > 0 else "warning",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/pipeline/agents")
async def get_pipeline_agent_roles(db: Session = Depends(get_db)):
    """AI 파이프라인에서 사용되는 에이전트 역할 분석"""
    try:
        # 실제 사용된 task_type들 조회
        task_types = db.query(AIUsageLog.task_type).distinct().all()
        
        # 각 task_type별 사용량 통계
        task_stats = []
        for task_type_row in task_types:
            task_type = task_type_row[0]
            if task_type:  # None이 아닌 경우만
                stats = db.query(
                    func.count(AIUsageLog.id).label('requests'),
                    func.sum(AIUsageLog.cost).label('cost'),
                    func.sum(AIUsageLog.total_tokens).label('tokens'),
                    func.avg(AIUsageLog.duration_seconds).label('avg_duration')
                ).filter(AIUsageLog.task_type == task_type).first()
                
                task_stats.append({
                    "role": task_type,
                    "total_requests": int(stats.requests or 0),
                    "total_cost": float(stats.cost or 0),
                    "total_tokens": int(stats.tokens or 0),
                    "avg_duration": float(stats.avg_duration or 0)
                })
        
        # 기존 AI 에이전트들
        existing_agents = db.query(AIAgent).all()
        
        return {
            "success": True,
            "pipeline_roles": task_stats,
            "existing_agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "agent_type": agent.agent_type,
                    "model": agent.model_name,
                    "is_active": agent.is_active
                }
                for agent in existing_agents
            ],
            "total_pipeline_usage": sum(stat["total_requests"] for stat in task_stats),
            "total_pipeline_cost": sum(stat["total_cost"] for stat in task_stats)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }