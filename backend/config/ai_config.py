# AI 서비스 API 키 및 설정 관리
import os
from typing import Dict, Optional
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

class AIConfig:
    def __init__(self):
        # 환경변수에서 API 키 로드
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
    def get_api_key(self, model_name: str) -> Optional[str]:
        """모델명에 따른 API 키 반환"""
        if model_name.startswith("gpt"):
            return self.openai_api_key
        elif model_name.startswith("claude"):
            return self.anthropic_api_key
        elif model_name.startswith("gemini"):
            return self.google_api_key
        return None
    
    def is_model_available(self, model_name: str) -> bool:
        """모델 사용 가능 여부 확인"""
        return self.get_api_key(model_name) is not None

# 글로벌 설정 인스턴스
ai_config = AIConfig()