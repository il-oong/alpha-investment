"""FUNDAMENTAL AI - 펀더멘털 분석 에이전트
PER/PBR/PEG/ROE + CAN SLIM + Peter Lynch
스케줄: 주 1회 + 실적시즌
"""
import json
import logging
from datetime import datetime

from app.agents.base import BaseAgent
from app.services import kis_service, us_market_service, gemini_service, supabase_service
from app.utils.scoring import calc_fundamental_score

logger = logging.getLogger(__name__)


class FundamentalAI(BaseAgent):
    def __init__(self):
        super().__init__(
            name="fundamental_ai",
            description="펀더멘털 분석 (PER/PBR/PEG/CAN SLIM)",
            schedule="0 7 * * 1",
        )

    async def analyze(self, **kwargs) -> dict:
        """재무 데이터 수집 → CAN SLIM + PEG 분석"""
        ticker = kwargs.get("ticker", "")
        market = kwargs.get("market", "KR")

        # 1. 펀더멘털 데이터 수집
        if market == "KR":
            fundamentals = await kis_service.get_stock_info(ticker)
        else:
            fundamentals = await us_market_service.get_stock_fundamentals(ticker)

        if not fundamentals or fundamentals.get("error"):
            return {"agent": self.name, "ticker": ticker, "error": "데이터 없음"}

        # 2. 펀더멘털 점수 계산
        fund_score = calc_fundamental_score(fundamentals)

        # 3. Gemini에 CAN SLIM + Lynch 분석 요청
        prompt = await self.get_prompt(
            ticker=ticker, fundamentals=fundamentals, fund_score=fund_score
        )
        system = (
            "당신은 William O'Neil(CAN SLIM)과 Peter Lynch(PEG ratio)의 "
            "투자 철학을 통합한 펀더멘털 분석가입니다.\n"
            "- O'Neil: CAN SLIM 7항목 (C/A/N/S/L/I/M)\n"
            "- Lynch: PEG < 1.0 우선, 이해하는 사업에 투자, 기관 미발굴 종목"
        )

        result = await gemini_service.ask_gemini_json(
            prompt=prompt, system_instruction=system
        )
        result["fundamentals"] = fundamentals
        result["fund_score"] = fund_score

        # 4. DB 저장
        await supabase_service.save_agent_report(
            agent_name=self.name, ticker=ticker, report=result, score=fund_score
        )

        self.last_run = datetime.now()
        return result

    async def get_prompt(self, **kwargs) -> str:
        ticker = kwargs.get("ticker", "")
        fundamentals = kwargs.get("fundamentals", {})
        fund_score = kwargs.get("fund_score", 50)

        return f"""종목 '{ticker}'의 펀더멘털을 분석하세요.

## 재무 데이터
{json.dumps(fundamentals, indent=2, default=str)}

## 펀더멘털 점수: {fund_score}/100

## 분석 요청
CAN SLIM 7항목과 PEG ratio를 기반으로 분석하세요.
다음 JSON 형식으로 응답하세요:
{{
  "canslim": {{
    "C_current_eps": {{"score": 0~10, "comment": "분기 EPS 성장률"}},
    "A_annual_eps": {{"score": 0~10, "comment": "연간 EPS 성장률"}},
    "N_new": {{"score": 0~10, "comment": "신제품/신고가/신경영"}},
    "S_supply_demand": {{"score": 0~10, "comment": "공급수요"}},
    "L_leader": {{"score": 0~10, "comment": "업종 리더 여부"}},
    "I_institutional": {{"score": 0~10, "comment": "기관 보유"}},
    "M_market": {{"score": 0~10, "comment": "시장 방향성"}}
  }},
  "canslim_total": 0~70,
  "peg_ratio": PEG값,
  "peg_assessment": "저평가" | "적정" | "고평가",
  "lynch_category": "slow_grower" | "stalwart" | "fast_grower" | "cyclical" | "turnaround" | "asset_play",
  "moat": "경제적 해자 평가",
  "value_assessment": "저평가" | "적정가" | "고평가",
  "fair_value_estimate": 적정가추정,
  "action": "매수" | "보유" | "관망" | "매도",
  "summary": "3줄 펀더멘털 분석"
}}"""
