"""DARK POOL DETECTOR - 세력 탐지 에이전트
VCP·블록딜·공매도 + Minervini SEPA
스케줄: 실시간
"""
from app.agents.base import BaseAgent


class DarkPoolDetector(BaseAgent):
    def __init__(self):
        super().__init__(
            name="dark_pool_detector",
            description="세력 탐지 (VCP/블록딜/공매도)",
            schedule="*/15 9-16 * * 1-5",
        )

    async def analyze(self, **kwargs) -> dict:
        # TODO: 거래량 이상 탐지 → VCP 패턴 → Gemini 분석
        return {"agent": self.name, "status": "not_implemented"}

    async def get_prompt(self, **kwargs) -> str:
        return "변동성 수축 패턴(VCP)과 비정상 거래량을 탐지하고 Minervini SEPA 기준으로 평가하세요."
