"""QUANT ENGINE - 기술적 분석 에이전트
RSI/MACD/BB/VCP + Livermore 피벗 + Weinstein Stage
스케줄: 장중 30분 간격
"""
import json
import logging
from datetime import datetime

from app.agents.base import BaseAgent
from app.services import kis_service, us_market_service, gemini_service, supabase_service
from app.utils.technical import calc_all_technicals
from app.utils.scoring import calc_technical_score

logger = logging.getLogger(__name__)


class QuantEngine(BaseAgent):
    def __init__(self):
        super().__init__(
            name="quant_engine",
            description="기술적 분석 (RSI/MACD/BB/VCP/Stage)",
            schedule="*/30 9-16 * * 1-5",
        )

    async def analyze(self, **kwargs) -> dict:
        """주가 데이터 → 기술적 지표 계산 → Gemini 해석"""
        ticker = kwargs.get("ticker", "")
        market = kwargs.get("market", "KR")

        # 1. 주가 데이터 수집
        if market == "KR":
            prices = await kis_service.get_daily_prices(ticker, days=200)
        else:
            prices = await us_market_service.get_stock_history(ticker, period="1y")

        if not prices:
            return {"agent": self.name, "ticker": ticker, "error": "데이터 없음"}

        closes = [p["close"] for p in prices]
        volumes = [p["volume"] for p in prices]

        # 최신순 → 과거순 정렬 (지표 계산용)
        if prices[0]["date"] > prices[-1]["date"]:
            closes = closes[::-1]
            volumes = volumes[::-1]

        # 2. 기술적 지표 계산
        technicals = calc_all_technicals(closes, volumes)
        tech_score = calc_technical_score(technicals)

        # 3. Gemini에 해석 요청
        prompt = await self.get_prompt(
            ticker=ticker, technicals=technicals, tech_score=tech_score
        )
        system = (
            "당신은 Jesse Livermore, Stan Weinstein, Mark Minervini의 "
            "투자 철학을 통합한 기술적 분석가입니다.\n"
            "- Livermore: 피벗 포인트, 거래량 동반 브레이크아웃, 추세 추종\n"
            "- Weinstein: 30주 MA 기준 Stage 1~4 분석\n"
            "- Minervini: VCP 패턴, SEPA 기준, 리스크 대비 보상 3:1 이상"
        )

        result = await gemini_service.ask_gemini_json(
            prompt=prompt, system_instruction=system
        )
        result["technicals"] = technicals
        result["tech_score"] = tech_score

        # 4. DB 저장
        await supabase_service.save_agent_report(
            agent_name=self.name, ticker=ticker, report=result, score=tech_score
        )
        await supabase_service.save_daily_analysis({
            "ticker": ticker,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "rsi": technicals.get("rsi"),
            "macd": technicals.get("macd", {}).get("macd") if technicals.get("macd") else None,
            "macd_signal": technicals.get("macd", {}).get("signal") if technicals.get("macd") else None,
            "bollinger_upper": technicals.get("bollinger", {}).get("upper") if technicals.get("bollinger") else None,
            "bollinger_lower": technicals.get("bollinger", {}).get("lower") if technicals.get("bollinger") else None,
            "stage": technicals.get("weinstein_stage", {}).get("stage"),
            "vcp_detected": technicals.get("vcp", {}).get("detected", False),
            "volume_ratio": None,
            "score": tech_score,
        })

        self.last_run = datetime.now()
        return result

    async def get_prompt(self, **kwargs) -> str:
        ticker = kwargs.get("ticker", "")
        technicals = kwargs.get("technicals", {})
        tech_score = kwargs.get("tech_score", 50)

        return f"""종목 '{ticker}'의 기술적 지표를 해석하세요.

## 계산된 기술적 지표
{json.dumps(technicals, indent=2, default=str)}

## 기술적 점수: {tech_score}/100

## 분석 요청
다음 JSON 형식으로 응답하세요:
{{
  "trend": "상승" | "횡보" | "하락",
  "stage": 1~4,
  "stage_description": "Stage 해석",
  "breakout_signal": true/false,
  "vcp_assessment": "VCP 패턴 평가",
  "support_levels": [지지선1, 지지선2],
  "resistance_levels": [저항선1, 저항선2],
  "pivot_point": 피벗포인트,
  "risk_reward_ratio": 리스크보상비율,
  "livermore_view": "Livermore 관점 한줄",
  "weinstein_view": "Weinstein 관점 한줄",
  "minervini_view": "Minervini 관점 한줄",
  "action": "매수" | "보유" | "관망" | "매도 준비" | "매도",
  "summary": "3줄 종합 기술적 분석"
}}"""
