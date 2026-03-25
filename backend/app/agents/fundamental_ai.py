"""FUNDAMENTAL AI - 펀더멘털 분석 에이전트
PER/PBR/PEG/ROE + CAN SLIM + Peter Lynch
스케줄: 주 1회 + 실적시즌
"""
from app.agents.base import BaseAgent


class FundamentalAI(BaseAgent):
    def __init__(self):
        super().__init__(
            name="fundamental_ai",
            description="펀더멘털 분석 (PER/PBR/PEG/CAN SLIM)",
            schedule="0 7 * * 1",
        )

    async def analyze(self, **kwargs) -> dict:
        # TODO: 재무 데이터 수집 → CAN SLIM 7항목 + PEG 분석
        return {"agent": self.name, "status": "not_implemented"}

    async def get_prompt(self, **kwargs) -> str:
        return "CAN SLIM 7항목과 PEG ratio를 분석하고 O'Neil/Lynch 관점에서 평가하세요."
