"""종목 즉시 분석 리포트 API"""
from fastapi import APIRouter, Query

from app.agents.jkp_persona import JKPPersona
from app.agents.quant_engine import QuantEngine
from app.agents.fundamental_ai import FundamentalAI

router = APIRouter()
jkp = JKPPersona()
quant = QuantEngine()
fundamental = FundamentalAI()


@router.get("/{ticker}")
async def analyze_stock(
    ticker: str,
    market: str = Query("KR", description="KR 또는 US"),
):
    """종목 검색 후 전체 분석 출력 (JKP 통합 판단)
    - 기술적: RSI / MACD / Stage / VCP
    - 펀더멘털: PER / PBR / PEG / CAN SLIM
    - 수급: 외인·기관 매매 동향
    - JKP: 매수구간 / 목표가 / 손절가
    - 종합점수 0~100점
    """
    result = await jkp.analyze(ticker=ticker, market=market)
    return {"ticker": ticker, "market": market, "analysis": result}


@router.get("/{ticker}/technical")
async def analyze_technical(
    ticker: str,
    market: str = Query("KR"),
):
    """기술적 분석만 (빠른 조회)"""
    result = await quant.analyze(ticker=ticker, market=market)
    return {"ticker": ticker, "analysis": result}


@router.get("/{ticker}/fundamental")
async def analyze_fundamental(
    ticker: str,
    market: str = Query("KR"),
):
    """펀더멘털 분석만"""
    result = await fundamental.analyze(ticker=ticker, market=market)
    return {"ticker": ticker, "analysis": result}
