"""FLOW TRACKER - 수급 분석 에이전트
외인·기관·개인 동향
스케줄: 장중 1시간 간격
"""
from app.agents.base import BaseAgent


class FlowTracker(BaseAgent):
    def __init__(self):
        super().__init__(
            name="flow_tracker",
            description="수급 분석 (외인·기관·개인 동향)",
            schedule="0 10-15 * * 1-5",
        )

    async def analyze(self, **kwargs) -> dict:
        # TODO: KIS API 수급 데이터 → Gemini 분석
        return {"agent": self.name, "status": "not_implemented"}

    async def get_prompt(self, **kwargs) -> str:
        return "외인/기관/개인 매매 동향을 분석하고 수급 신호를 판단하세요."
