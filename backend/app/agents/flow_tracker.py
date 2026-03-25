"""FLOW TRACKER - 수급 분석 에이전트
외인·기관·개인 동향
스케줄: 장중 1시간 간격
"""
import json
import logging
from datetime import datetime

from app.agents.base import BaseAgent
from app.services import kis_service, gemini_service, supabase_service
from app.utils.scoring import calc_flow_score

logger = logging.getLogger(__name__)


class FlowTracker(BaseAgent):
    def __init__(self):
        super().__init__(
            name="flow_tracker",
            description="수급 분석 (외인·기관·개인 동향)",
            schedule="0 10-15 * * 1-5",
        )

    async def analyze(self, **kwargs) -> dict:
        """KIS API 수급 데이터 → Gemini 분석"""
        ticker = kwargs.get("ticker", "")

        # 1. 투자자별 매매 동향 수집
        flow_data = await kis_service.get_investor_trends(ticker)

        if not flow_data:
            return {"agent": self.name, "ticker": ticker, "error": "데이터 없음"}

        # 2. 수급 점수 계산
        flow_score_val = calc_flow_score(flow_data)

        # 3. Gemini 분석
        prompt = await self.get_prompt(
            ticker=ticker, flow_data=flow_data, flow_score=flow_score_val
        )
        system = (
            "당신은 수급 전문 분석가입니다. "
            "JKP 투자 원칙에 따라 외인/기관 흐름을 추적하고, "
            "세력의 매집/분산 패턴을 판별하세요."
        )

        result = await gemini_service.ask_gemini_json(
            prompt=prompt, system_instruction=system
        )
        result["flow_data"] = flow_data
        result["flow_score"] = flow_score_val

        # 4. DB 저장
        await supabase_service.save_agent_report(
            agent_name=self.name, ticker=ticker, report=result, score=flow_score_val
        )

        self.last_run = datetime.now()
        return result

    async def get_prompt(self, **kwargs) -> str:
        ticker = kwargs.get("ticker", "")
        flow_data = kwargs.get("flow_data", {})
        flow_score = kwargs.get("flow_score", 50)

        return f"""종목 '{ticker}'의 수급을 분석하세요.

## 투자자별 매매 동향
{json.dumps(flow_data, indent=2, default=str)}

## 수급 점수: {flow_score}/100

## 분석 요청
다음 JSON 형식으로 응답하세요:
{{
  "foreign_trend": "순매수" | "순매도" | "중립",
  "institution_trend": "순매수" | "순매도" | "중립",
  "individual_trend": "순매수" | "순매도" | "중립",
  "foreign_consecutive_days": 외인연속매수일수,
  "accumulation_signal": true/false,
  "distribution_signal": true/false,
  "smart_money_action": "매집 중" | "분산 중" | "관망",
  "volume_analysis": "거래량 분석",
  "action": "매수" | "보유" | "관망" | "매도",
  "summary": "3줄 수급 분석"
}}"""
