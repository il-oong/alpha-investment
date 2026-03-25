"""US SENTINEL - 미국 시장 감시 에이전트
3대지수·VIX·섹터ETF
스케줄: 06:00 / 23:30
"""
from app.agents.base import BaseAgent


class USSentinel(BaseAgent):
    def __init__(self):
        super().__init__(
            name="us_sentinel",
            description="미국 시장 감시 (3대지수/VIX/섹터ETF)",
            schedule="0 6 * * *",
        )

    async def analyze(self, **kwargs) -> dict:
        # TODO: yfinance + Alpha Vantage → 미국 시장 분석
        return {"agent": self.name, "status": "not_implemented"}

    async def get_prompt(self, **kwargs) -> str:
        return "미국 3대지수, VIX, 섹터 ETF를 분석하고 한국 시장 영향을 예측하세요."
