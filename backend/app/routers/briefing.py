"""매일 자동 브리핑 API"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/morning")
async def morning_briefing():
    """07:00 JKP 오전 전략 브리핑"""
    return {"status": "not_implemented"}


@router.get("/us-close")
async def us_close_briefing():
    """06:00 미장 마감 브리핑"""
    return {"status": "not_implemented"}


@router.get("/noon")
async def noon_briefing():
    """12:00 점심 뉴스 브리핑"""
    return {"status": "not_implemented"}


@router.get("/market-close")
async def market_close_briefing():
    """15:30 장마감 수급 정리"""
    return {"status": "not_implemented"}


@router.get("/us-open")
async def us_open_briefing():
    """23:30 미장 시작 감시"""
    return {"status": "not_implemented"}
