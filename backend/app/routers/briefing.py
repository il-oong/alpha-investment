"""매일 자동 브리핑 API"""
from fastapi import APIRouter

from app.agents.macro_sentinel import MacroSentinel
from app.agents.news_scanner import NewsScanner
from app.agents.us_sentinel import USSentinel
from app.services import telegram_service, gemini_service

router = APIRouter()
macro = MacroSentinel()
news = NewsScanner()
us = USSentinel()


@router.get("/morning")
async def morning_briefing():
    """07:00 JKP 오전 전략 브리핑"""
    macro_result = await macro.analyze()
    news_result = await news.analyze()

    summary = await gemini_service.ask_gemini(
        prompt=f"매크로: {macro_result.get('summary','')}\n뉴스: {news_result.get('summary','')}",
        system_instruction="JKP 오전 전략 브리핑을 5줄 이내로 작성하세요. 핵심만 간결하게.",
    )

    await telegram_service.send_daily_briefing("morning", summary)
    return {"briefing": summary, "macro": macro_result, "news": news_result}


@router.get("/us-close")
async def us_close_briefing():
    """06:00 미장 마감 브리핑"""
    us_result = await us.analyze()
    summary = us_result.get("summary", "")
    await telegram_service.send_daily_briefing("us_close", summary)
    return {"briefing": summary, "us_market": us_result}


@router.get("/noon")
async def noon_briefing():
    """12:00 점심 뉴스 브리핑"""
    news_result = await news.analyze()
    summary = news_result.get("summary", "")
    await telegram_service.send_daily_briefing("noon", summary)
    return {"briefing": summary, "news": news_result}


@router.get("/market-close")
async def market_close_briefing():
    """15:30 장마감 수급 정리"""
    # 장마감 시 포트폴리오 전체 수급 분석
    from app.agents.flow_tracker import FlowTracker
    flow = FlowTracker()

    summary = await gemini_service.ask_gemini(
        prompt="장마감 수급을 정리해주세요.",
        system_instruction="장마감 수급 브리핑을 5줄로 작성하세요.",
    )
    await telegram_service.send_daily_briefing("market_close", summary)
    return {"briefing": summary}


@router.get("/us-open")
async def us_open_briefing():
    """23:30 미장 시작 감시"""
    us_result = await us.analyze()
    summary = us_result.get("summary", "")
    await telegram_service.send_daily_briefing("us_open", summary)
    return {"briefing": summary, "us_market": us_result}
