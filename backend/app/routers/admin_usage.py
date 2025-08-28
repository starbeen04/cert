"""
관리자용 실시간 사용량 모니터링 라우터
/api/admin/real-time-usage 엔드포인트 구현
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.auth import get_admin_user
from app.models import User
from app.services.unified_usage_service import unified_usage_service
from app.services.openai_usage_api import openai_usage_api
from app.services.anthropic_usage_api import anthropic_usage_api
from app.services.agent_usage_tracker import agent_usage_tracker, AgentType

router = APIRouter(prefix="/api/admin", tags=["Admin Usage Monitoring"])

@router.get("/real-time-usage")
async def get_real_time_usage_admin(
    minutes: int = Query(60, ge=5, le=1440, description="조회 시간 범위 (분)"),
    include_external: bool = Query(True, description="외부 API 메트릭 포함"),
    agent_type: Optional[str] = Query(None, description="특정 에이전트 타입 필터"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    관리자용 실시간 사용량 모니터링
    
    - API별, 에이전트별 실시간 사용량 집계
    - OpenAI, Anthropic Usage API 통합 데이터
    - 에이전트별 성능 메트릭
    - 비용 분석 및 추천사항
    """
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=minutes)
        
        # 1. 기본 실시간 통계
        basic_stats = await _get_basic_realtime_stats(db, start_time, end_time)
        
        # 2. 에이전트별 분석
        agent_analysis = await _get_agent_realtime_analysis(db, start_time, agent_type)
        
        # 3. API 제공사별 성능 비교
        provider_performance = await _get_provider_performance(db, start_time)
        
        # 4. 외부 API 메트릭 (선택적)
        external_metrics = {}
        if include_external:
            try:
                sync_result = await unified_usage_service.sync_with_external_apis(
                    db=db, 
                    hours=minutes/60
                )
                external_metrics = sync_result.get("sync_results", {})
            except Exception as e:
                external_metrics = {"error": f"외부 API 조회 실패: {str(e)}"}
        
        # 5. 알림 및 경고사항
        alerts = await _generate_usage_alerts(db, start_time)
        
        # 6. 요약 및 추천사항
        summary = {
            "period_minutes": minutes,
            "total_requests": basic_stats.get("total_requests", 0),
            "total_cost": basic_stats.get("total_cost", 0),
            "active_agents": basic_stats.get("active_agents", 0),
            "active_users": basic_stats.get("active_users", 0),
            "cost_per_minute": basic_stats.get("total_cost", 0) / minutes if minutes > 0 else 0,
            "requests_per_minute": basic_stats.get("total_requests", 0) / minutes if minutes > 0 else 0
        }
        
        recommendations = _generate_recommendations(basic_stats, provider_performance, alerts)
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "period": {
                "minutes": minutes,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "summary": summary,
            "basic_statistics": basic_stats,
            "agent_analysis": agent_analysis,
            "provider_performance": provider_performance,
            "external_metrics": external_metrics,
            "alerts": alerts,
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"실시간 사용량 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/usage-sync")
async def sync_usage_data(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """외부 API와 사용량 데이터 동기화"""
    
    try:
        # 통합 서비스를 통한 동기화
        sync_result = await unified_usage_service.sync_with_external_apis(db=db)
        
        # 동기화 후 데이터베이스 업데이트 상태 확인
        updated_stats = db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_logs,
                    MAX(created_at) as last_log,
                    SUM(cost) as total_cost_today
                FROM ai_usage_logs
                WHERE DATE(created_at) = DATE('now')
            """)
        ).fetchone()
        
        return {
            "success": True,
            "sync_result": sync_result,
            "database_status": {
                "total_logs_today": updated_stats.total_logs or 0,
                "last_log": updated_stats.last_log,
                "total_cost_today": float(updated_stats.total_cost_today or 0)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"사용량 동기화 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/comprehensive-report")
async def get_comprehensive_usage_report(
    days: int = Query(7, ge=1, le=90, description="보고서 기간 (일)"),
    include_external: bool = Query(True, description="외부 API 데이터 포함"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """종합 사용량 보고서"""
    
    try:
        report = await unified_usage_service.get_comprehensive_usage_report(
            db=db,
            days=days,
            include_external=include_external
        )
        
        return {
            "success": True,
            "report": report,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"종합 보고서 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health-check")
async def health_check_admin(
    current_user: User = Depends(get_admin_user)
):
    """서비스 상태 확인"""
    
    try:
        health_status = await unified_usage_service.health_check()
        
        return {
            "success": True,
            "health_status": health_status,
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "checked_at": datetime.now().isoformat()
        }

@router.post("/test-tracking")
async def test_usage_tracking(
    provider: str = Query(..., description="API 제공사 (openai, anthropic)"),
    model: str = Query(..., description="사용할 모델"),
    agent_type: str = Query("chat_assistant", description="에이전트 타입"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """사용량 추적 시스템 테스트"""
    
    # 테스트용 API 키 (실제 환경에서는 DB에서 가져와야 함)
    test_api_keys = {
        "openai": "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",
        "anthropic": "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"
    }
    
    if provider.lower() not in test_api_keys:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 제공사: {provider}. 지원: {list(test_api_keys.keys())}"
        )
    
    try:
        # 테스트 에이전트 ID 조회
        test_agent = db.execute(
            text("SELECT id FROM ai_agents WHERE agent_type = :agent_type AND is_active = 1 LIMIT 1"),
            {"agent_type": agent_type}
        ).fetchone()
        
        if not test_agent:
            raise HTTPException(
                status_code=404,
                detail=f"활성화된 {agent_type} 에이전트를 찾을 수 없습니다"
            )
        
        # 테스트 메시지
        test_messages = [
            {"role": "user", "content": "사용량 추적 시스템 테스트입니다. 간단히 응답해주세요."}
        ]
        
        # 통합 사용량 추적 테스트
        tracking_result = await unified_usage_service.track_ai_usage(
            db=db,
            agent_id=test_agent[0],
            agent_type=agent_type,
            api_key=test_api_keys[provider.lower()],
            provider=provider,
            model=model,
            messages=test_messages,
            user_id=current_user.id,
            task_type="test",
            metadata={"test": True, "admin_user": current_user.id}
        )
        
        return {
            "success": True,
            "test_result": tracking_result,
            "test_info": {
                "provider": provider,
                "model": model,
                "agent_type": agent_type,
                "agent_id": test_agent[0],
                "user_id": current_user.id
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"사용량 추적 테스트 중 오류가 발생했습니다: {str(e)}"
        )

# 내부 헬퍼 함수들

async def _get_basic_realtime_stats(db: Session, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """기본 실시간 통계 조회"""
    
    stats = db.execute(
        text("""
            SELECT 
                COUNT(*) as total_requests,
                COUNT(DISTINCT ul.agent_id) as active_agents,
                COUNT(DISTINCT ul.user_id) as active_users,
                COUNT(DISTINCT ul.api_key_id) as active_api_keys,
                SUM(ul.total_tokens) as total_tokens,
                SUM(ul.cost) as total_cost,
                AVG(ul.duration_seconds) as avg_duration
            FROM ai_usage_logs ul
            WHERE ul.created_at >= :start_time AND ul.created_at <= :end_time
        """),
        {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    ).fetchone()
    
    return {
        "total_requests": stats.total_requests or 0,
        "active_agents": stats.active_agents or 0,
        "active_users": stats.active_users or 0,
        "active_api_keys": stats.active_api_keys or 0,
        "total_tokens": stats.total_tokens or 0,
        "total_cost": float(stats.total_cost or 0),
        "avg_duration": float(stats.avg_duration or 0)
    }

async def _get_agent_realtime_analysis(db: Session, start_time: datetime, agent_type_filter: Optional[str]) -> Dict[str, Any]:
    """에이전트별 실시간 분석"""
    
    where_clause = "WHERE ul.created_at >= :start_time"
    params = {"start_time": start_time.isoformat()}
    
    if agent_type_filter:
        where_clause += " AND ag.agent_type = :agent_type"
        params["agent_type"] = agent_type_filter
    
    agent_stats = db.execute(
        text(f"""
            SELECT 
                ag.name,
                ag.agent_type,
                ag.provider,
                COUNT(*) as requests,
                SUM(ul.total_tokens) as tokens,
                SUM(ul.cost) as cost,
                AVG(ul.duration_seconds) as avg_duration,
                COUNT(DISTINCT ul.user_id) as unique_users
            FROM ai_usage_logs ul
            JOIN ai_agents ag ON ul.agent_id = ag.id
            {where_clause}
            GROUP BY ag.id, ag.name, ag.agent_type, ag.provider
            ORDER BY cost DESC
        """),
        params
    ).fetchall()
    
    return {
        "agent_statistics": [
            {
                "name": row.name,
                "type": row.agent_type,
                "provider": row.provider,
                "requests": row.requests,
                "tokens": row.tokens or 0,
                "cost": float(row.cost or 0),
                "avg_duration": float(row.avg_duration or 0),
                "unique_users": row.unique_users or 0
            } for row in agent_stats
        ],
        "total_agents": len(agent_stats)
    }

async def _get_provider_performance(db: Session, start_time: datetime) -> Dict[str, Any]:
    """API 제공사별 성능 비교"""
    
    provider_stats = db.execute(
        text("""
            SELECT 
                ak.provider,
                COUNT(*) as requests,
                SUM(ul.total_tokens) as tokens,
                SUM(ul.cost) as cost,
                AVG(ul.duration_seconds) as avg_duration,
                COUNT(CASE WHEN ul.status = 'error' THEN 1 END) as errors
            FROM ai_usage_logs ul
            JOIN api_keys ak ON ul.api_key_id = ak.id
            WHERE ul.created_at >= :start_time
            GROUP BY ak.provider
            ORDER BY cost DESC
        """),
        {"start_time": start_time.isoformat()}
    ).fetchall()
    
    return {
        "provider_comparison": [
            {
                "provider": row.provider,
                "requests": row.requests,
                "tokens": row.tokens or 0,
                "cost": float(row.cost or 0),
                "avg_duration": float(row.avg_duration or 0),
                "error_count": row.errors or 0,
                "error_rate": (row.errors / row.requests * 100) if row.requests > 0 else 0,
                "cost_per_token": (row.cost / row.tokens) if row.tokens > 0 else 0,
                "cost_per_request": (row.cost / row.requests) if row.requests > 0 else 0
            } for row in provider_stats
        ]
    }

async def _generate_usage_alerts(db: Session, start_time: datetime) -> List[Dict[str, Any]]:
    """사용량 관련 알림 생성"""
    
    alerts = []
    
    try:
        # 1. 높은 비용의 API 키
        high_cost_keys = db.execute(
            text("""
                SELECT 
                    ak.key_name,
                    ak.provider,
                    SUM(ul.cost) as period_cost
                FROM ai_usage_logs ul
                JOIN api_keys ak ON ul.api_key_id = ak.id
                WHERE ul.created_at >= :start_time
                GROUP BY ak.id, ak.key_name, ak.provider
                HAVING SUM(ul.cost) > 5
                ORDER BY period_cost DESC
            """),
            {"start_time": start_time.isoformat()}
        ).fetchall()
        
        for key in high_cost_keys:
            alerts.append({
                "type": "high_cost",
                "severity": "medium",
                "message": f"API 키 '{key.key_name}' ({key.provider})의 비용이 ${key.period_cost:.2f}입니다",
                "data": {"key_name": key.key_name, "cost": float(key.period_cost)}
            })
        
        # 2. 에러율이 높은 에이전트
        error_prone_agents = db.execute(
            text("""
                SELECT 
                    ag.name,
                    COUNT(*) as total_requests,
                    COUNT(CASE WHEN ul.status = 'error' THEN 1 END) as errors
                FROM ai_usage_logs ul
                JOIN ai_agents ag ON ul.agent_id = ag.id
                WHERE ul.created_at >= :start_time
                GROUP BY ag.id, ag.name
                HAVING COUNT(CASE WHEN ul.status = 'error' THEN 1 END) > 3
                   AND (COUNT(CASE WHEN ul.status = 'error' THEN 1 END) * 100.0 / COUNT(*)) > 10
            """),
            {"start_time": start_time.isoformat()}
        ).fetchall()
        
        for agent in error_prone_agents:
            error_rate = (agent.errors / agent.total_requests * 100) if agent.total_requests > 0 else 0
            alerts.append({
                "type": "high_error_rate",
                "severity": "high",
                "message": f"에이전트 '{agent.name}'의 에러율이 {error_rate:.1f}%입니다",
                "data": {"agent_name": agent.name, "error_rate": error_rate}
            })
        
        # 3. 응답 시간이 느린 에이전트
        slow_agents = db.execute(
            text("""
                SELECT 
                    ag.name,
                    AVG(ul.duration_seconds) as avg_duration
                FROM ai_usage_logs ul
                JOIN ai_agents ag ON ul.agent_id = ag.id
                WHERE ul.created_at >= :start_time
                  AND ul.duration_seconds > 0
                GROUP BY ag.id, ag.name
                HAVING AVG(ul.duration_seconds) > 15
                ORDER BY avg_duration DESC
            """),
            {"start_time": start_time.isoformat()}
        ).fetchall()
        
        for agent in slow_agents:
            alerts.append({
                "type": "slow_response",
                "severity": "medium",
                "message": f"에이전트 '{agent.name}'의 평균 응답시간이 {agent.avg_duration:.1f}초입니다",
                "data": {"agent_name": agent.name, "avg_duration": float(agent.avg_duration)}
            })
            
    except Exception as e:
        alerts.append({
            "type": "system_error",
            "severity": "low",
            "message": f"알림 생성 중 오류: {str(e)}"
        })
    
    return alerts

def _generate_recommendations(basic_stats: Dict, provider_performance: Dict, alerts: List) -> List[Dict[str, Any]]:
    """추천사항 생성"""
    
    recommendations = []
    
    try:
        # 1. 비용 최적화 추천
        if basic_stats.get("total_cost", 0) > 20:
            recommendations.append({
                "type": "cost_optimization",
                "priority": "high",
                "message": "일일 비용이 $20을 초과했습니다. 사용량을 검토하고 불필요한 요청을 줄이는 것을 고려하세요.",
                "action": "비용 분석 및 최적화"
            })
        
        # 2. 성능 최적화 추천
        if basic_stats.get("avg_duration", 0) > 10:
            recommendations.append({
                "type": "performance_optimization",
                "priority": "medium",
                "message": "평균 응답시간이 10초를 초과합니다. 더 빠른 모델 사용을 고려하세요.",
                "action": "모델 최적화"
            })
        
        # 3. 제공사 비교 기반 추천
        providers = provider_performance.get("provider_comparison", [])
        if len(providers) > 1:
            cheapest = min(providers, key=lambda x: x.get("cost_per_token", float('inf')))
            most_expensive = max(providers, key=lambda x: x.get("cost_per_token", 0))
            
            if cheapest["cost_per_token"] > 0 and most_expensive["cost_per_token"] > cheapest["cost_per_token"] * 2:
                recommendations.append({
                    "type": "provider_optimization",
                    "priority": "medium",
                    "message": f"{cheapest['provider']}가 {most_expensive['provider']}보다 토큰당 비용이 절반 수준입니다.",
                    "action": f"{cheapest['provider']} 사용량 늘리기 고려"
                })
        
        # 4. 알림 기반 추천
        high_error_alerts = [a for a in alerts if a["type"] == "high_error_rate"]
        if high_error_alerts:
            recommendations.append({
                "type": "reliability_improvement",
                "priority": "high",
                "message": f"{len(high_error_alerts)}개 에이전트에서 높은 에러율이 감지되었습니다.",
                "action": "에러 로그 분석 및 에이전트 설정 검토"
            })
    
    except Exception as e:
        recommendations.append({
            "type": "system",
            "priority": "low",
            "message": f"추천사항 생성 중 오류: {str(e)}"
        })
    
    return recommendations