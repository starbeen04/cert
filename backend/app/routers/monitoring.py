from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text, distinct
from app.database import get_db
from app.models import (
    AIAgent, User, Certificate, Question, StudySession, 
    AIUsageLog, APIKey, ChatSession, ChatMessage, AITask
)
from app.auth import get_current_admin_user
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/dashboard/overview")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """관리자 대시보드 전체 개요"""
    try:
        # 기본 통계
        total_users = db.query(User).count()
        total_certificates = db.query(Certificate).count()
        total_questions = db.query(Question).count()
        total_agents = db.query(AIAgent).count()
        
        # 활성 데이터
        active_certificates = db.query(Certificate).filter(Certificate.status == "active").count()
        active_agents = db.query(AIAgent).filter(AIAgent.is_active == True).count()
        active_api_keys = db.query(APIKey).filter(APIKey.is_active == True).count()
        
        # 최근 7일 활동
        week_ago = datetime.now() - timedelta(days=7)
        
        # 학습 활동
        recent_study_sessions = db.query(StudySession).filter(
            StudySession.started_at >= week_ago
        ).count()
        
        # AI 사용량
        recent_ai_usage = db.query(
            func.sum(AIUsageLog.cost).label('cost'),
            func.sum(AIUsageLog.total_tokens).label('tokens'),
            func.count(AIUsageLog.id).label('requests')
        ).filter(
            AIUsageLog.created_at >= week_ago
        ).first()
        
        # 채팅 활동
        recent_chat_messages = db.query(ChatMessage).filter(
            ChatMessage.created_at >= week_ago
        ).count()
        
        # 시스템 상태
        system_health = {
            "api_keys_active": active_api_keys > 0,
            "agents_available": active_agents > 0,
            "certificates_published": active_certificates > 0,
            "overall_status": "healthy" if (active_api_keys > 0 and active_agents > 0) else "warning"
        }
        
        return {
            "success": True,
            "overview": {
                "total_users": total_users,
                "total_certificates": total_certificates,
                "total_questions": total_questions,
                "total_agents": total_agents,
                "active_certificates": active_certificates,
                "active_agents": active_agents,
                "active_api_keys": active_api_keys
            },
            "recent_activity": {
                "study_sessions": recent_study_sessions,
                "ai_requests": int(recent_ai_usage.requests or 0),
                "ai_cost": float(recent_ai_usage.cost or 0),
                "ai_tokens": int(recent_ai_usage.tokens or 0),
                "chat_messages": recent_chat_messages
            },
            "system_health": system_health
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대시보드 데이터 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/dashboard/realtime-stats")
async def get_realtime_stats(
    hours: int = 24,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """실시간 통계 데이터"""
    try:
        start_time = datetime.now() - timedelta(hours=hours)
        
        # 시간별 AI 사용량
        hourly_ai_usage = db.query(
            func.date_trunc('hour', AIUsageLog.created_at).label('hour'),
            func.sum(AIUsageLog.cost).label('cost'),
            func.sum(AIUsageLog.total_tokens).label('tokens'),
            func.count(AIUsageLog.id).label('requests')
        ).filter(
            AIUsageLog.created_at >= start_time
        ).group_by(
            func.date_trunc('hour', AIUsageLog.created_at)
        ).order_by(
            func.date_trunc('hour', AIUsageLog.created_at)
        ).all()
        
        # 시간별 학습 활동
        hourly_study = db.query(
            func.date_trunc('hour', StudySession.started_at).label('hour'),
            func.count(StudySession.id).label('sessions'),
            func.count(distinct(StudySession.user_id)).label('users')
        ).filter(
            StudySession.started_at >= start_time
        ).group_by(
            func.date_trunc('hour', StudySession.started_at)
        ).order_by(
            func.date_trunc('hour', StudySession.started_at)
        ).all()
        
        # 시간별 채팅 활동
        hourly_chat = db.query(
            func.date_trunc('hour', ChatMessage.created_at).label('hour'),
            func.count(ChatMessage.id).label('messages'),
            func.count(distinct(ChatMessage.session_id)).label('sessions')
        ).filter(
            ChatMessage.created_at >= start_time
        ).group_by(
            func.date_trunc('hour', ChatMessage.created_at)
        ).order_by(
            func.date_trunc('hour', ChatMessage.created_at)
        ).all()
        
        # 현재 활성 사용자 (최근 1시간 내 활동)
        active_users = db.query(
            func.count(distinct(StudySession.user_id)).label('study_users'),
            func.count(distinct(ChatSession.user_id)).label('chat_users')
        ).select_from(
            StudySession.join(ChatSession, ChatSession.user_id == StudySession.user_id, isouter=True)
        ).filter(
            StudySession.started_at >= datetime.now() - timedelta(hours=1)
        ).first()
        
        return {
            "success": True,
            "period_hours": hours,
            "realtime_data": {
                "hourly_ai_usage": [
                    {
                        "hour": usage.hour.isoformat() if usage.hour else None,
                        "cost": float(usage.cost or 0),
                        "tokens": int(usage.tokens or 0),
                        "requests": int(usage.requests or 0)
                    } for usage in hourly_ai_usage
                ],
                "hourly_study_activity": [
                    {
                        "hour": study.hour.isoformat() if study.hour else None,
                        "sessions": int(study.sessions or 0),
                        "unique_users": int(study.users or 0)
                    } for study in hourly_study
                ],
                "hourly_chat_activity": [
                    {
                        "hour": chat.hour.isoformat() if chat.hour else None,
                        "messages": int(chat.messages or 0),
                        "sessions": int(chat.sessions or 0)
                    } for chat in hourly_chat
                ],
                "current_active_users": {
                    "study_users": int(active_users.study_users or 0),
                    "chat_users": int(active_users.chat_users or 0)
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"실시간 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/dashboard/performance-metrics")
async def get_performance_metrics(
    days: int = 7,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """시스템 성능 메트릭"""
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # AI 에이전트 성능
        agent_performance = db.query(
            AIAgent.name,
            AIAgent.agent_type,
            func.count(AIUsageLog.id).label('total_requests'),
            func.avg(AIUsageLog.duration_seconds).label('avg_response_time'),
            func.sum(case([(AIUsageLog.status == 'error', 1)], else_=0)).label('error_count'),
            func.sum(AIUsageLog.cost).label('total_cost')
        ).join(
            AIUsageLog, AIAgent.id == AIUsageLog.agent_id
        ).filter(
            AIUsageLog.created_at >= start_date
        ).group_by(
            AIAgent.id, AIAgent.name, AIAgent.agent_type
        ).order_by(
            func.count(AIUsageLog.id).desc()
        ).limit(10).all()
        
        # API 키 성능
        api_performance = db.query(
            APIKey.key_name,
            APIKey.provider,
            func.count(AIUsageLog.id).label('requests'),
            func.sum(AIUsageLog.cost).label('cost'),
            func.avg(AIUsageLog.duration_seconds).label('avg_duration')
        ).join(
            AIUsageLog, APIKey.id == AIUsageLog.api_key_id
        ).filter(
            AIUsageLog.created_at >= start_date
        ).group_by(
            APIKey.id, APIKey.key_name, APIKey.provider
        ).order_by(
            func.sum(AIUsageLog.cost).desc()
        ).all()
        
        # 학습 성과 지표
        learning_metrics = db.query(
            Certificate.title,
            func.count(StudySession.id).label('sessions'),
            func.avg(StudySession.score_percentage).label('avg_score'),
            func.count(case([(StudySession.passed == True, 1)], else_=None)).label('passed_sessions'),
            func.avg(StudySession.time_spent_minutes).label('avg_duration')
        ).join(
            StudySession, Certificate.id == StudySession.certificate_id
        ).filter(
            StudySession.started_at >= start_date,
            StudySession.completed == True
        ).group_by(
            Certificate.id, Certificate.title
        ).order_by(
            func.count(StudySession.id).desc()
        ).limit(10).all()
        
        # 시스템 에러 분석
        error_analysis = db.query(
            AIUsageLog.error_message,
            func.count(AIUsageLog.id).label('count')
        ).filter(
            AIUsageLog.created_at >= start_date,
            AIUsageLog.status == 'error',
            AIUsageLog.error_message.isnot(None)
        ).group_by(
            AIUsageLog.error_message
        ).order_by(
            func.count(AIUsageLog.id).desc()
        ).limit(10).all()
        
        return {
            "success": True,
            "period_days": days,
            "performance_metrics": {
                "agent_performance": [
                    {
                        "name": agent.name,
                        "type": agent.agent_type,
                        "total_requests": int(agent.total_requests or 0),
                        "avg_response_time": float(agent.avg_response_time or 0),
                        "error_count": int(agent.error_count or 0),
                        "total_cost": float(agent.total_cost or 0),
                        "error_rate": (agent.error_count / agent.total_requests * 100) if agent.total_requests > 0 else 0
                    } for agent in agent_performance
                ],
                "api_performance": [
                    {
                        "key_name": api.key_name,
                        "provider": api.provider,
                        "requests": int(api.requests or 0),
                        "cost": float(api.cost or 0),
                        "avg_duration": float(api.avg_duration or 0)
                    } for api in api_performance
                ],
                "learning_metrics": [
                    {
                        "certificate": cert.title,
                        "sessions": int(cert.sessions or 0),
                        "avg_score": float(cert.avg_score or 0),
                        "passed_sessions": int(cert.passed_sessions or 0),
                        "pass_rate": (cert.passed_sessions / cert.sessions * 100) if cert.sessions > 0 else 0,
                        "avg_duration_minutes": float(cert.avg_duration or 0)
                    } for cert in learning_metrics
                ],
                "error_analysis": [
                    {
                        "error_message": error.error_message[:100] + "..." if len(error.error_message) > 100 else error.error_message,
                        "count": int(error.count or 0)
                    } for error in error_analysis
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"성능 메트릭 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/dashboard/resource-utilization")
async def get_resource_utilization(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """리소스 사용률 분석"""
    try:
        # API 키 사용률
        api_utilization = db.query(
            APIKey.key_name,
            APIKey.provider,
            APIKey.daily_limit,
            APIKey.monthly_limit,
            APIKey.current_daily_usage,
            APIKey.current_monthly_usage,
            APIKey.is_active
        ).all()
        
        # 에이전트별 작업 큐 상태
        agent_workload = db.query(
            AIAgent.name,
            AIAgent.agent_type,
            func.count(AITask.id).label('pending_tasks'),
            func.count(case([(AITask.status == 'processing', 1)], else_=None)).label('processing_tasks'),
            func.count(case([(AITask.status == 'completed', 1)], else_=None)).label('completed_tasks'),
            func.count(case([(AITask.status == 'failed', 1)], else_=None)).label('failed_tasks')
        ).outerjoin(
            AITask, AIAgent.id == AITask.agent_id
        ).group_by(
            AIAgent.id, AIAgent.name, AIAgent.agent_type
        ).all()
        
        # 데이터베이스 크기 정보 (PostgreSQL 전용)
        db_size_query = text("""
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation,
                most_common_vals
            FROM pg_stats 
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        
        # 시스템 리소스 요약
        total_storage = db.query(
            func.count(Question.id).label('total_questions'),
            func.count(ChatMessage.id).label('total_messages'),
            func.count(AIUsageLog.id).label('total_logs')
        ).first()
        
        return {
            "success": True,
            "resource_utilization": {
                "api_keys": [
                    {
                        "key_name": api.key_name,
                        "provider": api.provider,
                        "daily_usage_percent": (api.current_daily_usage / api.daily_limit * 100) if api.daily_limit else 0,
                        "monthly_usage_percent": (api.current_monthly_usage / api.monthly_limit * 100) if api.monthly_limit else 0,
                        "is_active": api.is_active,
                        "status": "healthy" if (api.current_daily_usage < (api.daily_limit * 0.8) if api.daily_limit else True) else "warning"
                    } for api in api_utilization
                ],
                "agent_workload": [
                    {
                        "name": agent.name,
                        "type": agent.agent_type,
                        "pending_tasks": int(agent.pending_tasks or 0),
                        "processing_tasks": int(agent.processing_tasks or 0),
                        "completed_tasks": int(agent.completed_tasks or 0),
                        "failed_tasks": int(agent.failed_tasks or 0),
                        "total_tasks": int((agent.pending_tasks or 0) + (agent.processing_tasks or 0) + (agent.completed_tasks or 0) + (agent.failed_tasks or 0))
                    } for agent in agent_workload
                ],
                "storage_summary": {
                    "total_questions": int(total_storage.total_questions or 0),
                    "total_messages": int(total_storage.total_messages or 0),
                    "total_usage_logs": int(total_storage.total_logs or 0)
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"리소스 사용률 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/alerts/system-health")
async def get_system_health_alerts(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """시스템 상태 알림"""
    try:
        alerts = []
        
        # API 키 상태 확인
        inactive_api_keys = db.query(APIKey).filter(APIKey.is_active == False).count()
        if inactive_api_keys > 0:
            alerts.append({
                "type": "warning",
                "message": f"{inactive_api_keys}개의 API 키가 비활성화되어 있습니다.",
                "category": "api_keys",
                "severity": "medium"
            })
        
        # 높은 사용률 API 키
        high_usage_keys = db.query(APIKey).filter(
            APIKey.is_active == True,
            APIKey.current_daily_usage / APIKey.daily_limit > 0.9
        ).all()
        
        for key in high_usage_keys:
            alerts.append({
                "type": "warning",
                "message": f"API 키 '{key.key_name}'의 일일 사용률이 90%를 초과했습니다.",
                "category": "api_usage",
                "severity": "high"
            })
        
        # 최근 에러 많은 에이전트
        recent_errors = db.query(
            AIAgent.name,
            func.count(AIUsageLog.id).label('error_count')
        ).join(
            AIUsageLog, AIAgent.id == AIUsageLog.agent_id
        ).filter(
            AIUsageLog.created_at >= datetime.now() - timedelta(hours=1),
            AIUsageLog.status == 'error'
        ).group_by(
            AIAgent.id, AIAgent.name
        ).having(
            func.count(AIUsageLog.id) > 5
        ).all()
        
        for agent in recent_errors:
            alerts.append({
                "type": "error",
                "message": f"AI 에이전트 '{agent.name}'에서 최근 1시간 내 {agent.error_count}개의 에러가 발생했습니다.",
                "category": "agent_errors",
                "severity": "high"
            })
        
        # 비활성 에이전트
        inactive_agents = db.query(AIAgent).filter(AIAgent.is_active == False).count()
        if inactive_agents > 0:
            alerts.append({
                "type": "info",
                "message": f"{inactive_agents}개의 AI 에이전트가 비활성화되어 있습니다.",
                "category": "agents",
                "severity": "low"
            })
        
        # 느린 응답 시간
        slow_agents = db.query(
            AIAgent.name,
            func.avg(AIUsageLog.duration_seconds).label('avg_duration')
        ).join(
            AIUsageLog, AIAgent.id == AIUsageLog.agent_id
        ).filter(
            AIUsageLog.created_at >= datetime.now() - timedelta(hours=1)
        ).group_by(
            AIAgent.id, AIAgent.name
        ).having(
            func.avg(AIUsageLog.duration_seconds) > 10
        ).all()
        
        for agent in slow_agents:
            alerts.append({
                "type": "warning",
                "message": f"AI 에이전트 '{agent.name}'의 평균 응답 시간이 {agent.avg_duration:.2f}초입니다.",
                "category": "performance",
                "severity": "medium"
            })
        
        return {
            "success": True,
            "alerts": alerts,
            "alert_counts": {
                "total": len(alerts),
                "high": len([a for a in alerts if a["severity"] == "high"]),
                "medium": len([a for a in alerts if a["severity"] == "medium"]),
                "low": len([a for a in alerts if a["severity"] == "low"])
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 상태 확인 중 오류가 발생했습니다: {str(e)}"
        )

# Import case function
from sqlalchemy import case

# 새로운 사용량 추적 서비스 import
from app.services.openai_usage_api import openai_usage_api
from app.services.anthropic_usage_api import anthropic_usage_api
from app.services.agent_usage_tracker import agent_usage_tracker, AgentType

@router.get("/real-time-usage")
async def get_real_time_usage(
    minutes: int = Query(60, ge=5, le=1440),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    실시간 사용량 모니터링
    - API별, 에이전트별 실시간 사용량 집계 및 반환
    - OpenAI, Anthropic Usage API 통합
    """
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=minutes)
        
        # 1. 기본 실시간 통계 (기존 로그 기반)
        realtime_stats = db.execute(
            text("""
                SELECT 
                    ak.provider,
                    ak.key_name,
                    ag.name as agent_name,
                    ag.agent_type,
                    COUNT(*) as requests,
                    SUM(ul.total_tokens) as total_tokens,
                    SUM(ul.cost) as total_cost,
                    AVG(ul.duration_seconds) as avg_duration,
                    MAX(ul.created_at) as last_used
                FROM ai_usage_logs ul
                JOIN api_keys ak ON ul.api_key_id = ak.id
                JOIN ai_agents ag ON ul.agent_id = ag.id
                WHERE ul.created_at >= :start_time
                GROUP BY ak.provider, ak.key_name, ag.name, ag.agent_type
                ORDER BY total_cost DESC
            """),
            {
                "start_time": start_time.isoformat()
            }
        ).fetchall()
        
        # 2. 분당 활동 트렌드
        minute_trends = db.execute(
            text("""
                SELECT 
                    strftime('%Y-%m-%d %H:%M', ul.created_at) as minute,
                    ak.provider,
                    COUNT(*) as requests,
                    SUM(ul.cost) as cost,
                    SUM(ul.total_tokens) as tokens
                FROM ai_usage_logs ul
                JOIN api_keys ak ON ul.api_key_id = ak.id
                WHERE ul.created_at >= :start_time
                GROUP BY strftime('%Y-%m-%d %H:%M', ul.created_at), ak.provider
                ORDER BY minute DESC
                LIMIT 60
            """),
            {
                "start_time": start_time.isoformat()
            }
        ).fetchall()
        
        # 3. 에이전트별 성능 메트릭
        agent_performance = []
        for agent_type in AgentType:
            metrics = await agent_usage_tracker.get_agent_performance_metrics(
                db=db,
                agent_id=None,  # 타입별 전체 조회를 위해 별도 쿼리 필요
                hours=minutes/60
            )
            if not metrics.get("no_data"):
                agent_performance.append({
                    "agent_type": agent_type.value,
                    "metrics": metrics
                })
        
        # 4. API 키별 실시간 상태
        api_key_status = db.execute(
            text("""
                SELECT 
                    ak.id,
                    ak.key_name,
                    ak.provider,
                    ak.daily_limit,
                    ak.monthly_limit,
                    ak.current_daily_usage,
                    ak.current_monthly_usage,
                    ak.is_active,
                    COUNT(ul.id) as recent_requests,
                    SUM(ul.cost) as recent_cost,
                    MAX(ul.created_at) as last_request
                FROM api_keys ak
                LEFT JOIN ai_usage_logs ul ON ak.id = ul.api_key_id 
                    AND ul.created_at >= :start_time
                WHERE ak.is_active = 1
                GROUP BY ak.id, ak.key_name, ak.provider, ak.daily_limit, 
                         ak.monthly_limit, ak.current_daily_usage, 
                         ak.current_monthly_usage, ak.is_active
                ORDER BY recent_cost DESC
            """),
            {
                "start_time": start_time.isoformat()
            }
        ).fetchall()
        
        # 5. 현재 활성 사용자 및 세션
        active_sessions = db.execute(
            text("""
                SELECT 
                    COUNT(DISTINCT ul.user_id) as active_users,
                    COUNT(DISTINCT CASE WHEN ag.agent_type = 'document_analyzer' THEN ul.user_id END) as doc_users,
                    COUNT(DISTINCT CASE WHEN ag.agent_type = 'quiz_master' THEN ul.user_id END) as quiz_users,
                    COUNT(DISTINCT CASE WHEN ag.agent_type = 'study_tutor' THEN ul.user_id END) as tutor_users,
                    COUNT(*) as total_requests
                FROM ai_usage_logs ul
                JOIN ai_agents ag ON ul.agent_id = ag.id
                WHERE ul.created_at >= :start_time
            """),
            {
                "start_time": start_time.isoformat()
            }
        ).fetchone()
        
        # 응답 데이터 구성
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "period_minutes": minutes,
            "realtime_metrics": {
                "summary": {
                    "total_requests": sum(row.requests for row in realtime_stats),
                    "total_tokens": sum(row.total_tokens or 0 for row in realtime_stats),
                    "total_cost": sum(row.total_cost or 0 for row in realtime_stats),
                    "active_api_keys": len([row for row in api_key_status if row.recent_requests > 0]),
                    "active_users": active_sessions.active_users or 0,
                    "requests_per_minute": sum(row.requests for row in realtime_stats) / minutes if minutes > 0 else 0
                },
                "api_provider_breakdown": [
                    {
                        "provider": row.provider,
                        "key_name": row.key_name,
                        "requests": row.requests,
                        "tokens": row.total_tokens or 0,
                        "cost": float(row.total_cost or 0),
                        "avg_duration": float(row.avg_duration or 0),
                        "last_used": row.last_used
                    } for row in realtime_stats
                ],
                "agent_breakdown": [
                    {
                        "agent_name": row.agent_name,
                        "agent_type": row.agent_type,
                        "provider": row.provider,
                        "requests": row.requests,
                        "tokens": row.total_tokens or 0,
                        "cost": float(row.total_cost or 0),
                        "avg_duration": float(row.avg_duration or 0)
                    } for row in realtime_stats
                ],
                "minute_trends": [
                    {
                        "minute": row.minute,
                        "provider": row.provider,
                        "requests": row.requests,
                        "cost": float(row.cost or 0),
                        "tokens": row.tokens or 0
                    } for row in minute_trends
                ],
                "api_key_status": [
                    {
                        "key_id": row.id,
                        "key_name": row.key_name,
                        "provider": row.provider,
                        "daily_usage_percent": (row.current_daily_usage / row.daily_limit * 100) if row.daily_limit else 0,
                        "monthly_usage_percent": (row.current_monthly_usage / row.monthly_limit * 100) if row.monthly_limit else 0,
                        "recent_requests": row.recent_requests or 0,
                        "recent_cost": float(row.recent_cost or 0),
                        "last_request": row.last_request,
                        "is_active": bool(row.is_active),
                        "status": "healthy" if row.recent_requests > 0 else "idle"
                    } for row in api_key_status
                ],
                "active_sessions": {
                    "total_active_users": active_sessions.active_users or 0,
                    "document_analyzer_users": active_sessions.doc_users or 0,
                    "quiz_master_users": active_sessions.quiz_users or 0,
                    "study_tutor_users": active_sessions.tutor_users or 0,
                    "total_requests_period": active_sessions.total_requests or 0
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"실시간 사용량 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/usage-api/sync")
async def sync_usage_with_providers(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    외부 API 제공사들의 Usage API와 동기화
    - OpenAI Usage API
    - Anthropic Usage and Cost API
    """
    try:
        sync_results = {}
        
        # 활성 API 키 조회
        api_keys = db.execute(
            text("""
                SELECT id, provider, key_name, api_key 
                FROM api_keys 
                WHERE is_active = 1
            """)
        ).fetchall()
        
        # OpenAI API 키 동기화
        openai_keys = [k for k in api_keys if k.provider.lower() == "openai"]
        for key in openai_keys:
            try:
                result = await openai_usage_api.track_api_key_usage(
                    db=db,
                    api_key_id=key.id,
                    openai_api_key=key.api_key
                )
                sync_results[f"openai_{key.key_name}"] = result
            except Exception as e:
                sync_results[f"openai_{key.key_name}"] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Anthropic API 키 동기화 (Admin API 키 필요)
        anthropic_admin_key = "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"
        anthropic_keys = [k for k in api_keys if k.provider.lower() == "anthropic"]
        
        for key in anthropic_keys:
            try:
                result = await anthropic_usage_api.track_api_key_usage(
                    db=db,
                    api_key_id=key.id,
                    admin_api_key=anthropic_admin_key,
                    user_api_key=key.api_key
                )
                sync_results[f"anthropic_{key.key_name}"] = result
            except Exception as e:
                sync_results[f"anthropic_{key.key_name}"] = {
                    "success": False,
                    "error": str(e)
                }
        
        # 동기화 결과 요약
        successful_syncs = len([r for r in sync_results.values() if r.get("success")])
        total_syncs = len(sync_results)
        
        return {
            "success": True,
            "sync_summary": {
                "total_api_keys": total_syncs,
                "successful_syncs": successful_syncs,
                "failed_syncs": total_syncs - successful_syncs,
                "sync_rate": (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0
            },
            "detailed_results": sync_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용량 동기화 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/usage-api/external-metrics")
async def get_external_usage_metrics(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    외부 API 제공사의 실시간 메트릭 조회
    """
    try:
        # 기본 API 키 정보 (실제 환경에서는 보안 저장소에서 가져와야 함)
        openai_api_key = "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"
        anthropic_admin_key = "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"
        
        external_metrics = {}
        
        # OpenAI 실시간 메트릭
        try:
            openai_metrics = await openai_usage_api.get_realtime_metrics(
                api_key=openai_api_key,
                minutes=hours * 60
            )
            external_metrics["openai"] = openai_metrics
        except Exception as e:
            external_metrics["openai"] = {
                "success": False,
                "error": str(e)
            }
        
        # Anthropic 실시간 메트릭
        try:
            anthropic_metrics = await anthropic_usage_api.get_realtime_metrics(
                admin_api_key=anthropic_admin_key,
                hours=hours
            )
            external_metrics["anthropic"] = anthropic_metrics
        except Exception as e:
            external_metrics["anthropic"] = {
                "success": False,
                "error": str(e)
            }
        
        # 모델별 사용량 분석 (Anthropic)
        try:
            model_breakdown = await anthropic_usage_api.get_model_usage_breakdown(
                admin_api_key=anthropic_admin_key,
                days=hours // 24 if hours >= 24 else 1
            )
            external_metrics["anthropic_models"] = model_breakdown
        except Exception as e:
            external_metrics["anthropic_models"] = {
                "success": False,
                "error": str(e)
            }
        
        return {
            "success": True,
            "period_hours": hours,
            "timestamp": datetime.now().isoformat(),
            "external_metrics": external_metrics,
            "data_freshness": {
                "openai": "real-time" if external_metrics.get("openai", {}).get("success") else "unavailable",
                "anthropic": "real-time" if external_metrics.get("anthropic", {}).get("success") else "unavailable",
                "note": "External API data may have delays up to 5-15 minutes"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"외부 메트릭 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/usage-api/agent-analytics")
async def get_agent_usage_analytics(
    agent_type: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    에이전트별 상세 사용량 분석
    """
    try:
        # 에이전트 타입 파싱
        agent_type_enum = None
        if agent_type:
            try:
                agent_type_enum = AgentType(agent_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"잘못된 에이전트 타입: {agent_type}. 유효한 타입: {[t.value for t in AgentType]}"
                )
        
        # 에이전트별 사용량 요약
        usage_summary = await agent_usage_tracker.get_agent_usage_summary(
            db=db,
            agent_type=agent_type_enum,
            days=days
        )
        
        # 에이전트 성능 비교
        performance_comparison = []
        
        if not agent_type_enum:
            # 모든 에이전트 타입 비교
            for a_type in AgentType:
                try:
                    # 해당 타입의 에이전트 ID 조회
                    agent_ids = db.execute(
                        text("""
                            SELECT id FROM ai_agents 
                            WHERE agent_type = :agent_type AND is_active = 1
                            LIMIT 1
                        """),
                        {"agent_type": a_type.value}
                    ).fetchone()
                    
                    if agent_ids:
                        perf_metrics = await agent_usage_tracker.get_agent_performance_metrics(
                            db=db,
                            agent_id=agent_ids[0],
                            hours=days * 24
                        )
                        if not perf_metrics.get("no_data"):
                            performance_comparison.append({
                                "agent_type": a_type.value,
                                "performance": perf_metrics
                            })
                except Exception as e:
                    # 개별 에이전트 오류는 무시하고 계속 진행
                    continue
        
        # 비용 효율성 분석
        cost_efficiency = db.execute(
            text("""
                SELECT 
                    ag.agent_type,
                    ag.provider,
                    COUNT(*) as requests,
                    AVG(ul.cost / ul.total_tokens) as cost_per_token,
                    AVG(ul.duration_seconds) as avg_response_time,
                    SUM(ul.cost) / COUNT(*) as cost_per_request
                FROM ai_usage_logs ul
                JOIN ai_agents ag ON ul.agent_id = ag.id
                WHERE ul.created_at >= :start_date
                  AND ul.total_tokens > 0
                  AND ul.cost > 0
                GROUP BY ag.agent_type, ag.provider
                ORDER BY cost_per_token ASC
            """),
            {
                "start_date": (datetime.now() - timedelta(days=days)).isoformat()
            }
        ).fetchall()
        
        return {
            "success": True,
            "period_days": days,
            "agent_type_filter": agent_type,
            "timestamp": datetime.now().isoformat(),
            "analytics": {
                "usage_summary": usage_summary,
                "performance_comparison": performance_comparison,
                "cost_efficiency": [
                    {
                        "agent_type": row.agent_type,
                        "provider": row.provider,
                        "requests": row.requests,
                        "cost_per_token": float(row.cost_per_token or 0),
                        "avg_response_time": float(row.avg_response_time or 0),
                        "cost_per_request": float(row.cost_per_request or 0)
                    } for row in cost_efficiency
                ],
                "recommendations": [
                    {
                        "type": "cost_optimization",
                        "message": "Document Analyzer에 더 저렴한 모델 사용 고려",
                        "priority": "medium"
                    } if len(cost_efficiency) > 0 else None,
                    {
                        "type": "performance",
                        "message": "평균 응답시간 10초 이상인 에이전트 최적화 필요",
                        "priority": "high"
                    } if any(row.avg_response_time > 10 for row in cost_efficiency) else None
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"에이전트 분석 중 오류가 발생했습니다: {str(e)}"
        )