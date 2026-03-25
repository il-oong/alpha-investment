"""AI 에이전트 베이스 클래스"""
from abc import ABC, abstractmethod
from datetime import datetime


class BaseAgent(ABC):
    """모든 AI 에이전트의 공통 인터페이스"""

    def __init__(self, name: str, description: str, schedule: str):
        self.name = name
        self.description = description
        self.schedule = schedule  # cron 표현식 또는 간격
        self.last_run: datetime | None = None

    @abstractmethod
    async def analyze(self, **kwargs) -> dict:
        """분석 실행 후 결과 반환"""
        ...

    @abstractmethod
    async def get_prompt(self, **kwargs) -> str:
        """Gemini에 보낼 프롬프트 생성"""
        ...

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "schedule": self.schedule,
            "last_run": self.last_run.isoformat() if self.last_run else None,
        }
