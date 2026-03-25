"""미국 시장 데이터 서비스
yfinance + Alpha Vantage
3대지수, VIX, 섹터ETF, 개별종목
"""
import logging
from datetime import datetime, timedelta

import httpx
import yfinance as yf

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

# 주요 티커
US_INDICES = {
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "dow": "^DJI",
    "vix": "^VIX",
}

SECTOR_ETFS = {
    "tech": "XLK",
    "healthcare": "XLV",
    "finance": "XLF",
    "energy": "XLE",
    "consumer": "XLY",
    "industrial": "XLI",
    "materials": "XLB",
    "utilities": "XLU",
    "realestate": "XLRE",
    "communication": "XLC",
    "staples": "XLP",
}


async def get_us_indices() -> dict:
    """미국 3대지수 + VIX 현재값"""
    result = {}
    for name, ticker in US_INDICES.items():
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            result[name] = {
                "price": round(info.last_price, 2),
                "prev_close": round(info.previous_close, 2),
                "change_pct": round(
                    (info.last_price - info.previous_close) / info.previous_close * 100, 2
                ),
            }
        except Exception as e:
            logger.error(f"US index {name} 조회 실패: {e}")
            result[name] = None
    return result


async def get_sector_etf_performance() -> dict:
    """섹터 ETF 수익률"""
    result = {}
    tickers_str = " ".join(SECTOR_ETFS.values())
    try:
        data = yf.download(
            tickers_str,
            period="5d",
            group_by="ticker",
            progress=False,
            threads=True,
        )
        for name, ticker in SECTOR_ETFS.items():
            try:
                closes = data[ticker]["Close"].dropna()
                if len(closes) >= 2:
                    change = (closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100
                    result[name] = {
                        "ticker": ticker,
                        "price": round(float(closes.iloc[-1]), 2),
                        "change_pct": round(float(change), 2),
                    }
            except Exception:
                result[name] = None
    except Exception as e:
        logger.error(f"섹터 ETF 조회 실패: {e}")
    return result


async def get_stock_history(ticker: str, period: str = "6mo") -> list[dict]:
    """미국 개별 종목 히스토리 (기술적 분석용)"""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period)
        results = []
        for date, row in df.iterrows():
            results.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })
        return results
    except Exception as e:
        logger.error(f"종목 {ticker} 히스토리 조회 실패: {e}")
        return []


async def get_stock_fundamentals(ticker: str) -> dict:
    """미국 종목 펀더멘털 (PER/PBR/PEG/ROE 등)"""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "ticker": ticker,
            "name": info.get("shortName", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "market_cap": info.get("marketCap", 0),
            "per": info.get("trailingPE", 0),
            "forward_per": info.get("forwardPE", 0),
            "pbr": info.get("priceToBook", 0),
            "peg": info.get("pegRatio", 0),
            "roe": info.get("returnOnEquity", 0),
            "eps": info.get("trailingEps", 0),
            "forward_eps": info.get("forwardEps", 0),
            "dividend_yield": info.get("dividendYield", 0),
            "52w_high": info.get("fiftyTwoWeekHigh", 0),
            "52w_low": info.get("fiftyTwoWeekLow", 0),
            "avg_volume": info.get("averageVolume", 0),
        }
    except Exception as e:
        logger.error(f"종목 {ticker} 펀더멘털 조회 실패: {e}")
        return {"ticker": ticker, "error": str(e)}


async def get_alpha_vantage_quote(ticker: str) -> dict:
    """Alpha Vantage 실시간 시세 (보조)"""
    settings = get_settings()
    if not settings.alpha_vantage_api_key:
        return {}

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "GLOBAL_QUOTE",
                "symbol": ticker,
                "apikey": settings.alpha_vantage_api_key,
            },
        )
        resp.raise_for_status()
        quote = resp.json().get("Global Quote", {})

    return {
        "ticker": ticker,
        "price": float(quote.get("05. price", 0)),
        "change": float(quote.get("09. change", 0)),
        "change_pct": quote.get("10. change percent", "0%"),
        "volume": int(quote.get("06. volume", 0)),
    }
