"""
실제 Anthropic Console / OpenAI Dashboard 사용량 데이터 가져오기 서비스
- Anthropic Console CSV 파일 파싱
- OpenAI Dashboard 데이터 가져오기  
- 실제 빌링 데이터와 시스템 동기화
"""
import csv
import json
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import httpx
import asyncio

class RealUsageImporter:
    """실제 외부 사용량 데이터 가져오기 및 동기화"""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '../cert_fast.db')
    
    async def import_anthropic_console_csv(self, csv_file_path: str) -> Dict[str, Any]:
        """Anthropic Console에서 다운로드한 CSV 파일 파싱"""
        
        try:
            imported_data = []
            
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # CSV 헤더 확인
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    # Anthropic Console CSV 형식 파싱
                    usage_data = {
                        'timestamp': self._parse_timestamp(row.get('Date', row.get('Timestamp', ''))),
                        'model': row.get('Model', 'claude-3-haiku'),
                        'input_tokens': int(row.get('Input Tokens', row.get('input_tokens', 0))),
                        'output_tokens': int(row.get('Output Tokens', row.get('output_tokens', 0))),
                        'total_tokens': int(row.get('Total Tokens', row.get('total_tokens', 0))),
                        'cost_usd': float(row.get('Cost (USD)', row.get('cost', 0))),
                        'api_key_id': row.get('API Key', 'console_data'),
                        'source': 'anthropic_console'
                    }
                    imported_data.append(usage_data)
            
            # 데이터베이스에 저장
            saved_count = await self._save_real_usage_data(imported_data)
            
            return {
                "success": True,
                "imported_records": len(imported_data),
                "saved_records": saved_count,
                "data_source": "anthropic_console_csv",
                "file_path": csv_file_path
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data_source": "anthropic_console_csv"
            }
    
    async def import_openai_dashboard_csv(self, csv_file_path: str) -> Dict[str, Any]:
        """OpenAI Dashboard에서 다운로드한 CSV 파일 파싱"""
        
        try:
            imported_data = []
            
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    # OpenAI Dashboard CSV 형식 파싱
                    usage_data = {
                        'timestamp': self._parse_timestamp(row.get('Date', row.get('date', ''))),
                        'model': row.get('Model', row.get('model_name', 'gpt-3.5-turbo')),
                        'input_tokens': int(row.get('Prompt Tokens', row.get('n_prompt_tokens', 0))),
                        'output_tokens': int(row.get('Completion Tokens', row.get('n_completion_tokens', 0))),
                        'total_tokens': int(row.get('Total Tokens', row.get('n_tokens', 0))),
                        'cost_usd': float(row.get('Cost', row.get('cost_usd', 0))),
                        'api_key_id': row.get('API Key', row.get('api_key_id', 'dashboard_data')),
                        'source': 'openai_dashboard'
                    }
                    imported_data.append(usage_data)
            
            # 데이터베이스에 저장
            saved_count = await self._save_real_usage_data(imported_data)
            
            return {
                "success": True,
                "imported_records": len(imported_data),
                "saved_records": saved_count,
                "data_source": "openai_dashboard_csv",
                "file_path": csv_file_path
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data_source": "openai_dashboard_csv"
            }
    
    async def try_anthropic_admin_api(self, admin_api_key: str) -> Dict[str, Any]:
        """Anthropic Admin API를 사용해서 실제 사용량 데이터 가져오기"""
        
        if not admin_api_key.startswith('sk-ant-admin'):
            return {
                "success": False,
                "error": "Admin API 키가 필요합니다 (sk-ant-admin...)",
                "data_source": "anthropic_admin_api"
            }
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': admin_api_key,
                'anthropic-version': '2023-06-01'
            }
            
            # 최근 7일 데이터
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            params = {
                'starting_at': start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'ending_at': end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'bucket_width': '1h'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://api.anthropic.com/v1/organizations/usage_report/messages',
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Admin API 응답 데이터 파싱
                    imported_data = []
                    for usage_record in data.get('usage_data', []):
                        usage_data = {
                            'timestamp': usage_record.get('timestamp'),
                            'model': usage_record.get('model'),
                            'input_tokens': usage_record.get('input_tokens', 0),
                            'output_tokens': usage_record.get('output_tokens', 0), 
                            'total_tokens': usage_record.get('total_tokens', 0),
                            'cost_usd': usage_record.get('cost_usd', 0),
                            'api_key_id': usage_record.get('api_key_id', 'admin_api_data'),
                            'source': 'anthropic_admin_api'
                        }
                        imported_data.append(usage_data)
                    
                    saved_count = await self._save_real_usage_data(imported_data)
                    
                    return {
                        "success": True,
                        "imported_records": len(imported_data),
                        "saved_records": saved_count,
                        "data_source": "anthropic_admin_api"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "data_source": "anthropic_admin_api"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data_source": "anthropic_admin_api"
            }
    
    async def try_openai_usage_api(self, api_key: str, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """OpenAI Usage API를 사용해서 실제 사용량 데이터 가져오기"""
        
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            if organization_id:
                headers['OpenAI-Organization'] = organization_id
            
            # 최근 7일 데이터
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            params = {
                'start_time': start_date.strftime('%Y-%m-%d'),
                'end_time': end_date.strftime('%Y-%m-%d'),
                'bucket_width': 'day'
            }
            
            # 2025년 최신 Usage API 엔드포인트
            usage_endpoints = [
                'https://api.openai.com/v1/usage',
                'https://api.openai.com/v1/usage/completions'
            ]
            
            async with httpx.AsyncClient() as client:
                for endpoint in usage_endpoints:
                    try:
                        response = await client.get(endpoint, headers=headers, params=params, timeout=30.0)
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # OpenAI Usage API 응답 파싱
                            imported_data = []
                            usage_data_list = data.get('data', data.get('usage_data', []))
                            
                            for usage_record in usage_data_list:
                                usage_data = {
                                    'timestamp': usage_record.get('timestamp', usage_record.get('date')),
                                    'model': usage_record.get('model', usage_record.get('model_name')),
                                    'input_tokens': usage_record.get('prompt_tokens', usage_record.get('input_tokens', 0)),
                                    'output_tokens': usage_record.get('completion_tokens', usage_record.get('output_tokens', 0)),
                                    'total_tokens': usage_record.get('total_tokens', 0),
                                    'cost_usd': usage_record.get('cost', usage_record.get('cost_usd', 0)),
                                    'api_key_id': api_key[-8:],  # 마지막 8자리만
                                    'source': 'openai_usage_api'
                                }
                                imported_data.append(usage_data)
                            
                            saved_count = await self._save_real_usage_data(imported_data)
                            
                            return {
                                "success": True,
                                "imported_records": len(imported_data),
                                "saved_records": saved_count,
                                "data_source": "openai_usage_api",
                                "endpoint": endpoint
                            }
                    except Exception as endpoint_error:
                        print(f"Endpoint {endpoint} failed: {endpoint_error}")
                        continue
                
                return {
                    "success": False,
                    "error": "All OpenAI Usage API endpoints failed",
                    "data_source": "openai_usage_api"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data_source": "openai_usage_api"
            }
    
    async def _save_real_usage_data(self, usage_data_list: List[Dict[str, Any]]) -> int:
        """실제 사용량 데이터를 데이터베이스에 저장"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 실제 사용량 로그 테이블 생성 (존재하지 않는 경우)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS real_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    cost_usd REAL DEFAULT 0.0,
                    api_key_id TEXT,
                    source TEXT NOT NULL,
                    imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(timestamp, model, api_key_id, source)
                )
            """)
            
            saved_count = 0
            for usage_data in usage_data_list:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO real_usage_logs 
                        (timestamp, model, input_tokens, output_tokens, total_tokens, 
                         cost_usd, api_key_id, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        usage_data['timestamp'],
                        usage_data['model'],
                        usage_data['input_tokens'],
                        usage_data['output_tokens'],
                        usage_data['total_tokens'],
                        usage_data['cost_usd'],
                        usage_data['api_key_id'],
                        usage_data['source']
                    ))
                    saved_count += 1
                except Exception as e:
                    print(f"Failed to save usage record: {e}")
            
            conn.commit()
            return saved_count
            
        finally:
            conn.close()
    
    def _parse_timestamp(self, timestamp_str: str) -> str:
        """다양한 형식의 타임스탬프를 표준화"""
        
        if not timestamp_str:
            return datetime.now().isoformat()
        
        # 다양한 날짜 형식 처리
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        # 파싱 실패시 현재 시간 반환
        return datetime.now().isoformat()
    
    async def get_real_usage_summary(self) -> Dict[str, Any]:
        """실제 사용량 데이터 요약 조회"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 최근 7일 실제 사용량
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            cursor.execute("""
                SELECT source, COUNT(*) as records, SUM(total_tokens) as tokens, SUM(cost_usd) as cost
                FROM real_usage_logs 
                WHERE timestamp >= ?
                GROUP BY source
            """, (week_ago,))
            
            source_summary = {}
            for row in cursor.fetchall():
                source_summary[row[0]] = {
                    "records": row[1],
                    "total_tokens": row[2] or 0,
                    "total_cost": row[3] or 0.0
                }
            
            # 전체 통계
            cursor.execute("""
                SELECT COUNT(*) as total_records, SUM(total_tokens) as total_tokens, SUM(cost_usd) as total_cost
                FROM real_usage_logs 
                WHERE timestamp >= ?
            """, (week_ago,))
            
            total_stats = cursor.fetchone()
            
            return {
                "success": True,
                "summary_period": "last_7_days",
                "by_source": source_summary,
                "totals": {
                    "records": total_stats[0] or 0,
                    "tokens": total_stats[1] or 0,
                    "cost_usd": total_stats[2] or 0.0
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            conn.close()

# 전역 인스턴스
real_usage_importer = RealUsageImporter()