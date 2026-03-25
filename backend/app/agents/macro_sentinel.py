"""MACRO SENTINEL - 글로벌 거시경제 분석 에이전트
FRED / DXY / 금리 / 유가
스케줄: 매일 06:30
"""
import json
import logging
from datetime import datetime

from app.agents.base import BaseAgent
from app.services import fred_service, gemini_service, supabase_service

logger = logging.getLogger(__name__)


class MacroSentinel(BaseAgent):
    def __init__(self):
        super().__init__(
            name="macro_sentinel",
            description="글로벌 거시경제 분석 (FRED/DXY/금리/유가)",
            schedule="30 6 * * *",
        )

    async def analyze(self, **kwargs) -> dict:
        """거시경제 데이터 수집 → Gemini 분석"""
        # 1. FRED 매크로 스냅샷 수집
        snapshot = await fred_service.get_macro_snapshot()

        # 2. Gemini에 분석 요청
        prompt = await self.get_prompt(snapshot=snapshot)
        system = (
            "당신은 글로벌 매크로 전략가입니다. "
            "JKP 투자 원칙에 따라 거시경제가 가장 중요합니다. "
            "데이터를 기반으로 현재 매크로 환경을 진단하고, "
            "한국·미국 주식시장에 미치는 영향을 분석하세요."
        )

        result = await gemini_service.ask_gemini_json(
            prompt=prompt,
            system_instruction=system,
            temperature=0.3,
        )

        # 3. DB 저장
        score = result.get("macro_score", 50)
        await supabase_service.save_agent_report(
            agent_name=self.name,
            ticker=None,
            report=result,
            score=score,
        )
        await supabase_service.save_market_snapshot({
            "date": datetime.now().strftime("%Y-%m-%d"),
            **{k: v.get("value") if isinstance(v, dict) else v
               for k, v in snapshot.items()
               if k in ("vix", "wti", "gold")},
        })

        self.last_run = datetime.now()
        return result

    async def get_prompt(self, **kwargs) -> str:
        snapshot = kwargs.get("snapshot", {})
        return f"""다음 거시경제 데이터를 분석하세요.

## 현재 매크로 데이터
{json.dumps(snapshot, indent=2, default=str)}

## 분석 요청
다음 JSON 형식으로 응답하세요:
{{
  "macro_score": 0~100 (높을수록 주식시장에 우호적),
  "environment": "risk_on" | "risk_off" | "neutral",
  "yield_curve_signal": "정상" | "플래트닝" | "역전",
  "inflation_trend": "상승" | "안정" | "하락",
  "fed_stance": "hawkish" | "neutral" | "dovish",
  "key_risks": ["리스크1", "리스크2"],
  "opportunities": ["기회1", "기회2"],
  "kr_market_impact": "긍정적" | "중립" | "부정적",
  "summary": "3줄 요약"
}}"""
