"""
실제 OpenAI와 Anthropic API를 호출하는 서비스
"""
import openai
import anthropic
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import json
from .enhanced_usage_tracker import enhanced_usage_tracker

class RealAIService:
    """실제 AI API 호출 서비스"""
    
    def __init__(self):
        # API 클라이언트 초기화
        self.openai_client = None
        self.anthropic_client = None
        
        # 실제 API 키들
        self.openai_key = "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"
        self.anthropic_key = "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"
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """API 클라이언트 초기화"""
        try:
            # OpenAI 클라이언트 (유효성 확인 후)
            if self.openai_key and self.openai_key.startswith('sk-'):
                self.openai_client = openai.OpenAI(api_key=self.openai_key)
            
            # Anthropic 클라이언트
            if self.anthropic_key and self.anthropic_key.startswith('sk-ant'):
                self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)
                
        except Exception as e:
            print(f"API 클라이언트 초기화 오류: {e}")
    
    async def call_openai_chat(self, message: str, model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """실제 OpenAI Chat API 호출"""
        if not self.openai_client:
            return {
                "error": "OpenAI 클라이언트를 사용할 수 없습니다",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
        
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": message}
                ],
                max_tokens=150
            )
            
            return {
                "response": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"OpenAI API 호출 오류: {str(e)}",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
    
    async def call_anthropic_chat(self, message: str, model: str = "claude-3-haiku-20240307") -> Dict[str, Any]:
        """실제 Anthropic Claude API 호출 (향상된 사용량 추적)"""
        
        # 향상된 추적기를 사용한 호출
        messages = [{"role": "user", "content": message}]
        
        # 실제 Claude API 키 가져오기
        claude_api_key = "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"
        
        result = await enhanced_usage_tracker.track_anthropic_usage(
            api_key=claude_api_key,
            messages=messages, 
            model=model
        )
        
        # 성공한 경우 데이터베이스에 로깅
        if result.get("success"):
            await enhanced_usage_tracker.log_enhanced_usage(
                api_key=claude_api_key,
                endpoint="/ai/chat",
                usage_result=result
            )
        
        return result
    
    async def analyze_document(self, document_text: str, api_key: str) -> Dict[str, Any]:
        """문서 분석 (실제 API 호출)"""
        
        # API 키에 따라 적절한 서비스 선택
        if "openai" in api_key or "sk-proj" in api_key:
            prompt = f"다음 문서를 분석해주세요: {document_text[:500]}..."
            return await self.call_openai_chat(prompt, "gpt-3.5-turbo")
        
        elif "anthropic" in api_key or "sk-ant" in api_key:
            prompt = f"다음 문서를 간략히 분석하고 요약해주세요: {document_text[:500]}..."
            return await self.call_anthropic_chat(prompt, "claude-3-haiku-20240307")
        
        else:
            # 기본값으로 Claude 사용
            prompt = f"문서 분석: {document_text[:500]}..."
            return await self.call_anthropic_chat(prompt)
    
    async def complete_text(self, prompt: str, api_key: str) -> Dict[str, Any]:
        """텍스트 완성 (실제 API 호출)"""
        
        if "openai" in api_key or "sk-proj" in api_key:
            return await self.call_openai_chat(f"다음 텍스트를 완성해주세요: {prompt}", "gpt-3.5-turbo")
        
        elif "anthropic" in api_key or "sk-ant" in api_key:
            return await self.call_anthropic_chat(f"다음 텍스트를 자연스럽게 완성해주세요: {prompt}", "claude-3-haiku-20240307")
        
        else:
            return await self.call_anthropic_chat(f"텍스트 완성: {prompt}")
    
    async def generate_questions(self, topic: str, count: int, api_key: str) -> Dict[str, Any]:
        """문제 생성 (실제 API 호출)"""
        
        prompt = f"{topic} 주제로 {count}개의 객관식 문제를 생성해주세요. 각 문제는 4개의 선택지와 정답을 포함해주세요."
        
        if "openai" in api_key or "sk-proj" in api_key:
            return await self.call_openai_chat(prompt, "gpt-4")  # 문제 생성은 GPT-4 사용
        
        elif "anthropic" in api_key or "sk-ant" in api_key:
            return await self.call_anthropic_chat(prompt, "claude-3-sonnet-20241022")  # 문제 생성은 Sonnet 사용
        
        else:
            return await self.call_anthropic_chat(prompt, "claude-3-sonnet-20241022")
    
    def get_available_models(self) -> Dict[str, list]:
        """사용 가능한 모델 목록"""
        return {
            "openai": [
                "gpt-3.5-turbo",
                "gpt-4",
                "gpt-4-turbo"
            ],
            "anthropic": [
                "claude-3-haiku-20240307",
                "claude-3-sonnet-20241022", 
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229"
            ]
        }
    
    def is_api_available(self, provider: str) -> bool:
        """API 사용 가능 여부 확인"""
        if provider == "openai":
            return self.openai_client is not None
        elif provider == "anthropic":
            return self.anthropic_client is not None
        return False

# 전역 서비스 인스턴스
real_ai_service = RealAIService()