"""NEWS SCANNER - 뉴스 감성 분석 에이전트
매경/한경/WSJ/Bloomberg
스케줄: 07:00, 12:00, 16:00
"""
from app.agents.base import BaseAgent


class NewsScanner(BaseAgent):
    def __init__(self):
        super().__init__(
            name="news_scanner",
            description="뉴스 감성 분석 (매경/한경/WSJ/Bloomberg)",
            schedule="0 7,12,16 * * *",
        )

    async def analyze(self, **kwargs) -> dict:
        # TODO: RSS 뉴스 수집 → Gemini 감성분석
        return {"agent": self.name, "status": "not_implemented"}

    async def get_prompt(self, **kwargs) -> str:
        return "다음 뉴스를 분석하고 투자 심리 점수(-100~100)를 산출하세요."
