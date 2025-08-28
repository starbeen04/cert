"""
통합 사용량 추적 서비스
- 기존 사용량 추적과 새로운 API들을 통합
- 실시간 동기화 및 일관성 보장
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from .enhanced_usage_tracker import enhanced_usage_tracker
from .openai_usage_api import openai_usage_api
from .anthropic_usage_api import anthropic_usage_api
from .agent_usage_tracker import agent_usage_tracker, AgentType

class UnifiedUsageService:
    """통합 사용량 추적 서비스"""
    
    def __init__(self):
        self.openai_api_key = "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"
        self.anthropic_admin_key = "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"
    
    async def track_ai_usage(
        self,
        db: Session,
        agent_id: int,
        agent_type: str,
        api_key: str,
        provider: str,
        model: str,
        messages: List[Dict],
        user_id: Optional[int] = None,
        task_type: str = "general",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        AI 사용량을 통합적으로 추적
        
        1. 실제 API 호출 및 응답 처리
        2. 사용량 로깅 (기존 방식 + 새로운 방식)
        3. 에이전트별 통계 업데이트
        4. 외부 API와 동기화
        """
        
        try:
            # 1. 실제 AI API 호출
            if provider.lower() == "anthropic":
                usage_result = await enhanced_usage_tracker.track_anthropic_usage(
                    api_key=api_key,
                    messages=messages,
                    model=model
                )
            elif provider.lower() == "openai":
                usage_result = await enhanced_usage_tracker.track_openai_usage(
                    api_key=api_key,
                    messages=messages,
                    model=model
                )
            else:
                return {
                    "success": False,
                    "error": f"지원하지 않는 제공사: {provider}"
                }
            
            if not usage_result.get("success"):
                return usage_result
            
            # 2. 에이전트별 사용량 추적
            try:
                agent_type_enum = AgentType(agent_type.lower())
            except ValueError:
                agent_type_enum = AgentType.CHAT_ASSISTANT  # 기본값
            
            # API 키 ID 조회
            api_key_result = await self._get_api_key_id(db, api_key)
            if not api_key_result["success"]:
                return api_key_result
            
            api_key_id = api_key_result["api_key_id"]
            
            # 에이전트별 로깅
            agent_tracking_result = await agent_usage_tracker.track_agent_usage(
                db=db,
                agent_id=agent_id,
                agent_type=agent_type_enum,
                api_key_id=api_key_id,
                user_id=user_id,
                task_type=task_type,
                model_used=model,
                usage_data=usage_result["usage"],
                cost=usage_result["cost"],
                duration_seconds=usage_result["duration_seconds"],
                status="success",
                request_metadata={"messages": len(messages), "metadata": metadata},
                response_metadata={"response_length": len(usage_result.get("response", ""))}
            )
            
            # 3. 기존 향상된 추적 시스템도 사용
            enhanced_log_result = await enhanced_usage_tracker.log_enhanced_usage(
                api_key=api_key,
                endpoint=f"/ai/{task_type}",
                usage_result=usage_result
            )
            
            return {
                "success": True,
                "response": usage_result.get("response"),
                "usage": usage_result["usage"],
                "cost": usage_result["cost"],
                "duration": usage_result["duration_seconds"],
                "tracking_results": {
                    "agent_tracking": agent_tracking_result,
                    "enhanced_logging": enhanced_log_result
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"통합 사용량 추적 중 오류: {str(e)}"
            }
    
    async def sync_with_external_apis(
        self,
        db: Session,
        hours: int = 24
    ) -> Dict[str, Any]:
        """외부 API들과 사용량 동기화"""
        
        sync_results = {}
        
        try:
            # 1. OpenAI Usage API와 동기화
            openai_sync = await openai_usage_api.get_realtime_metrics(
                api_key=self.openai_api_key,
                minutes=hours * 60
            )
            sync_results["openai"] = openai_sync
            
            # 2. Anthropic Usage API와 동기화
            anthropic_sync = await anthropic_usage_api.get_realtime_metrics(
                admin_api_key=self.anthropic_admin_key,
                hours=hours
            )
            sync_results["anthropic"] = anthropic_sync
            
            return {
                "success": True,
                "sync_results": sync_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"외부 API 동기화 중 오류: {str(e)}",
                "partial_results": sync_results
            }
    
    async def get_comprehensive_usage_report(
        self,
        db: Session,
        days: int = 7,
        include_external: bool = True
    ) -> Dict[str, Any]:
        """종합 사용량 보고서"""
        
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # 1. 에이전트별 사용량 요약
            agent_summary = await agent_usage_tracker.get_agent_usage_summary(
                db=db,
                days=days
            )
            
            # 2. 외부 API 메트릭 (옵션)
            external_metrics = {}
            if include_external:
                try:
                    # OpenAI 메트릭
                    openai_metrics = await openai_usage_api.get_realtime_metrics(
                        api_key=self.openai_api_key,
                        minutes=days * 24 * 60
                    )
                    external_metrics["openai"] = openai_metrics
                    
                    # Anthropic 메트릭  
                    anthropic_metrics = await anthropic_usage_api.get_realtime_metrics(
                        admin_api_key=self.anthropic_admin_key,
                        hours=days * 24
                    )
                    external_metrics["anthropic"] = anthropic_metrics
                    
                    # Anthropic 모델별 분석
                    model_breakdown = await anthropic_usage_api.get_model_usage_breakdown(
                        admin_api_key=self.anthropic_admin_key,
                        days=days
                    )
                    external_metrics["anthropic_models"] = model_breakdown
                    
                except Exception as e:
                    external_metrics["error"] = str(e)
            
            # 3. 내부 DB 통계
            from sqlalchemy import text
            internal_stats = db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_requests,
                        SUM(total_tokens) as total_tokens,
                        SUM(cost) as total_cost,
                        COUNT(DISTINCT api_key_id) as unique_api_keys,
                        COUNT(DISTINCT agent_id) as unique_agents,
                        COUNT(DISTINCT user_id) as unique_users
                    FROM ai_usage_logs
                    WHERE created_at >= :start_time
                """),
                {"start_time": start_time.isoformat()}
            ).fetchone()
            
            # 4. 제공사별 비교
            provider_comparison = db.execute(
                text("""
                    SELECT 
                        ak.provider,
                        COUNT(*) as requests,
                        SUM(ul.total_tokens) as tokens,
                        SUM(ul.cost) as cost,
                        AVG(ul.duration_seconds) as avg_duration
                    FROM ai_usage_logs ul
                    JOIN api_keys ak ON ul.api_key_id = ak.id
                    WHERE ul.created_at >= :start_time
                    GROUP BY ak.provider
                    ORDER BY cost DESC
                """),
                {"start_time": start_time.isoformat()}
            ).fetchall()
            
            # 5. 비용 분석 및 추천사항
            cost_analysis = self._analyze_cost_efficiency(provider_comparison, agent_summary)
            
            return {
                "success": True,
                "report_period": {
                    "days": days,
                    "start_date": start_time.date().isoformat(),
                    "end_date": end_time.date().isoformat()
                },
                "internal_statistics": {
                    "total_requests": internal_stats.total_requests or 0,
                    "total_tokens": internal_stats.total_tokens or 0,
                    "total_cost": float(internal_stats.total_cost or 0),
                    "unique_api_keys": internal_stats.unique_api_keys or 0,
                    "unique_agents": internal_stats.unique_agents or 0,
                    "unique_users": internal_stats.unique_users or 0
                },
                "agent_usage_summary": agent_summary,
                "provider_comparison": [
                    {
                        "provider": row.provider,
                        "requests": row.requests,
                        "tokens": row.tokens or 0,
                        "cost": float(row.cost or 0),
                        "avg_duration": float(row.avg_duration or 0)
                    } for row in provider_comparison
                ],
                "external_metrics": external_metrics,
                "cost_analysis": cost_analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"종합 보고서 생성 중 오류: {str(e)}"
            }
    
    async def _get_api_key_id(self, db: Session, api_key: str) -> Dict[str, Any]:
        """API 키로부터 키 ID 조회"""
        
        from sqlalchemy import text
        
        try:
            result = db.execute(
                text("SELECT id FROM api_keys WHERE api_key = :api_key AND is_active = 1"),
                {"api_key": api_key}
            ).fetchone()
            
            if result:
                return {
                    "success": True,
                    "api_key_id": result[0]
                }
            else:
                return {
                    "success": False,
                    "error": "API 키를 찾을 수 없습니다"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"API 키 조회 중 오류: {str(e)}"
            }
    
    def _analyze_cost_efficiency(
        self, 
        provider_data: List, 
        agent_data: Dict
    ) -> Dict[str, Any]:
        """비용 효율성 분석 및 추천사항"""
        
        analysis = {
            "cost_per_token": {},
            "cost_per_request": {},
            "recommendations": []
        }
        
        try:
            # 제공사별 비용 효율성
            for provider in provider_data:
                if provider.tokens > 0:
                    analysis["cost_per_token"][provider.provider] = provider.cost / provider.tokens
                if provider.requests > 0:
                    analysis["cost_per_request"][provider.provider] = provider.cost / provider.requests
            
            # 추천사항 생성
            if len(analysis["cost_per_token"]) > 1:
                cheapest_provider = min(analysis["cost_per_token"], key=analysis["cost_per_token"].get)
                most_expensive = max(analysis["cost_per_token"], key=analysis["cost_per_token"].get)
                
                if analysis["cost_per_token"][most_expensive] > analysis["cost_per_token"][cheapest_provider] * 1.5:
                    analysis["recommendations"].append({
                        "type": "cost_optimization",
                        "message": f"{cheapest_provider}가 {most_expensive}보다 토큰당 비용이 저렴합니다",
                        "priority": "medium"
                    })
            
            # 에이전트별 추천
            if "agent_stats" in agent_data:
                high_cost_agents = [
                    agent for agent in agent_data["agent_stats"]
                    if agent.get("total_cost", 0) > 10  # $10 이상
                ]
                
                if high_cost_agents:
                    analysis["recommendations"].append({
                        "type": "agent_optimization",
                        "message": f"{len(high_cost_agents)}개 에이전트의 비용이 높습니다. 모델 최적화를 고려하세요",
                        "priority": "high" if len(high_cost_agents) > 3 else "medium"
                    })
            
        except Exception as e:
            analysis["error"] = f"분석 중 오류: {str(e)}"
        
        return analysis
    
    async def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        
        health_status = {
            "unified_service": "healthy",
            "components": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 1. Enhanced Usage Tracker 상태
            health_status["components"]["enhanced_tracker"] = "healthy"
            
            # 2. OpenAI API 연결 테스트
            try:
                openai_test = await openai_usage_api.get_realtime_metrics(
                    api_key=self.openai_api_key,
                    minutes=1
                )
                health_status["components"]["openai_api"] = "healthy" if openai_test.get("success") else "degraded"
            except:
                health_status["components"]["openai_api"] = "unavailable"
            
            # 3. Anthropic API 연결 테스트  
            try:
                anthropic_test = await anthropic_usage_api.get_realtime_metrics(
                    admin_api_key=self.anthropic_admin_key,
                    hours=1
                )
                health_status["components"]["anthropic_api"] = "healthy" if anthropic_test.get("success") else "degraded"
            except:
                health_status["components"]["anthropic_api"] = "unavailable"
            
            # 4. Agent Usage Tracker 상태
            health_status["components"]["agent_tracker"] = "healthy"
            
            # 전체 상태 결정
            component_statuses = list(health_status["components"].values())
            if all(status == "healthy" for status in component_statuses):
                health_status["unified_service"] = "healthy"
            elif any(status == "unavailable" for status in component_statuses):
                health_status["unified_service"] = "degraded"
            else:
                health_status["unified_service"] = "partial"
            
        except Exception as e:
            health_status["unified_service"] = "error"
            health_status["error"] = str(e)
        
        return health_status

# 전역 인스턴스
unified_usage_service = UnifiedUsageService()