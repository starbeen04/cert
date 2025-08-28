# AI 모델 호출 서비스
import os
import openai
import anthropic
import google.generativeai as genai
from typing import Dict, Any, Optional
from config.ai_config import ai_config

class AIService:
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.google_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """API 클라이언트 초기화"""
        if ai_config.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=ai_config.openai_api_key)
        
        if ai_config.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=ai_config.anthropic_api_key)
        
        if ai_config.google_api_key:
            genai.configure(api_key=ai_config.google_api_key)
            self.google_client = genai
    
    async def generate_response(self, model_name: str, system_prompt: str, user_prompt: str) -> str:
        """AI 모델을 사용해 응답 생성"""
        try:
            if model_name.startswith("gpt"):
                return await self._call_openai(model_name, system_prompt, user_prompt)
            elif model_name.startswith("claude"):
                return await self._call_anthropic(model_name, system_prompt, user_prompt)
            elif model_name.startswith("gemini"):
                return await self._call_google(model_name, system_prompt, user_prompt)
            else:
                raise ValueError(f"지원되지 않는 모델: {model_name}")
        except Exception as e:
            return f"AI 모델 호출 중 오류가 발생했습니다: {str(e)}"
    
    async def _call_openai(self, model_name: str, system_prompt: str, user_prompt: str) -> str:
        """OpenAI API 호출"""
        if not self.openai_client:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다")
        
        response = self.openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    async def _call_anthropic(self, model_name: str, system_prompt: str, user_prompt: str) -> str:
        """Anthropic Claude API 호출"""
        if not self.anthropic_client:
            raise ValueError("Anthropic API 키가 설정되지 않았습니다")
        
        response = self.anthropic_client.messages.create(
            model=model_name,
            max_tokens=1000,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return response.content[0].text
    
    async def _call_google(self, model_name: str, system_prompt: str, user_prompt: str) -> str:
        """Google Gemini API 호출"""
        if not self.google_client:
            raise ValueError("Google API 키가 설정되지 않았습니다")
        
        model = self.google_client.GenerativeModel(model_name)
        
        # 시스템 프롬프트와 사용자 프롬프트 결합
        full_prompt = f"시스템 지시사항: {system_prompt}\n\n사용자 질문: {user_prompt}"
        
        response = model.generate_content(full_prompt)
        
        return response.text

# 글로벌 서비스 인스턴스
ai_service = AIService()