"""US SENTINEL - 미국 시장 감시 에이전트
3대지수·VIX·섹터ETF
스케줄: 06:00 / 23:30
"""
import json
import logging
from datetime import datetime

from app.agents.base import BaseAgent
from app.services import us_market_service, gemini_service, supabase_service

logger = logging.getLogger(__name__)


class USSentinel(BaseAgent):
    def __init__(self):
        super().__init__(
            name="us_sentinel",
            description="미국 시장 감시 (3대지수/VIX/섹터ETF)",
            schedule="0 6 * * *",
        )

    async def analyze(self, **kwargs) -> dict:
        """미국 시장 데이터 수집 → Gemini 분석"""
        # 1. 미국 3대지수 + VIX
        indices = await us_market_service.get_us_indices()

        # 2. 섹터 ETF 수익률
        sectors = await us_market_service.get_sector_etf_performance()

        # 3. Gemini 분석
        prompt = await self.get_prompt(indices=indices, sectors=sectors)
        system = (
            "당신은 미국 시장 전문 분석가입니다. "
            "미국 시장의 움직임이 다음날 한국 시장에 미치는 영향을 분석하세요. "
            "VIX 수준, 섹터 로테이션, 지수 흐름을 종합 판단하세요."
        )

        result = await gemini_service.ask_gemini_json(
            prompt=prompt, system_instruction=system
        )

        # 4. DB 저장
        score = result.get("us_market_score", 50)
        await supabase_service.save_agent_report(
            agent_name=self.name, ticker=None, report=result, score=score
        )

        # 시장 스냅샷 업데이트
        snapshot_data = {"date": datetime.now().strftime("%Y-%m-%d")}
        if indices.get("sp500"):
            snapshot_data["sp500"] = indices["sp500"]["price"]
        if indices.get("nasdaq"):
            snapshot_data["nasdaq"] = indices["nasdaq"]["price"]
        if indices.get("dow"):
            snapshot_data["dow"] = indices["dow"]["price"]
        if indices.get("vix"):
            snapshot_data["vix"] = indices["vix"]["price"]
        await supabase_service.save_market_snapshot(snapshot_data)

        self.last_run = datetime.now()
        return result

    async def get_prompt(self, **kwargs) -> str:
        indices = kwargs.get("indices", {})
        sectors = kwargs.get("sectors", {})

        return f"""미국 시장 현황을 분석하세요.

## 3대지수 + VIX
{json.dumps(indices, indent=2, default=str)}

## 섹터 ETF 수익률
{json.dumps(sectors, indent=2, default=str)}

## 분석 요청
다음 JSON 형식으로 응답하세요:
{{
  "us_market_score": 0~100 (높을수록 강세),
  "market_regime": "bull" | "correction" | "bear" | "recovery",
  "vix_level": "안정" | "경계" | "공포",
  "vix_interpretation": "VIX 해석",
  "sector_rotation": "성장→가치" | "가치→성장" | "방어적" | "공격적" | "불명확",
  "leading_sectors": ["강세 섹터1", "섹터2"],
  "lagging_sectors": ["약세 섹터1", "섹터2"],
  "kr_market_impact": {{
    "direction": "긍정" | "중립" | "부정",
    "affected_sectors": ["영향 받을 한국 섹터"],
    "gap_prediction": "갭업" | "보합" | "갭다운"
  }},
  "summary": "3줄 미국 시장 분석"
}}"""
