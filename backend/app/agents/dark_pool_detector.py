"""DARK POOL DETECTOR - 세력 탐지 에이전트
VCP·블록딜·공매도 + Minervini SEPA
스케줄: 실시간 (15분 간격)
"""
import json
import logging
from datetime import datetime

from app.agents.base import BaseAgent
from app.services import kis_service, gemini_service, supabase_service
from app.utils.technical import detect_vcp

logger = logging.getLogger(__name__)


class DarkPoolDetector(BaseAgent):
    def __init__(self):
        super().__init__(
            name="dark_pool_detector",
            description="세력 탐지 (VCP/블록딜/공매도)",
            schedule="*/15 9-16 * * 1-5",
        )

    async def analyze(self, **kwargs) -> dict:
        """거래량 이상 탐지 → VCP 패턴 → Gemini 분석"""
        ticker = kwargs.get("ticker", "")
        market = kwargs.get("market", "KR")

        # 1. 일별 시세 수집
        if market == "KR":
            prices = await kis_service.get_daily_prices(ticker, days=100)
        else:
            from app.services import us_market_service
            prices = await us_market_service.get_stock_history(ticker, period="6mo")

        if not prices:
            return {"agent": self.name, "ticker": ticker, "error": "데이터 없음"}

        closes = [p["close"] for p in prices]
        volumes = [p["volume"] for p in prices]

        if prices[0]["date"] > prices[-1]["date"]:
            closes = closes[::-1]
            volumes = volumes[::-1]

        # 2. VCP 패턴 탐지
        vcp = detect_vcp(closes, volumes)

        # 3. 거래량 이상 탐지
        if len(volumes) >= 20:
            avg_vol_20 = sum(volumes[-20:]) / 20
            latest_vol = volumes[-1]
            vol_ratio = latest_vol / avg_vol_20 if avg_vol_20 > 0 else 1
        else:
            vol_ratio = 1

        # 4. Gemini 분석
        prompt = await self.get_prompt(
            ticker=ticker, vcp=vcp, vol_ratio=vol_ratio,
            closes=closes[-20:], volumes=volumes[-20:]
        )
        system = (
            "당신은 Mark Minervini의 SEPA/VCP 전략을 기반으로 "
            "세력 움직임을 탐지하는 전문가입니다.\n"
            "- VCP: 변동성 수축 패턴\n"
            "- 리스크 대비 보상 3:1 이상 요구\n"
            "- 손절선 명확히 설정"
        )

        result = await gemini_service.ask_gemini_json(
            prompt=prompt, system_instruction=system
        )
        result["vcp"] = vcp
        result["volume_ratio"] = round(vol_ratio, 2)

        # 5. DB 저장
        score = result.get("dark_pool_score", 50)
        await supabase_service.save_agent_report(
            agent_name=self.name, ticker=ticker, report=result, score=score
        )

        self.last_run = datetime.now()
        return result

    async def get_prompt(self, **kwargs) -> str:
        ticker = kwargs.get("ticker", "")
        vcp = kwargs.get("vcp", {})
        vol_ratio = kwargs.get("vol_ratio", 1)
        closes = kwargs.get("closes", [])
        volumes = kwargs.get("volumes", [])

        return f"""종목 '{ticker}'의 세력 움직임을 탐지하세요.

## VCP 분석 결과
{json.dumps(vcp, indent=2, default=str)}

## 거래량 비율 (최근/20일평균): {vol_ratio:.2f}x

## 최근 20일 종가: {closes}
## 최근 20일 거래량: {volumes}

## 분석 요청
다음 JSON 형식으로 응답하세요:
{{
  "dark_pool_score": 0~100,
  "vcp_status": "형성 중" | "완성" | "브레이크아웃" | "미감지",
  "sepa_criteria_met": true/false,
  "volume_anomaly": "정상" | "이상 급증" | "이상 급감",
  "block_deal_suspected": true/false,
  "short_selling_pressure": "낮음" | "보통" | "높음",
  "smart_money_detected": true/false,
  "entry_point": 매수진입가격,
  "stop_loss": 손절가,
  "risk_reward_ratio": 리스크보상비율,
  "action": "매수" | "관망" | "주의",
  "summary": "3줄 세력 분석"
}}"""
