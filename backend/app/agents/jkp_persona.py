"""JKP PERSONA - 7개 에이전트 통합 판단
James K. Park 페르소나
최종 매수/매도 의견 산출 + 종합점수
"""
import json
import logging
from datetime import datetime

from app.agents.base import BaseAgent
from app.agents.macro_sentinel import MacroSentinel
from app.agents.news_scanner import NewsScanner
from app.agents.quant_engine import QuantEngine
from app.agents.fundamental_ai import FundamentalAI
from app.agents.flow_tracker import FlowTracker
from app.agents.dark_pool_detector import DarkPoolDetector
from app.agents.us_sentinel import USSentinel
from app.services import gemini_service, supabase_service
from app.utils.scoring import calc_composite_score

logger = logging.getLogger(__name__)


class JKPPersona(BaseAgent):
    def __init__(self):
        super().__init__(
            name="jkp_persona",
            description="7개 에이전트 통합 판단 (최종 매수/매도 의견)",
            schedule="on_demand",
        )
        self.agents = {
            "macro": MacroSentinel(),
            "news": NewsScanner(),
            "quant": QuantEngine(),
            "fundamental": FundamentalAI(),
            "flow": FlowTracker(),
            "dark_pool": DarkPoolDetector(),
            "us": USSentinel(),
        }

    async def analyze(self, **kwargs) -> dict:
        """7개 에이전트 결과 수집 → 통합 판단"""
        ticker = kwargs.get("ticker", "")
        market = kwargs.get("market", "KR")
        user_weights = kwargs.get("weights")

        # 1. 시장 전체 분석 (매크로 + 미국 + 뉴스)
        logger.info(f"[JKP] {ticker} 종합 분석 시작")

        macro_result = await self.agents["macro"].analyze()
        us_result = await self.agents["us"].analyze()
        news_result = await self.agents["news"].analyze(ticker=ticker)

        # 2. 종목별 분석 (기술적 + 펀더멘털 + 수급 + 세력)
        quant_result = await self.agents["quant"].analyze(ticker=ticker, market=market)
        fund_result = await self.agents["fundamental"].analyze(ticker=ticker, market=market)
        flow_result = await self.agents["flow"].analyze(ticker=ticker)
        dark_result = await self.agents["dark_pool"].analyze(ticker=ticker, market=market)

        # 3. 종합 점수 계산
        tech_score = quant_result.get("tech_score", 50)
        fund_score = fund_result.get("fund_score", 50)
        flow_score = flow_result.get("flow_score", 50)
        macro_score = macro_result.get("macro_score", 50)
        news_score = news_result.get("sentiment_score", 50)

        composite = calc_composite_score(
            tech_score, fund_score, flow_score, macro_score, news_score,
            weights=user_weights,
        )

        # 4. JKP 최종 판단 (Gemini)
        prompt = await self.get_prompt(
            ticker=ticker,
            macro=macro_result,
            us=us_result,
            news=news_result,
            quant=quant_result,
            fund=fund_result,
            flow=flow_result,
            dark=dark_result,
            composite=composite,
        )

        jkp_system = """당신은 JKP(James K. Park)입니다.
전 Bridgewater Associates 시니어 펀드매니저, 20년 경력.

투자 5원칙:
1. 매크로 우선 — 거시경제가 먼저다. 매크로가 나쁘면 개별종목이 아무리 좋아도 보수적으로.
2. 수급 중시 — 외인/기관 흐름이 개인 판단보다 우선.
3. 규율 — 손절선은 반드시 지킨다. 예외 없음.
4. 단순함 — 복잡한 전략을 지양하고 명확한 근거만 제시.
5. 리스크 퍼스트 — 수익보다 방어. "얼마 벌 수 있나"보다 "얼마 잃을 수 있나"를 먼저.

전설 트레이더 5인의 철학을 통합 적용:
- Livermore: 피벗 포인트, 추세 추종
- O'Neil: CAN SLIM
- Weinstein: Stage 분석
- Minervini: VCP, SEPA
- Lynch: PEG, 미발굴 성장주"""

        result = await gemini_service.ask_gemini_json(
            prompt=prompt, system_instruction=jkp_system, temperature=0.4
        )

        result["composite_score"] = composite
        result["agent_scores"] = {
            "technical": tech_score,
            "fundamental": fund_score,
            "flow": flow_score,
            "macro": macro_score,
            "news": news_score,
        }

        # 5. DB 저장
        await supabase_service.save_agent_report(
            agent_name=self.name, ticker=ticker, report=result, score=composite
        )

        self.last_run = datetime.now()
        logger.info(f"[JKP] {ticker} 분석 완료: {composite}점")
        return result

    async def get_prompt(self, **kwargs) -> str:
        ticker = kwargs.get("ticker", "")
        composite = kwargs.get("composite", 50)

        summaries = {}
        for key in ["macro", "us", "news", "quant", "fund", "flow", "dark"]:
            agent_result = kwargs.get(key, {})
            summaries[key] = agent_result.get("summary", "분석 없음")

        scores = {
            "technical": kwargs.get("quant", {}).get("tech_score", 50),
            "fundamental": kwargs.get("fund", {}).get("fund_score", 50),
            "flow": kwargs.get("flow", {}).get("flow_score", 50),
            "macro": kwargs.get("macro", {}).get("macro_score", 50),
            "news": kwargs.get("news", {}).get("sentiment_score", 50),
        }

        return f"""종목 '{ticker}'에 대한 최종 투자 판단을 내리세요.

## 종합 점수: {composite}/100

## 에이전트별 점수
{json.dumps(scores, indent=2)}

## 7개 에이전트 분석 요약
- 매크로: {summaries['macro']}
- 미국시장: {summaries['us']}
- 뉴스: {summaries['news']}
- 기술적: {summaries['quant']}
- 펀더멘털: {summaries['fund']}
- 수급: {summaries['flow']}
- 세력탐지: {summaries['dark']}

## JKP 최종 판단 요청
다음 JSON 형식으로 응답하세요:
{{
  "final_action": "강력매수" | "매수" | "보유" | "관망" | "매도 준비" | "매도" | "강력매도",
  "confidence": 0~100,
  "buy_zone": {{"entry_price": 매수진입가, "additional_buy": 추가매수가격}},
  "target_price": {{"target_1": 1차목표가, "target_2": 2차목표가}},
  "stop_loss": 손절가,
  "risk_reward_ratio": 리스크보상비율,
  "position_size": "종목 비중 추천 (%)",
  "time_horizon": "단기(1~2주)" | "중기(1~3개월)" | "장기(6개월+)",
  "key_catalysts": ["상승 촉매1", "촉매2"],
  "key_risks": ["핵심 리스크1", "리스크2"],
  "monitoring_points": ["모니터링 포인트1", "포인트2"],
  "jkp_comment": "JKP의 한마디 (2~3문장, 투자 원칙 기반)"
}}"""
