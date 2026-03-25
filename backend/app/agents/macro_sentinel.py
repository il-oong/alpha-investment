"""MACRO SENTINEL - 글로벌 거시경제 분석 에이전트
FRED / DXY / 금리 / 유가
스케줄: 매일 06:30
"""
from app.agents.base import BaseAgent


class MacroSentinel(BaseAgent):
    def __init__(self):
        super().__init__(
            name="macro_sentinel",
            description="글로벌 거시경제 분석 (FRED/DXY/금리/유가)",
            schedule="30 6 * * *",
        )

    async def analyze(self, **kwargs) -> dict:
        # TODO: FRED API 데이터 수집 → Gemini 분석
        return {"agent": self.name, "status": "not_implemented"}

    async def get_prompt(self, **kwargs) -> str:
        return "글로벌 거시경제 데이터를 분석하고 투자 시사점을 도출하세요."
