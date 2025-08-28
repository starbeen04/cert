"""
API 키별 에이전트 편성 및 할당 서비스
- API 키 사용량 모니터링
- 에이전트별 작업 분배
- 로드 밸런싱 및 비용 최적화
"""
import sqlite3
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

class AgentAssignmentService:
    """API 키별 에이전트 할당 및 관리"""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '../cert_fast.db')
        self.agent_configs = {
            'document_analyzer': {
                'preferred_models': ['claude-3-haiku-20240307', 'gpt-3.5-turbo'],
                'max_tokens': 2000,
                'cost_per_token': {'anthropic': 0.00000025, 'openai': 0.0000005}
            },
            'quiz_master': {
                'preferred_models': ['claude-3-sonnet-20241022', 'gpt-4'],
                'max_tokens': 3000,
                'cost_per_token': {'anthropic': 0.000003, 'openai': 0.00003}
            },
            'study_tutor': {
                'preferred_models': ['claude-3-haiku-20240307', 'gpt-3.5-turbo'],
                'max_tokens': 2500,
                'cost_per_token': {'anthropic': 0.00000025, 'openai': 0.0000005}
            }
        }
    
    def get_optimal_agent_assignment(self, task_type: str, content_size: int = 1000) -> Dict[str, Any]:
        """작업에 최적화된 에이전트 및 API 키 할당"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 활성 API 키들의 현재 사용량 조회
            cursor.execute("""
                SELECT id, provider, key_name, current_daily_usage, daily_limit, 
                       current_monthly_usage, monthly_limit, api_key
                FROM api_keys 
                WHERE is_active = 1
                ORDER BY current_daily_usage / daily_limit ASC
            """)
            
            active_keys = cursor.fetchall()
            
            if not active_keys:
                return {
                    "success": False,
                    "error": "활성화된 API 키가 없습니다",
                    "fallback_agent": "local_agent"
                }
            
            # 작업 유형에 따른 최적 에이전트 선택
            best_assignment = self._calculate_optimal_assignment(active_keys, task_type, content_size)
            
            conn.close()
            
            return {
                "success": True,
                "assignment": best_assignment,
                "estimated_cost": best_assignment["estimated_cost"],
                "estimated_tokens": best_assignment["estimated_tokens"],
                "selected_api_key": best_assignment["api_key_info"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"에이전트 할당 오류: {str(e)}",
                "fallback_agent": "local_agent"
            }
    
    def _calculate_optimal_assignment(self, active_keys: List[tuple], task_type: str, content_size: int) -> Dict[str, Any]:
        """최적 에이전트 할당 계산"""
        
        # 작업 유형별 에이전트 매핑
        task_agent_map = {
            'pdf_analysis': 'document_analyzer',
            'question_extraction': 'quiz_master',
            'study_material_generation': 'study_tutor',
            'document_analysis': 'document_analyzer',
            'quiz_generation': 'quiz_master',
            'tutoring': 'study_tutor'
        }
        
        agent_type = task_agent_map.get(task_type, 'document_analyzer')
        agent_config = self.agent_configs[agent_type]
        
        # 각 API 키에 대한 비용 및 성능 계산
        assignments = []
        
        for key in active_keys:
            key_id, provider, key_name, daily_usage, daily_limit, monthly_usage, monthly_limit, api_key = key
            
            # 사용량 여유 계산
            daily_remaining = (daily_limit - daily_usage) / daily_limit if daily_limit > 0 else 1.0
            monthly_remaining = (monthly_limit - monthly_usage) / monthly_limit if monthly_limit > 0 else 1.0
            
            # 여유도 점수 (0~1)
            availability_score = min(daily_remaining, monthly_remaining)
            
            if availability_score <= 0.1:  # 90% 이상 사용한 키는 제외
                continue
            
            # 예상 토큰 수 계산
            estimated_tokens = self._estimate_tokens_needed(content_size, agent_type)
            
            # 비용 계산
            cost_per_token = agent_config['cost_per_token'].get(provider, 0.000001)
            estimated_cost = estimated_tokens * cost_per_token
            
            # 선호 모델 확인
            preferred_models = agent_config['preferred_models']
            model_preference_score = 1.0 if any(provider in model for model in preferred_models) else 0.7
            
            # 종합 점수 계산
            total_score = (availability_score * 0.4 + 
                          model_preference_score * 0.3 + 
                          (1.0 - estimated_cost / 0.01) * 0.3)  # 비용 효율성
            
            assignments.append({
                'api_key_id': key_id,
                'api_key_info': {
                    'id': key_id,
                    'provider': provider,
                    'name': key_name,
                    'api_key': api_key
                },
                'agent_type': agent_type,
                'estimated_tokens': estimated_tokens,
                'estimated_cost': estimated_cost,
                'availability_score': availability_score,
                'total_score': total_score,
                'recommended_model': self._get_recommended_model(provider, agent_type)
            })
        
        if not assignments:
            # 모든 키가 한도 초과인 경우 가장 여유로운 키 선택
            fallback_key = min(active_keys, key=lambda x: x[3] / x[4] if x[4] > 0 else float('inf'))
            return {
                'api_key_id': fallback_key[0],
                'api_key_info': {
                    'id': fallback_key[0],
                    'provider': fallback_key[1],
                    'name': fallback_key[2],
                    'api_key': fallback_key[7]
                },
                'agent_type': agent_type,
                'estimated_tokens': 1500,
                'estimated_cost': 0.005,
                'availability_score': 0.0,
                'total_score': 0.0,
                'recommended_model': self._get_recommended_model(fallback_key[1], agent_type),
                'warning': '모든 API 키가 한도에 근접했습니다'
            }
        
        # 최고 점수의 할당 선택
        best_assignment = max(assignments, key=lambda x: x['total_score'])
        return best_assignment
    
    def _estimate_tokens_needed(self, content_size: int, agent_type: str) -> int:
        """콘텐츠 크기와 에이전트 타입에 따른 필요 토큰 수 추정"""
        
        # 기본 토큰 추정 (문자 수의 약 1/4)
        base_tokens = content_size // 4
        
        # 에이전트별 승수 적용
        multipliers = {
            'document_analyzer': 1.2,  # 문서 분석은 입출력 비슷
            'quiz_master': 2.0,        # 문제 생성은 출력이 많음
            'study_tutor': 1.5         # 학습자료는 중간
        }
        
        multiplier = multipliers.get(agent_type, 1.0)
        estimated_tokens = int(base_tokens * multiplier)
        
        # 최소/최대 토큰 제한
        min_tokens = self.agent_configs[agent_type].get('min_tokens', 100)
        max_tokens = self.agent_configs[agent_type].get('max_tokens', 4000)
        
        return max(min_tokens, min(estimated_tokens, max_tokens))
    
    def _get_recommended_model(self, provider: str, agent_type: str) -> str:
        """제공사와 에이전트 타입에 따른 추천 모델"""
        
        model_map = {
            'anthropic': {
                'document_analyzer': 'claude-3-haiku-20240307',
                'quiz_master': 'claude-3-sonnet-20241022',
                'study_tutor': 'claude-3-haiku-20240307'
            },
            'openai': {
                'document_analyzer': 'gpt-3.5-turbo',
                'quiz_master': 'gpt-4',
                'study_tutor': 'gpt-3.5-turbo'
            }
        }
        
        return model_map.get(provider, {}).get(agent_type, 'gpt-3.5-turbo')
    
    async def log_agent_usage(self, assignment: Dict[str, Any], actual_tokens: int, actual_cost: float, 
                             task_result: str) -> bool:
        """에이전트 사용 후 실제 사용량 로깅"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 에이전트 사용 로그 저장
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_assignment_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key_id INTEGER NOT NULL,
                    agent_type TEXT NOT NULL,
                    estimated_tokens INTEGER,
                    actual_tokens INTEGER,
                    estimated_cost REAL,
                    actual_cost REAL,
                    task_result TEXT,
                    accuracy_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 정확도 점수 계산 (추정 vs 실제)
            token_accuracy = 1.0 - abs(assignment['estimated_tokens'] - actual_tokens) / assignment['estimated_tokens']
            cost_accuracy = 1.0 - abs(assignment['estimated_cost'] - actual_cost) / assignment['estimated_cost']
            accuracy_score = (token_accuracy + cost_accuracy) / 2.0
            
            cursor.execute("""
                INSERT INTO agent_assignment_logs 
                (api_key_id, agent_type, estimated_tokens, actual_tokens, 
                 estimated_cost, actual_cost, task_result, accuracy_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                assignment['api_key_id'],
                assignment['agent_type'],
                assignment['estimated_tokens'],
                actual_tokens,
                assignment['estimated_cost'],
                actual_cost,
                task_result[:500],  # 결과를 500자로 제한
                accuracy_score
            ))
            
            conn.commit()
            conn.close()
            
            print(f"[에이전트 할당 로그] API키: {assignment['api_key_id']}, "
                  f"에이전트: {assignment['agent_type']}, 정확도: {accuracy_score:.2f}")
            
            return True
            
        except Exception as e:
            print(f"[에이전트 할당 로그] 오류: {e}")
            return False
    
    def get_assignment_statistics(self) -> Dict[str, Any]:
        """에이전트 할당 통계"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 최근 7일 할당 통계
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            cursor.execute("""
                SELECT agent_type, COUNT(*) as assignments, 
                       AVG(actual_tokens) as avg_tokens,
                       AVG(actual_cost) as avg_cost,
                       AVG(accuracy_score) as avg_accuracy
                FROM agent_assignment_logs 
                WHERE created_at >= ?
                GROUP BY agent_type
            """, (week_ago,))
            
            agent_stats = {}
            for row in cursor.fetchall():
                agent_stats[row[0]] = {
                    'assignments': row[1],
                    'avg_tokens': round(row[2] or 0, 0),
                    'avg_cost': round(row[3] or 0, 6),
                    'avg_accuracy': round(row[4] or 0, 3)
                }
            
            # API 키별 사용량
            cursor.execute("""
                SELECT al.api_key_id, ak.key_name, ak.provider,
                       COUNT(*) as assignments,
                       SUM(al.actual_cost) as total_cost
                FROM agent_assignment_logs al
                JOIN api_keys ak ON al.api_key_id = ak.id
                WHERE al.created_at >= ?
                GROUP BY al.api_key_id, ak.key_name, ak.provider
            """, (week_ago,))
            
            api_key_stats = {}
            for row in cursor.fetchall():
                api_key_stats[f"{row[1]}_{row[0]}"] = {
                    'provider': row[2],
                    'assignments': row[3],
                    'total_cost': round(row[4] or 0, 6)
                }
            
            conn.close()
            
            return {
                'success': True,
                'period': 'last_7_days',
                'agent_statistics': agent_stats,
                'api_key_statistics': api_key_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# 전역 인스턴스
agent_assignment_service = AgentAssignmentService()