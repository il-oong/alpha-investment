"""보유종목 & 관심종목 관리 API"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/holdings")
async def get_holdings():
    """보유종목 조회 (매수가/목표가/손절가)"""
    return {"holdings": [], "status": "not_implemented"}


@router.get("/watchlist")
async def get_watchlist():
    """관심종목 조회"""
    return {"watchlist": [], "status": "not_implemented"}


@router.post("/watchlist/{ticker}")
async def add_to_watchlist(ticker: str):
    """관심종목 추가"""
    return {"ticker": ticker, "status": "not_implemented"}
