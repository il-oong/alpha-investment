"""보유종목 & 관심종목 관리 API"""
from fastapi import APIRouter

from app.services import supabase_service

router = APIRouter()
DEFAULT_USER = "default"


@router.get("/holdings")
async def get_holdings():
    """보유종목 조회 (매수가/목표가/손절가)"""
    holdings = await supabase_service.get_portfolio(DEFAULT_USER)
    return {"holdings": holdings}


@router.get("/watchlist")
async def get_watchlist():
    """관심종목 조회"""
    watchlist = await supabase_service.get_watchlist(DEFAULT_USER)
    return {"watchlist": watchlist}


@router.post("/watchlist/{ticker}")
async def add_to_watchlist(ticker: str, market: str = "KR", name: str = ""):
    """관심종목 추가"""
    result = await supabase_service.add_watchlist(DEFAULT_USER, ticker, market, name)
    return {"added": result}


@router.delete("/watchlist/{ticker}")
async def remove_from_watchlist(ticker: str):
    """관심종목 삭제"""
    await supabase_service.remove_watchlist(DEFAULT_USER, ticker)
    return {"removed": ticker}
