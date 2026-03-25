"""APScheduler 기반 자동 브리핑 스케줄러
매일 정해진 시간에 에이전트 실행 + 텔레그램 알림 발송
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_us_close_briefing():
    """06:00 미장 마감 브리핑"""
    from app.agents.us_sentinel import USSentinel
    from app.services import telegram_service
    logger.info("[스케줄] 미장 마감 브리핑 시작")
    us = USSentinel()
    result = await us.analyze()
    await telegram_service.send_daily_briefing("us_close", result.get("summary", ""))


async def run_morning_briefing():
    """07:00 JKP 오전 전략 브리핑"""
    from app.agents.macro_sentinel import MacroSentinel
    from app.agents.news_scanner import NewsScanner
    from app.services import telegram_service, gemini_service
    logger.info("[스케줄] 오전 브리핑 시작")
    macro = MacroSentinel()
    news = NewsScanner()
    macro_result = await macro.analyze()
    news_result = await news.analyze()
    summary = await gemini_service.ask_gemini(
        prompt=f"매크로: {macro_result.get('summary','')}\n뉴스: {news_result.get('summary','')}",
        system_instruction="JKP 오전 전략 브리핑을 5줄 이내로 작성하세요.",
    )
    await telegram_service.send_daily_briefing("morning", summary)


async def run_noon_briefing():
    """12:00 점심 뉴스 브리핑"""
    from app.agents.news_scanner import NewsScanner
    from app.services import telegram_service
    logger.info("[스케줄] 점심 뉴스 브리핑 시작")
    news = NewsScanner()
    result = await news.analyze()
    await telegram_service.send_daily_briefing("noon", result.get("summary", ""))


async def run_us_open_briefing():
    """23:30 미장 시작 감시"""
    from app.agents.us_sentinel import USSentinel
    from app.services import telegram_service
    logger.info("[스케줄] 미장 시작 감시")
    us = USSentinel()
    result = await us.analyze()
    await telegram_service.send_daily_briefing("us_open", result.get("summary", ""))


def start_scheduler():
    """스케줄러 시작"""
    # 06:00 미장 마감 브리핑
    scheduler.add_job(run_us_close_briefing, CronTrigger(hour=6, minute=0), id="us_close")
    # 07:00 오전 전략 브리핑
    scheduler.add_job(run_morning_briefing, CronTrigger(hour=7, minute=0), id="morning")
    # 12:00 점심 뉴스 브리핑
    scheduler.add_job(run_noon_briefing, CronTrigger(hour=12, minute=0), id="noon")
    # 23:30 미장 시작 감시
    scheduler.add_job(run_us_open_briefing, CronTrigger(hour=23, minute=30), id="us_open")

    scheduler.start()
    logger.info("스케줄러 시작 완료 (06:00 / 07:00 / 12:00 / 23:30)")


def stop_scheduler():
    """스케줄러 중지"""
    scheduler.shutdown()
    logger.info("스케줄러 중지")
