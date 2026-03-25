"""NEWS SCANNER - 뉴스 감성 분석 에이전트
매경/한경/WSJ/Bloomberg
스케줄: 07:00, 12:00, 16:00
"""
import json
import logging
from datetime import datetime

from app.agents.base import BaseAgent
from app.services import news_service, gemini_service, supabase_service

logger = logging.getLogger(__name__)


class NewsScanner(BaseAgent):
    def __init__(self):
        super().__init__(
            name="news_scanner",
            description="뉴스 감성 분석 (매경/한경/WSJ/Bloomberg)",
            schedule="0 7,12,16 * * *",
        )

    async def analyze(self, **kwargs) -> dict:
        """뉴스 수집 → Gemini 감성분석"""
        ticker = kwargs.get("ticker")

        # 1. 뉴스 수집
        articles = await news_service.fetch_all_news()

        if not articles:
            return {"agent": self.name, "error": "뉴스 수집 실패", "sentiment_score": 50}

        # 2. 뉴스 요약 + 감성분석
        prompt = await self.get_prompt(articles=articles, ticker=ticker)
        system = (
            "당신은 금융 뉴스 전문 분석가입니다. "
            "뉴스의 투자 심리 영향을 정량적으로 평가하세요. "
            "과대 해석을 피하고, 팩트 기반으로 분석하세요."
        )

        result = await gemini_service.ask_gemini_json(
            prompt=prompt,
            system_instruction=system,
        )

        # 3. DB 저장
        score = result.get("sentiment_score", 50)
        await supabase_service.save_agent_report(
            agent_name=self.name,
            ticker=ticker,
            report=result,
            score=score,
        )

        # 뉴스 DB 저장
        news_to_save = []
        for article in result.get("analyzed_articles", [])[:20]:
            news_to_save.append({
                "title": article.get("title", ""),
                "source": article.get("source", ""),
                "url": article.get("url", ""),
                "sentiment_score": article.get("sentiment", 0),
                "tickers": article.get("related_tickers", []),
                "summary": article.get("summary", ""),
            })
        if news_to_save:
            await supabase_service.save_news(news_to_save)

        self.last_run = datetime.now()
        return result

    async def get_prompt(self, **kwargs) -> str:
        articles = kwargs.get("articles", [])
        ticker = kwargs.get("ticker")

        articles_text = ""
        for i, a in enumerate(articles[:30], 1):
            articles_text += f"{i}. [{a.get('source', '')}] {a.get('title', '')}\n"
            if a.get("summary"):
                articles_text += f"   {a['summary'][:200]}\n"

        ticker_filter = f"\n특히 종목 '{ticker}'에 관련된 뉴스를 중점 분석하세요." if ticker else ""

        return f"""다음 최신 뉴스를 분석하세요.{ticker_filter}

## 뉴스 목록
{articles_text}

## 분석 요청
다음 JSON 형식으로 응답하세요:
{{
  "sentiment_score": 0~100 (50=중립, 높을수록 긍정),
  "market_mood": "공포" | "불안" | "중립" | "낙관" | "과열",
  "key_themes": ["테마1", "테마2", "테마3"],
  "positive_news": ["긍정 뉴스 요약1", "요약2"],
  "negative_news": ["부정 뉴스 요약1", "요약2"],
  "analyzed_articles": [
    {{
      "title": "기사 제목",
      "source": "출처",
      "sentiment": -100~100,
      "related_tickers": ["005930", "AAPL"],
      "summary": "한줄 요약"
    }}
  ],
  "summary": "3줄 시장 뉴스 요약"
}}"""
