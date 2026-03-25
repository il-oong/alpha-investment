"""종목 즉시 분석 리포트 API"""
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/{ticker}")
async def analyze_stock(ticker: str):
    """종목 검색 후 15~30초 내 전체 분석 출력
    - 기술적: RSI / MACD / Stage / VCP
    - 펀더멘털: PER / PBR / PEG / CAN SLIM
    - 수급: 외인·기관 매매 동향
    - JKP: 매수구간 / 목표가 / 손절가
    - 종합점수 0~100점
    """
    return {"ticker": ticker, "status": "not_implemented"}
